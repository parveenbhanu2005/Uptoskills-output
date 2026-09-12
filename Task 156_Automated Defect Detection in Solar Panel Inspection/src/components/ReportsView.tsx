import React from "react";
import { useApp } from "../store/AppContext";
import { FileText, Download, AlertTriangle, ShieldCheck, Image as ImageIcon, BarChart2, Cpu, Clock, Target, Wrench, ShieldAlert } from "lucide-react";

export function ReportsView() {
  const { activeImage, inferenceComplete, addLog, inferenceResult } = useApp();

  const displayDetections = inferenceResult?.normalized_detections && inferenceResult.normalized_detections.length > 0
    ? inferenceResult.normalized_detections
    : inferenceResult?.detections || [];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Engineering Reports</h2>
          <p className="text-sm text-slate-400">Certified inspection results, severity breakdown, maintenance recommendations, and PDF/CSV export.</p>
        </div>
      </div>

      {!inferenceComplete || !inferenceResult ? (
        <div className="bg-amber-950/30 border border-amber-600/50 rounded-2xl p-8 text-center space-y-4">
          <AlertTriangle className="w-12 h-12 text-amber-400 mx-auto" />
          <h3 className="text-lg font-semibold text-amber-300">Report Generation Locked</h3>
          <p className="text-sm text-slate-300 max-w-md mx-auto">
            Engineering reports are generated after running the inference pipeline with loaded detection model weights.
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Images: Original and Annotated */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
              <div className="flex items-center gap-2">
                <ImageIcon className="w-4 h-4 text-slate-400" />
                <h3 className="font-semibold text-white text-sm">Original Image</h3>
              </div>
              <div className="rounded-xl overflow-hidden border border-slate-700 bg-slate-950 flex items-center justify-center" style={{ minHeight: "280px" }}>
                {activeImage && <img src={activeImage.url} alt="Original" className="max-h-72 max-w-full object-contain" />}
              </div>
              <p className="text-xs text-slate-400 font-mono">{inferenceResult.image_id}</p>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <h3 className="font-semibold text-white text-sm">Annotated Image</h3>
                </div>
                <a
                  href={`/outputs/${inferenceResult.annotated_image}`}
                  download
                  onClick={() => addLog("EXPORT", "Downloaded annotated image", "SUCCESS")}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs border border-slate-700 flex items-center gap-1.5 transition-colors"
                >
                  <Download className="w-3 h-3 text-amber-400" />
                  <span>Download</span>
                </a>
              </div>
              <div className="rounded-xl overflow-hidden border border-emerald-800/40 bg-slate-950 flex items-center justify-center" style={{ minHeight: "280px" }}>
                <img src={`/outputs/${inferenceResult.annotated_image}`} alt="Annotated" className="max-h-72 max-w-full object-contain" />
              </div>
              <div className="flex gap-3 text-xs text-slate-400 font-mono">
                <span>{inferenceResult.count} detections</span>
                <span>•</span>
                <span>{inferenceResult.time_ms}ms</span>
              </div>
            </div>
          </div>

          {/* Severity & Maintenance Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                <h3 className="font-semibold text-white text-sm">Severity Analysis Summary</h3>
              </div>
              <div className="grid grid-cols-4 gap-2 text-center text-xs">
                <div className="bg-slate-800/80 border border-slate-700/60 p-3 rounded-xl space-y-1">
                  <span className="text-slate-400 text-[11px]">LOW</span>
                  <p className="text-xl font-bold font-mono text-slate-300">{inferenceResult.severity_summary?.low || 0}</p>
                </div>
                <div className="bg-amber-500/10 border border-amber-500/20 p-3 rounded-xl space-y-1">
                  <span className="text-amber-400 text-[11px]">MEDIUM</span>
                  <p className="text-xl font-bold font-mono text-amber-300">{inferenceResult.severity_summary?.medium || 0}</p>
                </div>
                <div className="bg-orange-500/10 border border-orange-500/30 p-3 rounded-xl space-y-1">
                  <span className="text-orange-400 text-[11px]">HIGH</span>
                  <p className="text-xl font-bold font-mono text-orange-300">{inferenceResult.severity_summary?.high || 0}</p>
                </div>
                <div className="bg-rose-500/10 border border-rose-500/30 p-3 rounded-xl space-y-1">
                  <span className="text-rose-400 text-[11px]">CRITICAL</span>
                  <p className="text-xl font-bold font-mono text-rose-300">{inferenceResult.severity_summary?.critical || 0}</p>
                </div>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-3">
              <div className="flex items-center gap-2">
                <Wrench className="w-4 h-4 text-emerald-400" />
                <h3 className="font-semibold text-white text-sm">Maintenance Recommendations</h3>
              </div>
              <div className="grid grid-cols-4 gap-2 text-center text-xs">
                <div className="bg-slate-800/80 border border-slate-700/60 p-3 rounded-xl space-y-1">
                  <span className="text-slate-400 text-[10px]">MONITOR</span>
                  <p className="text-xl font-bold font-mono text-slate-300">{inferenceResult.maintenance_summary?.monitor_count || 0}</p>
                </div>
                <div className="bg-blue-500/10 border border-blue-500/20 p-3 rounded-xl space-y-1">
                  <span className="text-blue-400 text-[10px]">REVIEW</span>
                  <p className="text-xl font-bold font-mono text-blue-300">{inferenceResult.maintenance_summary?.review_count || 0}</p>
                </div>
                <div className="bg-amber-500/10 border border-amber-500/20 p-3 rounded-xl space-y-1">
                  <span className="text-amber-400 text-[9px] truncate">MAINT_REQ</span>
                  <p className="text-xl font-bold font-mono text-amber-300">{inferenceResult.maintenance_summary?.maintenance_required_count || 0}</p>
                </div>
                <div className="bg-rose-500/10 border border-rose-500/30 p-3 rounded-xl space-y-1">
                  <span className="text-rose-400 text-[9px] truncate">PRIORITY</span>
                  <p className="text-xl font-bold font-mono text-rose-300">{inferenceResult.maintenance_summary?.priority_maintenance_count || 0}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Statistics Grid */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-amber-400" />
              <h3 className="font-semibold text-white">Inspection Statistics</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60 space-y-1">
                <span className="text-xs text-slate-400 flex items-center gap-1"><Target className="w-3 h-3" /> Total Detections</span>
                <p className="text-2xl font-bold font-mono text-white">{inferenceResult.statistics.total_detections}</p>
              </div>
              <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60 space-y-1">
                <span className="text-xs text-slate-400">Average Confidence</span>
                <p className="text-2xl font-bold font-mono text-amber-400">{(inferenceResult.statistics.average_confidence * 100).toFixed(1)}%</p>
              </div>
              <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60 space-y-1">
                <span className="text-xs text-slate-400">Highest Confidence</span>
                <p className="text-2xl font-bold font-mono text-emerald-400">{(inferenceResult.statistics.highest_confidence * 100).toFixed(1)}%</p>
              </div>
              <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60 space-y-1">
                <span className="text-xs text-slate-400 flex items-center gap-1"><Clock className="w-3 h-3" /> Inference Time</span>
                <p className="text-2xl font-bold font-mono text-blue-400">{inferenceResult.statistics.inference_time_ms}ms</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60 space-y-2">
                <span className="text-xs text-slate-400 flex items-center gap-1"><Cpu className="w-3 h-3" /> Model Details</span>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Filename:</span>
                    <span className="text-white font-mono">{inferenceResult.statistics.model_filename}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Device:</span>
                    <span className="text-white font-mono">{inferenceResult.statistics.device}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Input Resolution:</span>
                    <span className="text-white font-mono">{inferenceResult.statistics.input_resolution}</span>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60 space-y-2">
                <span className="text-xs text-slate-400">Class Distribution</span>
                {Object.keys(inferenceResult.statistics.class_distribution).length > 0 ? (
                  <div className="space-y-1.5">
                    {Object.entries(inferenceResult.statistics.class_distribution).map(([cls, count]) => (
                      <div key={cls} className="flex items-center justify-between text-xs">
                        <span className="text-white">{cls}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-amber-500 rounded-full"
                              style={{ width: `${Math.min(100, ((count as number) / inferenceResult.statistics.total_detections) * 100)}%` }}
                            />
                          </div>
                          <span className="text-slate-300 font-mono w-6 text-right">{count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">No detections</p>
                )}
              </div>
            </div>
          </div>

          {/* Detection Table with Extended Phase 2 Details */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-amber-400" />
              Detection & Action Table
              <span className="text-xs text-slate-400 font-mono ml-2">({displayDetections.length} rows)</span>
            </h3>
            {displayDetections.length > 0 ? (
              <div className="overflow-x-auto rounded-xl border border-slate-800">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-slate-800/80 text-slate-300">
                      <th className="px-4 py-3 text-left font-semibold">ID</th>
                      <th className="px-4 py-3 text-left font-semibold">Crop</th>
                      <th className="px-4 py-3 text-left font-semibold">Class</th>
                      <th className="px-4 py-3 text-left font-semibold">Confidence</th>
                      <th className="px-4 py-3 text-left font-semibold">Severity Score</th>
                      <th className="px-4 py-3 text-left font-semibold">Severity Level</th>
                      <th className="px-4 py-3 text-left font-semibold">Recommended Action</th>
                      <th className="px-4 py-3 text-left font-semibold">Ticket ID</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayDetections.map((det, idx) => {
                      const sevLvl = det.severity_level || "LOW";
                      return (
                        <tr key={idx} className="border-t border-slate-800 hover:bg-slate-800/40 transition-colors">
                          <td className="px-4 py-2.5 font-mono text-slate-300">{det.detection_id}</td>
                          <td className="px-4 py-2.5">
                            {det.crop_path ? (
                              <img src={`/outputs/${det.crop_path}`} alt="Crop" className="w-10 h-10 object-cover rounded-lg border border-slate-700 bg-slate-950" />
                            ) : (
                              <span className="text-slate-600">—</span>
                            )}
                          </td>
                          <td className="px-4 py-2.5">
                            <span className="px-2 py-0.5 rounded-md bg-amber-500/10 border border-amber-500/20 text-amber-300 font-medium">
                              {det.class_name}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 font-mono text-emerald-400">{(det.confidence * 100).toFixed(1)}%</td>
                          <td className="px-4 py-2.5 font-mono text-slate-200">{det.severity_score ?? (det.confidence * 100).toFixed(1)}</td>
                          <td className="px-4 py-2.5 font-mono">
                            <span className={`px-2 py-0.5 rounded-md text-[11px] font-medium border ${
                              sevLvl === "CRITICAL" ? "bg-rose-500/10 border-rose-500/30 text-rose-300" :
                              sevLvl === "HIGH" ? "bg-orange-500/10 border-orange-500/30 text-orange-300" :
                              sevLvl === "MEDIUM" ? "bg-amber-500/10 border-amber-500/20 text-amber-300" :
                              "bg-slate-800 border-slate-700 text-slate-300"
                            }`}>
                              {sevLvl}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 font-mono text-slate-300">{det.recommended_action || "MONITOR"}</td>
                          <td className="px-4 py-2.5 font-mono text-amber-400">{det.ticket_id || "N/A"}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="py-8 text-center text-slate-500 text-sm">No defects detected.</div>
            )}
          </div>

          {/* Export Options */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="font-semibold text-white">Export Certified Reports</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              <a
                href={`/outputs/${inferenceResult.annotated_image}`}
                download
                onClick={() => addLog("EXPORT", "Downloaded annotated image", "SUCCESS")}
                className="py-3 px-4 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-medium text-xs flex items-center justify-center gap-2 cursor-pointer transition-colors text-center"
              >
                <Download className="w-4 h-4" />
                <span>Annotated Image</span>
              </a>
              <a
                href={`/outputs/${inferenceResult.csv}`}
                download
                onClick={() => addLog("EXPORT", "Downloaded CSV detections", "SUCCESS")}
                className="py-3 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-xs border border-slate-700 flex items-center justify-center gap-2 cursor-pointer transition-colors text-center"
              >
                <FileText className="w-4 h-4 text-amber-400" />
                <span>Download CSV</span>
              </a>
              <a
                href={`/outputs/${inferenceResult.pdf}`}
                download
                onClick={() => addLog("EXPORT", "Downloaded PDF report", "SUCCESS")}
                className="py-3 px-4 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-950 font-semibold text-xs flex items-center justify-center gap-2 cursor-pointer transition-colors shadow-lg shadow-amber-500/20 text-center"
              >
                <Download className="w-4 h-4" />
                <span>Download PDF Report</span>
              </a>
              <a
                href={`/outputs/${inferenceResult.detections_json}`}
                download
                onClick={() => addLog("EXPORT", "Downloaded JSON report", "SUCCESS")}
                className="py-3 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-xs border border-slate-700 flex items-center justify-center gap-2 cursor-pointer transition-colors text-center"
              >
                <FileText className="w-4 h-4 text-amber-400" />
                <span>Download JSON</span>
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
