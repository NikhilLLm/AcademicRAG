import fitz
from datetime import datetime
import json
import re
import pytesseract
from transformers import pipeline,BlipProcessor, BlipForConditionalGeneration
from PIL import Image
#FOR PDF
def extract_metadata(pdf_path_or_bytes):
    """Extract metadata from PDF. Accepts file path (str) or bytes."""
    from io import BytesIO
    
    # Handle both file path and bytes input
    if isinstance(pdf_path_or_bytes, bytes):
        doc = fitz.open(stream=BytesIO(pdf_path_or_bytes), filetype="pdf")
    else:
        doc = fitz.open(pdf_path_or_bytes)
    
    # Extract text from first 2 pages for better coverage
    first_page_blocks = doc[0].get_text("dict")["blocks"]
    second_page_blocks = doc[1].get_text("dict")["blocks"] if len(doc) > 1 else []
    
    title = extract_title(first_page_blocks)
    authors = extract_authors(first_page_blocks)
    abstract = extract_abstract(first_page_blocks, second_page_blocks)
    publication_date = extract_date(first_page_blocks)
    
    metadata = {
        "title": title,
        "abstract": abstract,
        "authors": authors,
        "publication_date": publication_date,
        
    }
    
    doc.close()
    return metadata


def extract_title(blocks):
    """Extract title - typically the largest font at the top of the page"""
    title_candidates = []
    
    for b in blocks[:10]:  # Check first 10 blocks only
        if b.get("type") != 0:  # Only text blocks
            continue
            
        for l in b.get("lines", []):
            y_pos = l["bbox"][1]  # Y position
            for s in l.get("spans", []):
                text = s["text"].strip()
                size = s["size"]
                
                # Title criteria: large font, reasonable length, near top
                if (size > 11 and 
                    len(text) > 15 and 
                    y_pos < 250 and
                    not text.isupper() or (text.isupper() and len(text) > 20)):
                    title_candidates.append({
                        "text": text,
                        "size": size,
                        "y_pos": y_pos
                    })
    
    if title_candidates:
        # Sort by size (desc) then y_pos (asc)
        title_candidates.sort(key=lambda x: (-x["size"], x["y_pos"]))
        
        # Combine multi-line titles
        best_title = title_candidates[0]["text"]
        best_y = title_candidates[0]["y_pos"]
        
        # Check if next line is continuation (similar y position, large font)
        for candidate in title_candidates[1:3]:
            if (abs(candidate["y_pos"] - best_y) < 30 and 
                candidate["size"] > 11):
                best_title += " " + candidate["text"]
        
        return best_title.strip()
    
    return ""


def extract_authors(blocks):
    """Extract authors - typically below title, may contain names, affiliations"""
    authors = []
    author_patterns = [
        r'^[A-Z][a-z]+\s+[A-Z][a-z]+',  # FirstName LastName
        r'^[A-Z]\.\s*[A-Z][a-z]+',  # F. LastName
        r'^[A-Z][a-z]+\s+[A-Z]\.',  # FirstName L.
    ]
    
    found_title = False
    potential_authors = []
    
    for b in blocks[:15]:
        if b.get("type") != 0:
            continue
            
        block_text = ""
        for l in b.get("lines", []):
            line_text = " ".join([s["text"] for s in l.get("spans", [])]).strip()
            block_text += line_text + " "
        
        block_text = block_text.strip()
        
        # Skip if it looks like title (very large font)
        max_size = max([s["size"] for l in b.get("lines", []) for s in l.get("spans", [])], default=0)
        if max_size > 16:
            found_title = True
            continue
        
        # Look for author patterns after title
        if found_title and block_text:
            # Check for common author patterns
            if any(re.search(pattern, block_text) for pattern in author_patterns):
                potential_authors.append(block_text)
            
            # Check for comma-separated names
            if "," in block_text and len(block_text.split()) < 30:
                # Split by commas and "and"
                parts = re.split(r',|\s+and\s+', block_text)
                for part in parts:
                    part = part.strip()
                    # Check if it looks like a name (2-4 words, starts with capital)
                    words = part.split()
                    if 2 <= len(words) <= 4 and words[0][0].isupper():
                        potential_authors.append(part)
    
    # Clean up and deduplicate
    seen = set()
    for author in potential_authors[:10]:  # Limit to first 10
        # Remove numbers, affiliations markers
        clean = re.sub(r'\d+|\*|†|‡', '', author).strip()
        clean = re.sub(r'\s+', ' ', clean)
        
        # Only keep if it looks like a name
        if clean and len(clean) > 3 and clean not in seen:
            authors.append(clean)
            seen.add(clean)
    
    return authors[:10]  # Return max 10 authors


