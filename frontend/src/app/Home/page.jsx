"use client";

import Button from "@/components/ui/Button";
import Link from "next/link";

export default function DashboardPage() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-white">
      {/* Title */}
      <h1 className="text-4xl font-bold mb-10">
        Make Search!
      </h1>

      {/* Actions */}
      <div className="w-full max-w-sm flex flex-col items-center gap-6 text-center ">
        <Link href="/Home/search_text" className="w-full">
          <Button variant="primary" className="w-full py-4 text-lg">
            Search Documents
          </Button>
        </Link>

        <span className="text-gray-400 text-2xl font-bold">
          OR
        </span>

        <Link href="/Home/upload_query" className="w-full">
          <Button variant="secondary" className="w-full py-4 text-lg">
            Upload Document
          </Button>
        </Link>
      </div>
    </div>
  );
}
