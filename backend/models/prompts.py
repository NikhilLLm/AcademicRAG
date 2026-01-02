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



