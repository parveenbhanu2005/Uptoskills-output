import React from "react";
import { useApp } from "../store/AppContext";
import { LayoutDashboard, UploadCloud, Database, Sliders, Layers, Cpu, PlayCircle, FileText, Wrench, Terminal, Settings } from "lucide-react";
import { ModelConfig } from "../types";

export function Sidebar() {
  const { activeTab, setActiveTab, models, activeImage, inferenceComplete, tickets } = useApp();

  const detectionLoaded = models.detection.loaded;

  const openTicketsCount = tickets.filter(t => t.status === "OPEN" || t.status === "IN_PROGRESS").length;

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard, badge: null },
    { id: "upload", label: "Image Upload", icon: UploadCloud, badge: activeImage ? "1" : null },
    { id: "datasets", label: "Dataset Manager", icon: Database, badge: "2 Active" },
    { id: "preprocess", label: "Preprocessing", icon: Sliders, badge: null },
    { id: "pipeline", label: "Inspection Pipeline", icon: Layers, badge: detectionLoaded ? "Ready" : "Weights Needed" },
    { id: "training", label: "Model Training", icon: PlayCircle, badge: "GPU Ready" },
    { id: "models", label: "Model Management", icon: Cpu, badge: (Object.values(models) as ModelConfig[]).filter(m => m.loaded).length + "/3" },
    { id: "reports", label: "Engineering Reports", icon: FileText, badge: inferenceComplete ? "Ready" : "Locked" },
    { id: "tickets", label: "Maintenance Tickets", icon: Wrench, badge: openTicketsCount > 0 ? `${openTicketsCount} Active` : "0" },
    { id: "logs", label: "System Logs", icon: Terminal, badge: null },
    { id: "settings", label: "Workstation Settings", icon: Settings, badge: "RTX 4090" },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between shrink-0 select-none">
      <div className="p-4 space-y-1.5 overflow-y-auto">
        <div className="px-3 py-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Pipeline Workflows
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-colors cursor-pointer ${
                isActive
                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white"
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? "text-amber-400" : "text-slate-400"}`} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono ${
                  item.badge === "Ready" || (typeof item.badge === "string" && item.badge.includes("/3"))
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                    : item.badge === "Weights Needed" || item.badge === "Locked"
                    ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                    : "bg-slate-800 text-slate-300 border border-slate-700"
                }`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="p-4 m-4 bg-slate-800/60 border border-slate-700/60 rounded-xl">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs font-semibold text-white">SolarLens AI Engine</span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          Phase 2 Workflow Active: Severity Engine, Maintenance Decision Engine, Evidence Crops & SQLite History operational.
        </p>
      </div>
    </aside>
  );
}
