"use client";

import Link from "next/link";

export default function Navbar() {
  return (
    <nav className="fixed top-6 left-0 w-full z-50 flex justify-center">
      {/* Centered Rounded Container */}
      <div
        className="flex items-center justify-between gap-12
                   px-8 py-5
                   w-full max-w-4xl
                   rounded-3xl
                   border border-gray-700
                   bg-black/60 backdrop-blur-md"
      >
        {/* Logo → Home */}
        <Link
          href="/"
          className="text-lg font-semibold tracking-wide hover:opacity-90 transition"
        >
          Paper<span className="text-blue-600">Semantic</span>
        </Link>

        {/* Dashboard Button */}
        <Link
          href="/login"
          className="bg-blue-600 hover:bg-blue-500 px-6 py-3 rounded-lg
                     border border-gray-600 hover:border-gray-400 borderd-none shadow-lg shadow-blue-500/30
                     transition text-sm font-medium"
        >
          Login
        </Link>
      </div>
    </nav>
  );
}
