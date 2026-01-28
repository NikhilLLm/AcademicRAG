import os
import time
import gc
from typing import Literal
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.image import partition_image
from unstructured.documents.elements import (
    Title,
    NarrativeText,
    Text,
)
from langchain_core.prompts import PromptTemplate
from Backend.models.hugging_face import hugging_face_query_expand
import re

# --------------------------------------------------
# SAFE FILE DELETE (WINDOWS FRIENDLY)
# --------------------------------------------------
query_enhancement_prompt = PromptTemplate.from_template(
    """
    Rewrite the following search query into a concise academic-style description.

    Rules:
    - Preserve original intent
    - Add relevant technical keywords and synonyms
    - Do NOT invent experiments or results
    - Suitable for academic search engines

    Query: {user_input} """)
def _safe_delete(filepath: str, max_attempts: int = 5) -> None:
    for _ in range(max_attempts):
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
            return
        except PermissionError:
            time.sleep(0.5)
            gc.collect()

# --------------------------------------------------
# CORE TEXT EXTRACTION
# --------------------------------------------------
def extract_text_for_search(
    file_bytes: bytes,
    file_type: Literal["pdf", "image"],
    tmp_dir: str = None,  # If None, uses system temp
) -> str:
    """
    Extract compact academic-style text from PDF or Image
    for embedding-based semantic retrieval.
    Uses hugging_face_query_expand for proper query/text enhancement.
    
    What changed:
    - Removed hardcoded path C:/Users/nshej/aisearch
    - Now uses system temp directory by default
    """
    import tempfile
    
    if tmp_dir is None:
        tmp_dir = tempfile.gettempdir()
    
    os.makedirs(tmp_dir, exist_ok=True)

    # ---------------- PDF ----------------
    if file_type == "pdf":
        tmp_path = os.path.join(tmp_dir, "tmp_doc.pdf")

        with open(tmp_path, "wb") as f:
            f.write(file_bytes)

        try:
            elements = partition_pdf(
                filename=tmp_path,
                strategy="fast",
                ocr=False
            )

            text_chunks = [
                el.text.strip()
                for el in elements
                if isinstance(el, (Title, NarrativeText, Text))
                and el.text
                and el.text.strip()
            ]

            if not text_chunks:
                raise ValueError("No extractable text found in PDF")

            extracted_text = " ".join(text_chunks)

            if len(extracted_text) < 100:
                raise ValueError("PDF text too short for semantic search")

            # Use query expansion instead of summarization
            enhanced_text = hugging_face_query_expand(
                text=extracted_text
            )

            if not enhanced_text or not enhanced_text.strip():
                raise ValueError("Query expansion failed")

            return enhanced_text.strip()

        finally:
            _safe_delete(tmp_path)

    # ---------------- IMAGE ----------------
    else:
        tmp_path = os.path.join(tmp_dir, "tmp_img.jpg")

        with open(tmp_path, "wb") as f:
            f.write(file_bytes)

        try:
            elements = partition_image(
                filename=tmp_path,
                strategy="hi_res"
            )

            text_chunks = [
                el.text.strip()
                for el in elements
                if hasattr(el, "text")
                and el.text
                and el.text.strip()
            ]

            if not text_chunks:
                raise ValueError("No text detected in image")

            extracted_text = " ".join(text_chunks)

            if len(extracted_text) < 50:
                raise ValueError("OCR text too short for semantic search")

            # Use query expansion instead of summarization
            enhanced_text = hugging_face_query_expand(
                text=extracted_text
            )

            if not enhanced_text or not enhanced_text.strip():
                raise ValueError("Query expansion failed")

            return enhanced_text.strip()

        finally:
            _safe_delete(tmp_path)

# --------------------------------------------------
# TEXT QUERY ENHANCEMENT
# --------------------------------------------------
def enhance_text_query(user_input: str) -> dict:
    """
    Enhance a user query for embedding-based semantic search.
    Preserves author detection and expands query with technical keywords.
    """
    if not user_input or not user_input.strip():
        raise ValueError("User input is empty")

    # Expand query using hugging_face_query_expand
    enhanced_text = hugging_face_query_expand(
        text=user_input
    )

    # Detect author if mentioned in query
    author_match = re.search(
        r'(?:author|by)\s+([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z\.]*)*)',
        user_input
    )

    return {
        "enhanced_text": enhanced_text,
        "author": author_match.group(1) if author_match else None
    }
