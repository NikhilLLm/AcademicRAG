// DemoPlaceholder.jsx
"use client";

import { motion } from "framer-motion";

export default function DemoPlaceholder() {
  return (
    <section className="relative py-40 px-6">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        viewport={{ once: true }}
        className="max-w-4xl mx-auto text-center bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl p-20 shadow-xl"
      >
        <div className="text-6xl mb-6">🚀</div>

        <h2 className="text-4xl font-bold mb-4 text-white">
          Live Demo Coming Soon
        </h2>

        <p className="text-gray-400 text-lg max-w-2xl mx-auto">
          We’re building an interactive demo so you can experience semantic
          search, notes, and paper chat directly in the browser.
        </p>
      </motion.div>
    </section>
  );
}
