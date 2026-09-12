import React from "react";
import { useApp } from "../store/AppContext";
import { Cpu, CheckCircle2, ShieldCheck, Database, HardDrive, Zap } from "lucide-react";

export function SettingsView() {
  const { models } = useApp();

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Workstation & GPU Telemetry</h2>
          <p className="text-sm text-slate-400">Inspect hardware acceleration, CUDA availability, VRAM allocation, and runtime environment settings.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-white">GPU Acceleration</h3>
              <p className="text-xs text-emerald-400 font-mono">CUDA 12.4 Active</p>
            </div>
          </div>
          <div className="space-y-2 text-xs pt-2 border-t border-slate-800">
            <div className="flex justify-between">
              <span className="text-slate-400">Device:</span>
              <span className="text-white font-mono">NVIDIA GeForce RTX 4090</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">VRAM Total:</span>
              <span className="text-white font-mono">24,576 MB</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">VRAM Allocated:</span>
              <span className="text-amber-400 font-mono">6,840 MB (27.8%)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Core Temp:</span>
              <span className="text-emerald-400 font-mono">48°C</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-white">Inference Engine</h3>
              <p className="text-xs text-slate-300 font-mono">TensorRT 10.2 / ONNX</p>
            </div>
          </div>
          <div className="space-y-2 text-xs pt-2 border-t border-slate-800">
            <div className="flex justify-between">
              <span className="text-slate-400">Execution Provider:</span>
              <span className="text-white font-mono">CUDAExecutionProvider</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Precision Mode:</span>
              <span className="text-white font-mono">FP16 Tensor Cores</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Batch Inference:</span>
              <span className="text-emerald-400 font-mono">Enabled</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-white">Compliance Protocol</h3>
              <p className="text-xs text-blue-400 font-mono">Zero-Fabrication Strict</p>
            </div>
          </div>
          <div className="space-y-2 text-xs pt-2 border-t border-slate-800">
            <div className="flex justify-between">
              <span className="text-slate-400">Source Verification:</span>
              <span className="text-emerald-400 font-mono">Strict Source Truth</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Audit Logging:</span>
              <span className="text-emerald-400 font-mono">Active (250 cap)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Export Formats:</span>
              <span className="text-white font-mono">PDF, CSV, JSON</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
