import React from "react";
import { useApp } from "../store/AppContext";
import { AlertTriangle, CheckCircle2, Play, FileText, Download, Image as ImageIcon, Table, ShieldAlert, Wrench, Eye } from "lucide-react";

export function InspectionPipelineView() {
  const { activeImage, models, inferenceComplete, runPipelineInference, isProcessing, setActiveTab, inferenceResult } = useApp();

  const detectionLoaded = models.detection.loaded;

  const displayDetections = inferenceResult?.normalized_detections && inferenceResult.normalized_detections.length > 0
    ? inferenceResult.normalized_detections
    : inferenceResult?.detections || [];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Industrial Inspection Pipeline</h2>
          <p className="text-sm text-slate-400">Sequential AI inference workflow with automated severity scoring & maintenance decisions.</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={async () => {
              const success = await runPipelineInference();
              if (success) {
                setActiveTab("reports");
              }
            }}
            disabled={!activeImage || isProcessing || !detectionLoaded}
            className="px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-950 font-semibold text-sm flex items-center gap-2 cursor-pointer transition-colors shadow-lg shadow-amber-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Play className={`w-4 h-4 ${isProcessing ? "animate-spin" : ""}`} />
            <span>{isProcessing ? "Running Pipeline..." : "Execute Full Pipeline"}</span>
          </button>
        </div>
      </div>

      {/* Model Status Warning Banner */}
      {!detectionLoaded && (
        <div className="bg-amber-950/30 border border-amber-600/50 rounded-2xl p-6 flex items-start gap-4">
          <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 shrink-0">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-amber-300">Detection model not loaded. Please load weights before running inference.</h3>
            <p className="text-xs text-amber-200/80 leading-relaxed">
              Upload your trained YOLO model weights (.pt) in the Model Management tab. Only the detection model is required for inference.
            </p>
            <div className="pt-2">
              <button
                onClick={() => setActiveTab("models")}
                className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-950 font-semibold text-xs transition-colors cursor-pointer"
              >
                Go to Model Management
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Results Area */}
      {inferenceComplete && inferenceResult ? (
        <div className="space-y-8">
          {/* Severity & Maintenance Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Severity Summary */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                <h3 className="font-semibold text-white text-sm">Severity Analysis Summary</h3>
              </div>
              <div className="grid grid-cols-4 gap-2 text-center text-xs">
                <div className="bg-slate-800/80 border border-slate-700/60 p-2.5 rounded-xl space-y-1">
                  <span className="text-slate-400 text-[11px]">LOW</span>
                  <p className="text-lg font-bold font-mono text-slate-300">{inferenceResult.severity_summary?.low || 0}</p>
                </div>
                <div className="bg-amber-500/10 border border-amber-500/20 p-2.5 rounded-xl space-y-1">
                  <span className="text-amber-400 text-[11px]">MEDIUM</span>
                  <p className="text-lg font-bold font-mono text-amber-300">{inferenceResult.severity_summary?.medium || 0}</p>
                </div>
                <div className="bg-orange-500/10 border border-orange-500/30 p-2.5 rounded-xl space-y-1">
                  <span className="text-orange-400 text-[11px]">HIGH</span>
                  <p className="text-lg font-bold font-mono text-orange-300">{inferenceResult.severity_summary?.high || 0}</p>
                </div>
                <div className="bg-rose-500/10 border border-rose-500/30 p-2.5 rounded-xl space-y-1">
                  <span className="text-rose-400 text-[11px]">CRITICAL</span>
                  <p className="text-lg font-bold font-mono text-rose-300">{inferenceResult.severity_summary?.critical || 0}</p>
                </div>
              </div>
            </div>

            {/* Maintenance Decision Summary */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Wrench className="w-4 h-4 text-emerald-400" />
                  <h3 className="font-semibold text-white text-sm">Maintenance Recommendations</h3>
                </div>
                {inferenceResult.tickets && inferenceResult.tickets.length > 0 && (
                  <button
                    onClick={() => setActiveTab("tickets")}
                    className="text-xs text-amber-400 hover:text-amber-300 flex items-center gap-1 cursor-pointer font-medium"
                  >
                    <span>View Tickets ({inferenceResult.tickets.length})</span>
                  </button>
                )}
              </div>
              <div className="grid grid-cols-4 gap-2 text-center text-xs">
                <div className="bg-slate-800/80 border border-slate-700/60 p-2.5 rounded-xl space-y-1">
                  <span className="text-slate-400 text-[11px]">MONITOR</span>
                  <p className="text-lg font-bold font-mono text-slate-300">{inferenceResult.maintenance_summary?.monitor_count || 0}</p>
                </div>
                <div className="bg-blue-500/10 border border-blue-500/20 p-2.5 rounded-xl space-y-1">
                  <span className="text-blue-400 text-[11px]">REVIEW</span>
                  <p className="text-lg font-bold font-mono text-blue-300">{inferenceResult.maintenance_summary?.review_count || 0}</p>
                </div>
                <div className="bg-amber-500/10 border border-amber-500/20 p-2.5 rounded-xl space-y-1">
                  <span className="text-amber-400 text-[10px] truncate">MAINT_REQ</span>
                  <p className="text-lg font-bold font-mono text-amber-300">{inferenceResult.maintenance_summary?.maintenance_required_count || 0}</p>
                </div>
                <div className="bg-rose-500/10 border border-rose-500/30 p-2.5 rounded-xl space-y-1">
                  <span className="text-rose-400 text-[10px] truncate">PRIORITY_MAINT</span>
                  <p className="text-lg font-bold font-mono text-rose-300">{inferenceResult.maintenance_summary?.priority_maintenance_count || 0}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Original → Annotated Flow */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Original Image */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
              <div className="flex items-center gap-2">
                <ImageIcon className="w-4 h-4 text-slate-400" />
                <h3 className="font-semibold text-white text-sm">Original Image</h3>
              </div>
              <div className="rounded-xl overflow-hidden border border-slate-700 bg-slate-950 flex items-center justify-center" style={{ minHeight: "320px" }}>
                {activeImage && (
                  <img src={activeImage.url} alt="Original" className="max-h-80 max-w-full object-contain" />
                )}
              </div>
              <p className="text-xs text-slate-400 font-mono">{inferenceResult.image_id}</p>
            </div>

            {/* Annotated Image */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <h3 className="font-semibold text-white text-sm">Annotated Image (YOLO Detections)</h3>
                </div>
                <a
                  href={`/outputs/${inferenceResult.annotated_image}`}
                  download
                  className="text-xs text-amber-400 hover:text-amber-300 flex items-center gap-1"
                >
                  <Download className="w-3 h-3" />
                  <span>Download</span>
                </a>
              </div>
              <div className="rounded-xl overflow-hidden border border-emerald-800/40 bg-slate-950 flex items-center justify-center" style={{ minHeight: "320px" }}>
                <img
                  src={`/outputs/${inferenceResult.annotated_image}`}
                  alt="Annotated"
                  className="max-h-80 max-w-full object-contain"
                />
              </div>
              <div className="flex items-center gap-4 text-xs text-slate-400 font-mono">
                <span>Model: {inferenceResult.model}</span>
                <span>•</span>
                <span>{inferenceResult.time_ms}ms</span>
                <span>•</span>
                <span>{inferenceResult.count} detections</span>
              </div>
            </div>
          </div>

          {/* Detection Table with Severity & Actions */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Table className="w-4 h-4 text-amber-400" />
                <h3 className="font-semibold text-white">Detection Results & Maintenance Decisions</h3>
                <span className="text-xs text-slate-400 font-mono ml-2">({displayDetections.length} detections)</span>
              </div>
              <div className="flex items-center gap-3">
                <a
                  href={`/outputs/${inferenceResult.csv}`}
                  download
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs border border-slate-700 flex items-center gap-1.5 transition-colors"
                >
                  <Download className="w-3 h-3 text-amber-400" />
                  <span>CSV</span>
                </a>
              </div>
            </div>

            {displayDetections.length > 0 ? (
              <div className="overflow-x-auto rounded-xl border border-slate-800">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-slate-800/80 text-slate-300">
                      <th className="px-4 py-3 text-left font-semibold">ID</th>
                      <th className="px-4 py-3 text-left font-semibold">Defect Evidence</th>
                      <th className="px-4 py-3 text-left font-semibold">Class</th>
                      <th className="px-4 py-3 text-left font-semibold">Confidence</th>
                      <th className="px-4 py-3 text-left font-semibold">Severity Score</th>
                      <th className="px-4 py-3 text-left font-semibold">Severity Band</th>
                      <th className="px-4 py-3 text-left font-semibold">Recommended Action</th>
                      <th className="px-4 py-3 text-left font-semibold">Ticket ID</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayDetections.map((det, idx) => {
                      const sevLvl = det.severity_level || "LOW";
                      const action = det.recommended_action || "MONITOR";
                      const cropPath = det.crop_path;

                      return (
                        <tr key={idx} className="border-t border-slate-800 hover:bg-slate-800/40 transition-colors">
                          <td className="px-4 py-2.5 font-mono text-slate-300">{det.detection_id}</td>
                          <td className="px-4 py-2.5">
                            {cropPath ? (
                              <img src={`/outputs/${cropPath}`} alt="Crop" className="w-12 h-12 object-cover rounded-lg border border-slate-700 bg-slate-950" />
                            ) : (
                              <span className="text-slate-600 italic">No crop</span>
                            )}
                          </td>
                          <td className="px-4 py-2.5">
                            <span className="px-2 py-0.5 rounded-md bg-amber-500/10 border border-amber-500/20 text-amber-300 font-medium">
                              {det.class_name}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 font-mono text-emerald-400">{(det.confidence * 100).toFixed(1)}%</td>
                          <td className="px-4 py-2.5 font-mono text-slate-200">
                            {det.severity_score !== undefined ? `${det.severity_score}` : `${(det.confidence * 100).toFixed(1)}`}
                          </td>
                          <td className="px-4 py-2.5">
                            <span className={`px-2 py-0.5 rounded-md font-medium text-[11px] border ${
                              sevLvl === "CRITICAL" ? "bg-rose-500/10 border-rose-500/30 text-rose-300" :
                              sevLvl === "HIGH" ? "bg-orange-500/10 border-orange-500/30 text-orange-300" :
                              sevLvl === "MEDIUM" ? "bg-amber-500/10 border-amber-500/20 text-amber-300" :
                              "bg-slate-800 border-slate-700 text-slate-300"
                            }`}>
                              {sevLvl}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 font-mono text-slate-300">{action}</td>
                          <td className="px-4 py-2.5 font-mono text-amber-400">
                            {det.ticket_id ? (
                              <button onClick={() => setActiveTab("tickets")} className="underline hover:text-amber-300 cursor-pointer">
                                {det.ticket_id}
                              </button>
                            ) : (
                              <span className="text-slate-600">—</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="py-12 text-center text-slate-500 text-sm">
                No defects detected in this image.
              </div>
            )}
          </div>

          {/* View Report Button */}
          <div className="flex justify-center">
            <button
              onClick={() => setActiveTab("reports")}
              className="px-6 py-3 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-950 font-semibold text-sm flex items-center gap-2 cursor-pointer transition-colors shadow-lg shadow-amber-500/20"
            >
              <FileText className="w-4 h-4" />
              <span>View Full Engineering Report</span>
            </button>
          </div>
        </div>
      ) : (
        /* Pre-inference view */
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6 min-h-[480px] flex flex-col items-center justify-center">
          {activeImage ? (
            <div className="text-center space-y-4">
              <div className="rounded-xl overflow-hidden border border-slate-700 bg-slate-950 inline-block">
                <img src={activeImage.url} alt="Preview" className="max-h-72 max-w-full object-contain" />
              </div>
              <p className="text-sm text-slate-300 font-medium">{activeImage.filename}</p>
              <p className="text-xs text-slate-500">
                {detectionLoaded
                  ? "Ready to run inference. Click 'Execute Full Pipeline' above."
                  : "Load the detection model first, then run inference."
                }
              </p>
            </div>
          ) : (
            <div className="text-center text-slate-500 text-sm space-y-2">
              <AlertTriangle className="w-10 h-10 text-slate-600 mx-auto" />
              <p>No active image loaded. Please upload an inspection image first.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
