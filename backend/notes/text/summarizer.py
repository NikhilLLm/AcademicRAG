import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from transformers import pipeline
import re
from langchain_core.prompts import PromptTemplate
from backend.notes.chunks_embeddings import TextPreprocessor


# ----------------------------------------------------
# Load environment variables
# ----------------------------------------------------
load_dotenv("C:/Users/nshej/aisearch/.env")


# ====================================================
# PASS 1: MISTRAL (Reasoning + Structuring)
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


def mistral_llm(prompt: str):
    client = get_mistral_client()

    response = client.chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.2
    )

    return response.choices[0].message.content


# ----------------------------------------------------
# ✅ IMPROVED PASS-1 PROMPT WITH EXAMPLES
# ----------------------------------------------------
PASS1_PROMPT = PromptTemplate(
    input_variables=["context"],
    template="""You are creating DETAILED exam notes from an academic paper.
    You are NOT summarizing.
You are an examiner extracting marks-bearing points.


🚨 CRITICAL RULES:
1. DO NOT SUMMARIZE. DO NOT SHORTEN. EXTRACT VERBATIM.
2. Keep ALL technical terms, formulas, dataset names, metrics exactly as written
3. If you see equations like "J = q μ n E", write them EXACTLY: "J = q μ n E"
4. If you see values like "accuracy = 94.2%", keep them: "accuracy = 94.2%"
5. Use 4-6 bullets per section with nested sub-points
6. Write 5-8 bullets per section. Each bullet should be 2-3 lines long.
Every bullet must correspond to something that can appear in an exam answer
- Include numbers, ranges, datasets, metrics, equations
- If a paragraph contains 3 facts → produce 3 bullets
- Never generalize (no “framework is flexible”, “scalable”, “robust”)
- If content is vague, say “Not specified in paper”

EXAMPLE OUTPUT FORMAT (follow this EXACTLY):

### Problem / Motivation 🚗
- Main problem: Existing AutoML systems require extensive manual hyperparameter tuning
  - Why it matters: Manual tuning takes 40-60 hours per competition
  - Existing limitation: Current tools like Hyperopt explore unnecessarily large search spaces
- Current approaches fail because: They don't exploit competition-specific constraints

### Proposed Method ⚡
- Main technique: Automated ML pipeline with restricted hyperparameter search
  - Step 1: Automated feature encoding and scaling
  - Step 2: Model selection using Random Forest (n_estimators = [100, 200, 500]) and SVM (C = [0.1, 1, 10])
  - Key equation: Final prediction = argmax(votes from ensemble)
- Differs from prior work by: Limiting search space to 80% fewer configurations

### Key Contributions 🎯
- Contribution 1: First end-to-end AutoML framework for Kaggle-style competitions
  - Technical detail: Achieves competitive leaderboard positions with minimal tuning
- Contribution 2: Demonstrates that restricted search spaces maintain performance

### Results / Evaluation 📊
- Datasets used: UCI ML Repository (Iris, Wine, Breast Cancer datasets)
  - Size: 150-569 samples across datasets
  - Characteristics: 4-30 features, binary and multi-class tasks
- Metrics achieved:
  - F1-score: 0.89 average across 5 tasks
  - Training time: 12.3 minutes average per task
  - Accuracy: 92.1% on Iris, 94.5% on Wine
- Compared to baseline: Outperforms Hyperopt by 12% in speed with 98% of accuracy

### Limitations ⚠️
- Limitation 1: Restricted to tabular data only (no image/text support)
- Limitation 2: Limited model diversity (only RF and SVM tested)
- Future work needed: Extend to deep learning architectures

NOW EXTRACT FROM THIS CONTENT (maintain same detail level as example):
{context}

IMPORTANT: Your output should be 3-4x LONGER than a typical summary. We want DETAILED notes, not a summary.
"""
)
# ====================================================
# MULTI-QUERY RETRIEVAL (EXAM-ORIENTED)
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
        return text[:8000]  # More context

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




