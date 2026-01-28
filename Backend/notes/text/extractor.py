import re
import bs4
import requests
import tempfile
import os
import time
import gc
from typing import Dict, List
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import (
    NarrativeText,
    Title,
    Image,
    Table,
    ListItem,
)

class DocumentChunkExtractor:
    """
    Robust PDF extractor using Unstructured.
    Downloads PDF temporarily, extracts structured chunks,
    then removes the temporary file.
    """

    def __init__(self, pdf_url: str, ocr: bool = False):
        """
        pdf_url: ArXiv or other PDF URL
        ocr: if True, apply OCR for scanned PDFs
        """
        self.pdf_url = pdf_url.replace("abs", "pdf")
        self.ocr = ocr

    # --------------------------------------------------
    # SAFE TEXT CLEANER
    # --------------------------------------------------
    def _clean_text(self, text: str) -> str:
        try:
            soup = bs4.BeautifulSoup(text, "html.parser")
            text = soup.get_text()
            text = re.sub(r"\n+", "\n", text)
            text = re.sub(r"[ \t]+", " ", text)
            text = re.sub(r"@xmath\d+", "", text)
            text = text.replace("<n>", "\n")
            return text.strip()
        except Exception:
            return text.strip()

    # --------------------------------------------------
    # CHUNK BUILDER (NORMALIZED SCHEMA)
    # --------------------------------------------------
    def _build_chunk(
        self,
        *,
        chunk_type: str,
        section: str,
        content: str = "",
        metadata: dict | None = None,
    ) -> dict:
        metadata = metadata or {}
        return {
            "id": f"{chunk_type}_{abs(hash((section, content))) % (10**10)}",
            "type": chunk_type,
            "section": section,
            "content": content,
            "page": metadata.get("page_number"),
            "confidence": metadata.get("confidence"),
            "metadata": metadata,
        }

    # --------------------------------------------------
    # SAFE FILE DELETION WITH RETRY
    # --------------------------------------------------
    def _safe_delete(self, filepath: str, max_attempts: int = 5):
        """Safely delete file with retry logic for Windows file locking"""
        for attempt in range(max_attempts):
            try:
                time.sleep(0.3)  # Small delay to let handles release
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"✅ Deleted temporary file: {filepath}")
                return True
            except PermissionError as e:
                if attempt < max_attempts - 1:
                    print(f"⚠️ Delete attempt {attempt + 1} failed, retrying...")
                    time.sleep(1)
                    gc.collect()  # Force garbage collection
                else:
                    print(f"❌ Could not delete {filepath}: {e}")
                    print(f"   Please delete manually if needed.")
                    return False
            except Exception as e:
                print(f"❌ Unexpected error deleting {filepath}: {e}")
                return False

    # --------------------------------------------------
    # MAIN EXTRACTION LOGIC
    # --------------------------------------------------
    def extract_chunks(self) -> Dict[str, List[dict]]:
        text_chunks = []
        image_chunks = []
        table_chunks = []
        other_chunks = []

        # ---- DOWNLOAD PDF TEMPORARILY ----
        tmp_dir = r"C:/Users/nshej/aisearch"
        os.makedirs(tmp_dir, exist_ok=True)  # ensure folder exists
        tmp_path = os.path.join(tmp_dir, "tmp_arxiv.pdf")
        
        # Download PDF
        try:
            response = requests.get(self.pdf_url)
            response.raise_for_status()
        except Exception as e:
            print(f"❌ Failed to download PDF: {e}")
            return {
                "text_chunks": [],
                "image_chunks": [],
                "table_chunks": [],
                "other_chunks": [],
            }

        # ---- WRITE PDF TO DISK (CLOSE FILE IMMEDIATELY) ----
        try:
            with open(tmp_path, "wb") as tmp:
                tmp.write(response.content)
            # File is now closed - this is critical!
            
        except Exception as e:
            print(f"❌ Failed to write PDF: {e}")
            return {
                "text_chunks": [],
                "image_chunks": [],
                "table_chunks": [],
                "other_chunks": [],
            }

        # ---- PDF PARTITION (file is closed now) ----
        elements = None
        try:
            elements = partition_pdf(
                filename=tmp_path,
                strategy="hi_res",
                extract_image_block_types=["Image", "Table"],  # Capture both images and tables as images
                extract_image_block_to_payload=True,           # Extract Base64
                infer_table_structure=True,
                ocr=self.ocr,
            )
        except Exception as e:
            print(f"❌ PDF partition failed: {e}")
            return {
                "text_chunks": [],
                "image_chunks": [],
                "table_chunks": [],
                "other_chunks": [],
            }
        finally:
            # Clean up: force garbage collection and delete temp file
            elements_copy = elements if elements else []
            elements = None
            gc.collect()
            
            # Safe deletion with retry logic
            self._safe_delete(tmp_path)

        # ---- PROCESS ELEMENTS ----
        current_section = "Introduction"

        for el in elements_copy:
            try:
                if isinstance(el, Title) and el.text:
                    current_section = self._clean_text(el.text)

                elif isinstance(el, (NarrativeText, ListItem)) and el.text:
                    text_chunks.append(
                        self._build_chunk(
                            chunk_type="text",
                            section=current_section,
                            content=self._clean_text(el.text),
                            metadata=el.metadata.to_dict() if el.metadata else {},
                        )
                    )

                elif isinstance(el, Image):
                    image_chunks.append(
                        self._build_chunk(
                            chunk_type="image",
                            section=current_section,
                            content=el.text or "",
                            metadata=el.metadata.to_dict() if el.metadata else {},
                        )
                    )

                elif isinstance(el, Table):
                    table_chunks.append(
                        self._build_chunk(
                            chunk_type="table",
                            section=current_section,
                            content=el.text or "",
                            metadata=el.metadata.to_dict() if el.metadata else {},
                        )
                    )

                else:
                    other_chunks.append(
                        self._build_chunk(
                            chunk_type="other",
                            section=current_section,
                            content=getattr(el, "text", "") or "",
                            metadata=el.metadata.to_dict() if el.metadata else {},
                        )
                    )

            except Exception:
                continue

        return {
            "text_chunks": text_chunks,
            "image_chunks": image_chunks,
            "table_chunks": table_chunks,
            "other_chunks": other_chunks,
        }
