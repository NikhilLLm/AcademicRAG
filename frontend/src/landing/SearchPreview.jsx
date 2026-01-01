"use client";

import { motion } from "framer-motion";

const features = [
  {
    title: "Semantic Search Results",
    description:
      "Papers are ranked by meaning and context, not just keyword matches.",
    icon: "🧠",
  },
  {
    title: "Structured Notes",
    description:
      "Auto-generated summaries, key points, and section-wise breakdowns.",
    icon: "📝",
  },
  {
    title: "Interactive Chat",
    description:
      "Ask questions directly from the paper and explore concepts deeply.",
    icon: "💬",
  },
];

export default function SearchPreview() {
  return (
    <section className="relative py-36 px-6">
      <div className="max-w-7xl mx-auto relative z-10">
        <motion.h2
          className="text-4xl md:text-5xl font-bold text-center mb-6 text-white"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
        >
          What You Get After Searching
        </motion.h2>

        <p className="text-center text-gray-400 max-w-3xl mx-auto mb-20 text-lg">
          Once your search is understood, the platform organizes knowledge so
          you can explore faster and deeper.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{
                duration: 0.6,
                delay: index * 0.15,
                ease: "easeOut",
              }}
              viewport={{ once: true }}
              whileHover={{ y: -10 }}
              className="group relative bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl p-10 min-h-65 shadow-xl hover:shadow-blue-500/20 hover:border-blue-500/40 transition-all duration-300"
            >
              {/* subtle hover gradient */}
              <div className="absolute inset-0 rounded-3xl bg-linear-to-br from-blue-500/0 to-purple-500/0 group-hover:from-blue-500/5 group-hover:to-purple-500/5 transition-all duration-300" />

              <div className="relative">
                <div className="text-5xl mb-6">{feature.icon}</div>

                <h3 className="text-2xl font-semibold mb-4 text-white group-hover:text-blue-400 transition-colors">
                  {feature.title}
                </h3>

                <p className="text-gray-400 text-base leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
