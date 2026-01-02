import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from transformers import pipeline
import re
from backend.notes.text.prompts import PASS1_TEXT_PROMPT, PASS2_MERGE_PROMPT
from backend.notes.text.chunks_embeddings import TextPreprocessor
from backend.notes.Visual.visual_summary import get_summary as get_visual_summary

# ----------------------------------------------------
# Load environment variables
# ----------------------------------------------------
load_dotenv("C:/Users/nshej/aisearch/.env")


# ====================================================
# PASS 1: MISTRAL (TEXT CONTENT EXTRACTION)
# ====================================================
_mistral_cache = None

def get_mistral_client():
    global _mistral_cache

    if _mistral_cache is None:
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            raise RuntimeError("HF_TOKEN not found in .env")

        print("Loading Mistral-7B-Instruct (Pass 1)...")

        _mistral_cache = InferenceClient(
            model="mistralai/Mistral-7B-Instruct-v0.2",
            token=hf_token
        )

    return _mistral_cache


def mistral_llm(prompt: str, max_tokens: int = 2500):
    client = get_mistral_client()

    response = client.chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.2
    )

    return response.choices[0].message.content




# ====================================================
# MULTI-QUERY RETRIEVAL
# ====================================================
RETRIEVAL_QUERIES = [
    "Problem definition and motivation",
    "Algorithm description and methodology",
    "Mathematical formulation and equations",
    "Experimental setup datasets and baselines",
    "Results metrics accuracy F1 runtime",
    "Limitations and future work",
    "Related work and referenced methods"
]

def format_docs(docs):
    text = "\n\n".join(doc.page_content for doc in docs)
    return text[:8000]

def collect_multi_query_context(retriever):
    seen = set()
    all_docs = []

    for q in RETRIEVAL_QUERIES:
        docs = retriever.invoke(q)
        for d in docs:
            if d.page_content not in seen:
                seen.add(d.page_content)
                all_docs.append(d)

    return format_docs(all_docs)

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
# ====================================================
# FORMULA PROTECTION
# ====================================================
def protect_formulas(text: str):
    formula_map = {}
    counter = 0
    
    patterns = [
        r'[A-Za-z_][A-Za-z0-9_]*\s*=\s*[^,\n]{3,60}',
        r'[A-Za-z][A-Za-z0-9\-_]*\s*[=:]\s*\d+\.?\d*%?',
        r'\([A-Za-z0-9\s+\-*/^√]+\)',
        r'\[[^\]]{5,50}\]',
        r'[A-Za-z]\s*=\s*[A-Za-z0-9²³⁴]+',
        r'\w+\s*=\s*\[[\d\s,\.]+\]',
    ]
    
    protected_text = text
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if match in formula_map.values():
                continue
                
            placeholder = f"__FORMULA_{counter}__"
            formula_map[placeholder] = match
            protected_text = protected_text.replace(match, placeholder, 1)
            counter += 1
    
    return protected_text, formula_map


def restore_formulas(text: str, formula_map: dict):
    restored = text
    for placeholder, formula in formula_map.items():
        restored = restored.replace(placeholder, formula)
    return restored


# ====================================================
# NOISE FILTER
# ====================================================
def apply_noise_filter(text: str):
    """Remove unrelated URLs, phone numbers, promotional content, hallucinated info"""
    lines = text.split('\n')
    filtered_lines = []
    
    # Expanded noise patterns
    noise_patterns = [
        r'for more information',
        r'visit.*website',
        r'call.*on.*\d',  # Phone numbers in sentences
        r'\d{3,}[-.\s]?\d{3,}[-.\s]?\d{4}',  # Phone formats
        r'1-800-\d',  # Toll-free numbers
        r'08457',  # UK numbers
        r'samaritans',
        r'suicide prevention',
        r'confidential support',
        r'click here',
        r'subscribe',
        r'follow us',
        r'available now on',
        r'download from',
        r'google play',
        r'gofundme',
        r'for details',
        r'see www\.',
        r'visit www\.',
    ]
    
    # URLs to remove (hallucinated or promotional)
    bad_url_patterns = [
        r'googleplay\.com',
        r'gofundme\.com',
        r'samaritans\.org',
        r'suicidepreventionlifeline',
        r'autocompete\.com',
        r'autocompete\.org',
        r'blog/\d{4}/',  # Blog URLs
    ]
    
    in_references = False
    
    for line in lines:
        # Track if we're in References section
        if '### References' in line:
            in_references = True
            filtered_lines.append(line)
            continue
        
        # Skip empty lines
        if not line.strip():
            filtered_lines.append(line)
            continue
        
        # Check noise patterns
        is_noise = any(re.search(pattern, line, re.IGNORECASE) for pattern in noise_patterns)
        
        # Check for bad URLs (unless in References)
        if not in_references and 'http' in line:
            has_bad_url = any(re.search(pattern, line, re.IGNORECASE) for pattern in bad_url_patterns)
            if has_bad_url:
                is_noise = True
        
        # Keep line if not noise
        if not is_noise:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)


