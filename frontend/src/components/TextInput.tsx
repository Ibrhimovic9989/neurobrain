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
    <form onSubmit={handleSubmit} className="glass-card p-6">
      <label className="block text-sm font-medium mb-3 text-[var(--text-secondary)]">
        Input Stimulus
      </label>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={placeholder}
        rows={3}
        className="w-full bg-[var(--bg-primary)] border border-white/10 rounded-xl p-4 text-[var(--text-primary)] placeholder:text-[var(--text-secondary)]/50 focus:outline-none focus:border-[var(--accent)] transition resize-none"
      />
      <button
        type="submit"
        disabled={loading || !text.trim()}
        className={`mt-4 w-full py-3 rounded-xl font-medium transition-all ${
          loading
            ? "bg-[var(--accent)]/50 cursor-wait animate-glow"
            : "bg-[var(--accent)] hover:opacity-90"
        } disabled:opacity-40`}
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Processing brain prediction...
          </span>
        ) : (
          buttonText
        )}
      </button>
    </form>
  );
}
