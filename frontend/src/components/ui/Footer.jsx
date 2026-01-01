// Footer.jsx
"use client";

export default function Footer() {
  return (
    <footer className="relative border-t border-white/10 py-10 px-6">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="text-gray-400 text-sm">
          © {new Date().getFullYear()}{" "}
          <span className="text-white font-medium">PaperSemantic</span>. All
          rights reserved.
        </div>

        <div className="flex gap-6 text-sm text-gray-400">
          <a href="#" className="hover:text-white transition">
            About
          </a>
          <a href="#" className="hover:text-white transition">
            Docs
          </a>
          <a href="#" className="hover:text-white transition">
            GitHub
          </a>
        </div>
      </div>
    </footer>
  );
}
