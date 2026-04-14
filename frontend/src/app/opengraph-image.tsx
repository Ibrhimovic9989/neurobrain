import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "NeuroBrain — Real-time Brain Activity Predictions";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "80px",
          background: "#050507",
          backgroundImage: "radial-gradient(circle at 75% 30%, rgba(124, 106, 255, 0.15), transparent 50%)",
          fontFamily: "Inter, system-ui, sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "32px" }}>
          <div style={{ width: "8px", height: "8px", borderRadius: "999px", background: "#7c6aff" }} />
          <div style={{ color: "#71717a", fontSize: "20px", letterSpacing: "0.2em", textTransform: "uppercase" }}>
            Brain Encoding Platform
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", color: "#fafafa", fontSize: "80px", fontWeight: 500, letterSpacing: "-0.03em", lineHeight: 1.05, marginBottom: "32px" }}>
          <div>Predict the{" "}
            <span style={{ background: "linear-gradient(135deg, #cb6be5 0%, #9b6aff 50%, #f5b400 100%)", backgroundClip: "text", color: "transparent" }}>
              Neurodiverse Brain
            </span>
          </div>
        </div>

        <div style={{ color: "#a1a1aa", fontSize: "24px", fontWeight: 300, maxWidth: "900px", marginBottom: "48px" }}>
          Compare neurotypical vs neurodiverse brain responses in real-time. 177M parameters · 20,484 cortical vertices · 7 brain networks.
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "16px", marginTop: "auto" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "28px", color: "transparent", backgroundImage: "linear-gradient(135deg, #cb6be5, #9b6aff, #f5b400)", backgroundClip: "text", fontWeight: 500 }}>Neuro</span>
            <span style={{ fontSize: "28px", color: "#d4d4d8", fontWeight: 500 }}>Brain</span>
          </div>
          <div style={{ marginLeft: "auto", color: "#71717a", fontSize: "18px" }}>neuro.mind.new</div>
        </div>
      </div>
    ),
    { ...size }
  );
}
