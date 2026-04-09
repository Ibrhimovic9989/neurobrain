"use client";

import { motion } from "framer-motion";

interface SensoryProfileProps {
  profile: Record<string, number>;
}

const NETWORK_INFO: Record<string, { label: string; color: string; description: string }> = {
  visual: { label: "Visual", color: "#ef4444", description: "Processing what you see" },
  auditory: { label: "Auditory", color: "#f59e0b", description: "Processing what you hear" },
  language: { label: "Language", color: "#6c63ff", description: "Understanding words and speech" },
  default_mode: { label: "Default Mode", color: "#22c55e", description: "Internal thoughts, self-reflection" },
  motor: { label: "Motor", color: "#06b6d4", description: "Movement and body awareness" },
  social: { label: "Social", color: "#ec4899", description: "Understanding others' emotions" },
};

export default function SensoryProfile({ profile }: SensoryProfileProps) {
  const sorted = Object.entries(profile).sort(([, a], [, b]) => b - a);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="glass-card p-6 relative overflow-hidden"
    >
      <div className="absolute -bottom-20 -left-20 w-40 h-40 rounded-full bg-[var(--neon-pink)]/10 blur-[60px] pointer-events-none" />

      <div className="relative z-10">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-8 h-8 rounded-lg bg-[var(--neon-purple)]/10 flex items-center justify-center">
            <svg className="w-4 h-4 text-[var(--neon-purple)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="text-lg font-bold">Sensory Processing Profile</h3>
        </div>
        <p className="text-sm text-[var(--text-secondary)] mb-8">
          How differently the neurodiverse brain processes each type of information.
        </p>

        <div className="space-y-6">
          {sorted.map(([key, value], idx) => {
            const info = NETWORK_INFO[key] || { label: key, color: "#6c63ff", description: "" };
            const pct = Math.round(value * 100);

            return (
              <motion.div
                key={key}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
              >
                <div className="flex justify-between items-center mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full" style={{ background: info.color, boxShadow: `0 0 8px ${info.color}66` }} />
                    <span className="font-medium text-white text-sm">{info.label}</span>
                    <span className="text-xs text-[var(--text-secondary)]">{info.description}</span>
                  </div>
                  <span className="text-sm font-bold font-mono" style={{ color: info.color }}>
                    {pct}%
                  </span>
                </div>
                <div className="w-full h-2 bg-[var(--bg-primary)] rounded-full overflow-hidden border border-white/5">
                  <motion.div
                    className="h-full rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ delay: idx * 0.1 + 0.2, duration: 1, ease: "easeOut" }}
                    style={{ background: `linear-gradient(90deg, ${info.color}, ${info.color}88)`, boxShadow: `0 0 10px ${info.color}44` }}
                  />
                </div>
              </motion.div>
            );
          })}
        </div>

        <div className="mt-8 p-4 bg-[var(--bg-primary)]/60 rounded-xl border border-white/5">
          <p className="text-sm text-[var(--text-secondary)]">
            <strong className="text-white">What this means: </strong>
            The highest-scoring networks show where the neurodiverse brain
            processes information most differently. This helps design
            personalized accommodations and learning strategies.
          </p>
        </div>
      </div>
    </motion.div>
  );
}
