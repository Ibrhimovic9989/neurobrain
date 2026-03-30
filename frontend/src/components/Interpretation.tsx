"use client";

import { useState, useEffect } from "react";

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
    <div className="glass-card p-6 border-l-4 border-[var(--accent)]">
      <div className="flex items-center gap-2 mb-3">
        <svg
          className="w-5 h-5 text-[var(--accent)]"
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
        <h4 className="font-semibold text-[var(--accent)]">
          AI Interpretation
        </h4>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-[var(--text-secondary)]">
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
              fill="none"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          Generating interpretation...
        </div>
      ) : (
        <p className="text-[var(--text-primary)] leading-relaxed whitespace-pre-line">
          {text}
        </p>
      )}
    </div>
  );
}
