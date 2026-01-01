
"use client";

import { motion } from "framer-motion";
import Particles from "react-tsparticles";

export default function AnimatedBackground({ children }) {
  return (
    <>
      {/* PARTICLES LAYER */}
      <div className="fixed inset-0 -z-20">
        <Particles
          options={{
            fullScreen: { enable: false },
            particles: {
              number: { value: 60 },
              color: { value: "#3b82f6" },
              links: {
                enable: true,
                color: "#3b82f6",
                opacity: 0.15,
              },
              move: { enable: true, speed: 0.35 },
              size: { value: 2 },
              opacity: { value: 0.3 },
            },
          }}
          className="w-full h-full"
        />
      </div>

      {/* ANIMATED GRADIENT OVERLAY */}
      <motion.div
        className="fixed inset-0 -z-10"
        animate={{
          backgroundPosition: ["0% 0%", "100% 100%", "0% 0%"],
        }}
        transition={{
          duration: 30,
          repeat: Infinity,
          ease: "linear",
        }}
        style={{
          background:
            "radial-gradient(circle at top left, rgba(59,130,246,0.12), transparent 60%), radial-gradient(circle at bottom right, rgba(37,99,235,0.12), transparent 60%), #020617",
          backgroundSize: "200% 200%",
        }}
      />

      {/* CONTENT */}
      <div className="relative min-h-screen text-white">
        {children}
      </div>
    </>
  );
}

