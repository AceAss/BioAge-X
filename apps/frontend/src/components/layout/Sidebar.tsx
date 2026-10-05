"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Database,
  Workflow,
  Cpu,
  Sparkles,
  Dna,
  Share2,
  Network,
  GitBranch,
  History,
  FileSpreadsheet,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Datasets", href: "/datasets", icon: Database },
  { label: "Guided Analysis", href: "/analysis", icon: Workflow },
  { label: "Models & Benchmarks", href: "/models", icon: Cpu },
  { label: "SHAP Explainability", href: "/explainability", icon: Sparkles },
  { label: "Biomarkers", href: "/biomarkers", icon: Dna },
  { label: "Biological Network", href: "/network", icon: Share2 },
  { label: "GNN Module", href: "/gnn", icon: Network },
  { label: "Pathways", href: "/pathways", icon: GitBranch },
  { label: "Experiments", href: "/experiments", icon: History },
  { label: "Research Reports", href: "/reports", icon: FileSpreadsheet },
  { label: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-16 z-40 h-[calc(100vh-4rem)] w-64 border-r border-slate-800 bg-[#090d16]/95 backdrop-blur-md">
      <div className="flex flex-col h-full justify-between p-4">
        {/* Navigation list */}
        <div className="space-y-1">
          <div className="px-3 pb-2 pt-1 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            Research Modules
          </div>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-xs font-medium transition-all duration-150",
                  isActive
                    ? "bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 shadow-[0_0_12px_rgba(14,165,233,0.15)]"
                    : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                )}
              >
                <Icon className={cn("h-4 w-4", isActive ? "text-cyan-400" : "text-slate-500")} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>

        {/* Footer / Educational Disclaimer */}
        <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-3 text-[11px] text-slate-400">
          <p className="font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
            Research Platform
          </p>
          <p className="text-[10px] leading-relaxed text-slate-500">
            For computational biology & educational research only. Not for clinical diagnosis.
          </p>
        </div>
      </div>
    </aside>
  );
}
