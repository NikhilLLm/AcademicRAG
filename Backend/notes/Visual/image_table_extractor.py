import fitz
import requests
import re
import os
import tempfile
import camelot
import pandas as pd

FIGURE_REGEX = re.compile(
    r'^(figure|fig\.?|table|tbl\.?)\s*(\d+|[ivxlcdm]+)',
    re.IGNORECASE
)

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

            ev["usefulness_score"] = self.score_figure(ev)

            # ---- HARD FILTER: only pass useful figures ----
            if ev["usefulness_score"] >= 0.5:
                ev_cleaned = {
                    k: v for k, v in ev.items()
                    if k not in {"bbox"} and v is not None
                }
                enriched_visuals.append(ev_cleaned)

        # -------- TABLE EXTRACTION --------
        raw_tables = self.extract_tables()
        clean_tables = []

        for t in raw_tables:
            t["usefulness_score"] = self.score_table(t)

            if t["usefulness_score"] >= 0.6:
                clean_tables.append({
                    "type": "table",
                    "id": t["id"],
                    "page": t["page"],
                    "columns": t["columns"],
                    "rows": t["rows"],
                    "confidence": t["accuracy"],
                    "usefulness_score": t["usefulness_score"]
                })

        return {
            "figures": enriched_visuals,
            "tables": clean_tables
        }

    # --------------------------------------------------
    # PASS 1: EXTRACT VISUALS + TEXT
    # --------------------------------------------------
    def extract_images(self):
        content = requests.get(self.pdf_url).content
        doc = fitz.open(stream=content, filetype="pdf")

        visuals = []
        text_blocks = []
        visual_count = 1

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            blocks = page.get_text("dict")["blocks"]

            for b in blocks:
                if b["type"] == 0:
                    text = " ".join(
                        span["text"]
                        for line in b.get("lines", [])
                        for span in line.get("spans", [])
                    ).strip()

                    if text:
                        text_blocks.append({
                            "text": text,
                            "page": page_num + 1,
                            "bbox": b["bbox"]
                        })

                elif b["type"] in (1, 2):
                    visuals.append({
                        "type": "figure",
                        "id": f"Visual_{visual_count}",
                        "page": page_num + 1,
                        "bbox": b["bbox"]
                    })
                    visual_count += 1

        return visuals, text_blocks

    # --------------------------------------------------
    # PASS 2: CAPTION + CONTEXT
    # --------------------------------------------------
    def match_caption_and_context(self, visual, text_blocks):
        vt, vb, vl, vr = visual["bbox"][1], visual["bbox"][3], visual["bbox"][0], visual["bbox"][2]
        vw = max(vr - vl, 1)
        page = visual["page"]

        caption, context = "", ""
        cap_dist, ctx_dist = float("inf"), float("inf")

        for block in text_blocks:
            if block["page"] != page:
                continue

            text = block["text"].strip()
            bt, bb, bl, br = block["bbox"][1], block["bbox"][3], block["bbox"][0], block["bbox"][2]

            overlap = min(vr, br) - max(vl, bl)
            overlap_ratio = max(overlap / vw, 0)

            # ---- CAPTION ----
            if bt > vb and overlap_ratio > 0.3:
                m = FIGURE_REGEX.match(text)
                if m:
                    dist = bt - vb
                    if dist < cap_dist and dist < 120:
                        caption = text
                        visual["figure_label"] = m.group(0).strip()
                        visual["figure_number"] = m.group(2)
                        visual["id"] = m.group(0).replace(" ", "_").capitalize()
                        cap_dist = dist

            # ---- CONTEXT ----
            if bb < vt and overlap_ratio > 0.2:
                dist = vt - bb
                if dist < ctx_dist and dist < 350 and len(text) > 40:
                    context = text
                    ctx_dist = dist

        visual["caption"] = caption
        visual["context"] = context
        visual["caption_confidence"] = 0.9 if caption else 0.0
        visual["context_confidence"] = 0.6 if context else 0.0
        visual["text_density"] = len((caption + context).split())

        return visual

    # --------------------------------------------------
    # TABLE EXTRACTION (SECURE)
    # --------------------------------------------------
    def extract_tables(self):
        pdf_bytes = requests.get(self.pdf_url).content
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_bytes)
            pdf_path = f.name

        try:
            tables = camelot.read_pdf(pdf_path, pages="all", flavor="stream")
            results, seen = [], set()

            for table in tables:
                acc = table.parsing_report["accuracy"]
                if acc < 85:
                    continue

                df = table.df.replace("", pd.NA).dropna(how="all").dropna(axis=1, how="all")
                if df.shape[0] < 3 or df.shape[1] < 2:
                    continue

                numeric_ratio = df.map(
                    lambda x: str(x).replace('.', '', 1).isdigit()
                ).sum().sum() / (df.shape[0] * df.shape[1])

                if numeric_ratio < 0.3:
                    continue

                key = (table.page, df.shape)
                if key in seen:
                    continue
                seen.add(key)

                results.append({
                    "type": "table",
                    "id": f"Table_{len(results)+1}",
                    "page": table.page,
                    "accuracy": acc,
                    "rows": df.shape[0],
                    "columns": list(df.columns)
                })

            return results
        finally:
            os.remove(pdf_path)

    # --------------------------------------------------
    # SCORING
    # --------------------------------------------------
    def score_figure(self, v):
        score = 0.0
        if v.get("caption"): score += 0.4
        if v.get("context"): score += 0.3
        if v.get("text_density", 0) > 40: score += 0.2
        if "architecture" in (v.get("caption","") + v.get("context","")).lower():
            score += 0.1
        return round(min(score, 1.0), 2)

    def score_table(self, t):
        score = 0.4 if t["accuracy"] >= 90 else 0.2
        score += 0.2 if t["rows"] >= 5 else 0
        score += 0.2 if len(t["columns"]) >= 3 else 0
        score += 0.2
        return round(min(score, 1.0), 2)
