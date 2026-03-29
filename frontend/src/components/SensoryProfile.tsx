"use client";

interface SensoryProfileProps {
  profile: Record<string, number>;
}

const NETWORK_INFO: Record<string, { label: string; color: string; description: string }> = {
  visual: {
    label: "Visual",
    color: "#ef4444",
    description: "Processing what you see",
  },
  auditory: {
    label: "Auditory",
    color: "#f59e0b",
    description: "Processing what you hear",
  },
  language: {
    label: "Language",
    color: "#6c63ff",
    description: "Understanding words and speech",
  },
  default_mode: {
    label: "Default Mode",
    color: "#22c55e",
    description: "Internal thoughts, self-reflection",
  },
  motor: {
    label: "Motor",
    color: "#06b6d4",
    description: "Movement and body awareness",
  },
  social: {
    label: "Social",
    color: "#ec4899",
    description: "Understanding others' emotions",
  },
};

export default function SensoryProfile({ profile }: SensoryProfileProps) {
  const sorted = Object.entries(profile).sort(([, a], [, b]) => b - a);

  return (
    <div className="glass-card p-6">
      <h3 className="text-lg font-semibold mb-2">Sensory Processing Profile</h3>
      <p className="text-sm text-[var(--text-secondary)] mb-6">
        How differently the neurodiverse brain processes each type of information
        compared to the neurotypical baseline.
      </p>

      <div className="space-y-5">
        {sorted.map(([key, value]) => {
          const info = NETWORK_INFO[key] || {
            label: key,
            color: "#6c63ff",
            description: "",
          };
          const pct = Math.round(value * 100);

          return (
            <div key={key}>
              <div className="flex justify-between items-center mb-1">
                <div>
                  <span className="font-medium">{info.label}</span>
                  <span className="text-xs text-[var(--text-secondary)] ml-2">
                    {info.description}
                  </span>
                </div>
                <span
                  className="text-sm font-bold"
                  style={{ color: info.color }}
                >
                  {pct}% different
                </span>
              </div>
              <div className="w-full h-3 bg-[var(--bg-primary)] rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-1000"
                  style={{
                    width: `${pct}%`,
                    background: `linear-gradient(90deg, ${info.color}, ${info.color}88)`,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-8 p-4 bg-[var(--bg-primary)] rounded-xl">
        <p className="text-sm text-[var(--text-secondary)]">
          <strong className="text-[var(--text-primary)]">What this means: </strong>
          The highest-scoring networks show where the neurodiverse brain
          processes information most differently. This can help design
          personalized sensory accommodations and learning strategies.
        </p>
      </div>
    </div>
  );
}
