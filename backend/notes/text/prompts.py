from langchain_core.prompts import PromptTemplate



# ----------------------------------------------------
# ✅ PASS-1 PROMPT: TEXT CONTENT ONLY (NO FIGURES/TABLES)
# ----------------------------------------------------
PASS1_TEXT_PROMPT = PromptTemplate(
    input_variables=["context"],
    template="""You are creating DETAILED exam notes from an academic paper's TEXT CONTENT ONLY.

🚨 CRITICAL RULES:
1. DO NOT SUMMARIZE. EXTRACT VERBATIM with all details.
2. Keep ALL technical terms, formulas, equations, metrics EXACTLY as written
3. Write 5-8 detailed bullets per section. Each bullet = 2-3 lines
4. Include numbers, datasets, parameter values, ranges
5. DO NOT mention figures, tables, or visual elements (they will be added separately)

MANDATORY STRUCTURE (Use EXACTLY these sections):

### Brief Overview 📋
- Paper's main contribution in one sentence
- Primary problem being solved
- Core solution approach with key technique name

### Key Points 🎯
- Most important takeaway 1 with specific metrics
- Most important takeaway 2 with technical details
- Most important takeaway 3 with results

### Abstract 📄
- Problem statement: [Extract exact problem from abstract]
- Proposed solution: [Extract methodology details]
- Key results: [Extract specific metrics like "accuracy = 94.2%"]

### Introduction / Motivation 🚗
- Main problem: [Problem with full context]
  - Why it matters: [Real-world impact with numbers if available]
  - Existing limitation: [Current approaches and specific failures]
- Research gap: [What's missing in existing literature]
- Paper's approach: [How this paper addresses the gap]

### Method / Framework ⚡
- Main technique: [Core algorithm/approach name]
  - Step 1: [Detailed first step with parameters]
  - Step 2: [Detailed second step with equations]
  - Step 3: [Additional steps as needed]
- Key equations: [Mathematical formulations like "J = q μ n E"]
- Architecture: [Model structure, layers, components]
- Differs from prior work: [Specific technical differences]

### Components 🔧
- Component 1: [Name and purpose]
  - Implementation: [Technical details]
  - Parameters: [Values like "learning_rate = 0.001"]
- Component 2: [Additional components]

### Experiments & Results 📊
- Datasets: [Exact names like "MNIST", "ImageNet"]
  - Size: [Samples, features, dimensions]
  - Preprocessing: [Steps taken]
- Baseline methods: [What was compared against]
- Metrics: [DO NOT include table data - only text mentions]
  - [Metric name]: [Value from text]
- Training details: [Time, hardware, iterations]

### Limitations ⚠️
- Limitation 1: [Specific constraint or failure]
- Limitation 2: [Additional limitations]
- Computational requirements: [If mentioned]

### Future Work 🔮
- Direction 1: [Specific extension proposed]
- Direction 2: [Additional future research]

NOW EXTRACT FROM THIS TEXT (maintain 3-4x detail of summary):
{context}

REMEMBER: Extract ALL details. Do NOT mention "Figure X" or "Table Y" anywhere.
"""
)


# ----------------------------------------------------
# ✅ PASS-2 PROMPT: MERGE TEXT + VISUAL CONTENT
# ----------------------------------------------------
PASS2_MERGE_PROMPT = PromptTemplate(
    input_variables=["text_notes", "visual_notes"],
    template="""You are merging TEXT notes with VISUAL content (figures/tables) into ONE cohesive document.

INPUT:
1. TEXT NOTES: Detailed notes from paper's text
2. VISUAL NOTES: Figures and tables with insights

YOUR TASK: Create FINAL notes following the EXACT structure below.

MANDATORY OUTPUT STRUCTURE:

### Brief Overview 📋
[Keep from text notes as-is]

### Key Points 🎯
[Merge: Include points from BOTH text and visual content]
- [Text insight 1]
- [Text insight 2]  
- [Visual insight: e.g., "Figure 1 shows accuracy improved by 15%"]

### Abstract 📄
[Keep from text notes as-is]

### Introduction / Motivation 🚗
[Keep from text notes as-is]

### Method / Framework ⚡
[Keep text content, then ADD figure references]
[After describing algorithm, add:]
- Visual representation: Figure X (Page Y) shows [architecture/workflow]
  - Key insight from figure: [Extract from visual notes]

### Components 🔧
[Keep text content]
[If figures show components, add:]
- Architectural diagram: Figure X illustrates [component structure]

### Experiments & Results 📊
[THIS IS THE MOST IMPORTANT SECTION - Merge carefully]

#### Datasets Used
[From text notes]

#### Performance Metrics
[Merge text metrics WITH table data]
- [Metric 1]: [Value from text] (see Table X on Page Y)
  - Comparison: [Extract comparison data from tables]
- [Metric 2]: [Value] as shown in Table Z
  - Details: [Table insights]

#### Visual Results
- Figure X (Page Y): [Caption]
  - Shows: [Key finding from figure]
  - Insight: [Specific observation]

#### Result Tables
[For each table, format as:]
- Table X (Page Y): [Description]
  - Key comparison: [Extract main comparison]
  - Best result: [Highlight top performance]
  - Notable: [Any interesting pattern]

### Limitations ⚠️
[Keep from text notes]

### Future Work 🔮
[Keep from text notes]

### References 🔗
[URLs if any]

---

TEXT NOTES:
{text_notes}

---

VISUAL NOTES:
{visual_notes}

---

CRITICAL RULES:
1. Keep ALL technical details, equations, numbers from text notes
2. Integrate visual insights naturally (don't just append them)
3. In Experiments section, MERGE table data with text metrics
4. Reference figures/tables by number and page
5. Maintain the exact section structure above
6. Be detailed - output should be 2-3 pages of notes
"""
)