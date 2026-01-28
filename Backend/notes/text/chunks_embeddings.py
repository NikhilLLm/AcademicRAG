import hashlib
import uuid
import traceback
import logging
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.embeddings import Embeddings
from Backend.notes.text.extractor import DocumentChunkExtractor
from Backend.embedding.embed_local import embed_string_small
from langchain_qdrant import QdrantVectorStore
from qdrant_client.models import Distance, VectorParams, SparseVectorParams, SparseIndexParams
from Backend.models.groq import groq_llm
from Backend.models.prompts import BATCH_PROMPT_1
from Backend.database.qdrant_client import get_qdrant_client, get_collection_name, get_collection_name
from Backend.notes.text.model import summarize_chain
from Backend.notes.Visual.vision_service import describe_image
from collections import defaultdict
import time

# ------------------- Logging Setup -------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

# ------------------- Qdrant Client - Centralized -------------------
client = get_qdrant_client()

def generate_pdf_id(pdf_url: str)->str:
    """"Generating unique id for pdf"""
    return hashlib.md5(pdf_url.encode()).hexdigest()[:16]

class CustomEmbedder(Embeddings):
    def embed_documents(self, texts):
        embeddings=[]
        for text in texts:
            result=embed_string_small(text)
            dense=result["dense_embedding"]
            embeddings.append(dense)
        return embeddings

    def embed_query(self, text):
        result=embed_string_small(text)
        return result["dense_embedding"]


