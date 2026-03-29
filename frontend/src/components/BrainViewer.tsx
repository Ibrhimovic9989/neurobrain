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
    <div className="glass-card p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Brain Activity</h3>
        <div className="flex items-center gap-3">
          <button
            onClick={play}
            disabled={playing}
            className="px-4 py-2 bg-[var(--accent)] rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50 transition"
          >
            {playing ? "Playing..." : "Play Timeline"}
          </button>
          <span className="text-sm text-[var(--text-secondary)]">
            t = {currentStep}s
          </span>
        </div>
      </div>

      {/* Main brain image */}
      <div className="bg-black rounded-xl overflow-hidden">
        <img
          src={`data:image/png;base64,${images[currentStep]}`}
          alt={`Brain activity at t=${currentStep}s`}
          className="w-full"
        />
      </div>

      {/* Timeline scrubber */}
      <div className="mt-4">
        <input
          type="range"
          min={0}
          max={images.length - 1}
          value={currentStep}
          onChange={(e) => setCurrentStep(Number(e.target.value))}
          className="w-full accent-[var(--accent)]"
        />
        <div className="flex justify-between text-xs text-[var(--text-secondary)] mt-1">
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
            className={`flex-shrink-0 rounded-lg overflow-hidden border-2 transition ${
              i === currentStep
                ? "border-[var(--accent)] glow"
                : "border-transparent opacity-60 hover:opacity-100"
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
  );
}
