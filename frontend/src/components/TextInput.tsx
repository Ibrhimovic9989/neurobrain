"use client";

import { useState } from "react";

interface TextInputProps {
  onSubmit: (text: string) => void;
  loading?: boolean;
  placeholder?: string;
  buttonText?: string;
}

export default function TextInput({
  onSubmit,
  loading = false,
  placeholder = "Type a sentence to see how the brain responds...",
  buttonText = "Predict Brain Activity",
}: TextInputProps) {
  const [text, setText] = useState(
    "The child watched the colorful birds flying across the bright blue sky."
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim()) onSubmit(text.trim());
  };

  return (
    <form onSubmit={handleSubmit} className="glass-card p-6 relative overflow-hidden">
      {/* Holographic shimmer */}
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[var(--accent)]/3 to-transparent animate-shimmer pointer-events-none" style={{ backgroundSize: "200% 100%" }} />

      <div className="relative z-10">
        <label className="flex items-center gap-2 text-sm font-medium mb-3 text-[var(--text-secondary)]">
          <svg className="w-4 h-4 text-[var(--accent)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          Input Stimulus
        </label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={placeholder}
          rows={3}
          className="w-full bg-[var(--bg-primary)]/80 border border-white/10 rounded-xl p-4 text-[var(--text-primary)] placeholder:text-[var(--text-secondary)]/50 focus:outline-none focus:border-[var(--accent)]/50 focus:ring-1 focus:ring-[var(--accent)]/20 transition-all resize-none"
        />
        <button
          type="submit"
          disabled={loading || !text.trim()}
          className={`mt-4 w-full py-3.5 rounded-xl font-medium transition-all ${
            loading
              ? "bg-[var(--accent)]/50 cursor-wait animate-glow"
              : "btn-futuristic"
          } disabled:opacity-40`}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <span className="glow-neon-cyan">Processing neural prediction...</span>
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              {buttonText}
            </span>
          )}
        </button>
      </div>
    </form>
  );
}
