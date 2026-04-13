"use client";

import { useState, useRef, useEffect } from "react";

const NETWORKS = [
  { key: "visual", label: "Visual", color: "#ef4444", icon: "eye" },
  { key: "auditory", label: "Auditory", color: "#f59e0b", icon: "ear" },
  { key: "social", label: "Social", color: "#ec4899", icon: "people" },
  { key: "salience", label: "Salience", color: "#7c6aff", icon: "filter" },
  { key: "motor", label: "Motor", color: "#06b6d4", icon: "body" },
  { key: "default_mode", label: "Default Mode", color: "#22c55e", icon: "brain" },
  { key: "language", label: "Language", color: "#8b5cf6", icon: "speech" },
];

const SCENARIOS = [
  { id: 1, title: "Quiet library", desc: "Silent reading room with soft natural light. Two people reading. Occasional page turns.", cat: "low" },
  { id: 2, title: "Busy cafe", desc: "Crowded coffee shop, espresso machines, background music, 20+ conversations, bright lights.", cat: "high" },
  { id: 3, title: "Classroom transition", desc: "School hallway between classes. Students shouting, lockers slamming, fluorescent lights.", cat: "high" },
  { id: 4, title: "Outdoor park", desc: "Birds chirping, children in distance, gentle wind, dappled sunlight, a few walkers.", cat: "low" },
  { id: 5, title: "Shopping mall", desc: "Bright displays, escalator humming, music from stores, crowds passing close.", cat: "high" },
  { id: 6, title: "Family dinner", desc: "6 family members, multiple conversations, dishes clinking, TV on, warm lighting.", cat: "moderate" },
];

type Rating = { visual: number; auditory: number; social: number };

