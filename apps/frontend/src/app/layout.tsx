import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/layout/Navbar";
import { Sidebar } from "@/components/layout/Sidebar";

export const metadata: Metadata = {
  title: "BioAge-X | Explainable Multi-Omics Biological Age Platform",
  description:
    "Open-source computational biology research platform for biological age estimation, multi-omics fusion, SHAP explainability, biological interaction networks, and GNNs.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#060913] text-slate-100 antialiased selection:bg-cyan-500/30 selection:text-cyan-200">
        <Navbar />
        <Sidebar />
        <main className="pl-64 pt-6 min-h-[calc(100vh-4rem)] p-8 max-w-7xl mx-auto">
          {children}
        </main>
      </body>
    </html>
  );
}
