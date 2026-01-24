"use client";
import Link from "next/link";
export default function ResultCard({ title,download_url,id }) {
  const pdfUrl = download_url.replace("/abs/", "/pdf/") + ".pdf";
  console.log("ResultCard ID:", id, typeof id);
  const handleChatClick = () => {
    // Store PDF URL only for this session + paper
    sessionStorage.setItem(`pdf:${id}`, pdfUrl);
  };
  
  return (
    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 hover:border-blue-600 transition">
      <h4 className="text-white text-lg font-semibold mb-2">{title}</h4>
      <div className="flex gap-4 mt-4">
        <Link href={`/Home/notes/${id}`}>
           <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm">
             Generate Notes
           </button>
        </Link>
        <Link href={`/Home/chat/${id}`} onClick={handleChatClick}>
           <button className="bg-purple-700 hover:bg-purple-700 text-white px-4 py-2 rounded-md text-sm">
              Chat with Paper
           </button>
        </Link>
        <Link href={pdfUrl} target="_blank" rel="noopener noreferrer">
              <button className="bg-green-700 hover:bg-green-600 text-white px-4 py-2 rounded-md text-sm">View Paper</button>
        </Link>
      </div>
    </div>
  );
}
