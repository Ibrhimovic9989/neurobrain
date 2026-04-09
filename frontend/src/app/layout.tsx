import type { Metadata } from "next";
import "./globals.css";
import { Geist } from "next/font/google";
import { cn } from "@/lib/utils";

const geist = Geist({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "NeuroBrain - AI-Powered Neurodiverse Brain Intelligence Platform",
  description:
    "Visualize real-time brain activity predictions, compare neurotypical vs neurodiverse responses, and explore how autism shapes neural connectivity — powered by Meta's TRIBE v2 and the ABIDE dataset.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={cn("dark font-sans", geist.variable)}>
      <body className="antialiased">{children}</body>
    </html>
  );
}
