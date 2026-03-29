"use client";

export default function Header() {
  return (
    <header className="border-b border-white/5">
      <div className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            <span className="text-[var(--accent)]">Neuro</span>Brain
          </h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            AI-powered brain model for neurodiversity
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-[var(--success)] animate-pulse" />
          <span className="text-xs text-[var(--text-secondary)]">
            TRIBE v2 &middot; 177M params
          </span>
        </div>
      </div>
    </header>
  );
}
