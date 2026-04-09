"use client";

import { motion } from "framer-motion";

const PIPELINE = ["Text Input", "Feature Encoding", "Brain Mapping", "ND Transform", "Visualization"];

export default function TechShowcase() {
  return (
    <section className="py-20 px-6">
      <div className="max-w-[1024px] mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-12"
        >
          <span className="text-[10px] text-[var(--accent)] tracking-widest uppercase font-medium">Technology</span>
          <h2 className="text-[28px] tracking-tight mt-2">Built on cutting-edge science</h2>
          <p className="text-[14px] text-[var(--muted)] mt-2 max-w-md font-light">
            Combining deep learning with the largest open-source autism neuroimaging data.
          </p>
        </motion.div>

        {/* Pipeline */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="card-static p-6"
        >
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            {PIPELINE.map((step, i) => (
              <div key={step} className="flex items-center gap-3">
                <div className="flex flex-col items-center">
                  <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[var(--accent)] to-[var(--accent2)] flex items-center justify-center text-white text-[11px] font-semibold">
                    {i + 1}
                  </div>
                  <span className="text-[10px] text-[var(--muted)] mt-2 whitespace-nowrap font-light">{step}</span>
                </div>
                {i < PIPELINE.length - 1 && (
                  <div className="hidden md:block w-12 h-px bg-[var(--border)]" />
                )}
              </div>
            ))}
          </div>
        </motion.div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
          {[
            ["177M", "Model Parameters"],
            ["8-Layer", "Transformer Depth"],
            ["20,484", "Cortical Vertices"],
            ["2 Hz", "Temporal Resolution"],
          ].map(([val, label], i) => (
            <motion.div
              key={label}
              initial={{ opacity: 0, y: 15 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className="card-static p-4 text-center"
            >
              <div className="text-[16px] font-medium text-white tabular-nums">{val}</div>
              <div className="text-[10px] text-[var(--muted)] mt-1">{label}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
