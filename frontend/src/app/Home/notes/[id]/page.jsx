"use client";

import { useState, useEffect, useRef } from "react";
import { Download, User, Calendar, ArrowLeft, ExternalLink, Search, ChevronDown, ChevronUp, Maximize2, X, FileText } from "lucide-react";

import { startNotesJob, getJobStatus } from "@/lib/api_call";
import { useParams } from "next/navigation";
import { getNotes } from "@/lib/api_call";
import { useRouter } from "next/navigation";
import Link from "next/link";
export default function NotePage() {
  const defaultNote = {
    extracted_text: `📋 **1. Brief Overview**
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
      - Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., ... & Vanderplas, J. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2825-2830.`,
    papermetadata: {
      title: "Sample Paper",
      authors: ["John Doe"],
      publication_date: "2024-01-01",
      download_url: "",
    }
  }
  const router = useRouter()
  const { id } = useParams()
  const notesRef = useRef(null)
  const isMountedRef = useRef(true)
  const [note, setNote] = useState({ extracted_text: " ", papermetadata: {} })
  const [jobId, setJobId] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedImage, setSelectedImage] = useState(null); // For Lightbox
  const [expandedVisuals, setExpandedVisuals] = useState({}); // For Description Accordions
  const [isDownloading, setIsDownloading] = useState(false);
  //--------Derived values ------
  const papermetadata = note?.papermetadata || defaultNote.papermetadata;
  const content = note?.extracted_text || defaultNote.extracted_text;
  const visuals = note?.visuals || defaultNote.visuals;
  console.log(visuals)
  // Retry function to restart the job
  const handleRetry = async () => {
    setNote({ extracted_text: " ", papermetadata: {} })
    setJobId(null)
    setError(null)
    setLoading(true)

    // Call the API directly to start a new job
    try {
      const res = await startNotesJob(id)
      if (isMountedRef.current) {
        setJobId(res.job_id)
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err.message)
        setLoading(false)
      }
    }
  }
  //---------Start job--------
  useEffect(() => {
    isMountedRef.current = true
    return () => {
      isMountedRef.current = false
    }
  }, [])

  useEffect(() => {
    if (!id || !isMountedRef.current) return;

    setLoading(true)
    setError(null)

    startNotesJob(id)
      .then((res) => {
        if (isMountedRef.current) setJobId(res.job_id)
      })
      .catch((err) => {
        if (isMountedRef.current) {
          setError(err.message)
          setLoading(false)
        }
      })
  }, [id])
  //-----Storing notes id and title--------

  function saveNoteIndex({ id, title }) {
    const notes = JSON.parse(localStorage.getItem("notesIndex")) || [];
    if (notes.some(n => n.id === id)) return;

    const newNote = {
      id,
      title,
      createdAt: new Date().toISOString(),
    }

    //Newest note on the top
    notes.unshift(newNote)


    localStorage.setItem("notesIndex", JSON.stringify(notes))

  }
  //----Poll Job : Getting Notes----

  useEffect(() => {
    if (!jobId || !isMountedRef.current) return
    const interval = setInterval(async () => {
      try {
        const data = await getJobStatus(jobId)
        if (data.status === "done") {
          if (isMountedRef.current) {
            setNote(data.result)
            setLoading(false)
            const title = data.result?.papermetadata?.title || "Untitled Paper";
            sessionStorage.setItem(`title:${id}`, title);
            saveNoteIndex({
              id,
              title: title,
            })
          }
          clearInterval(interval)
        }
        if (data.status === "error") {
          if (isMountedRef.current) {
            setError(data.error || "Job Failed")
            setLoading(false)
          }
          clearInterval(interval)
        }
      } catch (err) {
        if (isMountedRef.current) {
          setError(err.message)
          setLoading(false)
        }
        clearInterval(interval)
      }
    }, 3000)
    return () => clearInterval(interval)
  }, [jobId])
  //-------Download handler------
  const toggleVisual = (index) => {
    setExpandedVisuals(prev => ({ ...prev, [index]: !prev[index] }));
  };

  const saveOriginalStyles = (root) => {
    const elements = [root, ...root.querySelectorAll("*")]; // Include root!
    return Array.from(elements).map((el) => ({
      el,
      color: el.style.color,
      bg: el.style.backgroundColor,
      border: el.style.borderColor,
    }));
  };

  const handleDownload = async () => {
    if (!notesRef.current) {
      alert("No Note yet!");
      return;
    }

    setIsDownloading(true);
    try {
      const html2canvas = (await import("html2canvas-pro")).default;
      const { jsPDF } = await import("jspdf");

      // Sanitize Filename with Regex
      const sanitizedTitle = (papermetadata.title || "notes")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/(^-|-$)/g, "");
      const fileName = `${sanitizedTitle}-summary.pdf`;

      // 1. Prepare for export (ensure all images are loaded)
      const element = notesRef.current;

      // 2. Capture canvas with high scale for quality
      const canvas = await html2canvas(element, {
        scale: 3,
        useCORS: true,
        backgroundColor: "#0f1120", // Matches the app background but slightly darkened for PDF
        logging: false,
        windowWidth: element.scrollWidth,
        windowHeight: element.scrollHeight,
      });

      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF({
        orientation: "portrait",
        unit: "pt", // Points for better precision
        format: "a4",
      });

      // A4 dimensions in points: 595.28 x 841.89
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();

      const imgWidth = pdfWidth;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;

      let heightLeft = imgHeight;
      let position = 0;

      // Add first page
      pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
      heightLeft -= pdfHeight;

      // Add more pages if content is longer
      while (heightLeft >= 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
        heightLeft -= pdfHeight;
      }

      pdf.save(fileName);
    } catch (err) {
      console.error("PDF download failed:", err);
      alert("Something went wrong while downloading the PDF.");
    } finally {
      setIsDownloading(false);
    }
  };
  //------Loading UI------
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-screen text-gray-400">
        <div className="flex items-center justify-center mb-6">
          <div className="relative w-16 h-16">
            {/* Outer rotating ring */}
            <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-indigo-500 border-r-indigo-400 animate-spin"></div>
            {/* Inner rotating ring (opposite direction) */}
            <div className="absolute inset-2 rounded-full border-3 border-transparent border-b-purple-500 border-l-purple-400 animate-spin" style={{ animationDirection: 'reverse', animationDuration: '2s' }}></div>
          </div>
        </div>
        <p className="text-lg font-medium">Generating notes…</p>
        <p className="text-sm text-gray-500 mt-2">This may take a moment</p>
      </div>
    );
  }

  //------Error UI------
  if (error || !content.trim()) {
    return (
      <div className="flex flex-col items-center justify-center h-screen text-gray-400">
        <div className="text-center mb-6">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-red-400 mb-2">Failed to fetch notes</h2>
          <p className="text-gray-500 mb-8">{"The notes content could not be retrieved. Please try again."}</p>
          <div className="flex gap-4 justify-center">
            <button
              onClick={handleRetry}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
            >
              🔄 Retry
            </button>
            <button
              onClick={() => router.push("/Home/notes")}
              className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors font-medium"
            >
              Back to Notes
            </button>
          </div>
        </div>
      </div>
    );
  }



  // -------------------------
  // MAIN UI
  // -------------------------
  return (
    <div className="min-h-screen pb-20 px-4 md:px-8 max-w-7xl mx-auto">
      {/* Top Header Section */}
      <header className="py-8 animate-in fade-in slide-in-from-top-4 duration-700">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
          <div className="flex-1">
            <button
              onClick={() => router.push("/Home/chat")}
              className="group flex items-center gap-2 text-indigo-400 hover:text-indigo-300 transition-colors mb-6 text-sm font-medium"
            >
              <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
              <span>Back to Conversations</span>
            </button>

            <h1 className="text-3xl md:text-5xl font-extrabold text-white leading-tight tracking-tight mb-4">
              {papermetadata.title || "Untitled Paper"}
            </h1>

            <div className="flex flex-wrap gap-6 text-gray-400">
              <div className="flex items-center gap-2.5 bg-white/5 px-3 py-1.5 rounded-full border border-white/10">
                <User className="w-4 h-4 text-indigo-400" />
                <span className="text-sm">
                  {Array.isArray(papermetadata.authors)
                    ? papermetadata.authors.join(", ")
                    : papermetadata.authors || "Unknown authors"}
                </span>
              </div>

              <div className="flex items-center gap-2.5 bg-white/5 px-3 py-1.5 rounded-full border border-white/10">
                <Calendar className="w-4 h-4 text-purple-400" />
                <span className="text-sm">
                  {papermetadata.publication_date
                    ? new Date(papermetadata.publication_date).toLocaleDateString(undefined, {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })
                    : "N/A"}
                </span>
              </div>

              {papermetadata.download_url && (
                <Link
                  href={papermetadata.download_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2.5 bg-indigo-500/10 hover:bg-indigo-500/20 px-3 py-1.5 rounded-full border border-indigo-500/30 text-indigo-400 transition-all"
                >
                  <ExternalLink className="w-4 h-4" />
                  <span className="text-sm font-medium">View on arXiv</span>
                </Link>
              )}
            </div>
          </div>

          <div className="flex shrink-0">
            <button
              onClick={handleDownload}
              className="w-full md:w-auto px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl flex items-center justify-center gap-3 font-semibold shadow-lg shadow-indigo-500/20 transition-all hover:scale-[1.02] active:scale-95"
            >
              <Download className="w-5 h-5" />
              Export PDF
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
        {/* Left Column: Notes Content (70%) */}
        <div className="lg:col-span-8 space-y-8 animate-in fade-in slide-in-from-left-4 duration-700 delay-200">
          <div
            ref={notesRef}
            className="relative overflow-hidden bg-[#15182b]/80 backdrop-blur-xl border border-white/10 rounded-3xl p-6 md:p-12 shadow-2xl"
          >
            {/* Subtle Gradient Background */}
            <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/5 blur-[120px] rounded-full pointer-events-none" />
            <div className="absolute bottom-0 left-0 w-96 h-96 bg-purple-500/5 blur-[120px] rounded-full pointer-events-none" />

            {/* Content Container */}
            <div className="relative z-10">
              <article className="prose prose-invert prose-headings:text-white prose-p:text-gray-300 prose-strong:text-indigo-300 prose-lg max-w-none">
                {content.split("\n").map((line, index) => {
                  // Section Headers
                  if (line.match(/^(\d+\.|📋|🎯|📄|🚀|⚡|🔧|📊|⚠️|🔮|📚).*$/)) {
                    return (
                      <div key={index} className="flex items-center gap-4 mt-12 mb-6 group">
                        <h2 className="text-2xl md:text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400 group-hover:from-indigo-300 group-hover:to-white transition-all duration-300">
                          {line}
                        </h2>
                        <div className="h-[1px] flex-1 bg-gradient-to-r from-indigo-500/20 to-transparent rounded-full" />
                      </div>
                    );
                  }

                  if (line.startsWith("### ")) {
                    return (
                      <h3 key={index} className="text-xl font-bold mt-10 mb-5 text-indigo-300 flex items-center gap-3">
                        <div className="w-1.5 h-6 bg-indigo-500 rounded-full" />
                        {line.replace("### ", "")}
                      </h3>
                    );
                  }

                  // Enhanced List Items
                  if (line.startsWith("- **")) {
                    const match = line.match(/- \*\*(.*?)\*\*: (.*)/);
                    if (match) {
                      return (
                        <div key={index} className="ml-2 mb-4 group flex items-start gap-3 p-3 rounded-2xl hover:bg-white/5 transition-colors border border-transparent hover:border-white/5">
                          <div className="mt-2.5 w-1.5 h-1.5 rounded-full bg-indigo-500/50 group-hover:bg-indigo-400 ring-4 ring-indigo-500/5 transition-all" />
                          <div>
                            <span className="text-indigo-300 font-bold block md:inline mb-1 md:mb-0">
                              {match[1]}:
                            </span>
                            <span className="text-gray-300/90 leading-relaxed ml-0 md:ml-1"> {match[2]}</span>
                          </div>
                        </div>
                      );
                    }
                  }

                  if (!line.trim()) return null;

                  // Standard Paragraphs
                  return (
                    <p key={index} className="text-gray-300/90 mb-6 leading-relaxed text-lg">
                      {line}
                    </p>
                  );
                })}
              </article>

              {/* Integrated Visuals - Included in notesRef for PDF Export */}
              {note?.visuals?.length > 0 && (
                <div className="mt-20 pt-10 border-t border-white/5">
                  <div className="flex items-center gap-3 mb-10">
                    <FileText className="w-6 h-6 text-indigo-400" />
                    <h2 className="text-3xl font-bold text-white tracking-tight">Extracted Visual Information</h2>
                  </div>

                  <div className="space-y-12">
                    {note.visuals.map((v, i) => (
                      <div
                        key={i}
                        className="group bg-white/5 border border-white/10 rounded-3xl p-6 transition-all hover:bg-white/[0.07]"
                      >
                        <div className="flex flex-col lg:flex-row gap-8">
                          {/* Image Preview Container */}
                          <div className="lg:w-1/2 shrink-0">
                            <div className="relative overflow-hidden rounded-2xl bg-white aspect-auto max-h-[400px]">
                              <img
                                src={v.base64?.startsWith('data:image') ? v.base64 : `data:image/jpeg;base64,${v.base64}`}
                                alt={`Figure ${i + 1}`}
                                className="w-full h-full object-contain cursor-zoom-in"
                                onClick={() => setSelectedImage(v)}
                                loading="lazy"
                              />
                              <button
                                onClick={() => setSelectedImage(v)}
                                className="absolute bottom-4 right-4 p-2 bg-black/60 hover:bg-black/80 text-white rounded-lg backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-opacity"
                              >
                                <Maximize2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>

                          {/* Info Container */}
                          <div className="lg:w-1/2 space-y-4">
                            <div className="flex items-center justify-between">
                              <span className="px-3 py-1 bg-indigo-500/20 text-indigo-400 text-xs font-bold rounded-full border border-indigo-500/30">
                                FIGURE {i + 1}
                              </span>
                            </div>

                            <h4 className="text-xl font-bold text-white leading-snug">
                              {v.caption}
                            </h4>

                            {/* Accordion for Full Description */}
                            <div className="pt-2">
                              <button
                                onClick={() => toggleVisual(i)}
                                className="flex items-center gap-2 text-indigo-400 hover:text-indigo-300 text-sm font-medium transition-colors"
                              >
                                {expandedVisuals[i] ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                {expandedVisuals[i] ? "Hide Detail Analysis" : "Show Full AI Analysis"}
                              </button>

                              {expandedVisuals[i] && (
                                <div className="mt-4 p-4 bg-black/20 rounded-2xl border border-white/5 animate-in fade-in slide-in-from-top-2 duration-300">
                                  <p className="text-gray-400 text-sm leading-relaxed italic whitespace-pre-wrap">
                                    {v.description || v.caption}
                                  </p>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Statistics & Highlights (Fixed) */}
        <aside className="lg:col-span-4 space-y-6 animate-in fade-in slide-in-from-right-4 duration-700 delay-300">
          <div className="sticky top-8 space-y-6">
            <div className="bg-[#15182b]/80 backdrop-blur-xl border border-white/10 rounded-3xl p-6 shadow-xl">
              <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500" />
                Paper Insights
              </h3>

              <div className="space-y-4">
                <div className="flex justify-between items-center p-3 rounded-xl bg-white/5">
                  <span className="text-gray-400 text-sm">Visuals Extracted</span>
                  <span className="text-white font-bold">{note?.visuals?.length || 0}</span>
                </div>
                <div className="flex justify-between items-center p-3 rounded-xl bg-white/5">
                  <span className="text-gray-400 text-sm">Data Chunks</span>
                  <span className="text-white font-bold">{note?.chunks_retrieved || "75+"}</span>
                </div>
                <div className="flex justify-between items-center p-3 rounded-xl bg-white/5">
                  <span className="text-gray-400 text-sm">AI Confidence</span>
                  <span className="text-white font-bold">High</span>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-indigo-600/20 to-purple-600/20 border border-white/10 rounded-3xl p-6">
              <h4 className="text-white font-bold mb-3">AI Synthesis</h4>
              <p className="text-gray-400 text-sm leading-relaxed">
                These notes were generated using semantic ranking and structure-aware extraction. Visual descriptions were synthesized using an 11B parameter vision model.
              </p>
            </div>
          </div>
        </aside>
      </div>

      {/* Lightbox Modal */}
      {selectedImage && (
        <div className="fixed inset-0 z-[100] bg-black/95 flex flex-col backdrop-blur-md animate-in fade-in duration-300">
          <div className="flex justify-between items-center p-6 border-b border-white/10">
            <h3 className="text-white font-bold">{selectedImage.caption}</h3>
            <button
              onClick={() => setSelectedImage(null)}
              className="p-3 bg-white/10 hover:bg-white/20 rounded-full text-white transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
          <div className="flex-1 flex items-center justify-center p-4">
            <img
              src={selectedImage.base64?.startsWith('data:image') ? selectedImage.base64 : `data:image/jpeg;base64,${selectedImage.base64}`}
              alt="Lightbox"
              className="max-w-full max-h-full object-contain shadow-2xl"
            />
          </div>
          <div className="p-8 max-w-4xl mx-auto">
            <p className="text-gray-300 text-center leading-relaxed">
              {selectedImage.description}
            </p>
          </div>
        </div>
      )}

      {/* Exporting Overlay */}
      {isDownloading && (
        <div className="fixed inset-0 z-[110] bg-black/60 backdrop-blur-sm flex flex-col items-center justify-center">
          <div className="bg-[#1a1d2e] p-8 rounded-3xl border border-white/10 shadow-2xl flex flex-col items-center">
            <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4" />
            <h4 className="text-white font-bold text-lg">Preparing your PDF</h4>
            <p className="text-gray-400 text-sm mt-1">Applying visual enhancements...</p>
          </div>
        </div>
      )}

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 5px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.2);
        }
      `}</style>
    </div>
  );
}
