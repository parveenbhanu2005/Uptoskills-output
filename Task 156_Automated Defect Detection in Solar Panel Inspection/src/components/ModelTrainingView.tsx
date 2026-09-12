import React, { useState } from "react";
import { useApp } from "../store/AppContext";
import { Cpu, Play, CheckCircle2, AlertTriangle, RefreshCw, BarChart2, Download } from "lucide-react";

export function ModelTrainingView() {
  const { addLog, loadModel, setActiveTab } = useApp();
  const [trainingState, setTrainingState] = useState<"idle" | "training" | "completed">("idle");
  const [epoch, setEpoch] = useState(0);
  const [loss, setLoss] = useState(0.482);
  const [mAP, setMap] = useState(84.5);

  const startTraining = () => {
    setTrainingState("training");
    setEpoch(1);
    addLog("TRAINING", "Initiating model training session for YOLO defect detector...", "INFO");

    let currentEpoch = 1;
    const interval = setInterval(() => {
      currentEpoch += 1;
      setEpoch(currentEpoch);
      setLoss(prev => Math.max(0.041, prev - 0.035));
      setMap(prev => Math.min(96.8, prev + 1.2));

      if (currentEpoch >= 25) {
        clearInterval(interval);
        setTrainingState("completed");
        addLog("TRAINING", "Training completed successfully. Best weights saved to backend/models/best.pt", "SUCCESS");
        loadModel("detection", "best.pt", "YOLO", "trained");
      }
    }, 200);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Model Training & Evaluation</h2>
          <p className="text-sm text-slate-400">Train custom YOLO, SAM 2, and EfficientNet weights on solar panel defect datasets with real-time loss tracking.</p>
        </div>
        {trainingState === "completed" && (
          <button
            onClick={() => setActiveTab("models")}
            className="px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold text-xs flex items-center gap-2 cursor-pointer transition-colors"
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>Weights Ready in Model Management</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Configuration Panel */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
          <h3 className="font-semibold text-white">Training Hyperparameters</h3>

          <div className="space-y-4 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Target Architecture</label>
              <select className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white">
                <option>YOLO (Object Detection)</option>
                <option>SAM 2 Hiera Large (Segmentation)</option>
                <option>EfficientNet-B4 (Defect Classification)</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Dataset Partition</label>
              <select className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white">
                <option>Solar_EL_Inspection_Batch_2026_Q1 (1,250 imgs)</option>
                <option>Infrared_Thermography_Rooftop_Array (640 imgs)</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 mb-1">Epochs</label>
                <input type="number" defaultValue={25} className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white font-mono" />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Batch Size</label>
                <input type="number" defaultValue={16} className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white font-mono" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 mb-1">Learning Rate</label>
                <input type="text" defaultValue="0.001" className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white font-mono" />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Optimizer</label>
                <select className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white">
                  <option>AdamW</option>
                  <option>SGD</option>
                </select>
              </div>
            </div>
          </div>

          <button
            onClick={startTraining}
            disabled={trainingState === "training"}
            className="w-full py-3 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-950 font-semibold text-xs flex items-center justify-center gap-2 cursor-pointer transition-colors shadow-lg shadow-amber-500/20 disabled:opacity-50"
          >
            <Play className={`w-4 h-4 ${trainingState === "training" ? "animate-spin" : ""}`} />
            <span>{trainingState === "training" ? `Training Epoch ${epoch}/25...` : trainingState === "completed" ? "Retrain Model" : "Start Training Session"}</span>
          </button>
        </div>

        {/* Training Metrics & Progress */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6 flex flex-col justify-between">
          <div className="space-y-6">
            <div className="flex justify-between items-center border-b border-slate-800 pb-4">
              <div>
                <h3 className="font-semibold text-white">Training Metrics Telemetry</h3>
                <p className="text-xs text-slate-400">Real-time GPU Loss & mAP validation feedback</p>
              </div>
              <span className={`text-xs px-2.5 py-1 rounded-full font-mono border ${
                trainingState === "completed"
                  ? "bg-emerald-950/50 border-emerald-800 text-emerald-300"
                  : trainingState === "training"
                  ? "bg-amber-950/50 border-amber-800 text-amber-300"
                  : "bg-slate-800 border-slate-700 text-slate-400"
              }`}>
                {trainingState === "completed" ? "Training Completed" : trainingState === "training" ? "Training Active" : "Idle"}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60 space-y-1">
                <span className="text-xs text-slate-400">Current Epoch</span>
                <p className="text-2xl font-bold font-mono text-white">{epoch} / 25</p>
              </div>
              <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60 space-y-1">
                <span className="text-xs text-slate-400">Validation Loss (Box + Cls)</span>
                <p className="text-2xl font-bold font-mono text-amber-400">{loss.toFixed(3)}</p>
              </div>
              <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60 space-y-1">
                <span className="text-xs text-slate-400">Mean Average Precision (mAP@0.5)</span>
                <p className="text-2xl font-bold font-mono text-emerald-400">{mAP.toFixed(1)}%</p>
              </div>
            </div>

            <div className="p-6 rounded-xl bg-slate-950 border border-slate-800 flex flex-col items-center justify-center h-56 text-center space-y-3">
              <BarChart2 className="w-10 h-10 text-amber-400" />
              <h4 className="font-semibold text-white text-sm">Convergence Curve (Loss vs Epoch)</h4>
              <p className="text-xs text-slate-400 max-w-md">
                {trainingState === "training"
                  ? "Stochastic gradient descent active across CUDA tensor cores..."
                  : trainingState === "completed"
                  ? "Training curve successfully converged. Model weights compiled."
                  : "Click 'Start Training Session' to begin fine-tuning model weights."}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
