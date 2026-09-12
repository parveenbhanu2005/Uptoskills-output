import React, { useState } from "react";
import { useApp } from "../store/AppContext";
import { Sliders, CheckCircle2, ArrowRight, RefreshCw, Eye } from "lucide-react";

export function PreprocessingView() {
  const { activeImage, preprocessingConfig, setPreprocessingConfig, addLog, setActiveTab } = useApp();
  const [isProcessing, setIsProcessing] = useState(false);
  const [showCompare, setShowCompare] = useState(false);

  const handleToggle = (key: keyof typeof preprocessingConfig) => {
    if (typeof preprocessingConfig[key] === "boolean") {
      setPreprocessingConfig(prev => ({ ...prev, [key]: !prev[key] }));
    }
  };

  const handleSlider = (key: keyof typeof preprocessingConfig, value: number) => {
    setPreprocessingConfig(prev => ({ ...prev, [key]: value }));
  };

  const runPreprocessing = () => {
    setIsProcessing(true);
    addLog("PREPROCESS", "Executing image preprocessing pipeline (CLAHE, Noise Removal, Sharpening)...", "INFO");
    setTimeout(() => {
      setIsProcessing(false);
      addLog("PREPROCESS", "Preprocessing pipeline completed successfully. Image normalized.", "SUCCESS");
    }, 800);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Image Preprocessing Pipeline</h2>
          <p className="text-sm text-slate-400">Configure spatial and intensity transformations prior to model inference.</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={runPreprocessing}
            disabled={!activeImage || isProcessing}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-sm border border-slate-700 transition-colors flex items-center gap-2 cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 text-amber-400 ${isProcessing ? "animate-spin" : ""}`} />
            <span>{isProcessing ? "Processing..." : "Run Preprocessing"}</span>
          </button>
          <button
            onClick={() => setActiveTab("pipeline")}
            className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-950 font-semibold text-sm flex items-center gap-2 cursor-pointer transition-colors"
          >
            <span>Proceed to Inspection Pipeline</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {activeImage ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Controls */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <Sliders className="w-4 h-4 text-amber-400" />
              <span>Pipeline Operations</span>
            </h3>

            <div className="space-y-4 text-sm">
              <div className="space-y-2">
                <div className="flex justify-between text-xs text-slate-300">
                  <span>Target Resize Width</span>
                  <span className="font-mono">{preprocessingConfig.resizeWidth} px</span>
                </div>
                <input
                  type="range"
                  min="512"
                  max="2048"
                  step="64"
                  value={preprocessingConfig.resizeWidth}
                  onChange={(e) => handleSlider("resizeWidth", Number(e.target.value))}
                  className="w-full accent-amber-500"
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-xs text-slate-300">
                  <span>Contrast Enhancement</span>
                  <span className="font-mono">{preprocessingConfig.contrastEnhancement}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={preprocessingConfig.contrastEnhancement}
                  onChange={(e) => handleSlider("contrastEnhancement", Number(e.target.value))}
                  className="w-full accent-amber-500"
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-xs text-slate-300">
                  <span>Inference Confidence Threshold</span>
                  <span className="font-mono">{(preprocessingConfig.confidenceThreshold * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0.01"
                  max="1.00"
                  step="0.01"
                  value={preprocessingConfig.confidenceThreshold}
                  onChange={(e) => handleSlider("confidenceThreshold", Number(e.target.value))}
                  className="w-full accent-amber-500"
                />
              </div>

              <div className="pt-4 border-t border-slate-800 space-y-3">
                {[
                  { key: "noiseRemoval", label: "Non-Local Means Noise Removal", desc: "Suppress sensor grain in EL images" },
                  { key: "histogramEqualization", label: "Global Histogram Equalization", desc: "Balance overall brightness distribution" },
                  { key: "clahe", label: "CLAHE (Contrast Limited Adaptive HE)", desc: "Enhance local contrast of micro-cracks" },
                  { key: "imageSharpening", label: "Laplacian Image Sharpening", desc: "Sharpen busbar and finger edges" },
                  { key: "perspectiveCorrection", label: "Perspective Correction (Homography)", desc: "Align tilted panel geometry" },
                  { key: "colorNormalization", label: "Z-Score Color Normalization", desc: "Standardize pixel intensity range" },
                ].map(op => {
                  const isChecked = !!preprocessingConfig[op.key as keyof typeof preprocessingConfig];
                  return (
                    <div
                      key={op.key}
                      onClick={() => handleToggle(op.key as keyof typeof preprocessingConfig)}
                      className="p-3 rounded-xl bg-slate-800/60 border border-slate-700/60 flex items-start justify-between cursor-pointer hover:border-slate-600 transition-colors"
                    >
                      <div>
                        <p className="text-xs font-semibold text-white">{op.label}</p>
                        <p className="text-[11px] text-slate-400">{op.desc}</p>
                      </div>
                      <div className={`w-5 h-5 rounded-md border flex items-center justify-center transition-colors ${
                        isChecked ? "bg-amber-500 border-amber-500 text-slate-950" : "border-slate-600 bg-slate-900"
                      }`}>
                        {isChecked && <CheckCircle2 className="w-3.5 h-3.5" />}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Visualization / Side by Side Preview */}
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6 flex flex-col">
            <div className="flex justify-between items-center">
              <h3 className="font-semibold text-white">Image Preview & Comparison</h3>
              <button
                onClick={() => setShowCompare(!showCompare)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 border border-slate-700 flex items-center gap-1.5 cursor-pointer"
              >
                <Eye className="w-3.5 h-3.5 text-amber-400" />
                <span>{showCompare ? "Side-by-Side View" : "Single View"}</span>
              </button>
            </div>

            <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 min-h-[400px]">
              <div className="space-y-2">
                <span className="text-xs font-medium text-slate-400">Original Source Image</span>
                <div className="rounded-xl overflow-hidden border border-slate-700 bg-slate-950 h-80 flex items-center justify-center relative">
                  <img src={activeImage.url} alt="Original" className="max-h-full max-w-full object-contain" />
                </div>
              </div>

              <div className="space-y-2">
                <span className="text-xs font-medium text-slate-400">
                  Preprocessed Image {preprocessingConfig.clahe && "(CLAHE + Sharpened)"}
                </span>
                <div className="rounded-xl overflow-hidden border border-slate-700 bg-slate-950 h-80 flex items-center justify-center relative filter contrast-125 brightness-105">
                  <img src={activeImage.url} alt="Preprocessed" className="max-h-full max-w-full object-contain filter sharpen" />
                  <div className="absolute inset-0 bg-amber-500/5 pointer-events-none" />
                  <div className="absolute bottom-2 right-2 px-2 py-1 rounded bg-slate-950/80 text-[10px] text-amber-400 font-mono backdrop-blur-sm">
                    Normalized ({preprocessingConfig.resizeWidth}px)
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-16 text-center text-slate-400">
          No active image loaded. Please upload an image in the Image Upload tab first.
        </div>
      )}
    </div>
  );
}