# ====================================================
# FORMULA PROTECTION (MUST BE BEFORE compress_sections_smart)
# ====================================================
def protect_formulas(text: str):
    """
    Find formula-like patterns and protect them
    Returns: (protected_text, formula_map)
    """
    formula_map = {}
    counter = 0
    
    # ✅ IMPROVED: More comprehensive patterns
    patterns = [
        # Standard equations: "J = q μ n E"
        r'[A-Za-z_][A-Za-z0-9_]*\s*=\s*[^,\n]{3,60}',
        
        # Metrics with hyphens: "F1-score = 0.89"
        r'[A-Za-z][A-Za-z0-9\-_]*\s*[=:]\s*\d+\.?\d*%?',
        
        # Parenthetical expressions: "(n + p)"
        r'\([A-Za-z0-9\s+\-*/^√]+\)',
        
        # Bracketed equations: "[σ = sqrt(variance)]"
        r'\[[^\]]{5,50}\]',
        
        # Greek letters and superscripts: "E = mc²"
        r'[A-Za-z]\s*=\s*[A-Za-z0-9²³⁴]+',
        
        # Value ranges: "n = [100, 200, 500]"
        r'\w+\s*=\s*\[[\d\s,\.]+\]',
    ]
    
    protected_text = text
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # Skip if already protected
            if match in formula_map.values():
                continue
                
            placeholder = f"__FORMULA_{counter}__"
            formula_map[placeholder] = match
            protected_text = protected_text.replace(match, placeholder, 1)
            counter += 1
    
    return protected_text, formula_map


def restore_formulas(text: str, formula_map: dict):
    """Restore formulas from placeholders"""
    restored = text
    for placeholder, formula in formula_map.items():
        restored = restored.replace(placeholder, formula)
    return restored


# ====================================================
# VALIDATION (BEFORE BART)
# ====================================================
def validate_extraction(text: str):
    """Check if extraction has good quality indicators"""
    indicators = {
        'has_formulas': bool(re.search(r'[A-Za-z_]\s*[=:]', text)),
        'has_numbers': bool(re.search(r'\d+\.?\d*%?', text)),
        'has_technical_terms': len(re.findall(r'\b[A-Z]{2,}\b', text)) > 2,
        'is_detailed': len(text) > 800  # Lowered from 1000 (more realistic)
    }
    
    print("\n🔍 Extraction Quality Check:")
    for check, passed in indicators.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check}: {passed}")
    
    # Show preview if quality is low
    if not all(indicators.values()):
        print("\n⚠️ WARNING: Low quality extraction detected!")
        print("First 300 chars:", text[:300], "...")
    
    return all(indicators.values())


# ====================================================
# PASS 2: SMART SECTION-WISE COMPRESSION
# ====================================================
_bart_cache = None

def get_bart_summarizer():
    global _bart_cache

    if _bart_cache is None:
        print("Loading local BART Large CNN (Pass 2)...")

        _bart_cache = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            tokenizer="facebook/bart-large-cnn",
            device=-1  # CPU (set 0 if GPU available)
        )

    return _bart_cache


def compress_sections_smart(structured_text: str):
    """
    ✅ SMART COMPRESSION:
    1. Split by sections
    2. Protect formulas in each section
    3. Compress only prose
    4. Restore formulas
    """
    summarizer = get_bart_summarizer()
    
    # Split by ### headers
    sections = re.split(r'(###[^\n]+)', structured_text)
    final_notes = []
    
    for i in range(1, len(sections), 2):  # Headers at odd indices
        if i + 1 >= len(sections):
            break
            
        header = sections[i].strip()
        content = sections[i + 1].strip()
        
        if len(content) < 100:  # Too short to compress
            final_notes.append(f"{header}\n{content}")
            continue
        
        try:
            # ✅ STEP 1: Protect formulas
            protected_content, formula_map = protect_formulas(content)
            
            print(f"\n📝 Processing section: {header}")
            print(f"   Protected {len(formula_map)} formulas")
            
            # ✅ STEP 2: Compress (BART never sees formulas)
            compressed = summarizer(
                protected_content,
                max_length=300,  # ✅ More generous (was 200)
                min_length=150,  # ✅ More generous (was 80)
                do_sample=False,
                truncation=True
            )[0]["summary_text"]
            
            # ✅ STEP 3: Restore formulas
            restored = restore_formulas(compressed, formula_map)
            
            final_notes.append(f"{header}\n{restored}")
            
        except Exception as e:
            print(f"⚠️ Section compression failed: {e}")
            # Keep original if BART fails
            final_notes.append(f"{header}\n{content}")
    
    return "\n\n".join(final_notes)


