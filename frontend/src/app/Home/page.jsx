"use client";

import Button from "@/components/ui/Button";
import Link from "next/link";

export default function DashboardPage() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-white">
      {/* Title */}
      <div className="mb-16 text-center">
        <h1 className="text-6xl font-bold mb-3 bg-gradient-to-r from-indigo-400 via-indigo-500 to-purple-500 bg-clip-text text-transparent drop-shadow-lg">
          Make Search!
        </h1>
        <p className="text-gray-300 text-sm tracking-wide">
          Explore and analyze research papers with semantic intelligence
        </p>
      </div>

      {/* Actions */}
      <div className="w-full max-w-md flex flex-col items-center gap-8 text-center">
        <Link href="/Home/search_text" className="w-full group">
          <Button variant="primary" className="w-full py-5 text-lg font-semibold transition-all duration-300 transform group-hover:scale-105">
            <span className="flex items-center justify-center gap-2">
              🔍 Search Documents
            </span>
          </Button>
        </Link>

        <div className="flex items-center gap-4 w-full">
          <div className="flex-1 h-px bg-gradient-to-r from-transparent to-gray-600"></div>
          <span className="text-gray-400 text-lg font-semibold px-2">
            OR
          </span>
          <div className="flex-1 h-px bg-gradient-to-l from-transparent to-gray-600"></div>
        </div>

        <Link href="/Home/upload_query" className="w-full group">
          <Button variant="secondary" className="w-full py-5 text-lg font-semibold transition-all duration-300 transform group-hover:scale-105">
            <span className="flex items-center justify-center gap-2">
              📤 Upload Document
            </span>
          </Button>
        </Link>
      </div>
    </div>
  );
}
