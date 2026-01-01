"use client";

import { useState, useEffect } from "react";
import { Download, User, Calendar,ArrowLeft,ExternalLink } from "lucide-react";
import { useParams } from "next/navigation";
import { getNotes } from "@/lib/api_call";
import { useSearchParams } from "next/navigation";
import { useRouter } from "next/navigation";
import { useRef } from "react";
import Link from "next/link";
export default function NotePage() {
  const [note, setNote] = useState({ content: "" }); // ✅ initialize with object so note.content exists
  const {id}=useParams();
  console.log(id)
  // const searchParams=useSearchParams();
  const [loading, setLoading] = useState(true);
  const router=useRouter()
  const notesRef=useRef("")//this hold the value of reference box but when we use it do not re-render
  const defaultNote ={
      content:`📋 **1. Brief Overview**
      The AutoCompete system is a novel framework for automated machine learning (AutoML) that leverages a combination of machine learning model selection, hyperparameter tuning, and model stacking to achieve high-performance results on various datasets. The system has been tested on multiple datasets, including the Adult dataset, MNIST dataset, and Newsgroups-20 dataset, and has achieved impressive results, including an AUC of 0.88 on the Adult dataset. The AutoCompete system has also been ranked 2nd in Phase 0 of the AutoML Challenge.
      
      🎯 **2. Key Contributions**
      - The AutoCompete system provides a comprehensive framework for AutoML, incorporating machine learning model selection, hyperparameter tuning, and model stacking.
      - The system utilizes a combination of random search and grid search for hyperparameter optimization, as well as sequential model-based optimization for general algorithm configuration.
      - The AutoCompete system has been tested on multiple datasets, including tabular and text datasets, and has achieved impressive results, including an AUC of 0.88 on the Adult dataset.
      
      📄 **3. Abstract/Problem Statement**
      The problem addressed by this paper is the automation of machine learning, which is a crucial aspect of modern data science. The importance of this problem lies in the fact that machine learning has become a key component of many applications, including image recognition, natural language processing, and predictive modeling. However, the process of selecting the best machine learning model and tuning its hyperparameters is often time-consuming and requires significant expertise.
      
      🚀 **4. Motivation & Background**
      The motivation behind this work is to develop a system that can automate the process of machine learning, making it more accessible to non-experts and reducing the time required to develop high-performance models. The background of this work lies in the fact that current approaches to machine learning often require significant expertise and can be time-consuming, which can limit their adoption in many applications. The AutoCompete system aims to address these gaps by providing a comprehensive framework for AutoML.
      
      ⚡ **5. Proposed Method/Framework**
      The AutoCompete system consists of two major components: the ML Model Selector and the Hyper-parameter Selector. The ML Model Selector is responsible for selecting the best machine learning model for a given dataset, while the Hyper-parameter Selector is responsible for tuning the hyperparameters of the selected model. The system utilizes a combination of random search and grid search for hyperparameter optimization, as well as sequential model-based optimization for general algorithm configuration. The system also incorporates a data splitter, data type identifier, feature stacker, decomposition tools, and feature selector.
      
      🔧 **6. Technical Components**
      The main components of the AutoCompete system include:
      - ML Model Selector: responsible for selecting the best machine learning model for a given dataset.
      - Hyper-parameter Selector: responsible for tuning the hyperparameters of the selected model.
      - Data Splitter: responsible for splitting the dataset into training and validation sets.
      - Data Type Identifier: responsible for identifying the data type of the dataset.
      - Feature Stacker: responsible for stacking features from multiple models.
      - Decomposition Tools: responsible for decomposing complex datasets into simpler components.
      - Feature Selector: responsible for selecting the most relevant features for the model.
      
      📊 **7. Experiments & Results**
      The AutoCompete system has been tested on multiple datasets, including:
      - Adult dataset: achieved an AUC of 0.88.
      - MNIST dataset: achieved a test dataset accuracy of 0.96.
      - Newsgroups-20 dataset: achieved a pipeline with TF-IDF and logistic regression in less than 10 minutes wall time.
      - Smartphone dataset: used for human activity prediction.
      - Housing dataset: used for testing the AutoCompete system.
      The system has also been ranked 2nd in Phase 0 of the AutoML Challenge. The evaluation metric used is the area under the ROC curve (AUC).
      
      ⚠️ **8. Limitations**
      Not explicitly mentioned in the paper.
      
      🔮 **9. Future Work**
      Not explicitly mentioned in the paper, but potential future work could include:
      - Extending the AutoCompete system to support more datasets and machine learning models.
      - Improving the efficiency of the system by utilizing more advanced optimization techniques.
      - Integrating the AutoCompete system with other machine learning frameworks to provide a more comprehensive solution.
      
      📚 **10. Key References**
      - Anguita, D., Ghio, A., Oneto, L., Parra, X., & Reyes-Ortiz, J. L. (2012). Human activity recognition on smartphones using a multiclass hardware-friendly support vector machine. Proceedings of the 4th International Conference on Ambient Assisted Living and Home Care, 216-223.
      - Breiman, L. (2001). Random forests. Mach. Learn., 45(1), 5-32.
      - Hutter, F., Hoos, H. H., & Leyton-Brown, K. (2014). Sequential model-based optimization for general algorithm configuration. Proceedings of the 13th International Conference on Autonomous Agents and Multiagent Systems, 507-514.
      - Komer, B., Bergstra, J., & Eliasmith, C. (2014). Hyperopt-sklearn: Automatic hyperparameter tuning for scikit-learn. Proceedings of the 13th Python in Science Conference, 33-39.
      - Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., ... & Vanderplas, J. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2825-2830.`}
    const fetchNote=async () =>{
      try {
        setLoading(true);
        const data=await getNotes(id);
        console.log(data)
        if(!data){
           setNote(defaultNote)
        }
       else {    
         setNote(data);
       }
      } catch (error) {
        console.error("Error fetching note:", error);
      }finally{
        setLoading(false);
      }
    }  
  
    useEffect(() => {
      fetchNote();
    }, [id]);
  const handleDownload = async () =>{
      if(!notesRef.current){
        alert("No notes yet!")
        return
      }
      try{
        const html2pdf = (await import("html2pdf.js")).default;
        html2pdf()
            .set({
              margin: 10,
              html2canvas: { scale: 2 },
              jsPDF: { unit: "mm", format: "a4", orientation: "portrait" }
            })
            .from(notesRef.current)
            .save();
      }
      catch(error){
        alert('Something went wrong while downloading.')
      }
  }
  
  if (loading){
    return (
        <div className="flex items-center justify-center h-96">
          <div className="text-gray-400">Loading note...</div>
        </div>
      );
  }
  if(!note){
    return (
        <div className="flex flex-col items-center justify-center h-96">
          <p className="text-gray-400 mb-4">Note not found</p>
          <button
            onClick={() => router.push("/Home/notes")}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Notes
          </button>
        </div>
      );
  }
  return (
    <>
     <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => router.push("/dashboard/notes")}
          className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Notes</span>
        </button>
      <h1 className="text-3xl font-bold text-white mb-4">{note.paperTitle}</h1>

      {/* Meta Info */}
      <div className="flex flex-wrap gap-4 text-sm text-gray-400 mb-4">
        <div className="flex items-center gap-2">
          <User className="w-4 h-4" />
          <span>{note.authors}</span>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4" />
          <span>{new Date(note.publishedDate).toLocaleDateString()}</span>
        </div>
      </div>
      <Link href={note.arxivUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            <span>View on arXiv</span>
        </Link>
      {/* Action */}
      <div className="flex gap-3">
        <button onClick={handleDownload}
        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all flex items-center gap-2 font-medium">
          <Download className="w-4 h-4" />
          Downlaod Notes
        </button>
      </div>
      {/* Content */}
      <div ref={notesRef} className="bg-[#1a1d2e] border border-gray-700 rounded-xl p-8">
        <div
          className="prose prose-invert prose-blue max-w-none"
          style={{
            color: "#e5e7eb",
          }}
        >
          {/* Render markdown content */}
          {note.content &&
            note.content.split("\n").map((line, index) => {
              // Headers
              if (line.startsWith("### ")) {
                return (
                  <h3
                    key={index}//concern 
                    className="text-2xl font-bold text-white mt-8 mb-4 flex items-center gap-2"
                  >
                    {line.replace("### ", "")}
                  </h3>
                );
              }

              // Bold text with list items
              if (line.startsWith("- **")) {
                const match = line.match(/- \*\*(.*?)\*\*: (.*)/);
                if (match) {
                  return (
                    <div key={index} className="ml-4 mb-3">
                      <span className="text-blue-400 font-semibold">
                        • {match[1]}:
                      </span>
                      <span className="text-gray-300"> {match[2]}</span>
                    </div>
                  );
                }
              }

              // Regular list items
              if (line.startsWith("- ")) {
                return (
                  <div key={index} className="ml-4 mb-2 text-gray-300">
                    • {line.replace("- ", "")}
                  </div>
                );
              }

              // Empty lines
              if (line.trim() === "") {
                return <br key={index} />;
              }

              // Regular paragraphs
              return (
                <p key={index} className="text-gray-300 mb-4 leading-relaxed">
                  {line}
                </p>
              );
            })}
        </div>
      </div>
    </div>
    </div>
    </>
  );
}
