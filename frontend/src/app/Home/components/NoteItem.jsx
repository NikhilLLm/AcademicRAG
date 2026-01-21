"use client";

import Link from "next/link";

export default function NoteCard({ note, onDelete }) {
  const { id, title, createdAt } = note;

  const formattedDate = createdAt
    ? new Date(createdAt).toLocaleString()
    : "Unknown date";

  return (
    <div className="bg-gray-800 border border-gray-700 hover:border-blue-600 transition rounded-xl px-6 py-5 w-full">
      <div className="flex items-center justify-between gap-6">
        
        {/* Left: Title + Date */}
        <div className="min-w-0">
          <h4 className="text-white text-xl font-semibold leading-snug truncate max-w-3xl">
            {title || "Untitled Note"}
          </h4>
          <p className="text-gray-400 text-sm mt-1">
            Created on {formattedDate}
          </p>
        </div>

        {/* Right: Actions */}
        <div className="flex gap-3 shrink-0">
          <Link
            href={`/Home/notes/${id}`}
            className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-md text-sm font-medium"
          >
            View
          </Link>

          <button
            onClick={() => onDelete(id)}
            className="bg-red-700 hover:bg-red-600 text-white px-5 py-2 rounded-md text-sm font-medium"
          >
            Delete
          </button>
        </div>

      </div>
    </div>
  );
}


