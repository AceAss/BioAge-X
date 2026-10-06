"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Database,
  Workflow,
  Cpu,
  Scale,
  Sparkles,
  Dna,
  Share2,
  Network,
  GitBranch,
  History,
  FileSpreadsheet,
  Settings,
  Globe,
  Search,
  ArrowRightLeft,
  Layers,
  ShieldAlert,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_GROUPS = [
  {
    group: "Overview & Data",
    items: [
      { label: "Research Overview", href: "/dashboard", icon: LayoutDashboard },
      { label: "Dataset Explorer", href: "/datasets/explorer", icon: Search },
      { label: "Multi-Omics Datasets", href: "/datasets", icon: Database },
      { label: "External Knowledge", href: "/integrations", icon: Globe },
    ],
  },
  {
    group: "Phase 1: BioAge Prediction",
    items: [
      { label: "Guided Analysis", href: "/analysis", icon: Workflow },
      { label: "Models & Multi-Omics", href: "/models", icon: Cpu },
      { label: "Epigenetic Benchmarks", href: "/benchmarks", icon: Scale },
      { label: "SHAP Explainability", href: "/explainability", icon: Sparkles },
      { label: "Candidate Biomarkers", href: "/biomarkers", icon: Dna },
    ],
  },
  {
    group: "Phase 2: GraphOmics-AI",
    items: [
      { label: "Biological Network", href: "/network", icon: Share2 },
      { label: "GNN Lab", href: "/gnn", icon: Network },
      { label: "Pathway Enrichment", href: "/pathways", icon: GitBranch },
    ],
  },
  {
    group: "Reproducibility & Rigor",
    items: [
      { label: "Experiment Tracking", href: "/experiments", icon: History },
      { label: "Compare Experiments", href: "/experiments/compare", icon: ArrowRightLeft },
      { label: "Ablation Studies", href: "/experiments/ablation", icon: Layers },
      { label: "Scientific Limitations", href: "/limitations", icon: ShieldAlert },
      { label: "Research Reports", href: "/reports", icon: FileSpreadsheet },
      { label: "Platform Settings", href: "/settings", icon: Settings },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-16 z-40 h-[calc(100vh-4rem)] w-64 border-r border-slate-800 bg-[#090d16]/95 backdrop-blur-md overflow-y-auto custom-scrollbar">
      <div className="flex flex-col min-h-full justify-between p-3.5 space-y-4">
        {/* Navigation list */}
        <div className="space-y-4">
          {NAV_GROUPS.map((grp) => (
            <div key={grp.group} className="space-y-1">
              <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-500">
                {grp.group}
              </div>
              {grp.items.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-all duration-150",
                      isActive
                        ? "bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 shadow-[0_0_12px_rgba(14,165,233,0.15)]"
                        : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                    )}
                  >
                    <Icon className={cn("h-3.5 w-3.5 shrink-0", isActive ? "text-cyan-400" : "text-slate-500")} />
                    <span className="truncate">{item.label}</span>
                  </Link>
                );
              })}
            </div>
          ))}
        </div>

        {/* Footer / Educational Disclaimer */}
        <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-3 text-[11px] text-slate-400">
          <p className="font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
            Research Platform
          </p>
          <p className="text-[10px] leading-relaxed text-slate-500">
            For computational biology & educational research only. Not for clinical diagnostic use.
          </p>
        </div>
      </div>
    </aside>
  );
}
