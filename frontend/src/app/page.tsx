"use client";

import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import BrainViewer from "@/components/BrainViewer";
import TextInput from "@/components/TextInput";
import ConnectivityChart from "@/components/ConnectivityChart";
import SensoryProfile from "@/components/SensoryProfile";
import Header from "@/components/Header";
import Interpretation from "@/components/Interpretation";
import BrainComparison from "@/components/BrainComparison";
import NeuralBackground from "@/components/NeuralBackground";
import HeroSection from "@/components/HeroSection";
import FeatureCards from "@/components/FeatureCards";
import TechShowcase from "@/components/TechShowcase";
import Footer from "@/components/Footer";

type TabId = "predict" | "compare" | "connectivity";

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabId>("predict");
  const workspaceRef = useRef<HTMLDivElement>(null);

  const tabs: { id: TabId; label: string; desc: string; icon: React.ReactNode }[] = [
    {
      id: "predict",
      label: "Brain Prediction",
      desc: "See how the brain responds to text or video in real-time",
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
    },
    {
      id: "compare",
      label: "NT vs ND",
      desc: "Compare neurotypical and neurodiverse brain responses side-by-side",
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
    },
    {
      id: "connectivity",
      label: "ASD Connectivity",
      desc: "Analyze brain wiring differences in autism using real fMRI data",
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5" />
        </svg>
      ),
    },
  ];

  const scrollToWorkspace = () => {
    workspaceRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleFeatureSelect = (id: string) => {
    setActiveTab(id as TabId);
    setTimeout(() => scrollToWorkspace(), 100);
  };

  return (
    <main className="min-h-screen noise-overlay">
      <NeuralBackground />
      <Header />

      {/* Hero */}
      <HeroSection onExplore={scrollToWorkspace} />

      {/* Divider */}
      <div className="section-divider" />

      {/* Feature Cards */}
      <FeatureCards onSelect={handleFeatureSelect} />

      {/* Divider */}
      <div className="section-divider" />

      {/* Tech Showcase */}
      <TechShowcase />

      {/* Divider */}
      <div className="section-divider" />

      {/* Workspace Section */}
      <section ref={workspaceRef} className="relative py-24 px-6" id="workspace">
        <div className="max-w-6xl mx-auto">
          {/* Section header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-12"
          >
            <span className="text-xs uppercase tracking-[0.3em] text-[var(--neon-purple)] font-medium mb-4 block">
              Workspace
            </span>
            <h2 className="text-3xl md:text-5xl font-bold mb-4">
              <span className="gradient-text">Neural</span>{" "}
              <span className="text-white">Analysis Lab</span>
            </h2>
            <p className="text-[var(--text-secondary)] max-w-xl mx-auto">
              Interact with the brain model in real-time. Select a module and start exploring.
            </p>
          </motion.div>

          {/* Tab Navigation */}
          <div className="flex justify-center mb-8">
            <div className="inline-flex gap-2 p-1.5 glass-card-static">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`tab-pill flex items-center gap-2 ${activeTab === tab.id ? "active" : ""}`}
                >
                  {tab.icon}
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Tab description */}
          <motion.p
            key={activeTab}
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center text-[var(--text-secondary)] text-sm mb-8"
          >
            {tabs.find((t) => t.id === activeTab)?.desc}
          </motion.p>

          {/* Content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {activeTab === "predict" && <PredictSection />}
              {activeTab === "compare" && <CompareSection />}
              {activeTab === "connectivity" && <ConnectivitySection />}
            </motion.div>
          </AnimatePresence>
        </div>
      </section>

      {/* Footer */}
      <Footer />
    </main>
  );
}

