"use client";

import { motion } from "framer-motion";

const features = [
  {
    id: "predict",
    num: "01",
    title: "Brain Prediction",
    description: "Input any text and watch how the brain processes it in real-time across 500+ regions with 20,484 cortical vertices.",
    tag: "Real-time",
  },
  {
    id: "compare",
    num: "02",
    title: "NT vs ND Comparison",
    description: "Compare neurotypical and neurodiverse brain responses side-by-side across 7 core brain networks.",
    tag: "Multi-site Data",
  },
  {
    id: "connectivity",
    num: "03",
    title: "ASD Connectivity",
    description: "Analyze how brain wiring differs in autism using real fMRI scans from 1,100+ subjects across 20 clinical sites.",
    tag: "fMRI Data",
  },
];

export default function FeatureCards({ onSelect }: { onSelect: (id: string) => void }) {
  return (
    <section className="py-20 px-6">
      <div className="max-w-[1024px] mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-12"
        >
          <span className="text-[10px] text-[var(--accent)] tracking-widest uppercase font-medium">Capabilities</span>
          <h2 className="text-[28px] tracking-tight mt-2">Three ways to explore</h2>
          <p className="text-[14px] text-[var(--muted)] mt-2 max-w-md font-light">
            Each module reveals a different dimension of how the neurodiverse brain processes information.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {features.map((f, i) => (
            <motion.button
              key={f.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              onClick={() => onSelect(f.id)}
              className="card p-6 text-left group cursor-pointer"
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-[10px] text-[var(--accent)] font-medium">{f.num}</span>
                <span className="text-[9px] px-2 py-0.5 rounded-full bg-[var(--accent)]/10 text-[var(--accent)] border border-[var(--accent)]/15">{f.tag}</span>
              </div>
              <h3 className="text-[15px] font-medium mb-2 group-hover:text-[var(--accent)] transition">{f.title}</h3>
              <p className="text-[12px] text-[var(--muted)] leading-relaxed font-light">{f.description}</p>
              <div className="flex items-center gap-1.5 mt-5 text-[11px] text-[var(--accent)] font-medium group-hover:gap-2.5 transition-all">
                <span>Explore</span>
                <span className="transition-transform group-hover:translate-x-0.5">→</span>
              </div>
            </motion.button>
          ))}
        </div>
      </div>
    </section>
  );
}
