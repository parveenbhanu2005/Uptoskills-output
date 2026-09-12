import React from "react";
import { useApp } from "../store/AppContext";
import { UploadCloud, Sliders, Cpu, Layers, FileText, CheckCircle2, AlertTriangle, ArrowRight, Eye, ShieldCheck } from "lucide-react";
import { ModelConfig } from "../types";

export function DashboardView() {
  const { setActiveTab, activeImage, models, inferenceComplete } = useApp();

  const detectionLoaded = models.detection.loaded;

  const steps = [
    { title: "1. Image Upload", desc: "Upload high-res EL or thermography images (JPG, PNG, TIFF)", icon: UploadCloud, tab: "upload", done: !!activeImage },
    { title: "2. Image Validation & Preprocessing", desc: "Validate resolution, remove noise, apply CLAHE & contrast enhancement", icon: Sliders, tab: "preprocess", done: !!activeImage },
    { title: "3. Model Management", desc: "Load trained detection weights (.pt) for the YOLO model", icon: Cpu, tab: "models", done: detectionLoaded },
    { title: "4. Inspection Pipeline", desc: "Run detection, segmentation, defect detection, and severity analysis", icon: Layers, tab: "pipeline", done: inferenceComplete },
    { title: "5. Engineering Reports", desc: "Export compliant engineering reports in PDF, CSV, or JSON", icon: FileText, tab: "reports", done: inferenceComplete },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Hero Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border border-slate-700/80 rounded-2xl p-8 text-white shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-amber-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="max-w-3xl space-y-4 relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-medium">
            <ShieldCheck className="w-4 h-4" />
            Industrial Grade Solar Inspection Architecture
          </div>
          <h2 className="text-3xl font-bold tracking-tight">AI-Powered Solar Panel Quality Assurance</h2>
          <p className="text-slate-300 text-sm leading-relaxed">
            Welcome to the Phase 1 Solar Inspection Platform. Designed for zero-fabrication strictness: uploaded images remain the primary source of truth, and deep learning models are dynamically loaded without hardcoded stubs or synthetic predictions.
          </p>
          <div className="flex items-center gap-4 pt-2">
            <button
              onClick={() => setActiveTab(activeImage ? "preprocess" : "upload")}
              className="px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-950 font-semibold text-sm flex items-center gap-2 transition-colors shadow-lg shadow-amber-500/20 cursor-pointer"
            >
              <span>{activeImage ? "Configure Preprocessing" : "Upload Inspection Images"}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => setActiveTab("models")}
              className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium text-sm transition-colors cursor-pointer"
            >
              Manage Model Weights
            </button>
          </div>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Primary Source Image</span>
              {activeImage ? <CheckCircle2 className="w-5 h-5 text-emerald-400" /> : <AlertTriangle className="w-5 h-5 text-amber-400" />}
            </div>
            <h3 className="text-lg font-semibold text-white mb-1">
              {activeImage ? activeImage.filename : "No Image Loaded"}
            </h3>
            <p className="text-xs text-slate-400">
              {activeImage ? `${activeImage.width}x${activeImage.height} px • ${(activeImage.size / 1024 / 1024).toFixed(2)} MB` : "Upload a single image, folder, or batch of TIFF/PNG/JPG files."}
            </p>
          </div>
          <div className="mt-6 pt-4 border-t border-slate-800 flex justify-between items-center">
            <span className="text-xs text-slate-400">Status: {activeImage ? "Ready for Preprocessing" : "Awaiting Upload"}</span>
            <button
              onClick={() => setActiveTab("upload")}
              className="text-xs text-amber-400 hover:text-amber-300 font-medium flex items-center gap-1 cursor-pointer"
            >
              <span>{activeImage ? "Change Image" : "Upload Now"}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Trained Model Weights</span>
              {detectionLoaded ? <CheckCircle2 className="w-5 h-5 text-emerald-400" /> : <AlertTriangle className="w-5 h-5 text-amber-400" />}
            </div>
            <h3 className="text-lg font-semibold text-white mb-1">
              {models.detection.loaded ? "Detection Model Loaded" : "Detection Model Required"}
            </h3>
            <p className="text-xs text-slate-400">
              Detection model weights required for inference pipeline.
            </p>
          </div>
          <div className="mt-6 pt-4 border-t border-slate-800 flex justify-between items-center">
            <span className="text-xs text-slate-400">{detectionLoaded ? "Detection weights active" : "Weights required"}</span>
            <button
              onClick={() => setActiveTab("models")}
              className="text-xs text-amber-400 hover:text-amber-300 font-medium flex items-center gap-1 cursor-pointer"
            >
              <span>Manage Models</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Inspection Status</span>
              {inferenceComplete ? <CheckCircle2 className="w-5 h-5 text-emerald-400" /> : <AlertTriangle className="w-5 h-5 text-slate-500" />}
            </div>
            <h3 className="text-lg font-semibold text-white mb-1">
              {inferenceComplete ? "Inspection Complete" : "Pipeline Pending"}
            </h3>
            <p className="text-xs text-slate-400">
              {inferenceComplete ? "Engineering reports and telemetry available for export." : "Run pipeline after uploading image and loading model weights."}
            </p>
          </div>
          <div className="mt-6 pt-4 border-t border-slate-800 flex justify-between items-center">
            <span className="text-xs text-slate-400">Status: {inferenceComplete ? "Passed" : "Not Run"}</span>
            <button
              onClick={() => setActiveTab("pipeline")}
              className="text-xs text-amber-400 hover:text-amber-300 font-medium flex items-center gap-1 cursor-pointer"
            >
              <span>Open Pipeline</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Pipeline Workflow Progress */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
        <h3 className="text-lg font-semibold text-white">Pipeline Execution Workflow</h3>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <div
                key={idx}
                onClick={() => setActiveTab(step.tab)}
                className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col justify-between ${
                  step.done
                    ? "bg-emerald-950/20 border-emerald-800/40 hover:border-emerald-700"
                    : "bg-slate-800/50 border-slate-700/60 hover:border-slate-600"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${step.done ? "bg-emerald-500/20 text-emerald-400" : "bg-slate-700 text-slate-300"}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    {step.done ? (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono">Done</span>
                    ) : (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">Pending</span>
                    )}
                  </div>
                  <h4 className="text-sm font-semibold text-white mb-1">{step.title}</h4>
                  <p className="text-[11px] text-slate-400 leading-relaxed">{step.desc}</p>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs font-medium text-amber-400">
                  <span>Go to stage</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
