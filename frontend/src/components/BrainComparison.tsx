"use client";

import { motion } from "framer-motion";

interface BrainComparisonProps {
  result: {
    sensory_profile: Record<string, number>;
    divergence_stats: { mean: number; max: number };
    n_asd_subjects: number;
    n_td_subjects: number;
    timesteps: number;
    stimulus_text?: string;
  };
}

const NETWORK_INFO: Record<
  string,
  { label: string; description: string; impact: string; ntExample: string; ndExample: string }
> = {
  motor: {
    label: "Motor / Body",
    description: "Movement, body awareness, coordination",
    impact: "May show different movement patterns, stimming, or motor planning",
    ntExample: "Hears a loud sound \u2192 brain registers it, body stays relaxed",
    ndExample: "Hears a loud sound \u2192 body tenses, may flinch, cover ears, or need to move",
  },
  visual: {
    label: "Visual",
    description: "Processing what you see",
    impact: "May notice details others miss, or find busy scenes overwhelming",
    ntExample: "Walks into a mall \u2192 takes in the whole scene, filters out clutter",
    ndExample: "Walks into a mall \u2192 notices every flickering light, every sign, can feel flooded",
  },
  attention: {
    label: "Attention",
    description: "Focusing and shifting focus",
    impact: "May hyperfocus on interests or struggle to shift attention",
    ntExample: "Teacher says 'now open your books' \u2192 switches tasks smoothly",
    ndExample: "Teacher says 'now open your books' \u2192 still processing the last topic, transition feels abrupt",
  },
  salience: {
    label: "Salience",
    description: "Deciding what's important",
    impact: "May prioritize different things as important vs background",
    ntExample: "In a meeting \u2192 focuses on the speaker, tunes out the AC hum",
    ndExample: "In a meeting \u2192 the AC hum feels as loud as the speaker, hard to filter",
  },
  emotional: {
    label: "Emotional",
    description: "Processing feelings and reactions",
    impact: "May experience emotions more intensely or differently",
    ntExample: "Friend seems sad \u2192 feels concern, offers comfort proportionally",
    ndExample: "Friend seems sad \u2192 absorbs their emotion fully, may feel overwhelmed or shut down",
  },
  control: {
    label: "Control",
    description: "Planning, decision-making",
    impact: "May prefer routine and predictability over spontaneous changes",
    ntExample: "Lunch plans change \u2192 'sure, let's go somewhere else instead'",
    ndExample: "Lunch plans change \u2192 feels disorienting, needs a moment to mentally rebuild the plan",
  },
  default_mode: {
    label: "Default Mode",
    description: "Self-reflection, imagination",
    impact: "May show different patterns of inner thought and self-awareness",
    ntExample: "Waiting for the bus \u2192 mind wanders casually between random topics",
    ndExample: "Waiting for the bus \u2192 deep-dives into one thought, builds a rich detailed inner world",
  },
};

