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
    tmp_dir: str = r"C:/Users/nshej/aisearch",
) -> str:
    """
    Extract compact academic-style text from PDF or Image
    for embedding-based semantic retrieval.
    Uses hugging_face_query_expand for proper query/text enhancement.
    """
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



# def preprocess_image(image_path: str) -> Image.Image:
#     """Preprocess image for better OCR results."""
#     image = Image.open(image_path).convert("L")  # Convert to grayscale
#     # Resize image if too small
#     if image.width < 800:
#         new_height = int((800 / image.width) * image.height)
#         image = image.resize((800, new_height), Image.ANTIALIAS)
#     # Apply binary threshold
#     threshold = 180
#     image = image.point(lambda p: p > threshold and 255)
#     return image

# # ✅ Use lightweight distilbart model to save memory (consistent with notes summarizer)

# processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
# blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

# # Set Tesseract path
# pytesseract.pytesseract.tesseract_cmd = r"C:/Users/nshej/AppData/Local/Programs/Tesseract-OCR/tesseract.exe"

# def extract_text_from_image(image_path_or_bytes) -> str:
#     """Return a single combined description string from OCR + BLIP for embedding.
#     Accepts file path (str) or bytes.
#     """
#     from io import BytesIO
    
#     # Handle both file path and bytes input
#     if isinstance(image_path_or_bytes, bytes):
#         image = Image.open(BytesIO(image_path_or_bytes)).convert("RGB")
#     else:
#         if not image_path_or_bytes or image_path_or_bytes.strip() == "":
#             raise ValueError("Image path is not provided.")
#         image = Image.open(image_path_or_bytes).convert("RGB")

#     # --- OCR ---
#     ocr_text = pytesseract.image_to_string(image).strip()

#     summary = ""
#     if ocr_text:
#         try:
#             response=requests.post(f"{BASE_URL}/short", data={"text": ocr_text})
#             summary = response.json()["short_notes"]
#         except Exception:
#             summary = ocr_text  # fallback if summarizer fails

#     # --- BLIP caption ---
#     inputs = processor(images=image, return_tensors="pt")
#     out = blip_model.generate(**inputs)
#     caption = processor.decode(out[0], skip_special_tokens=True)

#     # --- Combined description (single string) ---
#     description = f"OCR summary: {summary}. Visual caption: {caption}."

#     return description

#FOR TEXT 

