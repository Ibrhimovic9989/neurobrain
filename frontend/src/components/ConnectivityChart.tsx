"use client";

import { motion } from "framer-motion";

interface ConnectivityChartProps {
  data: {
    asd_subjects: number;
    td_subjects: number;
    network_differences: Record<string, number>;
  };
}

const NETWORK_LABELS: Record<string, string> = {
  Vis: "Visual",
  SomMot: "Somatomotor",
  DorsAttn: "Dorsal Attention",
  SalVentAttn: "Salience",
  Limbic: "Limbic",
  Cont: "Control",
  Default: "Default Mode",
};

const BAR_COLORS = [
  "from-[#6c63ff] to-[#4d7cff]",
  "from-[#00f0ff] to-[#6c63ff]",
  "from-[#b44aff] to-[#ff2d95]",
  "from-[#22c55e] to-[#06b6d4]",
  "from-[#f59e0b] to-[#ef4444]",
  "from-[#ec4899] to-[#b44aff]",
  "from-[#4d7cff] to-[#00f0ff]",
];

export default function ConnectivityChart({ data }: ConnectivityChartProps) {
  const entries = Object.entries(data.network_differences);
  const maxVal = Math.max(...entries.map(([, v]) => v));

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="glass-card p-6 relative overflow-hidden"
    >
      <div className="absolute -top-20 -left-20 w-40 h-40 rounded-full bg-[var(--neon-cyan)]/10 blur-[60px] pointer-events-none" />

      <div className="relative z-10">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[var(--neon-cyan)]/10 flex items-center justify-center">
              <svg className="w-4 h-4 text-[var(--neon-cyan)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5" />
              </svg>
            </div>
            <h3 className="text-lg font-bold">Network Connectivity Differences</h3>
          </div>
          <div className="flex gap-3">
            <span className="text-xs px-3 py-1.5 rounded-full bg-[var(--accent)]/10 text-[var(--accent)] border border-[var(--accent)]/20">
              ASD: {data.asd_subjects}
            </span>
            <span className="text-xs px-3 py-1.5 rounded-full bg-[var(--neon-cyan)]/10 text-[var(--neon-cyan)] border border-[var(--neon-cyan)]/20">
              TD: {data.td_subjects}
            </span>
          </div>
        </div>

        <div className="space-y-4">
          {entries.map(([network, value], idx) => {
            const pct = (value / maxVal) * 100;
            const label = NETWORK_LABELS[network] || network;

            return (
              <motion.div
                key={network}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.08 }}
                className="flex items-center gap-4 group"
              >
                <div className="w-36 text-sm text-right text-[var(--text-secondary)] flex-shrink-0 group-hover:text-white transition-colors">
                  {label}
                </div>
                <div className="flex-1 h-8 bg-[var(--bg-primary)]/80 rounded-lg overflow-hidden relative border border-white/5">
                  <motion.div
                    className={`h-full rounded-lg bg-gradient-to-r ${BAR_COLORS[idx % BAR_COLORS.length]}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ delay: idx * 0.1 + 0.2, duration: 1, ease: "easeOut" }}
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-mono text-white/80">
                    {value.toFixed(4)}
                  </span>
                </div>
              </motion.div>
            );
          })}
        </div>

        <div className="mt-8 p-4 bg-[var(--bg-primary)]/60 rounded-xl border border-white/5">
          <p className="text-sm text-[var(--text-secondary)]">
            <strong className="text-white">Reading this chart: </strong>
            Longer bars mean bigger differences in how brain networks
            communicate between autistic and non-autistic individuals. Data from
            {data.asd_subjects + data.td_subjects} real fMRI brain scans across multiple clinical sites.
          </p>
        </div>
      </div>
    </motion.div>
  );
}