export default function BrainComparison({ result }: BrainComparisonProps) {
  const profile = result.sensory_profile;
  const sorted = Object.entries(profile).sort(([, a], [, b]) => b - a);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="glass-card p-6 relative overflow-hidden"
    >
      {/* Ambient effects */}
      <div className="absolute -top-20 -right-20 w-40 h-40 rounded-full bg-[var(--neon-purple)]/10 blur-[60px] pointer-events-none" />

      <div className="relative z-10">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-8 h-8 rounded-lg bg-[var(--warning)]/10 flex items-center justify-center">
            <svg className="w-4 h-4 text-[var(--warning)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="text-lg font-bold">NT vs ND Difference Analysis</h3>
        </div>
        <p className="text-sm text-[var(--text-secondary)] mb-6">
          How each brain network responds differently to: &quot;{result.stimulus_text?.slice(0, 60) || "stimulus"}...&quot;
        </p>

        {/* Summary stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          {[
            { value: result.timesteps, label: "Time Points", color: "var(--accent)", icon: "clock" },
            { value: `${(result.divergence_stats.mean * 100).toFixed(1)}%`, label: "Mean Divergence", color: "var(--warning)", icon: "chart" },
            { value: `${(result.divergence_stats.max * 100).toFixed(1)}%`, label: "Peak Divergence", color: "var(--danger)", icon: "alert" },
          ].map((stat) => (
            <div key={stat.label} className="bg-[var(--bg-primary)]/80 rounded-xl p-4 text-center border border-white/5 hover:border-white/10 transition-colors">
              <div className="text-2xl font-bold" style={{ color: stat.color }}>
                {stat.value}
              </div>
              <div className="text-xs text-[var(--text-secondary)] mt-1">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Comparison table */}
        <div className="overflow-x-auto rounded-xl border border-white/5">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10 bg-[var(--bg-primary)]/50">
                <th className="text-left py-3 px-3 text-[var(--text-secondary)] font-medium">Brain Network</th>
                <th className="text-left py-3 px-3 text-[var(--text-secondary)] font-medium">Function</th>
                <th className="text-left py-3 px-3 text-[var(--success)] font-medium">NT Example</th>
                <th className="text-left py-3 px-3 text-[var(--warning)] font-medium">ND Example</th>
                <th className="text-center py-3 px-3 text-[var(--success)] font-medium">NT</th>
                <th className="text-center py-3 px-3 text-[var(--warning)] font-medium">ND</th>
                <th className="text-center py-3 px-3 text-[var(--text-secondary)] font-medium">Difference</th>
                <th className="text-left py-3 px-3 text-[var(--text-secondary)] font-medium">Impact</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map(([key, value], idx) => {
                const info = NETWORK_INFO[key] || { label: key, description: "", impact: "", ntExample: "", ndExample: "" };
                const pct = Math.round(value * 100);
                const barColor = pct > 70 ? "var(--danger)" : pct > 40 ? "var(--warning)" : "var(--success)";
                const level = pct > 70 ? "High" : pct > 40 ? "Moderate" : "Low";
                const ndDirection = pct > 50 ? "Heightened" : pct > 30 ? "Different" : "Similar";

                return (
                  <motion.tr
                    key={key}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className="border-b border-white/5 hover:bg-white/[0.03] transition"
                  >
                    <td className="py-3 px-3 font-medium text-white">{info.label}</td>
                    <td className="py-3 px-3 text-[var(--text-secondary)] text-xs">{info.description}</td>
                    <td className="py-3 px-3 text-xs text-[var(--success)]/80" style={{ maxWidth: "180px" }}>{info.ntExample}</td>
                    <td className="py-3 px-3 text-xs text-[var(--warning)]/80" style={{ maxWidth: "180px" }}>{info.ndExample}</td>
                    <td className="py-3 px-3 text-center">
                      <span className="text-[10px] px-2 py-1 rounded-full bg-[var(--success)]/10 text-[var(--success)] border border-[var(--success)]/20">Standard</span>
                    </td>
                    <td className="py-3 px-3 text-center">
                      <span className="text-[10px] px-2 py-1 rounded-full border" style={{ background: `color-mix(in srgb, ${barColor} 10%, transparent)`, color: barColor, borderColor: `color-mix(in srgb, ${barColor} 20%, transparent)` }}>
                        {ndDirection}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2 justify-center">
                        <div className="w-16 h-1.5 bg-[var(--bg-primary)] rounded-full overflow-hidden">
                          <motion.div
                            className="h-full rounded-full"
                            initial={{ width: 0 }}
                            animate={{ width: `${pct}%` }}
                            transition={{ delay: idx * 0.1, duration: 0.8 }}
                            style={{ background: barColor }}
                          />
                        </div>
                        <span className="text-xs font-mono font-bold min-w-[50px]" style={{ color: barColor }}>
                          {level} ({pct}%)
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-3 text-[var(--text-secondary)] text-xs">{info.impact}</td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="mt-4 p-3 bg-[var(--bg-primary)]/60 rounded-xl border border-white/5">
          <p className="text-xs text-[var(--text-secondary)]">
            Data source: ABIDE dataset ({result.n_asd_subjects} ASD + {result.n_td_subjects} TD subjects).
            Transform derived from statistically significant connectivity differences (p &lt; 0.05).
          </p>
        </div>
      </div>
    </motion.div>
  );
}
