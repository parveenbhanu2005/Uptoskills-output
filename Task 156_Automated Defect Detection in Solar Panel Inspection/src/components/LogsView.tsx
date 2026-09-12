import React from "react";
import { useApp } from "../store/AppContext";
import { Terminal, Trash2 } from "lucide-react";

export function LogsView() {
  const { logs } = useApp();

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">System & Telemetry Logs</h2>
          <p className="text-sm text-slate-400">Structured audit trail for uploads, model weight loading, preprocessing, and inference.</p>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2 text-white font-semibold text-sm">
            <Terminal className="w-4 h-4 text-amber-400" />
            <span>Audit Log Stream ({logs.length} entries)</span>
          </div>
          <span className="text-xs text-slate-400 font-mono">Real-time Container Feed</span>
        </div>

        <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2 font-mono text-xs">
          {logs.map((log) => (
            <div
              key={log.id}
              className={`p-3 rounded-xl border flex items-start gap-3 ${
                log.level === "ERROR"
                  ? "bg-rose-950/20 border-rose-800/40 text-rose-300"
                  : log.level === "SUCCESS"
                  ? "bg-emerald-950/20 border-emerald-800/40 text-emerald-300"
                  : log.level === "WARN"
                  ? "bg-amber-950/20 border-amber-800/40 text-amber-300"
                  : "bg-slate-800/50 border-slate-700/60 text-slate-300"
              }`}
            >
              <span className="text-slate-500 shrink-0">{log.timestamp}</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                log.category === "MODEL" ? "bg-purple-500/20 text-purple-300" :
                log.category === "INFERENCE" ? "bg-blue-500/20 text-blue-300" :
                log.category === "VALIDATION" ? "bg-amber-500/20 text-amber-300" :
                log.category === "UPLOAD" ? "bg-emerald-500/20 text-emerald-300" : "bg-slate-700 text-slate-300"
              }`}>
                {log.category}
              </span>
              <span className="flex-1 break-all">{log.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
