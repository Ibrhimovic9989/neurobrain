import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NeuroBrain - Neurodiverse Brain Model",
  description:
    "Predict and compare neurotypical vs neurodiverse brain activity using Meta's TRIBE v2",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