# ====================================================
# REFERENCES EXTRACTION
# ====================================================
def extract_links(text: str):
    urls = sorted(set(re.findall(r'https?://\S+', text)))
    if not urls:
        return ""
    return "\n\n### References / Related Work 🔗\n" + "\n".join(f"- {u}" for u in urls)

# ====================================================
# RAG PIPELINE
# ====================================================
def _get_rag_chain(pdf_url: str):
    text_preprocessor = TextPreprocessor(pdf_url=pdf_url)
    retriever = text_preprocessor.get_retriever()

    

    def rag_call():
        # -------- MULTI-QUERY CONTEXT --------
        context = collect_multi_query_context(retriever)
    
        print("\n🔄 PASS 1: Extracting with Mistral...")
        print(f"📄 Context length: {len(context)} chars")
    
        structured = mistral_llm(PASS1_PROMPT.format(context=context))
    
        print(f"\n📊 Mistral output length: {len(structured)} chars")
    
        quality_ok = validate_extraction(structured)
        if not quality_ok:
            print("⚠️ Consider increasing retriever k or context length")
    
        print("\n🔄 PASS 2: Smart compression with BART...")
        final_notes = compress_sections_smart(structured)
    
        # -------- REFERENCES --------
        refs = extract_links(context)
    
        return final_notes + refs

    return rag_call


# ====================================================
# PUBLIC API
# ====================================================
def summarize(pdf_url: str):
    """
    ✅ TurboLearn-style 2-pass note generation (PRODUCTION VERSION)
    
    Improvements:
    1. Detailed prompt with examples
    2. Formula protection before BART
    3. Validation checks
    4. Better error handling
    """
    try:
        rag_chain = _get_rag_chain(pdf_url)
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
        traceback.print_exc()  # ✅ Show full error for debugging
        return error_msg


# ====================================================
# ✅ OPTIONAL: ADVANCED FEATURES
# ====================================================
def summarize_with_bullet_control(pdf_url: str, max_bullets_per_section: int = 5):
    """
    Enhanced version with bullet-count control
    """
    try:
        rag_chain = _get_rag_chain(pdf_url)
        notes = rag_chain()
        
        # Post-process to limit bullets per section
        sections = notes.split("###")
        controlled = []
        
        for sec in sections:
            if not sec.strip():
                continue
            
            lines = sec.split("\n")
            header = lines[0] if lines else ""
            bullets = [l for l in lines[1:] if l.strip().startswith("-")]
            
            # Keep only top N bullets
            limited_bullets = bullets[:max_bullets_per_section]
            controlled.append(f"### {header}\n" + "\n".join(limited_bullets))
        
        return "\n\n".join(controlled)
    
    except Exception as e:
        return f"Error: {str(e)}"


def summarize_verbose(pdf_url: str):
    """
    Debug version that shows all intermediate outputs
    """
    print("\n" + "="*60)
    print("🔬 VERBOSE MODE - SHOWING ALL STEPS")
    print("="*60)
    
    text_preprocessor = TextPreprocessor(pdf_url=pdf_url)
    retriever = text_preprocessor.get_retriever()
    
    # Step 1: Retrieval
    docs = retriever.invoke("Extract detailed technical content")
    context = "\n\n".join(doc.page_content for doc in docs)[:5000]
    
    print("\n📄 STEP 1: RETRIEVED CONTEXT")
    print("-"*60)
    print(context[:500], "...\n")
    
    # Step 2: Mistral extraction
    structured = mistral_llm(PASS1_PROMPT.format(context=context))
    
    print("\n🧠 STEP 2: MISTRAL EXTRACTION")
    print("-"*60)
    print(structured, "\n")
    
    # Step 3: Validation
    print("\n🔍 STEP 3: VALIDATION")
    print("-"*60)
    validate_extraction(structured)
    
    # Step 4: BART compression
    final = compress_sections_smart(structured)
    
    print("\n📝 STEP 4: FINAL NOTES")
    print("-"*60)
    print(final)
    print("="*60)
    
    return final