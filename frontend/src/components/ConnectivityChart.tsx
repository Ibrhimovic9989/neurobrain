"use client";

interface ConnectivityChartProps {
  data: {
    asd_subjects: number;
    td_subjects: number;
    network_differences: Record<string, number>;
  };
}

const NETWORK_LABELS: Record<string, string> = {
  Vis: "Visual",
  SomMot: "Somatomotor",
  DorsAttn: "Dorsal Attention",
  SalVentAttn: "Salience",
  Limbic: "Limbic",
  Cont: "Control",
  Default: "Default Mode",
};

export default function ConnectivityChart({ data }: ConnectivityChartProps) {
  const entries = Object.entries(data.network_differences);
  const maxVal = Math.max(...entries.map(([, v]) => v));

  return (
    <div className="glass-card p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">
          Network-Level Connectivity Differences
        </h3>
        <div className="flex gap-4 text-sm text-[var(--text-secondary)]">
          <span>ASD: {data.asd_subjects} subjects</span>
          <span>TD: {data.td_subjects} subjects</span>
        </div>
      </div>

      <div className="space-y-4">
        {entries.map(([network, value]) => {
          const pct = (value / maxVal) * 100;
          const label = NETWORK_LABELS[network] || network;

          return (
            <div key={network} className="flex items-center gap-4">
              <div className="w-36 text-sm text-right text-[var(--text-secondary)] flex-shrink-0">
                {label}
              </div>
              <div className="flex-1 h-8 bg-[var(--bg-primary)] rounded-lg overflow-hidden relative">
                <div
                  className="h-full rounded-lg transition-all duration-1000"
                  style={{
                    width: `${pct}%`,
                    background: `linear-gradient(90deg, #6c63ff, #ff6b6b)`,
                  }}
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-mono">
                  {value.toFixed(4)}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-8 p-4 bg-[var(--bg-primary)] rounded-xl">
        <p className="text-sm text-[var(--text-secondary)]">
          <strong className="text-[var(--text-primary)]">Reading this chart: </strong>
          Longer bars mean bigger differences in how brain networks
          communicate between autistic and non-autistic individuals. Data from
          the ABIDE dataset ({data.asd_subjects + data.td_subjects} real fMRI
          brain scans).
        </p>
      </div>
    </div>
  );
}
