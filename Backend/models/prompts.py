from langchain_core.prompts import PromptTemplate





BATCH_PROMPT_1 = PromptTemplate(
    
    template="""
    "You are an expert at extracting key information from research paper chunks.

**Your task**: Extract and condense the most important information from the text below. 
Focus on facts, numbers, methodologies, results, and technical details.

**Rules**:
- Extract only factual information explicitly stated
- Preserve exact numbers, metrics, datasets, model names, and terminology
- Do NOT add structure or sections
- Do NOT hallucinate or infer
- Keep it concise but comprehensive

Text:
{element}

Extracted Information:""",
input_variables=["element"]

)
NOTES_PROMPT=PromptTemplate(
    template="""
    You are an expert at creating comprehensive, well-structured academic notes.

You will receive multiple extracted information chunks from a research paper. Your task is to synthesize them into a single, coherent, structured document.

**Required Structure**:

📋 **1. Brief Overview**
- 2-3 sentences summarizing the paper's main contribution

🎯 **2. Key Contributions**
- List 3-5 main contributions/innovations

📄 **3. Abstract/Problem Statement**
- What problem does this paper address?
- Why is it important?

🚀 **4. Motivation & Background**
- What gaps exist in current approaches?
- Why is this work needed?

⚡ **5. Proposed Method/Framework**
- Clear explanation of the approach
- Key algorithms or techniques
- Architecture/system design

🔧 **6. Technical Components**
- Main components/modules
- How they work together

📊 **7. Experiments & Results**
- Datasets used
- Baseline comparisons
- Performance metrics (accuracy, F1, speed, etc.)
- Key findings

⚠️ **8. Limitations**
- Acknowledged limitations
- Constraints or assumptions

🔮 **9. Future Work**
- Proposed extensions
- Open research questions

📚 **10. Key References**
- Important cited works

**Critical Rules**:
- Synthesize information across all chunks (remove redundancy)
- Preserve all exact numbers, metrics, model names, datasets
- If a section has no information, write "Not explicitly mentioned in the paper"
- Use clear, concise academic language
- Maintain logical flow between sections

Extracted chunks to synthesize:

{element}

Generate comprehensive structured notes:

    """,
    input_variables=["element"]
    
)

VALIDATION_PROMPT = PromptTemplate(
    template="""
You are a strict academic reviewer evaluating the factual accuracy of generated research notes.

You will be given:
1. Structured notes generated from a paper
2. Extracted factual information from the paper

Your task is to VERIFY the notes against the extracted information.

**Rules**:
- Use ONLY the provided extracted information as ground truth
- Do NOT rewrite or fix the notes
- Do NOT add explanations
- Do NOT infer missing information
- Be strict and conservative

**For each issue, classify it as one of the following**:
- INCORRECT: Contradicts the extracted information
- UNSUPPORTED: Not explicitly stated in the extracted information
- SPECULATIVE: Guess, assumption, or future-looking statement not stated
- MISSING: Important information present in extracted data but missing in notes

**Output Format (STRICT JSON ONLY)**:
{{
  "incorrect_claims": [string],
  "unsupported_claims": [string],
  "speculative_claims": [string],
  "missing_core_information": [string],
  "safe_sections": [string]
}}

Structured Notes to Validate:
{notes}

Extracted Information (Ground Truth):
{source}

Validation Output:
""",
    input_variables=["notes", "source"]
)

FINAL_NOTES_PROMPT = PromptTemplate(
    template="""
You are an academic editor producing final, publication-ready research notes.

You will receive:
1. Original structured notes
2. A validation report identifying issues

Your task is to produce corrected final notes.

⚠️ **CRITICAL REQUIREMENTS**:
- You MUST use the EXACT structure shown below
- You MUST keep all section titles and numbering IDENTICAL
- You MUST NOT add, remove, reorder, or rename sections

📋 **1. Brief Overview**
🎯 **2. Key Contributions**
📄 **3. Abstract/Problem Statement**
🚀 **4. Motivation & Background**
⚡ **5. Proposed Method/Framework**
🔧 **6. Technical Components**
📊 **7. Experiments & Results**
⚠️ **8. Limitations**
🔮 **9. Future Work**
📚 **10. Key References**

**Editing Rules**:
- Remove all INCORRECT claims
- Remove or soften UNSUPPORTED claims
- Remove SPECULATIVE content entirely
- Add missing information ONLY if explicitly listed as MISSING in the validation report
- If information is unavailable, write exactly: "Not explicitly mentioned in the paper"
- Do NOT add new facts
- Do NOT introduce new interpretations
- Preserve all exact terminology, numbers, datasets, and model names
- Keep the content concise and academic

Validation Report:
{validation}

Original Structured Notes:
{notes}

Produce corrected final structured notes using ONLY the structure above:
""",
    input_variables=["validation", "notes"]
)

