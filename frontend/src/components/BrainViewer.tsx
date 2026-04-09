"use client";

import { useState } from "react";

interface BrainViewerProps {
  images: string[];
}

export default function BrainViewer({ images }: BrainViewerProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [playing, setPlaying] = useState(false);

  const play = () => {
    setPlaying(true);
    let step = 0;
    const interval = setInterval(() => {
      step++;
      if (step >= images.length) {
        clearInterval(interval);
        setPlaying(false);
        return;
      }
      setCurrentStep(step);
    }, 800);
  };

  return (
    <div className="glass-card p-6 relative overflow-hidden">
      {/* Ambient glow */}
      <div className="absolute -top-20 -right-20 w-40 h-40 rounded-full bg-[var(--accent)]/10 blur-[60px] pointer-events-none" />

      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[var(--accent)]/10 flex items-center justify-center">
              <svg className="w-4 h-4 text-[var(--accent)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 2C8 2 4 6 4 10c0 3 1.5 5 4 6.5V22h8v-5.5c2.5-1.5 4-3.5 4-6.5 0-4-4-8-8-8z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold">Brain Activity</h3>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={play}
              disabled={playing}
              className="px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-50 btn-futuristic text-xs"
            >
              {playing ? (
                <span className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[var(--neon-cyan)] animate-pulse" />
                  Playing...
                </span>
              ) : (
                <span className="flex items-center gap-1.5">
                  <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                  Play Timeline
                </span>
              )}
            </button>
            <div className="px-3 py-1.5 rounded-lg bg-[var(--bg-primary)]/80 border border-white/5">
              <span className="text-xs text-[var(--neon-cyan)] font-mono">
                t = {currentStep}s
              </span>
            </div>
          </div>
        </div>

        {/* Main brain image */}
        <div className="bg-black/50 rounded-xl overflow-hidden border border-white/5 relative group">
          <img
            src={`data:image/png;base64,${images[currentStep]}`}
            alt={`Brain activity at t=${currentStep}s`}
            className="w-full"
          />
          {/* Scan overlay effect */}
          <div className="absolute inset-0 bg-gradient-to-b from-[var(--neon-cyan)]/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
        </div>

        {/* Timeline scrubber */}
        <div className="mt-4">
          <div className="relative">
            <input
              type="range"
              min={0}
              max={images.length - 1}
              value={currentStep}
              onChange={(e) => setCurrentStep(Number(e.target.value))}
              className="w-full accent-[var(--accent)] h-1.5 appearance-none bg-[var(--bg-primary)] rounded-full cursor-pointer"
              style={{
                background: `linear-gradient(to right, #6c63ff 0%, #00f0ff ${(currentStep / (images.length - 1)) * 100}%, rgba(255,255,255,0.1) ${(currentStep / (images.length - 1)) * 100}%, rgba(255,255,255,0.1) 100%)`
              }}
            />
          </div>
          <div className="flex justify-between text-xs text-[var(--text-secondary)] mt-1 font-mono">
            <span>0s</span>
            <span>{images.length - 1}s</span>
          </div>
        </div>

        {/* Thumbnail strip */}
        <div className="flex gap-2 mt-4 overflow-x-auto pb-2">
          {images.map((img, i) => (
            <button
              key={i}
              onClick={() => setCurrentStep(i)}
              className={`flex-shrink-0 rounded-lg overflow-hidden border-2 transition-all duration-300 ${
                i === currentStep
                  ? "border-[var(--accent)] glow scale-105"
                  : "border-transparent opacity-50 hover:opacity-80 hover:border-white/10"
              }`}
            >
              <img
                src={`data:image/png;base64,${img}`}
                alt={`t=${i}s`}
                className="w-20 h-12 object-cover"
              />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
