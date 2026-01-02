from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.embeddings import Embeddings
from backend.notes.text.extractor import PDFTextExtractor
from backend.embedding.embedd import embed_string
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
from langchain_qdrant import QdrantVectorStore
client = QdrantClient(host="localhost", port=6333)


class CustomEmbedder(Embeddings):
    def embed_documents(self, texts):
        return [embed_string(t) for t in texts]
    def embed_query(self, text):
        return embed_string(text)

class TextPreprocessor:
    def __init__(self, pdf_url: str):
        self.pdf_url = pdf_url

    def text_preprocessing(self):
        cleaned_text = self.get_cleaned_text()
        chunks = self.split_text(cleaned_text)
        vector_store = self.vectorize_chunks(chunks)
        return vector_store

    def get_cleaned_text(self) -> str:
        
        extractor = PDFTextExtractor(self.pdf_url)
        return extractor.final_text()

    def split_text(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
            add_start_index=True
        )
        return text_splitter.split_text(text)

    def vectorize_chunks(self, chunks: list):
        docs = [
            Document(page_content=chunk, metadata={"source": self.pdf_url, "chunk_index": i})
            for i, chunk in enumerate(chunks)
        ]
        embeddings = CustomEmbedder()
        vector_store = QdrantVectorStore.from_documents(
            documents=docs,
            embedding=embeddings,
            url="http://localhost:6333",
            collection_name="pdf_chunks_cleaned",
            prefer_grpc=False
        )
        return vector_store

    def get_retriever(self):
        """Get retriever from vectorstore for QA chain"""
        vector_store = self.text_preprocessing()
        return vector_store.as_retriever(search_kwargs={"k": 4})
