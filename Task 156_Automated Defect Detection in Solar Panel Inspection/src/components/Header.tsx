import React from "react";
import { useApp } from "../store/AppContext";
import { ShieldAlert, Cpu, Activity, Database, CheckCircle2, AlertTriangle } from "lucide-react";
import { ModelConfig } from "../types";

export function Header() {
  const { models, inferenceComplete, activeImage } = useApp();

  const allLoaded = (Object.values(models) as ModelConfig[]).every(m => m.loaded);
  const anyLoaded = (Object.values(models) as ModelConfig[]).some(m => m.loaded);

  return (
    <header className="bg-slate-900 border-b border-slate-800 text-slate-100 px-6 py-4 flex flex-col md:flex-row justify-between items-center gap-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
          <Cpu className="w-6 h-6" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-semibold tracking-tight text-white">SolarLens AI Inspector</h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300 font-mono">v2.4-Enterprise</span>
          </div>
          <p className="text-xs text-slate-400">Industrial Solar Panel Defect Detection & Quality Assurance Platform</p>
        </div>
      </div>

      <div className="flex items-center gap-4 flex-wrap">
        {/* Model status badges */}
        <div className="flex items-center gap-2 bg-slate-800/80 border border-slate-700/80 px-3 py-1.5 rounded-lg text-xs">
          <Database className="w-4 h-4 text-slate-400" />
          <span className="text-slate-300 font-medium">Models:</span>
          <div className="flex items-center gap-1.5">
            {(Object.values(models) as ModelConfig[]).map(m => (
              <span
                key={m.id}
                title={`${m.name} (${m.framework}): ${m.loaded ? "Loaded" : "Not Loaded"}`}
                className={`w-2.5 h-2.5 rounded-full ${m.loaded ? "bg-emerald-500 shadow-sm shadow-emerald-500/50" : "bg-rose-500/80"}`}
              />
            ))}
          </div>
          <span className="text-slate-400 ml-1">
            {allLoaded ? "All Active" : anyLoaded ? "Partial" : "Offline"}
          </span>
        </div>

        {/* Active image status */}
        <div className="flex items-center gap-2 bg-slate-800/80 border border-slate-700/80 px-3 py-1.5 rounded-lg text-xs">
          <Activity className="w-4 h-4 text-amber-400" />
          <span className="text-slate-300">Active Image:</span>
          <span className="text-white font-mono truncate max-w-[120px]" title={activeImage?.filename || "None"}>
            {activeImage ? activeImage.filename : "None selected"}
          </span>
        </div>

        {/* Pipeline status */}
        <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border ${
          inferenceComplete 
            ? "bg-emerald-950/50 border-emerald-800/60 text-emerald-300"
            : allLoaded
            ? "bg-blue-950/50 border-blue-800/60 text-blue-300"
            : "bg-amber-950/50 border-amber-800/60 text-amber-300"
        }`}>
          {inferenceComplete ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Inspection Ready</span>
            </>
          ) : allLoaded ? (
            <>
              <Activity className="w-3.5 h-3.5" />
              <span>Weights Loaded</span>
            </>
          ) : (
            <>
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>No Models Loaded</span>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