# ====================================================
# VALIDATION
# ====================================================
def validate_extraction(text: str):
    indicators = {
        'has_formulas': bool(re.search(r'[A-Za-z_]\s*[=:]', text)),
        'has_numbers': bool(re.search(r'\d+\.?\d*%?', text)),
        'has_technical_terms': len(re.findall(r'\b[A-Z]{2,}\b', text)) > 2,
        'is_detailed': len(text) > 800
    }
    
    print("\n🔍 Extraction Quality Check:")
    for check, passed in indicators.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check}: {passed}")
    
    if not all(indicators.values()):
        print("\n⚠️ WARNING: Low quality extraction detected!")
        print("First 300 chars:", text[:300], "...")
    
    return all(indicators.values())


# ====================================================
# PASS 3: BART COMPRESSION (FINAL POLISH)
# ====================================================
_bart_cache = None

def get_bart_summarizer():
    global _bart_cache

    if _bart_cache is None:
        print("Loading BART Large CNN (Pass 3)...")

        _bart_cache = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            tokenizer="facebook/bart-large-cnn",
            device=-1
        )

    return _bart_cache


def compress_sections_smart(structured_text: str):
    """
    BART compression with formula protection
    IMPROVEMENT: Skip compression for already concise sections to prevent hallucination
    """
    summarizer = get_bart_summarizer()
    
    sections = re.split(r'(###[^\n]+|####[^\n]+)', structured_text)
    final_notes = []
    
    # Sections that should NEVER be compressed
    SKIP_COMPRESSION = [
        'Brief Overview',
        'Key Points',
        'Abstract',
        'Limitations',
        'Future Work',
        'References'
    ]
    
    for i in range(1, len(sections), 2):
        if i + 1 >= len(sections):
            break
            
        header = sections[i].strip()
        content = sections[i + 1].strip()
        
        # Check if this section should skip compression
        skip = any(skip_word in header for skip_word in SKIP_COMPRESSION)
        
        # Don't compress if:
        # 1. Section is in skip list
        # 2. Content is too short (< 400 chars)
        # 3. Content has too few words (< 80 words)
        word_count = len(content.split())
        
        if skip or len(content) < 400 or word_count < 80:
            print(f"\n⏭️ Skipping: {header} (too short or protected)")
            final_notes.append(f"{header}\n{content}")
            continue
        
        try:
            protected_content, formula_map = protect_formulas(content)
            
            print(f"\n🔧 Compressing: {header}")
            print(f"   Protected {len(formula_map)} formulas")
            print(f"   Original: {word_count} words")
            
            # Adjust compression based on content length
            if word_count > 200:
                max_len = 300
                min_len = 150
            else:
                max_len = 200
                min_len = 100
            
            compressed = summarizer(
                protected_content,
                max_length=max_len,
                min_length=min_len,
                do_sample=False,
                truncation=True
            )[0]["summary_text"]
            
            compressed_words = len(compressed.split())
            print(f"   Compressed: {compressed_words} words")
            
            restored = restore_formulas(compressed, formula_map)
            final_notes.append(f"{header}\n{restored}")
            
        except Exception as e:
            print(f"⚠️ Compression failed for {header}: {e}")
            final_notes.append(f"{header}\n{content}")
    
    return "\n\n".join(final_notes)


# ====================================================
# REFERENCES EXTRACTION
# ====================================================
def extract_links(text: str):
    urls = sorted(set(re.findall(r'https?://\S+', text)))
    if not urls:
        return ""
    return "\n\n### References 🔗\n" + "\n".join(f"- {u}" for u in urls)