function PredictSection() {
  const [images, setImages] = useState<string[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handlePredict = async (text: string) => {
    setLoading(true);
    try {
      const form = new FormData();
      form.append("text", text);
      const res = await fetch(`https://neurobrain-api.eastus.cloudapp.azure.com/api/predict`, { method: "POST", body: form });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setImages(data.images || []);
      setStats(data);
    } catch (e: any) {
      alert("Prediction failed: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <TextInput onSubmit={handlePredict} loading={loading} />
      {stats && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-card p-6"
        >
          <div className="grid grid-cols-3 gap-4 text-center">
            {[
              { value: stats.timesteps, label: "Timesteps", color: "var(--accent)" },
              { value: stats.vertices?.toLocaleString(), label: "Brain Vertices", color: "var(--neon-cyan)" },
              { value: stats.mean_activation?.toFixed(4), label: "Mean Activation", color: "var(--neon-purple)" },
            ].map((s) => (
              <div key={s.label} className="p-3 bg-[var(--bg-primary)]/50 rounded-xl border border-white/5">
                <div className="text-2xl md:text-3xl font-bold" style={{ color: s.color }}>
                  {s.value}
                </div>
                <div className="text-xs text-[var(--text-secondary)] mt-1">{s.label}</div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
      {images.length > 0 && <BrainViewer images={images} />}
      {stats && <Interpretation data={stats} context="predict" />}
    </div>
  );
}

function CompareSection() {
  const [profile, setProfile] = useState<Record<string, number> | null>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleCompare = async (text: string) => {
    setLoading(true);
    try {
      const form = new FormData();
      form.append("text", text);
      const res = await fetch(`https://neurobrain-api.eastus.cloudapp.azure.com/api/compare`, { method: "POST", body: form });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setProfile(data.sensory_profile);
      setResult(data);
    } catch (e: any) {
      alert("Comparison failed: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <TextInput
        onSubmit={handleCompare}
        loading={loading}
        placeholder="Enter text to compare NT vs ND brain response..."
        buttonText="Compare Brains"
      />
      {result?.nt_images && result?.nd_images && (
        <div className="space-y-6">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="glass-card-static p-4 text-center"
          >
            <p className="text-sm text-[var(--text-secondary)]">
              Based on <span className="text-[var(--accent)] font-semibold">{result.n_asd_subjects} ASD</span> and{" "}
              <span className="text-[var(--neon-cyan)] font-semibold">{result.n_td_subjects} TD</span> brain scans from the ABIDE dataset
            </p>
          </motion.div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <div className="flex items-center justify-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[var(--success)]" />
                <h4 className="text-center font-semibold text-[var(--success)]">Neurotypical Brain</h4>
              </div>
              <BrainViewer images={result.nt_images} />
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[var(--warning)]" />
                <h4 className="text-center font-semibold text-[var(--warning)]">Neurodiverse Brain (ASD)</h4>
              </div>
              <BrainViewer images={result.nd_images} />
            </div>
          </div>
        </div>
      )}
      {result && <BrainComparison result={result} />}
      {profile && <SensoryProfile profile={profile} />}
      {result && <Interpretation data={result} context="compare" />}
    </div>
  );
}

function ConnectivitySection() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleLoad = async () => {
    setLoading(true);
    try {
      const res = await fetch(`https://neurobrain-api.eastus.cloudapp.azure.com/api/connectivity`);
      if (!res.ok) throw new Error(await res.text());
      setData(await res.json());
    } catch (e: any) {
      alert("Failed: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="glass-card p-8 text-center relative overflow-hidden">
        {/* Ambient effects */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-64 h-32 bg-[var(--accent)]/10 blur-[60px] rounded-full pointer-events-none" />

        <div className="relative z-10">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[var(--accent)] to-[var(--neon-cyan)] flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5" />
            </svg>
          </div>
          <h3 className="text-2xl font-bold mb-3">
            ASD vs TD Brain Connectivity
          </h3>
          <p className="text-[var(--text-secondary)] mb-8 max-w-lg mx-auto">
            Compare how brain regions communicate differently in autism using
            real fMRI data from the ABIDE dataset with 1,100+ subjects.
          </p>
          <button
            onClick={handleLoad}
            disabled={loading}
            className="btn-futuristic px-10 py-4 text-base disabled:opacity-50 mx-auto"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Analyzing brain scans...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Run Analysis
              </span>
            )}
          </button>
        </div>
      </div>
      {data && <ConnectivityChart data={data} />}
      {data && <Interpretation data={data} context="connectivity" />}
    </div>
  );
}
