from huggingface_hub import InferenceClient 
from Backend.notes.Visual.image_table_extractor import ImageTableExtractor 
from dotenv import load_dotenv 
import os 
import json 
 
load_dotenv("C:/Users/nshej/aisearch/.env") 
 
HF_TOKEN = os.getenv("HF_TOKEN") 
 
client = InferenceClient( 
    model="mistralai/Mistral-7B-Instruct-v0.2", 
    token=HF_TOKEN,

) 


def normalize_visual_notes(visual_notes: str):
    """
    Light cleanup ONLY.
    - Removes markdown bullets/headings
    - Preserves uncertainty, qualifiers, and factual statements
    - Does NOT drop semantic lines
    """
    lines = visual_notes.split("\n")
    clean = []

    for l in lines:
        l = l.strip()
        if not l:
            continue

        # Remove markdown bullets/headings only
        l = l.lstrip("-•# ").strip()

        clean.append(l)

    return "\n".join(clean)

def format_visual_evidence(figures: list, tables: list) -> str:
    """
    Format visual evidence into structured narrative input for LLM.
    Preserves metadata for confidence gating in merge phase.
    """
    data_text = ""
    
    if figures:
        data_text += "FIGURES (WITH CONFIDENCE METADATA):\n"
        data_text += "-" * 60 + "\n"
        for i, fig in enumerate(figures, 1):
            caption = fig.get("caption", "[No caption]").strip()
            context = fig.get("context", "[No context]").strip()
            caption_conf = fig.get("caption_confidence", 0)
            context_conf = fig.get("context_confidence", 0)
            usefulness = fig.get("usefulness_score", 0)
            
            data_text += f"""Figure {fig.get("id", i)} (Page {fig.get("page", "?")})
[Caption Confidence: {caption_conf:.2f}, Context Confidence: {context_conf:.2f}, Usefulness: {usefulness:.2f}]
Caption: {caption}
Context: {context}
\n"""
    
    if tables:
        data_text += "TABLES (WITH STRUCTURE METADATA):\n"
        data_text += "-" * 60 + "\n"
        for i, tbl in enumerate(tables, 1):
            rows = tbl.get("rows", "?")
            cols = tbl.get("columns", "?")
            conf = tbl.get("confidence", 0)
            usefulness = tbl.get("usefulness_score", 0)
            title = tbl.get("title", "[No title]")
            
            data_text += f"""Table {tbl.get("id", i)} (Page {tbl.get("page", "?")})
[Confidence: {conf:.2f}, Usefulness: {usefulness:.2f}]
Structure: {rows} rows × {cols} columns
Title/Purpose: {title}
\n"""
    
    return data_text


def get_summary(pdf_url: str):
    """
    VISUAL PASS ONLY:
    - Descriptive narrative format
    - Evidence-bound with confidence markers
    - NO interpretation or inference
    - Metadata preserved for merge phase gating
    """

    extractor = ImageTableExtractor(pdf_url)
    extracted = extractor.extracted_text()

    figures = extracted.get("figures", [])
    tables = extracted.get("tables", [])

    # -------- HARD FILTER BY USEFULNESS (confidence gate) --------
    figures = [f for f in figures if f.get("usefulness_score", 0) >= 0.6]
    tables  = [t for t in tables  if t.get("usefulness_score", 0) >= 0.6]

    # -------- BUILD STRUCTURED EVIDENCE WITH METADATA --------
    data_text = format_visual_evidence(figures, tables)
    
    if not data_text.strip():
        return "No visual evidence extracted with sufficient confidence."

    # -------- PROMPT (NARRATIVE FORMAT, ANTI-HALLUCINATION) --------
    messages = [
        {
            "role": "system",
            "content": """You are generating FACTUAL academic visual evidence descriptions (narrative format).

OUTPUT FORMAT:
- Write as flowing narrative paragraphs (NOT bullet points)
- One paragraph per figure/table
- Use phrases: "shows", "depicts", "displays", "presents"
- Reference by ID and page number

FACTUALITY RULES:
- ONLY describe what is in caption/context
- DO NOT infer trends, performance, or improvements
- DO NOT compare methods
- If no quantitative data: say "(illustrative only)"
- Low confidence: Add "caption unclear"
- Tables: Describe structure only unless data is explicit
"""
        },
        {
            "role": "user",
            "content": f"""Generate narrative visual evidence from this data. Be factual, no inference:

{data_text}
"""
        }
    ]

    response = client.chat_completion(
        messages=messages,
        max_tokens=1200,
        temperature=0.2,
        top_p=0.9
    )

    notes = response.choices[0].message.content
    notes = normalize_visual_notes(notes)

    return notes
