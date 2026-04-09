"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";

const STATS = [
  { value: 177, suffix: "M", label: "Parameters" },
  { value: 500, suffix: "+", label: "Brain Regions" },
  { value: 1100, suffix: "+", label: "Subjects" },
  { value: 20484, suffix: "", label: "Vertices" },
];

function AnimatedCounter({ value, suffix, duration = 2000 }: { value: number; suffix: string; duration?: number }) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const hasAnimated = useRef(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasAnimated.current) {
          hasAnimated.current = true;
          const start = performance.now();
          const animate = (now: number) => {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            setCount(Number((eased * value).toFixed(value % 1 !== 0 ? 1 : 0)));
            if (progress < 1) requestAnimationFrame(animate);
          };
          requestAnimationFrame(animate);
        }
      },
      { threshold: 0.5 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [value, duration]);

  return (
    <span ref={ref} className="tabular-nums">
      {value > 999 ? count.toLocaleString() : count}{suffix}
    </span>
  );
}

export default function HeroSection({ onExplore }: { onExplore: () => void }) {
  return (
    <section className="relative pt-28 pb-20 px-6 overflow-hidden">
      {/* Subtle glow */}
      <div className="absolute w-[500px] h-[300px] rounded-full bg-[var(--accent)] opacity-[0.03] blur-[100px] top-20 right-1/4 pointer-events-none" />
      <div className="absolute w-[400px] h-[250px] rounded-full bg-[var(--accent2)] opacity-[0.02] blur-[100px] bottom-20 left-1/4 pointer-events-none" />

      <div className="max-w-[1024px] mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          {/* Badge */}
          <div className="flex items-center gap-2 mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)]" />
            <span className="text-[11px] text-[var(--muted)] tracking-widest uppercase">AI Brain Encoding Platform</span>
          </div>

          {/* Heading */}
          <h1 className="text-[clamp(2rem,5vw,3.8rem)] leading-[1.08] tracking-[-0.03em] font-medium max-w-[700px]">
            Decode the{" "}
            <span className="gradient-text-hero">Neurodiverse</span>
            <br />Mind
          </h1>

          <p className="text-[15px] text-[var(--muted)] mt-5 max-w-[480px] leading-relaxed font-light">
            Visualize real-time brain activity, compare neurotypical vs neurodiverse
            responses, and explore how autism shapes neural connectivity.
          </p>

          {/* CTAs */}
          <div className="flex items-center gap-3 mt-8">
            <button onClick={onExplore} className="btn-futuristic text-[13px] px-6 py-3">
              Start Exploring
            </button>
            <a href="#" className="text-[13px] px-6 py-3 rounded-xl border border-[var(--border)] text-[var(--muted)] hover:text-white hover:border-white/15 transition font-medium">
              Learn More
            </a>
          </div>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.7 }}
          className="flex gap-10 mt-14 pt-7 border-t border-[var(--border)]"
        >
          {STATS.map((stat) => (
            <div key={stat.label}>
              <div className="text-[22px] font-medium text-white tabular-nums tracking-tight">
                <AnimatedCounter value={stat.value} suffix={stat.suffix} />
              </div>
              <div className="text-[10px] text-[var(--muted)] mt-0.5">{stat.label}</div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
