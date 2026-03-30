"use client";

interface BrainComparisonProps {
  result: {
    sensory_profile: Record<string, number>;
    divergence_stats: { mean: number; max: number };
    n_asd_subjects: number;
    n_td_subjects: number;
    timesteps: number;
    stimulus_text?: string;
  };
}

const NETWORK_INFO: Record<
  string,
  { label: string; description: string; impact: string }
> = {
  motor: {
    label: "Motor / Body",
    description: "Movement, body awareness, coordination",
    impact: "May show different movement patterns, stimming, or motor planning",
  },
  visual: {
    label: "Visual",
    description: "Processing what you see",
    impact: "May notice details others miss, or find busy scenes overwhelming",
  },
  attention: {
    label: "Attention",
    description: "Focusing and shifting focus",
    impact: "May hyperfocus on interests or struggle to shift attention",
  },
  salience: {
    label: "Salience",
    description: "Deciding what's important",
    impact: "May prioritize different things as important vs background",
  },
  emotional: {
    label: "Emotional",
    description: "Processing feelings and reactions",
    impact: "May experience emotions more intensely or differently",
  },
  control: {
    label: "Control",
    description: "Planning, decision-making",
    impact: "May prefer routine and predictability over spontaneous changes",
  },
  default_mode: {
    label: "Default Mode",
    description: "Self-reflection, imagination",
    impact: "May show different patterns of inner thought and self-awareness",
  },
};

export default function BrainComparison({ result }: BrainComparisonProps) {
  const profile = result.sensory_profile;
  const sorted = Object.entries(profile).sort(([, a], [, b]) => b - a);

  return (
    <div className="glass-card p-6">
      <h3 className="text-lg font-semibold mb-2">
        NT vs ND Difference Analysis
      </h3>
      <p className="text-sm text-[var(--text-secondary)] mb-4">
        How each brain network responds differently to: &quot;
        {result.stimulus_text?.slice(0, 60) || "stimulus"}...&quot;
      </p>

      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-[var(--bg-primary)] rounded-xl p-3 text-center">
          <div className="text-2xl font-bold text-[var(--accent)]">
            {result.timesteps}
          </div>
          <div className="text-xs text-[var(--text-secondary)]">
            Time Points
          </div>
        </div>
        <div className="bg-[var(--bg-primary)] rounded-xl p-3 text-center">
          <div className="text-2xl font-bold text-[var(--warning)]">
            {(result.divergence_stats.mean * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-[var(--text-secondary)]">
            Mean Divergence
          </div>
        </div>
        <div className="bg-[var(--bg-primary)] rounded-xl p-3 text-center">
          <div className="text-2xl font-bold text-[var(--danger)]">
            {(result.divergence_stats.max * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-[var(--text-secondary)]">
            Peak Divergence
          </div>
        </div>
      </div>

      {/* Comparison table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left py-3 px-2 text-[var(--text-secondary)]">
                Brain Network
              </th>
              <th className="text-left py-3 px-2 text-[var(--text-secondary)]">
                Function
              </th>
              <th className="text-center py-3 px-2 text-[var(--text-secondary)]">
                Difference
              </th>
              <th className="text-left py-3 px-2 text-[var(--text-secondary)]">
                What it means for autistic individuals
              </th>
            </tr>
          </thead>
          <tbody>
            {sorted.map(([key, value]) => {
              const info = NETWORK_INFO[key] || {
                label: key,
                description: "",
                impact: "",
              };
              const pct = Math.round(value * 100);
              const barColor =
                pct > 70
                  ? "var(--danger)"
                  : pct > 40
                    ? "var(--warning)"
                    : "var(--success)";
              const level =
                pct > 70 ? "High" : pct > 40 ? "Moderate" : "Low";

              return (
                <tr
                  key={key}
                  className="border-b border-white/5 hover:bg-white/5 transition"
                >
                  <td className="py-3 px-2 font-medium">{info.label}</td>
                  <td className="py-3 px-2 text-[var(--text-secondary)]">
                    {info.description}
                  </td>
                  <td className="py-3 px-2">
                    <div className="flex items-center gap-2 justify-center">
                      <div className="w-16 h-2 bg-[var(--bg-primary)] rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${pct}%`,
                            background: barColor,
                          }}
                        />
                      </div>
                      <span
                        className="text-xs font-bold min-w-[60px]"
                        style={{ color: barColor }}
                      >
                        {level} ({pct}%)
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-2 text-[var(--text-secondary)] text-xs">
                    {info.impact}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-4 p-3 bg-[var(--bg-primary)] rounded-xl">
        <p className="text-xs text-[var(--text-secondary)]">
          Data source: ABIDE dataset ({result.n_asd_subjects} ASD +{" "}
          {result.n_td_subjects} TD subjects). Transform derived from
          statistically significant connectivity differences (p &lt; 0.05).
        </p>
      </div>
    </div>
  );
}
