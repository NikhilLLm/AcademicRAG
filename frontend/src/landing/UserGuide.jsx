"use client";
import { motion } from "framer-motion";

const steps = [
  {
    step: "1",
    title: "Choose Your Search Mode",
    description:
      "Start with a natural language query or upload a research paper as a PDF or image.",
    icon: "🔍",
  },
  {
    step: "2",
    title: "Upload or Query",
    description:
      "Drop your file or type what you’re looking for — no strict keywords required.",
    icon: "📄",
  },
  {
    step: "3",
    title: "Semantic Interpretation",
    description:
      "The system understands context, intent, and relationships inside the paper.",
    icon: "🧠",
  },
  {
    step: "4",
    title: "Ready for Exploration",
    description:
      "Your search is now prepared for summaries, notes, and interactive discussion.",
    icon: "✨",
  },
];

export default function UserGuide() {
  return (
    <section className="relative py-36 px-6">
      <div className="relative z-10 max-w-7xl mx-auto">
        <motion.h2
          className="text-4xl md:text-5xl font-bold text-center mb-6 text-white"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
        >
          How Semantic Search Begins
        </motion.h2>

        <p className="text-center text-gray-400 max-w-3xl mx-auto mb-20 text-lg">
          Start your research by searching naturally or uploading papers.
          Everything else builds on this foundation.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10">
          {steps.map((step, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 50 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{
                duration: 0.6,
                delay: index * 0.15,
                ease: "easeOut",
              }}
              viewport={{ once: true }}
              whileHover={{ y: -10 }}
              className="group relative bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl p-10 min-h-70 shadow-xl hover:shadow-blue-500/20 hover:border-blue-500/40 transition-all duration-300"
            >
              {/* Step badge */}
              <div className="absolute -top-4 -right-4 w-10 h-10 rounded-full bg-blue-600 text-white flex items-center justify-center font-semibold">
                {step.step}
              </div>

              <div className="relative">
                <div className="text-5xl mb-6">{step.icon}</div>

                <h3 className="text-2xl font-semibold mb-4 text-white group-hover:text-blue-400 transition-colors">
                  {step.title}
                </h3>

                <p className="text-gray-400 text-base leading-relaxed">
                  {step.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
