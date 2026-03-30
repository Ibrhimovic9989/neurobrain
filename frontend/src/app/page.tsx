"use client";

import { useState } from "react";
import BrainViewer from "@/components/BrainViewer";
import TextInput from "@/components/TextInput";
import ConnectivityChart from "@/components/ConnectivityChart";
import SensoryProfile from "@/components/SensoryProfile";
import Header from "@/components/Header";

type TabId = "predict" | "compare" | "connectivity";

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabId>("predict");

  const tabs: { id: TabId; label: string; desc: string }[] = [
    {
      id: "predict",
      label: "Brain Prediction",
      desc: "See how the brain responds to text or video",
    },
    {
      id: "compare",
      label: "NT vs ND",
      desc: "Compare neurotypical and neurodiverse responses",
    },
    {
      id: "connectivity",
      label: "ASD Connectivity",
      desc: "Brain wiring differences in autism",
    },
  ];

  return (
    <main className="min-h-screen">
      <Header />

      {/* Tab Navigation */}
      <div className="max-w-6xl mx-auto px-6 mt-8">
        <div className="flex gap-2 p-1 glass-card inline-flex">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-3 rounded-xl text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? "bg-[var(--accent)] text-white glow"
                  : "text-[var(--text-secondary)] hover:text-white"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <p className="text-[var(--text-secondary)] mt-3 text-sm">
          {tabs.find((t) => t.id === activeTab)?.desc}
        </p>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-6 mt-8 pb-20">
        {activeTab === "predict" && <PredictSection />}
        {activeTab === "compare" && <CompareSection />}
        {activeTab === "connectivity" && <ConnectivitySection />}
      </div>
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
        <div className="glass-card p-6">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-3xl font-bold text-[var(--accent)]">
                {stats.timesteps}
              </div>
              <div className="text-sm text-[var(--text-secondary)]">Timesteps</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-[var(--accent)]">
                {stats.vertices?.toLocaleString()}
              </div>
              <div className="text-sm text-[var(--text-secondary)]">
                Brain Vertices
              </div>
            </div>
            <div>
              <div className="text-3xl font-bold text-[var(--accent)]">
                {stats.mean_activation?.toFixed(4)}
              </div>
              <div className="text-sm text-[var(--text-secondary)]">
                Mean Activation
              </div>
            </div>
          </div>
        </div>
      )}
      {images.length > 0 && <BrainViewer images={images} />}
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
      setProfile(data.estimated_divergence || data.sensory_profile);
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
      {result?.status === "simulated" && (
        <div className="glass-card p-4 border-[var(--warning)] border">
          <p className="text-[var(--warning)] text-sm">
            Showing estimated divergence from ABIDE data. Fine-tuned model
            will provide real per-stimulus comparison.
          </p>
        </div>
      )}
      {profile && <SensoryProfile profile={profile} />}
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
      <div className="glass-card p-6 text-center">
        <h3 className="text-xl font-semibold mb-4">
          ASD vs TD Brain Connectivity
        </h3>
        <p className="text-[var(--text-secondary)] mb-6">
          Compare how brain regions communicate differently in autism using
          real fMRI data from the ABIDE dataset.
        </p>
        <button
          onClick={handleLoad}
          disabled={loading}
          className="px-8 py-3 bg-[var(--accent)] rounded-xl font-medium hover:opacity-90 transition disabled:opacity-50"
        >
          {loading ? "Analyzing brain scans..." : "Run Analysis"}
        </button>
      </div>
      {data && <ConnectivityChart data={data} />}
    </div>
  );
}
