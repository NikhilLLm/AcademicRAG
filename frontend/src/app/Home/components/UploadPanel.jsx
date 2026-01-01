"use client";
import { useState } from "react";
import { Upload, File, X } from "lucide-react";
import { getUploadResult } from "@/lib/api_call";

export default function UploadPanel({setResults,setLoading}) {
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleUpload = (e) => {
    const uploadedFile = e.target.files[0];
    if (uploadedFile) {
      setFile(uploadedFile);
      console.log("Uploading:", uploadedFile);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
  e.preventDefault();
  e.stopPropagation();
  setDragActive(false);

  if (file) {
    // Already have a file, ignore new drops
    console.log("File already selected, remove it first.");
    return;
  }

  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
    setFile(e.dataTransfer.files[0]);
    console.log("Dropped file:", e.dataTransfer.files[0]);
  }
};


  const removeFile = () => {
    setFile(null);
  };

  const  handleAnalyze = async () => {
    if(!file) return;
    setLoading(true);
    try {
      const data=await getUploadResult(file);
      setResults(data.results || []);
    }
    catch (err) {
      console.error("Search failed:", err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto">  {/* ← Added mx-auto here */}
      <h3 className="text-xl font-semibold text-white mb-4 text-center">  {/* ← Added text-center for title */}
        Upload PDF or Image
      </h3>

      {/* Upload Area */}
      <label
        htmlFor="file-upload"
        className={`relative block w-full rounded-xl border-2 border-dashed cursor-pointer transition-all ${
          dragActive
            ? "border-blue-400 bg-blue-500/10"
            : "border-gray-600 hover:border-gray-500 bg-[#1a1d2e]/50"
        }`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
      >
        <input
          id="file-upload"
          type="file"
          accept=".pdf,image/*"
          className="hidden"
          onChange={handleUpload}
          disabled={!!file}
        />

        <div className="px-6 py-12 text-center">
          {file ? (
            // File selected state
            <div className="flex items-center justify-center gap-3">
              <File className="w-8 h-8 text-blue-400" />
              <div className="text-left">
                <p className="text-white font-medium">{file.name}</p>
                <p className="text-sm text-gray-400">
                  {(file.size / 1024).toFixed(2)} KB
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.preventDefault();
                  removeFile();
                }}
                className="ml-auto p-2 hover:bg-gray-700 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-400 hover:text-white" />
              </button>
            </div>
          ) : (
            // Empty state
            <>
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-white font-medium mb-1">
                Drag & drop a file here or click to upload
              </p>
              <p className="text-sm text-gray-400">
                Supports PDF and Image files
              </p>
            </>
          )}
        </div>
      </label>

      {/* Upload Button */}
      <button
        onClick={handleAnalyze}
        disabled={!file}
        className="mt-4 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white py-3 rounded-lg transition-all font-medium flex items-center justify-center gap-2"
      >
        <Upload className="w-5 h-5" />
        Upload & Analyze
      </button>
    </div>
  );
}