def extract_abstract(first_page_blocks, second_page_blocks):
    """Extract abstract - look for explicit label or extract from beginning"""
    all_blocks = first_page_blocks + second_page_blocks
    
    # Method 1: Look for explicit "Abstract" label
    for i, b in enumerate(all_blocks):
        if b.get("type") != 0:
            continue
            
        block_text = ""
        for l in b.get("lines", []):   
            line_text = " ".join([s["text"] for s in l.get("spans", [])]).strip()
            block_text += line_text + " "
        
        block_text = block_text.strip()
        
        # Check if this block contains "Abstract"
        if re.search(r'\babstract\b', block_text, re.IGNORECASE):
            # Extract text after "Abstract"
            abstract_text = re.sub(r'.*?\babstract\b[:\s]*', '', block_text, flags=re.IGNORECASE)
            
            # Get next few blocks if abstract continues
            for next_b in all_blocks[i+1:i+5]:
                if next_b.get("type") != 0:
                    continue
                next_text = ""
                for l in next_b.get("lines", []):
                    next_text += " ".join([s["text"] for s in l.get("spans", [])]).strip() + " "
                
                # Stop if we hit section headers
                if re.search(r'\b(introduction|keywords|1\.|I\.)\b', next_text, re.IGNORECASE):
                    break
                abstract_text += " " + next_text.strip()
            
            abstract_text = clean_text(abstract_text)
            if len(abstract_text) > 50:
                return abstract_text[:1000]  # Limit length
    
    # Method 2: If no explicit abstract, extract first substantial text block
    for i, b in enumerate(first_page_blocks):
        if b.get("type") != 0:
            continue
        
        y_pos = b["bbox"][1]
        if y_pos < 150:  # Skip title area
            continue
            
        block_text = ""
        for l in b.get("lines", []):
            line_text = " ".join([s["text"] for s in l.get("spans", [])]).strip()
            block_text += line_text + " "
        
        block_text = clean_text(block_text)
        
        # Look for substantial paragraph
        if len(block_text) > 100 and not re.search(r'\b(university|department|email)\b', block_text, re.IGNORECASE):
            return block_text[:800] + "..."
    
    return ""


def extract_date(blocks):
    """Try to extract publication date, fallback to current date"""
    date_patterns = [
        r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
        r'\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',
        r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',
    ]
    
    for b in blocks[:5]:
        if b.get("type") != 0:
            continue
        
        block_text = ""
        for l in b.get("lines", []):
            line_text = " ".join([s["text"] for s in l.get("spans", [])]).strip()
            block_text += line_text + " "
        
        for pattern in date_patterns:
            match = re.search(pattern, block_text, re.IGNORECASE)
            if match:
                return match.group(0)
    
    return datetime.now().strftime("%Y-%m-%d")


def clean_text(text):
    """Clean extracted text"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove hyphenation at line breaks
    text = re.sub(r'-\s+', '', text)
    return text.strip()


#FOR IMAGE

#image preprocessing before ocr

def preprocess_image(image_path: str) -> Image.Image:
    """Preprocess image for better OCR results."""
    image = Image.open(image_path).convert("L")  # Convert to grayscale
    # Resize image if too small
    if image.width < 800:
        new_height = int((800 / image.width) * image.height)
        image = image.resize((800, new_height), Image.ANTIALIAS)
    # Apply binary threshold
    threshold = 180
    image = image.point(lambda p: p > threshold and 255)
    return image

# ✅ Use lightweight distilbart model to save memory (consistent with notes summarizer)
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-6-6")
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:/Users/nshej/AppData/Local/Programs/Tesseract-OCR/tesseract.exe"

def extract_text_from_image(image_path_or_bytes) -> str:
    """Return a single combined description string from OCR + BLIP for embedding.
    Accepts file path (str) or bytes.
    """
    from io import BytesIO
    
    # Handle both file path and bytes input
    if isinstance(image_path_or_bytes, bytes):
        image = Image.open(BytesIO(image_path_or_bytes)).convert("RGB")
    else:
        if not image_path_or_bytes or image_path_or_bytes.strip() == "":
            raise ValueError("Image path is not provided.")
        image = Image.open(image_path_or_bytes).convert("RGB")

    # --- OCR ---
    ocr_text = pytesseract.image_to_string(image).strip()

    summary = ""
    if ocr_text:
        try:
            summary = summarizer(ocr_text, max_length=80, min_length=30, do_sample=False)[0]['summary_text']
        except Exception:
            summary = ocr_text  # fallback if summarizer fails

    # --- BLIP caption ---
    inputs = processor(images=image, return_tensors="pt")
    out = blip_model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)

    # --- Combined description (single string) ---
    description = f"OCR summary: {summary}. Visual caption: {caption}."

    return description

#FOR TEXT 

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base")
import re
def enhance_text_query(user_input: str) -> dict:
    prompt = f"Rewrite this query into a detailed academic research description: {user_input}"
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_length=128)
    #extraacting authors name from the user input 
    result = re.search(r'(?:author|by)\s+([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z\.]*)*)', user_input)
    author=result.group(1) if result else None

    return {
        "enhanced_text": tokenizer.decode(outputs[0], skip_special_tokens=True),
        "author": author
    }