# ====================================================
# MAIN PIPELINE (3 PASSES)
# ====================================================
def _get_integrated_rag_chain(pdf_url: str):
    """
    Complete 3-layer pipeline:
    1. Text extraction (Mistral Pass 1)
    2. Visual extraction + Merging (Mistral Pass 2)  
    3. Compression (BART Pass 3)
    """
    text_preprocessor = TextPreprocessor(pdf_url=pdf_url)
    retriever = text_preprocessor.get_retriever()

    def rag_call():
        # ============================================
        # LAYER 1: TEXT CONTENT EXTRACTION
        # ============================================
        print("\n" + "="*60)
        print("📄 LAYER 1: TEXT EXTRACTION")
        print("="*60)
        
        context = collect_multi_query_context(retriever)
        print(f"📄 Context length: {len(context)} chars")
        
        text_notes = mistral_llm(PASS1_TEXT_PROMPT.format(context=context), max_tokens=2500)
        print(f"✅ Text notes: {len(text_notes)} chars")
        
        validate_extraction(text_notes)
        
        # ============================================
        # LAYER 2: VISUAL CONTENT EXTRACTION
        # ============================================
        print("\n" + "="*60)
        print("🖼️ LAYER 2: VISUAL EXTRACTION")
        print("="*60)
        
        try:
            visual_notes = get_visual_summary(pdf_url)
            
            print(f"✅ Visual notes: {len(visual_notes)} chars")
        except Exception as e:
            print(f"⚠️ Visual extraction failed: {e}")
            visual_notes = "No visual content extracted."
        text_notes = apply_noise_filter(text_notes)
        visual_notes = apply_noise_filter(visual_notes)
        # ============================================
        # LAYER 2.5: MERGE TEXT + VISUAL
        # ============================================
        print("\n" + "="*60)
        print("🔗 LAYER 2.5: MERGING TEXT + VISUAL")
        print("="*60)
        
        merged_notes = mistral_llm(
            PASS2_MERGE_PROMPT.format(
                text_notes=text_notes,
                visual_notes=visual_notes
            ),
            max_tokens=3500
        )
        print(f"✅ Merged notes: {len(merged_notes)} chars")
        
        # ============================================
        # LAYER 3: BART COMPRESSION
        # ============================================
        print("\n" + "="*60)
        print("✂️ LAYER 3: BART COMPRESSION")
        print("="*60)
        
        final_notes = compress_sections_smart(merged_notes)
        refs = extract_links(merged_notes)

        # ============================================
        # POST-PROCESSING: CLEAN UP
        # ============================================
        print("\n" + "="*60)
        print("🧹 POST-PROCESSING: NOISE REMOVAL & CLEANUP")
        print("="*60)
        
        # Step 1: Apply noise filter
        
        
        # Step 2: Fix empty sections
        # If Components section is empty, add a note
        cleaned_notes = re.sub(
            r'### Components 🔧\s*\n\s*\n\s*###',
            '### Components 🔧\n- Components not explicitly detailed in paper\n\n###',
            final_notes
        )
        
        # Step 3: Remove duplicate Reference sections
        cleaned_notes = re.sub(r'### References 🔗\s*\n\s*\[URLs if any\]\s*\n', '', cleaned_notes)
        
        # Step 4: Add actual references
        
        
        # Step 5: Final cleanup - remove multiple blank lines
        cleaned_notes = re.sub(r'\n{3,}', '\n\n', cleaned_notes)
        
        # Step 6: Remove any remaining promotional phrases
        cleanup_phrases = [
            r'For confidential support.*?\.',
            r'In the U\.S\. call.*?\.',
            r'visit a local.*?branch.*?\.',
        ]
        for phrase in cleanup_phrases:
            cleaned_notes = re.sub(phrase, '', cleaned_notes, flags=re.IGNORECASE | re.DOTALL)
        
        return cleaned_notes + refs

    return rag_call


# ====================================================
# PUBLIC API
# ====================================================
def summarize(pdf_url: str):
    """
    ✅ TurboLearn-style 3-layer note generation
    
    Pipeline:
    1. Text extraction (Mistral) → Structured text notes
    2. Visual extraction (Mistral) → Figure/table insights
    3. Merging (Mistral) → Combined notes
    4. Compression (BART) → Final polished notes
    """
    try:
        rag_chain = _get_integrated_rag_chain(pdf_url)
        result = rag_chain()
        
        print("\n" + "="*60)
        print("✅ FINAL NOTES GENERATED")
        print("="*60)
        print(result)
        print("="*60)
        
        return result
    except Exception as e:
        error_msg = f"Error generating notes: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return error_msg


def summarize_verbose(pdf_url: str):
    """Debug version showing all steps"""
    print("\n" + "="*60)
    print("🔬 VERBOSE MODE")
    print("="*60)
    
    return summarize(pdf_url)


#