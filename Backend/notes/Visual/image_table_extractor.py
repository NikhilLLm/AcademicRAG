import fitz
import requests
import re
import os
import tempfile
import camelot
import pandas as pd
class ImageTableExtractor:
    def __init__(self, pdf_url: str):
        self.pdf_url = pdf_url.replace("abs", "pdf")
    
    # --------------------------------------------------
    # PUBLIC ENTRY POINT
    # --------------------------------------------------
    def extracted_text(self):
       visuals, text_blocks = self.extract_images()
       enriched_visuals = []

       for v in visuals:
           ev = self.match_caption_and_context(v, text_blocks)
           ev_cleaned = {}
       
           for k, val in ev.items():
               if k in {"bbox", "data"}:
                   continue
               if val is None:
                   continue
               if isinstance(val, str) and len(val) > 800:
                   continue
       
               ev_cleaned[k] = val
       
           enriched_visuals.append(ev_cleaned)
       
       # -------- CLEAN TABLES --------
       raw_tables = self.extract_tables()
       clean_tables = []
       
       for t in raw_tables:
           clean_tables.append({
               "type": "table",
               "id": t["id"],
               "page": t["page"],
               "summary": f"Table compares models, datasets, or evaluation metrics with approx accuracy {t.get('accuracy', 'N/A')}."
           })
       
       return enriched_visuals + clean_tables

    # --------------------------------------------------
    # PASS 1: COLLECT VISUALS + ALL TEXT BLOCKS
    # --------------------------------------------------
    def extract_images(self):
        """Extract image/drawing visuals + ALL text blocks"""

        content = requests.get(self.pdf_url).content
        doc = fitz.open(stream=content, filetype="pdf")

        visuals = []
        text_blocks = []
        visual_count = 1

        # -------- PASS 1A: COLLECT TEXT BLOCKS --------
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            blocks = page.get_text("dict")["blocks"]
            
            for b in blocks:
                if b["type"] == 0:  # Text block
                    text = ""
                    for line in b.get("lines", []):
                        for span in line.get("spans", []):
                            text += span.get("text", "") + " "
                    
                    text = text.strip()
                    if text:
                        text_blocks.append({
                            "text": text,
                            "page": page_num + 1,
                            "bbox": b["bbox"]
                        })

        # -------- PASS 1B: COLLECT VISUAL BLOCKS --------
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            blocks = page.get_text("dict")["blocks"]
            
            for b in blocks:
                # Images + drawings (tables are drawings in PDFs)
                if b["type"] in (1, 2):
                    visuals.append({
                        "type": "visual",
                        "id": f"Visual_{visual_count}",
                        "page": page_num + 1,
                        "bbox": b["bbox"]
                    })
                    visual_count += 1

        return visuals, text_blocks

    # --------------------------------------------------
    # PASS 2: CAPTION + CONTEXT MATCHING
    # --------------------------------------------------
    def match_caption_and_context(self, visual, text_blocks):
        """Match caption (below) and context (above)"""

        visual_top = visual["bbox"][1]
        visual_bottom = visual["bbox"][3]
        visual_left = visual["bbox"][0]
        visual_right = visual["bbox"][2]
        page = visual["page"]

        caption = ""
        context = ""

        min_caption_dist = float("inf")
        min_context_dist = float("inf")

        caption_patterns = [
            r'^(figure|fig\.?|table|tbl\.?)\s*\d+',
            r'^(figure|fig\.?|table|tbl\.?)\s*[ivxlcdm]+',
        ]

        visual_width = max(visual_right - visual_left, 1)

        for block in text_blocks:
            if block["page"] != page:
                continue

            text = block["text"].strip()
            if not text:
                continue

            bbox = block["bbox"]
            block_top = bbox[1]
            block_bottom = bbox[3]
            block_left = bbox[0]
            block_right = bbox[2]

            # Horizontal overlap ratio
            overlap = min(visual_right, block_right) - max(visual_left, block_left)
            horizontal_overlap = max(overlap / visual_width, 0)

            # ---------- CAPTION (BELOW) ----------
            if block_top > visual_bottom and horizontal_overlap > 0.3:
                if any(re.match(p, text.lower()) for p in caption_patterns):
                    dist = block_top - visual_bottom
                    if dist < min_caption_dist and dist < 120:
                        caption = text
                        min_caption_dist = dist

            # ---------- CONTEXT (ABOVE) ----------
            if block_bottom < visual_top and horizontal_overlap > 0.2:
                dist = visual_top - block_bottom
                if dist < min_context_dist and dist < 350:
                    if len(text) > 30 and not text.isupper():
                        context = text
                        min_context_dist = dist

        visual["caption"] = caption
        visual["context"] = context
        return visual
    
    #---------------------------------------------------
    # 3.Table Extraxctioon
    #---------------------------------------------------
   
    def extract_tables(self):
        pdf_bytes = requests.get(self.pdf_url).content
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_bytes)
            pdf_path = f.name
        
        try:
            tables = camelot.read_pdf(
                pdf_path, 
                pages="all", 
                flavor="stream",
                edge_tol=50,
                row_tol=15
            )
    
            results = []
            seen = set()
            
            for i, table in enumerate(tables):
                # Skip low-accuracy tables
                if table.parsing_report['accuracy'] < 80:  # Adjust threshold
                    continue
                    
                df = table.df
                
                # Clean and validate
                df = df.replace('', pd.NA).dropna(how='all').dropna(axis=1, how='all')
                
                if df.empty or df.shape[0] < 2 or df.shape[1] < 2:
                    continue
                
                key = (table.page, df.shape)
                if key in seen:
                    continue
                seen.add(key)
            
                results.append({
                    "type": "table",
                    "id": f"Table_{len(results)+1}",
                    "page": table.page,
                    "accuracy": table.parsing_report['accuracy'],
                    "data": df.to_dict()
                })
                
            return results
        finally:
            os.remove(pdf_path)
    
    # --------------------------------------------------
    # OPTIONAL: CAPTION STRUCTURING
    # --------------------------------------------------
    def extract_caption_details(self, caption: str):
        if not caption:
            return {"label": "", "description": ""}

        match = re.match(
            r'^((?:figure|fig\.?|table|tbl\.?)\s*\d+[:\.\-\s]+)(.*)',
            caption, re.IGNORECASE
        )

        if match:
            return {
                "label": match.group(1).strip(),
                "description": match.group(2).strip()
            }
        return {"label": "", "description": caption}
