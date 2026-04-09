"use client";

import { useState, useRef, useEffect, ReactNode } from "react";

const API = "https://neurobrain-api.eastus.cloudapp.azure.com/api";

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

function S({ children, id }: { children: ReactNode; id?: string }) {
  const ref = useReveal();
  return <section ref={ref} id={id} className="py-24 px-6">{children}</section>;
}

function Dv() { return <div className="h-px bg-[var(--border)] max-w-[1024px] mx-auto" />; }

type TabId = "predict" | "compare" | "connectivity";

export default function Home() {
  const [tab, setTab] = useState<TabId>("predict");
  const workRef = useRef<HTMLDivElement>(null);

  return (
    <main>
      <Nav />
      <Hero onExplore={() => workRef.current?.scrollIntoView({ behavior: "smooth" })} />
      <Dv />
      <Features onSelect={(id) => { setTab(id as TabId); setTimeout(() => workRef.current?.scrollIntoView({ behavior: "smooth" }), 100); }} />
      <Dv />
      <div ref={workRef}>
        <Workspace tab={tab} setTab={setTab} />
      </div>
      <Footer />
    </main>
  );
}

/* ─── NAV ─── */
function Nav() {
  const [s, setS] = useState(false);
  const [open, setOpen] = useState(false);
  useEffect(() => { const h = () => setS(window.scrollY > 40); window.addEventListener("scroll", h); return () => window.removeEventListener("scroll", h); }, []);
  const links = [
    { href: "https://mind.new", label: "Home" },
    { href: "https://sensory.mind.new", label: "Sensory Audit" },
    { href: "https://mind.new/paper", label: "Paper" },
  ];
  return (
    <nav className={`fixed top-0 w-full z-50 transition-all duration-300 ${s || open ? "bg-[#050507]/80 backdrop-blur-xl border-b border-[var(--border)]" : ""}`}>
      <div className="max-w-[1024px] mx-auto px-6 h-14 flex items-center justify-between">
        <a href="https://mind.new" className="flex items-center gap-2">
          <span className="text-[15px] font-medium tracking-tight">
            <span className="gradient-text">Neuro</span>
            <span className="text-[var(--text)]">Brain</span>
          </span>
        </a>
        <div className="hidden md:flex items-center gap-7 text-[13px] text-[var(--muted)]">
          {links.map((l) => <a key={l.href} href={l.href} className="hover:text-white transition">{l.label}</a>)}
        </div>
        <div className="flex items-center gap-3">
          <span className="hidden sm:inline text-[13px] px-4 py-1.5 rounded-full border border-white/10 text-[var(--muted)]">neuro.mind.new</span>
          <button onClick={() => setOpen(!open)} className="md:hidden w-9 h-9 flex items-center justify-center rounded-lg hover:bg-white/5 transition" aria-label="Menu">
            {open ? (
              <svg className="w-5 h-5 text-[var(--text)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M6 18L18 6M6 6l12 12" /></svg>
            ) : (
              <svg className="w-5 h-5 text-[var(--text)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 6h16M4 12h16M4 18h16" /></svg>
            )}
          </button>
        </div>
      </div>
      {open && (
        <div className="md:hidden border-t border-[var(--border)] bg-[#050507]/95 backdrop-blur-xl">
          <div className="max-w-[1024px] mx-auto px-6 py-4 flex flex-col gap-1">
            {links.map((l) => (
              <a key={l.href} href={l.href} onClick={() => setOpen(false)}
                className="text-[14px] text-[var(--muted)] hover:text-white py-2.5 px-3 rounded-lg hover:bg-white/5 transition font-light">
                {l.label}
              </a>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
}

/* ─── HERO ─── */
function Hero({ onExplore }: { onExplore: () => void }) {
  return (
    <section className="relative pt-24 pb-12 px-6">
      <div className="absolute w-[500px] h-[300px] rounded-full bg-[#7c6aff] opacity-[0.04] blur-[100px] top-16 right-1/4 pointer-events-none" />
      <div className="relative max-w-[1024px] mx-auto">
        <div className="flex items-center gap-2 mb-5">
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)]" />
          <span className="text-[11px] text-[var(--muted)] tracking-widest uppercase">AI Brain Encoding Platform</span>
        </div>
        <h1 className="text-[clamp(2rem,4.5vw,3.5rem)] leading-[1.1] tracking-[-0.03em] font-medium">
          Predict the <span className="gradient-text">Neurodiverse Brain</span>
        </h1>
        <p className="text-[15px] text-[var(--muted)] mt-4 max-w-[480px] leading-relaxed font-light">
          Visualize real-time brain activity, compare neurotypical vs neurodiverse
          responses, and explore how autism shapes neural connectivity.
        </p>
        <div className="flex items-center gap-3 mt-7">
          <button onClick={onExplore} className="text-[13px] px-5 py-2 rounded-full bg-white text-[#050507] font-medium hover:bg-white/90 transition">Start Exploring</button>
          <a href="https://mind.new/paper" className="text-[13px] px-5 py-2 rounded-full border border-white/10 text-[var(--text)] hover:border-white/20 transition">Read the Paper</a>
        </div>
        <div className="grid grid-cols-2 sm:flex sm:gap-8 gap-4 mt-10 pt-5 border-t border-[var(--border)]">
          {[["177M", "parameters"], ["20,484", "vertices"], ["1,100+", "subjects"], ["820", "connections"]].map(([n, l]) => (
            <div key={l}><div className="text-[16px] sm:text-[18px] font-medium text-white tabular-nums">{n}</div><div className="text-[10px] text-[var(--muted)] mt-0.5">{l}</div></div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── FEATURES ─── */
function Features({ onSelect }: { onSelect: (id: string) => void }) {
  return (
    <S>
      <div className="max-w-[1024px] mx-auto">
        <h2 className="reveal text-[26px] tracking-tight mb-3">Capabilities</h2>
        <p className="reveal reveal-delay-1 text-[14px] text-[var(--muted)] mb-8 font-light max-w-md">Three modules for exploring how the neurodiverse brain processes information.</p>
        <div className="grid md:grid-cols-3 gap-3">
          {[
            { id: "predict", n: "01", t: "Brain Prediction", d: "Input text and see real-time brain activation across 20,484 cortical vertices.", tag: "Real-time" },
            { id: "compare", n: "02", t: "NT vs ND", d: "Compare neurotypical and neurodiverse brain responses across 7 brain networks.", tag: "Comparison" },
            { id: "connectivity", n: "03", t: "ASD Connectivity", d: "Analyze brain wiring differences in autism using fMRI data from 1,100+ subjects.", tag: "Analysis" },
          ].map((f, i) => (
            <button key={f.id} onClick={() => onSelect(f.id)} className={`reveal reveal-delay-${i + 1} card p-5 text-left group cursor-pointer`}>
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] text-[var(--accent)] font-medium">{f.n}</span>
                <span className="text-[9px] px-2 py-0.5 rounded-full bg-[var(--accent)]/10 text-[var(--accent)]">{f.tag}</span>
              </div>
              <h3 className="text-[14px] font-medium mb-1.5">{f.t}</h3>
              <p className="text-[12px] text-[var(--muted)] leading-relaxed font-light">{f.d}</p>
            </button>
          ))}
        </div>
      </div>
    </S>
  );
}

/* ─── WORKSPACE ─── */
function Workspace({ tab, setTab }: { tab: TabId; setTab: (t: TabId) => void }) {
  return (
    <S id="workspace">
      <div className="max-w-[1024px] mx-auto">
        <h2 className="reveal text-[26px] tracking-tight mb-3">Workspace</h2>
        <p className="reveal reveal-delay-1 text-[14px] text-[var(--muted)] mb-8 font-light">Interact with the brain model in real-time.</p>

        {/* Tabs */}
        <div className="reveal reveal-delay-2 flex gap-1 p-1 rounded-lg bg-white/[0.03] border border-[var(--border)] inline-flex mb-8">
          {(["predict", "compare", "connectivity"] as const).map((t) => (
            <button key={t} onClick={() => setTab(t)}
              className={`text-[12px] px-4 py-2 rounded-md transition ${tab === t ? "bg-white/10 text-white" : "text-[var(--muted)] hover:text-white"}`}>
              {t === "predict" ? "Predict" : t === "compare" ? "NT vs ND" : "Connectivity"}
            </button>
          ))}
        </div>

        {tab === "predict" && <PredictSection />}
        {tab === "compare" && <CompareSection />}
        {tab === "connectivity" && <ConnectivitySection />}
      </div>
    </S>
  );
}

/* ─── PREDICT ─── */
function PredictSection() {
  const [images, setImages] = useState<string[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [text, setText] = useState("The child watched the colorful birds flying across the bright blue sky.");
  const [step, setStep] = useState(0);

  const handlePredict = async () => {
    setLoading(true);
    try {
      const form = new FormData(); form.append("text", text);
      const res = await fetch(`${API}/predict`, { method: "POST", body: form });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setImages(data.images || []); setStats(data); setStep(0);
    } catch (e: any) { alert("Failed: " + e.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <label className="text-[12px] text-[var(--muted)] mb-2 block">Input Stimulus</label>
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={3}
          className="w-full bg-[var(--bg)] border border-[var(--border)] rounded-lg p-3 text-[14px] font-light focus:outline-none focus:border-[var(--accent)]/30 resize-none" />
        <button onClick={handlePredict} disabled={loading || !text.trim()}
          className="mt-3 w-full py-2.5 rounded-lg bg-white text-[#050507] font-medium text-[13px] hover:bg-white/90 disabled:opacity-40 transition">
          {loading ? "Processing..." : "Predict Brain Activity"}
        </button>
      </div>

      {stats && (
        <div className="card p-5">
          <div className="grid grid-cols-3 gap-4 text-center">
            {[[stats.timesteps, "Timesteps"], [stats.vertices?.toLocaleString(), "Vertices"], [stats.mean_activation?.toFixed(4), "Mean Activation"]].map(([v, l]) => (
              <div key={String(l)}><div className="text-[18px] font-medium text-white tabular-nums">{v}</div><div className="text-[10px] text-[var(--muted)] mt-0.5">{l}</div></div>
            ))}
          </div>
        </div>
      )}

      {images.length > 0 && <BrainViewer images={images} step={step} setStep={setStep} />}
    </div>
  );
}

/* ─── COMPARE ─── */
function CompareSection() {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [text, setText] = useState("The child watched the colorful birds flying across the bright blue sky.");
  const [ntStep, setNtStep] = useState(0);
  const [ndStep, setNdStep] = useState(0);

  const handleCompare = async () => {
    setLoading(true);
    try {
      const form = new FormData(); form.append("text", text);
      const res = await fetch(`${API}/compare`, { method: "POST", body: form });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json()); setNtStep(0); setNdStep(0);
    } catch (e: any) { alert("Failed: " + e.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <label className="text-[12px] text-[var(--muted)] mb-2 block">Compare NT vs ND Response</label>
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={3}
          className="w-full bg-[var(--bg)] border border-[var(--border)] rounded-lg p-3 text-[14px] font-light focus:outline-none focus:border-[var(--accent)]/30 resize-none" />
        <button onClick={handleCompare} disabled={loading || !text.trim()}
          className="mt-3 w-full py-2.5 rounded-lg bg-white text-[#050507] font-medium text-[13px] hover:bg-white/90 disabled:opacity-40 transition">
          {loading ? "Comparing..." : "Compare Brains"}
        </button>
      </div>

      {result?.nt_images && result?.nd_images && (
        <>
          <div className="card p-4 text-center">
            <p className="text-[12px] text-[var(--muted)] font-light">Based on {result.n_asd_subjects} ASD and {result.n_td_subjects} TD subjects</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="card p-4">
              <div className="text-[12px] text-[var(--success)] font-medium mb-3 text-center">Neurotypical</div>
              <BrainViewer images={result.nt_images} step={ntStep} setStep={setNtStep} />
            </div>
            <div className="card p-4">
              <div className="text-[12px] text-[var(--warning)] font-medium mb-3 text-center">Neurodiverse (ASD)</div>
              <BrainViewer images={result.nd_images} step={ndStep} setStep={setNdStep} />
            </div>
          </div>
        </>
      )}

      {result?.sensory_profile && (
        <div className="card p-5">
          <h3 className="text-[14px] font-medium mb-4">Sensory Profile</h3>
          <div className="space-y-3">
            {Object.entries(result.sensory_profile as Record<string, number>).sort(([,a],[,b]) => b - a).map(([k, v]) => {
              const pct = Math.round(v * 100);
              return (
                <div key={k}>
                  <div className="flex justify-between text-[12px] mb-1">
                    <span className="capitalize font-light">{k.replace("_", " ")}</span>
                    <span className="text-[var(--accent)] font-medium">{pct}%</span>
                  </div>
                  <div className="w-full h-[3px] bg-white/[0.04] rounded-full overflow-hidden">
                    <div className="h-full rounded-full bg-gradient-to-r from-[var(--accent)] to-[var(--accent2)] metric-grow" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── CONNECTIVITY ─── */
function ConnectivitySection() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleLoad = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/connectivity`);
      if (!res.ok) throw new Error(await res.text());
      setData(await res.json());
    } catch (e: any) { alert("Failed: " + e.message); }
    finally { setLoading(false); }
  };

  const labels: Record<string, string> = { Vis: "Visual", SomMot: "Somatomotor", DorsAttn: "Dorsal Attention", SalVentAttn: "Salience", Limbic: "Limbic", Cont: "Control", Default: "Default Mode" };

  return (
    <div className="space-y-4">
      <div className="card p-5 text-center">
        <h3 className="text-[16px] font-medium mb-2">ASD vs TD Brain Connectivity</h3>
        <p className="text-[13px] text-[var(--muted)] font-light mb-5">Compare how brain regions communicate differently in autism.</p>
        <button onClick={handleLoad} disabled={loading}
          className="text-[13px] px-6 py-2.5 rounded-full bg-white text-[#050507] font-medium hover:bg-white/90 disabled:opacity-40 transition">
          {loading ? "Analyzing..." : "Run Analysis"}
        </button>
      </div>

      {data && (
        <div className="card p-5">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-[14px] font-medium">Network Differences</h3>
            <div className="flex gap-3 text-[11px] text-[var(--muted)]">
              <span>ASD: {data.asd_subjects}</span>
              <span>TD: {data.td_subjects}</span>
            </div>
          </div>
          <div className="space-y-3">
            {Object.entries(data.network_differences as Record<string, number>).map(([net, val]) => {
              const max = Math.max(...Object.values(data.network_differences as Record<string, number>));
              const pct = (val / max) * 100;
              return (
                <div key={net} className="flex items-center gap-4">
                  <div className="w-32 text-[12px] text-right text-[var(--muted)] font-light flex-shrink-0">{labels[net] || net}</div>
                  <div className="flex-1 h-6 bg-white/[0.03] rounded overflow-hidden relative">
                    <div className="h-full rounded bg-gradient-to-r from-[var(--accent)] to-[var(--accent2)] metric-grow" style={{ width: `${pct}%` }} />
                    <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] font-mono text-white/60">{val.toFixed(4)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── BRAIN VIEWER ─── */
function BrainViewer({ images, step, setStep }: { images: string[]; step: number; setStep: (n: number) => void }) {
  return (
    <div className="card p-4">
      <div className="bg-black rounded-lg overflow-hidden">
        <img src={`data:image/png;base64,${images[step]}`} alt="Brain" className="w-full" />
      </div>
      <div className="mt-3">
        <input type="range" min={0} max={images.length - 1} value={step} onChange={(e) => setStep(Number(e.target.value))}
          className="w-full accent-[var(--accent)] h-1" />
        <div className="flex justify-between text-[10px] text-[var(--muted)] mt-1">
          <span>t=0s</span>
          <span className="text-[var(--accent)] font-medium">t={step}s</span>
          <span>t={images.length - 1}s</span>
        </div>
      </div>
    </div>
  );
}

/* ─── FOOTER ─── */
function Footer() {
  return (
    <footer className="border-t border-[var(--border)] py-5 px-6">
      <div className="max-w-[1024px] mx-auto flex items-center justify-between text-[11px] text-[var(--muted)]">
        <span>NeuroBrain by Leeza Care</span>
        <a href="https://mind.new" className="hover:text-white transition">mind.new</a>
      </div>
    </footer>
  );
}
