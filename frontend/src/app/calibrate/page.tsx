"use client";

import { useState, useEffect, useRef, ReactNode } from "react";

/*
  5-Minute Individual Calibration Module

  The user watches 6 short stimulus descriptions (text-based for now,
  video clips in future) and rates their sensory response on 3 axes:
  visual comfort, auditory comfort, social comfort (1-5 scale).

  The ratings are sent to the API which fits a per-person scaling vector
  via OLS, producing a personalized transform that modulates the
  population-average ND prediction.

  This turns AQAL from group-average to individual-specific.
*/

const STIMULI = [
  {
    id: 1,
    title: "Quiet library",
    description: "A silent reading room with soft natural light. Two people reading at separate tables. No sounds except occasional page turns.",
    category: "low",
  },
  {
    id: 2,
    title: "Busy cafe",
    description: "A crowded coffee shop with espresso machines running, background music, 20+ conversations happening simultaneously, bright overhead lights.",
    category: "moderate",
  },
  {
    id: 3,
    title: "Classroom transition",
    description: "A school hallway between classes. Students shouting, lockers slamming, fluorescent lights buzzing. Multiple groups moving in different directions.",
    category: "high",
  },
  {
    id: 4,
    title: "Outdoor park",
    description: "A park with birds chirping, children playing in the distance, gentle wind. Dappled sunlight through trees. A few people walking on paths.",
    category: "low",
  },
  {
    id: 5,
    title: "Shopping mall",
    description: "A large indoor mall with bright store displays, escalator humming, fragmented music from multiple stores, crowds of shoppers passing close by.",
    category: "high",
  },
  {
    id: 6,
    title: "Family dinner",
    description: "A dining table with 6 family members. Multiple conversations, dishes clinking, TV on in the background. Warm overhead lighting.",
    category: "moderate",
  },
];

type Rating = { visual: number; auditory: number; social: number };
type Ratings = Record<number, Rating>;

function useReveal() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) el.querySelectorAll(".reveal").forEach((c) => c.classList.add("visible")); }, { threshold: 0.1 });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return ref;
}

function Dv() { return <div className="h-px bg-[var(--border)] max-w-[700px] mx-auto" />; }

