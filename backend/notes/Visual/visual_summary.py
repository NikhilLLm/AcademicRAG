from huggingface_hub import InferenceClient 
from backend.notes.Visual.image_table_extractor import ImageTableExtractor 
from dotenv import load_dotenv 
import os 
import json 
 
load_dotenv("C:/Users/nshej/aisearch/.env") 
 
HF_TOKEN = os.getenv("HF_TOKEN") 
 
client = InferenceClient( 
    model="mistralai/Mistral-7B-Instruct-v0.2", 
    token=HF_TOKEN 
) 

def normalize_visual_notes(visual_notes: str):
    """
    Convert figures/tables into clean textual facts.
    No markdown noise, no redundancy.
    """
    lines = visual_notes.split("\n")
    clean = []

    for l in lines:
        if any(x in l.lower() for x in ["figure", "table", "page"]):
            clean.append(l.strip())
        elif ":" in l and len(l) < 300:
            clean.append(l.strip())

    return "\n".join(clean)

 
def get_summary(pdf_url: str): 
    """Generate final bullet-point notes from visuals + tables""" 
 
    # 1️⃣ Extract cleaned semantic facts 
    extractor = ImageTableExtractor(pdf_url) 
    extracted_items = extractor.extracted_text() 
 
    # 2️⃣ Separate figures and tables for better organization
    figures = [item for item in extracted_items if item.get('type') == 'figure']
    tables = [item for item in extracted_items if item.get('type') == 'table']
    
    # 3️⃣ Build structured data string
    data_text = ""
    
    if figures:
        data_text += "FIGURES:\n"
        for fig in figures:
            data_text += f"\n- Figure {fig.get('id', 'Unknown')} (Page {fig.get('page', '?')})\n"
            data_text += f"  Caption: {fig.get('caption', 'No caption')}\n"
            if 'extracted_text' in fig:
                data_text += f"  Content: {fig['extracted_text']}\n"
    
    if tables:
        data_text += "\n\nTABLES:\n"
        for tbl in tables:
            data_text += f"\n- Table {tbl.get('id', 'Unknown')} (Page {tbl.get('page', '?')})\n"
            if 'data' in tbl:
                data_text += f"  Data: {json.dumps(tbl['data'], indent=2)}\n"
 
    # 4️⃣ Chat completion format with system + user messages
    messages = [
        {
            "role": "system",
            "content": """You are an expert academic note-taker specializing in research papers.

Your task is to create clear, structured bullet-point notes from figures and tables.

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

## Figures

### Figure 1 (Page X): [Caption]
- Key finding or insight
- Important detail or metric
- Comparison or result

### Figure 2 (Page Y): [Caption]
- Key finding or insight
- Important detail

## Tables

### Table 1 (Page X): [Description]
- Main result or comparison
- Key metrics and values
- Notable patterns

RULES:
- Always include figure/table number and page
- Include the original caption/description
- Extract KEY insights, don't just describe the visual
- For tables: highlight important comparisons and metrics
- Use bullet points (•) for each insight
- Be concise but informative
- NO mentions of "bounding boxes", "layout", or technical extraction details"""
        },
        {
            "role": "user",
            "content": f"""Create structured study notes from the following research paper visuals:

{data_text}

Remember to:
1. Start with figure number and page
2. Include caption/description
3. Extract meaningful insights in bullet points
4. For tables, highlight key comparisons and metrics"""
        }
    ]
 
    # 5️⃣ Call with chat completion format
    response = client.chat_completion(
        messages=messages,
        max_tokens=1500,  # Increased for detailed notes
        temperature=0.3,  # Lower for more focused output
        top_p=0.9
    )
    
    # 6️⃣ Extract the generated text
    notes = response.choices[0].message.content
    notes= normalize_visual_notes(notes)
    return notes