export default function PassportPage() {
  const [step, setStep] = useState(0); // 0=intro, 1-6=scenarios, 7=name, 8=result
  const [ratings, setRatings] = useState<Record<number, Rating>>({});
  const [name, setName] = useState("");
  const [profile, setProfile] = useState<Record<string, number> | null>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  const currentScenario = step >= 1 && step <= 6 ? SCENARIOS[step - 1] : null;
  const currentRating = currentScenario ? ratings[currentScenario.id] : null;
  const canNext = currentRating && currentRating.visual && currentRating.auditory && currentRating.social;

  const setR = (id: number, axis: keyof Rating, val: number) => {
    setRatings(prev => ({ ...prev, [id]: { ...prev[id], [axis]: val } }));
  };

  const computeProfile = () => {
    const axes = { visual: 0, auditory: 0, social: 0 };
    let count = 0;
    Object.values(ratings).forEach(r => {
      axes.visual += r.visual; axes.auditory += r.auditory; axes.social += r.social; count++;
    });
    return {
      visual: Math.round((1 - (axes.visual / count - 1) / 4) * 100),
      auditory: Math.round((1 - (axes.auditory / count - 1) / 4) * 100),
      social: Math.round((1 - (axes.social / count - 1) / 4) * 100),
      salience: Math.round((1 - ((axes.visual / count + axes.auditory / count) / 2 - 1) / 4) * 100),
      motor: Math.round((1 - (axes.visual / count - 1) / 4 * 0.6) * 100),
      default_mode: Math.round((1 - (axes.social / count - 1) / 4 * 0.8) * 100),
      language: Math.round((1 - (axes.auditory / count - 1) / 4 * 0.7) * 100),
    };
  };

  const handleGenerate = () => {
    setProfile(computeProfile());
    setStep(8);
  };

  const shareUrl = typeof window !== "undefined" && profile && name
    ? `${window.location.origin}/passport?name=${encodeURIComponent(name)}&data=${encodeURIComponent(JSON.stringify(profile))}`
    : "";

  const copyLink = () => {
    navigator.clipboard.writeText(shareUrl);
    alert("Link copied!");
  };

  const downloadImage = async () => {
    if (!cardRef.current) return;
    try {
      const html2canvas = (await import("html2canvas")).default;
      const canvas = await html2canvas(cardRef.current, { backgroundColor: "#050507", scale: 2 });
      const link = document.createElement("a");
      link.download = `sensory-passport-${name.replace(/\s+/g, "-").toLowerCase()}.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
    } catch {
      alert("Install html2canvas for image export: npm i html2canvas");
    }
  };

  // Check URL params for shared passport
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const sharedName = params.get("name");
    const sharedData = params.get("data");
    if (sharedName && sharedData) {
      try {
        setName(sharedName);
        setProfile(JSON.parse(sharedData));
        setStep(8);
      } catch {}
    }
  }, []);

  return (
    <main>
      <Nav />

      {/* Intro */}
      {step === 0 && (
        <section className="pt-24 pb-16 px-6">
          <div className="max-w-[700px] mx-auto">
            <div className="flex items-center gap-2 mb-5">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)]" />
              <span className="text-[11px] text-[var(--muted)] tracking-widest uppercase">Sensory Passport</span>
            </div>
            <h1 className="text-[clamp(1.8rem,4vw,3rem)] leading-[1.1] tracking-[-0.03em] font-medium mb-4">
              Your personal <span className="gradient-text">Sensory Profile</span>
            </h1>
            <p className="text-[15px] text-[var(--muted)] leading-relaxed font-light mb-4 max-w-lg">
              A portable document showing your sensory processing patterns across 7 brain networks. Share it with schools, therapists, or workplaces so they understand your sensory needs.
            </p>
            <div className="flex items-center gap-6 mb-8 text-[var(--muted)]">
              {[["6", "Scenarios"], ["~5", "Minutes"], ["7", "Networks"]].map(([n, l]) => (
                <div key={l}><div className="text-[18px] font-medium text-white tabular-nums">{n}</div><div className="text-[10px] mt-0.5">{l}</div></div>
              ))}
            </div>
            <button onClick={() => setStep(1)} className="text-[13px] px-5 py-2 rounded-full bg-white text-[#050507] font-medium hover:bg-white/90 transition">Create My Passport</button>
          </div>
        </section>
      )}

      {/* Scenarios */}
      {currentScenario && (
        <section className="pt-24 pb-16 px-6">
          <div className="max-w-[700px] mx-auto">
            <div className="flex gap-1 mb-8">
              {SCENARIOS.map((_, i) => (
                <div key={i} className={`flex-1 h-1 rounded-full ${i < step ? "bg-[var(--accent)]" : "bg-white/5"}`} />
              ))}
            </div>
            <div className="text-[10px] text-[var(--muted)] mb-2">{step} of 6</div>
            <h2 className="text-[22px] tracking-tight font-medium mb-2">{currentScenario.title}</h2>
            <div className="card p-5 mb-6">
              <p className="text-[14px] text-[var(--text)] leading-relaxed font-light">{currentScenario.desc}</p>
            </div>
            <p className="text-[12px] text-[var(--muted)] mb-5 font-light">How comfortable would you feel?</p>
            <div className="space-y-5">
              {(["visual", "auditory", "social"] as const).map(axis => (
                <div key={axis}>
                  <div className="flex justify-between text-[13px] mb-2">
                    <span className="font-medium capitalize">{axis}</span>
                    <span className="text-[11px] text-[var(--muted)]">
                      {!currentRating?.[axis] ? "—" : currentRating[axis] === 1 ? "Very uncomfortable" : currentRating[axis] === 2 ? "Uncomfortable" : currentRating[axis] === 3 ? "Neutral" : currentRating[axis] === 4 ? "Comfortable" : "Very comfortable"}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    {[1,2,3,4,5].map(v => (
                      <button key={v} onClick={() => setR(currentScenario.id, axis, v)}
                        className={`flex-1 py-2.5 rounded-lg text-[12px] font-medium transition ${
                          currentRating?.[axis] === v ? "bg-[var(--accent)] text-white" : "bg-white/[0.03] border border-[var(--border)] text-[var(--muted)] hover:text-white"
                        }`}>{v}</button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className="flex gap-3 mt-8">
              {step > 1 && <button onClick={() => setStep(step-1)} className="text-[13px] px-5 py-2 rounded-full border border-white/10 text-[var(--muted)] hover:text-white transition">Back</button>}
              {step < 6 ? (
                <button onClick={() => setStep(step+1)} disabled={!canNext} className="text-[13px] px-5 py-2 rounded-full bg-white text-[#050507] font-medium hover:bg-white/90 disabled:opacity-30 transition">Next</button>
              ) : (
                <button onClick={() => setStep(7)} disabled={!canNext} className="text-[13px] px-5 py-2 rounded-full bg-white text-[#050507] font-medium hover:bg-white/90 disabled:opacity-30 transition">Continue</button>
              )}
            </div>
          </div>
        </section>
      )}

      {/* Name input */}
      {step === 7 && (
        <section className="pt-24 pb-16 px-6">
          <div className="max-w-[700px] mx-auto">
            <h2 className="text-[22px] tracking-tight font-medium mb-4">Name your Passport</h2>
            <p className="text-[13px] text-[var(--muted)] font-light mb-6">This name will appear on your shareable Sensory Passport. Use your name, a nickname, or your child&apos;s name.</p>
            <input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Sarah, Alex, Room 4B"
              className="w-full bg-[var(--card)] border border-[var(--border)] rounded-lg p-3 text-[14px] font-light focus:outline-none focus:border-[var(--accent)]/30 transition mb-4" />
            <button onClick={handleGenerate} disabled={!name.trim()} className="text-[13px] px-5 py-2 rounded-full bg-white text-[#050507] font-medium hover:bg-white/90 disabled:opacity-30 transition">Generate Passport</button>
          </div>
        </section>
      )}

      {/* Result */}
      {step === 8 && profile && (
        <section className="pt-24 pb-16 px-6">
          <div className="max-w-[700px] mx-auto">
            {/* Passport card */}
            <div ref={cardRef} className="card p-6 mb-6" style={{ background: "#0c0c12" }}>
              <div className="flex items-center justify-between mb-5">
                <div>
                  <div className="text-[10px] text-[var(--accent)] font-medium tracking-widest uppercase">Sensory Passport</div>
                  <h2 className="text-[22px] tracking-tight font-medium">{name}</h2>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-[var(--muted)]">Powered by AQAL</div>
                  <div className="text-[10px] text-[var(--muted)]">mind.new</div>
                </div>
              </div>

              <div className="space-y-3 mb-6">
                {NETWORKS.map(net => {
                  const val = profile[net.key] || 0;
                  return (
                    <div key={net.key}>
                      <div className="flex justify-between text-[12px] mb-1">
                        <span className="font-light">{net.label}</span>
                        <span className="font-medium tabular-nums" style={{ color: net.color }}>{val}%</span>
                      </div>
                      <div className="w-full h-[4px] bg-white/[0.04] rounded-full overflow-hidden">
                        <div className="h-full rounded-full" style={{ width: `${val}%`, background: net.color }} />
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Summary */}
              <div className="bg-[var(--bg)] rounded-lg p-4 border border-[var(--border)]">
                <p className="text-[11px] text-[var(--muted)] font-light leading-relaxed">
                  {(() => {
                    const sorted = NETWORKS.map(n => ({ ...n, val: profile[n.key] || 0 })).sort((a,b) => b.val - a.val);
                    const top = sorted[0];
                    const low = sorted[sorted.length - 1];
                    return `Highest sensitivity: ${top.label} (${top.val}%). Lowest: ${low.label} (${low.val}%). This means ${name} may need extra accommodation for ${top.label.toLowerCase()} stimuli, while ${low.label.toLowerCase()} input is processed more comfortably.`;
                  })()}
                </p>
              </div>

              <p className="text-[9px] text-[var(--muted)]/40 mt-4 font-light">Self-reported sensory profile. Not a clinical assessment. Generated at neuro.mind.new/passport</p>
            </div>

            {/* Actions */}
            <div className="flex flex-wrap gap-3 mb-6">
              <button onClick={copyLink} className="text-[13px] px-5 py-2 rounded-full bg-white text-[#050507] font-medium hover:bg-white/90 transition flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
                Copy Link
              </button>
              <button onClick={downloadImage} className="text-[13px] px-5 py-2 rounded-full border border-white/10 text-[var(--muted)] hover:text-white transition flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                Download Image
              </button>
              <button onClick={() => { setStep(0); setRatings({}); setProfile(null); setName(""); }}
                className="text-[13px] px-5 py-2 rounded-full border border-white/10 text-[var(--muted)] hover:text-white transition">
                Create New
              </button>
            </div>

            <div className="card p-4 border-l-2 border-[var(--accent)]">
              <p className="text-[11px] text-[var(--muted)] leading-relaxed font-light">
                <strong className="text-white font-normal">How to use:</strong> Share this passport with teachers, therapists, or employers so they understand sensory needs. The link stays valid — anyone with it can view the profile. You can also download it as an image to print or attach to documents.
              </p>
            </div>
          </div>
        </section>
      )}

      <footer className="border-t border-[var(--border)] py-5 px-6">
        <div className="max-w-[700px] mx-auto">
          <p className="text-[10px] text-[var(--muted)]/50 mb-3 font-light">Sensory Passport is a self-reported profile, not a clinical assessment. If concerned about sensory processing, consult a professional.</p>
          <div className="flex items-center justify-between text-[11px] text-[var(--muted)]">
            <span>NeuroBrain by Leeza Care</span>
            <a href="https://mind.new" className="hover:text-white transition">mind.new</a>
          </div>
        </div>
      </footer>
    </main>
  );
}

function Nav() {
  return (
    <nav className="fixed top-0 w-full z-50 bg-[#050507]/80 backdrop-blur-xl border-b border-[var(--border)]">
      <div className="max-w-[700px] mx-auto px-6 h-14 flex items-center justify-between">
        <a href="https://neuro.mind.new" className="flex items-center gap-2">
          <span className="text-[15px] font-medium tracking-tight">
            <span className="gradient-text">Neuro</span><span className="text-[var(--text)]">Brain</span>
          </span>
        </a>
        <span className="text-[12px] px-2.5 py-1 rounded-full bg-[var(--accent)]/10 text-[var(--accent)]">Sensory Passport</span>
      </div>
    </nav>
  );
}