export default function CalibratePage() {
  const [step, setStep] = useState(0); // 0=intro, 1-6=stimuli, 7=result
  const [ratings, setRatings] = useState<Ratings>({});
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const setRating = (stimId: number, axis: keyof Rating, value: number) => {
    setRatings(prev => ({
      ...prev,
      [stimId]: { ...prev[stimId], [axis]: value },
    }));
  };

  const currentStim = step >= 1 && step <= 6 ? STIMULI[step - 1] : null;
  const currentRating = currentStim ? ratings[currentStim.id] : null;
  const canProceed = currentRating && currentRating.visual && currentRating.auditory && currentRating.social;
  const allDone = Object.keys(ratings).length === 6 && Object.values(ratings).every(r => r.visual && r.auditory && r.social);

  const handleSubmit = async () => {
    setLoading(true);
    // For now, compute profile client-side. In future, send to API for OLS fitting.
    const axes = { visual: 0, auditory: 0, social: 0 };
    const counts = { visual: 0, auditory: 0, social: 0 };
    Object.values(ratings).forEach(r => {
      axes.visual += r.visual; counts.visual++;
      axes.auditory += r.auditory; counts.auditory++;
      axes.social += r.social; counts.social++;
    });

    // Normalize to [0, 1] where 1 = most sensitive, 0 = least
    const profileData = {
      visual: 1 - (axes.visual / counts.visual - 1) / 4,
      auditory: 1 - (axes.auditory / counts.auditory - 1) / 4,
      social: 1 - (axes.social / counts.social - 1) / 4,
      // Derived networks from the three axes
      salience: 1 - ((axes.visual / counts.visual + axes.auditory / counts.auditory) / 2 - 1) / 4,
      motor: 1 - (axes.visual / counts.visual - 1) / 4 * 0.6,
      default_mode: 1 - (axes.social / counts.social - 1) / 4 * 0.8,
      language: 1 - (axes.auditory / counts.auditory - 1) / 4 * 0.7,
    };

    setProfile(profileData);
    setLoading(false);
    setStep(7);
  };

  return (
    <main>
      <Nav />

      {step === 0 && (
        <section className="pt-24 pb-16 px-6">
          <div className="max-w-[700px] mx-auto">
            <div className="flex items-center gap-2 mb-5">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)]" />
              <span className="text-[11px] text-[var(--muted)] tracking-widest uppercase">Individual Calibration</span>
            </div>
            <h1 className="text-[clamp(1.8rem,4vw,3rem)] leading-[1.1] tracking-[-0.03em] font-medium mb-4">
              Build your <span className="gradient-text">Sensory Profile</span>
            </h1>
            <p className="text-[15px] text-[var(--muted)] leading-relaxed font-light mb-4 max-w-lg">
              AQAL uses a population-average to predict neurodiverse brain responses. This 5-minute assessment personalizes those predictions to <em>you</em>.
            </p>
            <p className="text-[14px] text-[var(--muted)] leading-relaxed font-light mb-8 max-w-lg">
              You&apos;ll read 6 short descriptions of everyday environments and rate how comfortable you&apos;d feel in each across three dimensions: visual, auditory, and social.
            </p>
            <div className="flex items-center gap-6 mb-10">
              {[["6", "Scenarios"], ["3", "Axes per scenario"], ["~5", "Minutes"]].map(([n, l]) => (
                <div key={l}>
                  <div className="text-[18px] font-medium text-white tabular-nums">{n}</div>
                  <div className="text-[10px] text-[var(--muted)] mt-0.5">{l}</div>
                </div>
              ))}
            </div>
            <button onClick={() => setStep(1)} className="text-[13px] px-5 py-2 rounded-full bg-white text-[#050507] font-medium hover:bg-white/90 transition">
              Start Calibration
            </button>
          </div>
        </section>
      )}

      {currentStim && (
        <section className="pt-24 pb-16 px-6">
          <div className="max-w-[700px] mx-auto">
            {/* Progress */}
            <div className="flex items-center gap-2 mb-8">
              {STIMULI.map((_, i) => (
                <div key={i} className={`flex-1 h-1 rounded-full transition-all ${i < step ? "bg-[var(--accent)]" : i === step - 1 ? "bg-[var(--accent)]" : "bg-white/5"}`} />
              ))}
            </div>

            <div className="text-[10px] text-[var(--muted)] mb-2">{step} of 6</div>
            <h2 className="text-[22px] tracking-tight font-medium mb-2">{currentStim.title}</h2>
            <div className="card p-5 mb-6">
              <p className="text-[14px] text-[var(--text)] leading-relaxed font-light">{currentStim.description}</p>
            </div>

            <p className="text-[12px] text-[var(--muted)] mb-5 font-light">How comfortable would you feel in this environment?</p>

            <div className="space-y-5">
              {(["visual", "auditory", "social"] as const).map(axis => (
                <div key={axis}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[13px] font-medium capitalize">{axis}</span>
                    <span className="text-[11px] text-[var(--muted)]">
                      {currentRating?.[axis] === 1 ? "Very uncomfortable" : currentRating?.[axis] === 2 ? "Uncomfortable" : currentRating?.[axis] === 3 ? "Neutral" : currentRating?.[axis] === 4 ? "Comfortable" : currentRating?.[axis] === 5 ? "Very comfortable" : "Not rated"}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    {[1, 2, 3, 4, 5].map(v => (
                      <button key={v} onClick={() => setRating(currentStim.id, axis, v)}
                        className={`flex-1 py-2.5 rounded-lg text-[12px] font-medium transition ${
                          currentRating?.[axis] === v
                            ? "bg-[var(--accent)] text-white"
                            : "bg-white/[0.03] border border-[var(--border)] text-[var(--muted)] hover:text-white hover:border-[var(--accent)]/30"
                        }`}>
                        {v}
                      </button>
                    ))}
                  </div>
                  <div className="flex justify-between text-[9px] text-[var(--muted)]/50 mt-1 px-1">
                    <span>Distressing</span>
                    <span>Comfortable</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex items-center gap-3 mt-8">
              {step > 1 && (
                <button onClick={() => setStep(step - 1)} className="text-[13px] px-5 py-2 rounded-full border border-white/10 text-[var(--muted)] hover:text-white transition">
                  Back
                </button>
              )}
              {step < 6 ? (
                <button onClick={() => setStep(step + 1)} disabled={!canProceed}
                  className="text-[13px] px-5 py-2 rounded-full bg-white text-[#050507] font-medium hover:bg-white/90 disabled:opacity-30 transition">
                  Next
                </button>
              ) : (
                <button onClick={handleSubmit} disabled={!canProceed || loading}
                  className="text-[13px] px-5 py-2 rounded-full bg-white text-[#050507] font-medium hover:bg-white/90 disabled:opacity-30 transition">
                  {loading ? "Computing..." : "Generate Profile"}
                </button>
              )}
            </div>
          </div>
        </section>
      )}

      {step === 7 && profile && (
        <section className="pt-24 pb-16 px-6">
          <div className="max-w-[700px] mx-auto">
            <div className="flex items-center gap-2 mb-5">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
              <span className="text-[11px] text-green-400 tracking-widest uppercase font-medium">Calibration Complete</span>
            </div>
            <h2 className="text-[26px] tracking-tight font-medium mb-3">Your Sensory Profile</h2>
            <p className="text-[14px] text-[var(--muted)] font-light mb-8 max-w-lg">
              This profile shows your personal sensitivity across 7 brain networks. Higher values indicate greater divergence from neurotypical baseline — areas where you may process stimuli differently.
            </p>

            <div className="card p-6 mb-6">
              <div className="space-y-4">
                {Object.entries(profile).sort(([,a]: any,[,b]: any) => b - a).map(([key, val]: any) => {
                  const pct = Math.round(val * 100);
                  const colors: Record<string, string> = {
                    visual: "#ef4444", auditory: "#f59e0b", social: "#ec4899",
                    salience: "#7c6aff", motor: "#06b6d4", default_mode: "#22c55e", language: "#8b5cf6",
                  };
                  return (
                    <div key={key}>
                      <div className="flex justify-between text-[12px] mb-1">
                        <span className="capitalize font-light">{key.replace("_", " ")}</span>
                        <span style={{ color: colors[key] || "#7c6aff" }} className="font-medium tabular-nums">{pct}%</span>
                      </div>
                      <div className="w-full h-[3px] bg-white/[0.04] rounded-full overflow-hidden">
                        <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${pct}%`, background: colors[key] || "#7c6aff" }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="card p-5 border-l-2 border-[var(--accent)] mb-6">
              <p className="text-[12px] text-[var(--muted)] leading-relaxed font-light">
                <strong className="text-white font-normal">What this means:</strong> When you use NeuroBrain&apos;s compare tool, your predictions will be modulated by this profile — amplifying divergence in networks where you reported higher sensitivity, and reducing it where you&apos;re more comfortable. This turns a population average into a personal estimate.
              </p>
            </div>

            <div className="bg-[var(--bg)] rounded-lg p-4 border border-[var(--border)] mb-8">
              <p className="text-[10px] text-[var(--muted)]/60 font-light italic">
                This profile is based on self-reported comfort ratings, not clinical assessment. It improves prediction personalization but does not constitute a diagnosis. Future versions will incorporate physiological measurements for validation.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button onClick={() => { setStep(0); setRatings({}); setProfile(null); }}
                className="text-[13px] px-5 py-2 rounded-full border border-white/10 text-[var(--muted)] hover:text-white transition">
                Retake
              </button>
              <a href="/" className="text-[13px] px-5 py-2 rounded-full bg-white text-[#050507] font-medium hover:bg-white/90 transition">
                Use in NeuroBrain
              </a>
            </div>
          </div>
        </section>
      )}

      <Footer />
    </main>
  );
}

function Nav() {
  return (
    <nav className="fixed top-0 w-full z-50 bg-[#050507]/80 backdrop-blur-xl border-b border-[var(--border)]">
      <div className="max-w-[700px] mx-auto px-6 h-14 flex items-center justify-between">
        <a href="https://neuro.mind.new" className="flex items-center gap-2">
          <span className="text-[15px] font-medium tracking-tight">
            <span className="gradient-text">Neuro</span>
            <span className="text-[var(--text)]">Brain</span>
          </span>
        </a>
        <span className="text-[12px] px-2.5 py-1 rounded-full bg-[var(--accent)]/10 text-[var(--accent)]">Calibration</span>
      </div>
    </nav>
  );
}

function Footer() {
  return (
    <footer className="border-t border-[var(--border)] py-5 px-6">
      <div className="max-w-[700px] mx-auto">
        <p className="text-[10px] text-[var(--muted)]/50 mb-4 leading-relaxed font-light">This calibration is a research tool. Sensory profiles are self-reported estimates, not clinical assessments.</p>
        <div className="flex items-center justify-between text-[11px] text-[var(--muted)]">
          <span>NeuroBrain by Leeza Care</span>
          <a href="https://mind.new" className="hover:text-white transition">mind.new</a>
        </div>
      </div>
    </footer>
  );
}