class TextPreprocessor:
    def __init__(self, pdf_url: str):
        self.pdf_url = pdf_url
        self.pdf_id=generate_pdf_id(pdf_url)
        self.embedder = CustomEmbedder()
        self.collection_name = get_collection_name("pdf_vectors_v2")
    def extraction(self):
        try:
            logging.info("Starting PDF processing pipeline...")
            extracted = self._extract_chunks()
            return extracted
        except Exception as e:
            logging.error("Error in processing PDF: %s", str(e))
            traceback.print_exc()
            return None

    def process_pdf(self):
        try:
            extracted=self.extraction()
            if extracted is None:
                raise ValueError("PDF extraction failed")
            
            # --- PROCESS IMAGES & TABLES ---
            visual_chunks = extracted.get("image_chunks", []) + extracted.get("table_chunks", [])
            logging.info(f"Processing {len(visual_chunks)} visual elements with Vision Model...")
            
            processed_visuals = []
            for v_chunk in visual_chunks:
                # 1. Get Base64
                base64_data = v_chunk.get("metadata", {}).get("image_base64")
                if not base64_data:
                    continue
                
                # 2. Generate Description
                logging.info(f"Generating description for visual chunk {v_chunk['id']}...")
                description = describe_image(base64_data)
                
                # 3. Create a text-like chunk, but keep the base64 in metadata
                v_chunk["content"] = f"<figure_description>{description}</figure_description>"
                v_chunk["type"] = "visual" # mark it
                processed_visuals.append(v_chunk)
            
            # Combine text and visual chunks - PRIORITIZE VISUALS
            all_raw_chunks = processed_visuals + extracted["text_chunks"]
            
            merged_chunks = self._token_aware_merge(all_raw_chunks)
            summary_docs = self._summarize_and_prepare_docs(merged_chunks)
            vector_store = self._store_in_qdrant(summary_docs)
            logging.info("PDF processing completed successfully.")
            return vector_store

        except Exception as e:
            logging.error("Error in processing PDF: %s", str(e))
            traceback.print_exc()
            return None

    # ---------- Extraction ----------
    def _extract_chunks(self):
        try:
            logging.info("Extracting chunks from PDF...")
            extractor = DocumentChunkExtractor(self.pdf_url)
            chunks = extractor.extract_chunks()
            logging.info(
                "Extraction done: %d text chunks, %d image chunks, %d table chunks, %d other chunks",
                len(chunks["text_chunks"]),
                len(chunks.get("image_chunks", [])),
                len(chunks.get("table_chunks", [])),
                len(chunks.get("other_chunks", []))
            )
            return chunks
        except Exception as e:
            logging.error("Failed to extract chunks: %s", str(e))
            traceback.print_exc()
            return {
                "text_chunks": [],
                "image_chunks": [],
                "table_chunks": [],
                "other_chunks": []
            }

    # ---------- Token-aware merging ----------
    def _token_aware_merge(self, chunks, max_tokens=800):
        logging.info("Starting token-aware merging of chunks...")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_tokens,
            chunk_overlap=100,
            separators=["\n\n### ","\n\n", "\n", " ", ""],#first one is for section header
        )
        merged = []
        try:
            for chunk in chunks:
                text = chunk.get("content", "")
                if text.strip():
                    split_texts = splitter.split_text(text)
                    for st in split_texts:
                        merged.append({
                            "text": st,
                            "source": chunk.get("source", self.pdf_url),
                            "section": chunk.get("section", ""),
                            "chunk_id": chunk.get("id", str(uuid.uuid4())),
                            "image_base64": chunk.get("metadata", {}).get("image_base64", None), # ✅ Pass through
                            "original_type": chunk.get("type", "text")
                        })
            logging.info("Merging done. Total merged chunks: %d", len(merged))
        except Exception as e:
            logging.error("Error during token-aware merging: %s", str(e))
            traceback.print_exc()
        return merged
    #---------------------filtering chunks from section ------------
    
    def _limit_chunks_per_section(
        self,
        merged_chunks,
        max_per_section=7,
        max_total_chunks=100
    ):
        """
        Limits how many chunks per section go forward.
        This drastically reduces LLM + embedding load.
        """
    
        section_counts = defaultdict(int)
        filtered = []
    
        for chunk in merged_chunks:
            section = chunk.get("section") or "UNKNOWN"
    
            # per-section cap
            if section_counts[section] >= max_per_section:
                continue
    
            filtered.append(chunk)
            section_counts[section] += 1
    
            # global hard stop
            if len(filtered) >= max_total_chunks:
                break
    
        logging.info(
            "Chunk limiting applied | Before=%d After=%d Sections=%d",
            len(merged_chunks),
            len(filtered),
            len(section_counts)
        )
    
        return filtered

    # ---------- Summarize (IN MEMORY ONLY) ----------
    def _summarize_and_prepare_docs(self, merged_chunks):
        logging.info("Generating summaries for merged chunks...")
        docs = []
        try:
            merged_chunks=self._limit_chunks_per_section(merged_chunks)
            for idx, chunk in enumerate(merged_chunks, 1):
                logging.info("Summarizing chunk %d/%d", idx, len(merged_chunks))
                
                summary = groq_llm(text=chunk["text"],MODEL_NAME="llama-3.1-8b-instant",max_token=50,temperature=0.2,prompt_template=BATCH_PROMPT_1)
                docs.append(
                    Document(
                        page_content=summary,
                        metadata={
                            "source": chunk["source"],
                            "chunk_id": chunk["chunk_id"],
                            "section": chunk["section"],
                            "type": "text_summary",
                            "pdf_id":self.pdf_id,
                            "pdf_url":self.pdf_url,
                            "image_base64": chunk.get("image_base64"), # ✅ Persist to Doc metadata
                            "original_type": chunk.get("original_type")
                        }
                    )
                )
                time.sleep(0.6)
            logging.info("Summarization completed. Total summary docs: %d", len(docs))
        except Exception as e:
            logging.error("Error during summarization: %s", str(e))
            traceback.print_exc()
        return docs

    # ---------- Vector Store ----------
    def _store_in_qdrant(self, docs):
        try:
            logging.info(f"Storing hybrid embeddings for PDF ID: {self.pdf_id}")
            #step1: get embeddin dimensions
            test_result=embed_string_small("test")
            dense_dim=len(test_result["dense_embedding"])
            logging.info(f"Dense embedding dimension: {dense_dim}")
            try:
                client.get_collection(self.collection_name)
                logging.info(f"Collection '{self.collection_name}' already exists. Bypassing creation.")
            except Exception:
                  logging.info(f"Creating new collection '{self.collection_name}' with hybrid search (Dim: {dense_dim})")
                  client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={
                        "dense": VectorParams(
                            size=dense_dim,
                            distance=Distance.COSINE
                        )
                    },
                    sparse_vectors_config={
                        "sparse": SparseVectorParams(
                            index=SparseIndexParams()
                        )
                    }
                )
            points=[]
            for idx,doc in enumerate(docs):
                logging.info(f"Processing document {idx + 1}/{len(docs)}")
                embedding_result = embed_string_small(doc.page_content)
                point = {
                    "id": str(uuid.uuid4()),
                    "vector": {
                        "dense": embedding_result["dense_embedding"],
                        "sparse": {
                            "indices": embedding_result["sparse_embedding"]["indices"],
                            "values": embedding_result["sparse_embedding"]["values"]
                        }
                    },
                    "payload": {
                        "page_content": doc.page_content,
                        "pdf_id": self.pdf_id,  # ← Critical: Store PDF ID
                        "pdf_url": self.pdf_url,
                        "chunk_id": doc.metadata.get("chunk_id"),
                        "section": doc.metadata.get("section"),
                        "source": doc.metadata.get("source"),
                        "type": doc.metadata.get("type"),
                        "image_base64": doc.metadata.get("image_base64"), # ✅ Persist to Payload
                        "original_type": doc.metadata.get("original_type")
                    }
                }
                points.append(point)
                # client.create_payload_index(
                #     collection_name=self.collection_name,
                #     field_name="pdf_id",
                #     field_schema=PayloadSchemaType.KEYWORD
                # ) # DO NOT USE THIS IT GIVES O(N^2) TIME COMPLEXITY

            #step 4
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
                logging.info(f"Uploaded batch {i // batch_size + 1}/{(len(points) + batch_size - 1) // batch_size}")
            
            # Step 5: Create LangChain wrapper (for compatibility, optional)
            vector_store = QdrantVectorStore(
                client=client,
                collection_name=self.collection_name,
                embedding=self.embedder,
                vector_name="dense",
            )
            
            logging.info(f"✅ Hybrid storage completed for PDF ID: {self.pdf_id}")
            return vector_store
        except Exception as e:
            logging.error("Failed to store in Qdrant: %s", str(e))
            traceback.print_exc()
            return None
