"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";

interface InterpretationProps {
  data: any;
  context: "predict" | "compare" | "connectivity";
}

export default function Interpretation({ data, context }: InterpretationProps) {
  const [text, setText] = useState<string>("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!data) return;
    setLoading(true);
    setText("");

    fetch(
      "https://neurobrain-api.eastus.cloudapp.azure.com/api/interpret",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ context, data }),
      }
    )
      .then((res) => res.json())
      .then((result) => setText(result.interpretation || ""))
      .catch(() => setText("Interpretation unavailable."))
      .finally(() => setLoading(false));
  }, [data, context]);

  if (!data) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="glass-card p-6 relative overflow-hidden"
    >
      {/* Left accent border */}
      <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-[var(--accent)] via-[var(--neon-cyan)] to-[var(--neon-purple)]" />

      {/* Ambient glow */}
      <div className="absolute -bottom-10 -left-10 w-32 h-32 rounded-full bg-[var(--accent)]/10 blur-[40px] pointer-events-none" />

      <div className="relative z-10 pl-4">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 rounded-lg bg-[var(--accent)]/10 flex items-center justify-center">
            <svg
              className="w-4 h-4 text-[var(--accent)]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
          </div>
          <h4 className="font-bold text-white">
            AI Interpretation
          </h4>
          <span className="text-[10px] uppercase tracking-widest text-[var(--neon-cyan)] font-medium px-2 py-0.5 rounded-full bg-[var(--neon-cyan)]/10 border border-[var(--neon-cyan)]/20">
            GPT-4 Powered
          </span>
        </div>

        {loading ? (
          <div className="flex items-center gap-3 text-[var(--text-secondary)] py-4">
            <div className="relative w-5 h-5">
              <div className="absolute inset-0 rounded-full border-2 border-[var(--accent)]/20" />
              <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-[var(--accent)] animate-spin" />
            </div>
            <span className="text-sm">Generating neural interpretation...</span>
            <div className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="w-1.5 h-1.5 rounded-full bg-[var(--accent)]"
                  style={{ animation: `pulse-glow 1.5s ease-in-out ${i * 0.2}s infinite` }}
                />
              ))}
            </div>
          </div>
        ) : (
          <div
            className="text-[var(--text-primary)] leading-relaxed text-sm"
            dangerouslySetInnerHTML={{
              __html: text
                .replace(/\*\*(.*?)\*\*/g, "<strong class='text-white'>$1</strong>")
                .replace(/\n/g, "<br />"),
            }}
          />
        )}
      </div>
    </motion.div>
  );
}
