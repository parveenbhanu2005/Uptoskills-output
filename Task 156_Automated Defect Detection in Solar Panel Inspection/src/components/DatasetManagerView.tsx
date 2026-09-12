import React, { useState } from "react";
import { useApp } from "../store/AppContext";
import { Database, Upload, CheckCircle2, AlertTriangle, Plus, Layers, Play, ArrowRight } from "lucide-react";

export function DatasetManagerView() {
  const { addLog, setActiveTab } = useApp();
  const [datasets, setDatasets] = useState([
    {
      id: "ds-1",
      name: "Solar_EL_Inspection_Batch_2026_Q1",
      imageCount: 1250,
      annotatedCount: 1250,
      classes: ["Micro Cracks", "Broken Glass", "Delamination", "Burn Marks", "Soiling"],
      splitRatio: { train: 80, val: 10, test: 10 },
      status: "Partitioned" as const,
      createdAt: "2026-03-15"
    },
    {
      id: "ds-2",
      name: "Infrared_Thermography_Rooftop_Array",
      imageCount: 640,
      annotatedCount: 610,
      classes: ["Hotspot", "Diode Failure", "String Disconnection"],
      splitRatio: { train: 75, val: 15, test: 10 },
      status: "Ready" as const,
      createdAt: "2026-04-02"
    }
  ]);

  const [newDsName, setNewDsName] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);

  const handleCreateDataset = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDsName) return;
    const newDs = {
      id: `ds-${Date.now()}`,
      name: newDsName,
      imageCount: 320,
      annotatedCount: 320,
      classes: ["Micro Cracks", "Delamination", "Soiling"],
      splitRatio: { train: 80, val: 10, test: 10 },
      status: "Partitioned" as const,
      createdAt: new Date().toLocaleDateString()
    };
    setDatasets([newDs, ...datasets]);
    addLog("UPLOAD", `Created and partitioned dataset: ${newDs.name} (${newDs.imageCount} images)`, "SUCCESS");
    setNewDsName("");
    setShowCreateModal(false);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Dataset Manager</h2>
          <p className="text-sm text-slate-400">Manage inspection datasets, verify class distributions, check annotations, and partition train/val/test splits.</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-950 font-semibold text-xs flex items-center gap-2 cursor-pointer transition-colors shadow-md shadow-amber-500/10"
        >
          <Plus className="w-4 h-4" />
          <span>Upload / Create Dataset</span>
        </button>
      </div>

      {showCreateModal && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 className="font-semibold text-white">Create New Dataset Partition</h3>
          <form onSubmit={handleCreateDataset} className="space-y-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Dataset Name</label>
              <input
                type="text"
                value={newDsName}
                onChange={(e) => setNewDsName(e.target.value)}
                placeholder="e.g. Solar_EL_Inspection_Batch_Summer"
                className="w-full px-4 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-amber-500"
              />
            </div>
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs hover:bg-slate-700 cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-amber-500 text-slate-950 font-semibold text-xs cursor-pointer"
              >
                Partition & Save
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {datasets.map((ds) => (
          <div key={ds.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                  <Database className="w-5 h-5" />
                </div>
                <span className={`text-xs px-2.5 py-1 rounded-full font-mono border ${
                  ds.status === "Partitioned" ? "bg-emerald-950/50 border-emerald-800 text-emerald-300" : "bg-blue-950/50 border-blue-800 text-blue-300"
                }`}>
                  {ds.status}
                </span>
              </div>

              <div>
                <h3 className="text-base font-semibold text-white">{ds.name}</h3>
                <p className="text-xs text-slate-400">Created: {ds.createdAt}</p>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs pt-2 border-t border-slate-800">
                <div className="p-3 rounded-xl bg-slate-800/60 border border-slate-700/60">
                  <span className="text-slate-400">Total Images</span>
                  <p className="text-white font-mono text-sm mt-1">{ds.imageCount}</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-800/60 border border-slate-700/60">
                  <span className="text-slate-400">Annotated Labels</span>
                  <p className="text-emerald-400 font-mono text-sm mt-1">{ds.annotatedCount} (100%)</p>
                </div>
              </div>

              <div className="space-y-2">
                <span className="text-xs text-slate-400">Target Classes ({ds.classes.length})</span>
                <div className="flex flex-wrap gap-1.5">
                  {ds.classes.map((cls, i) => (
                    <span key={i} className="text-[10px] px-2 py-0.5 rounded-md bg-slate-800 border border-slate-700 text-slate-300 font-mono">
                      {cls}
                    </span>
                  ))}
                </div>
              </div>

              <div className="space-y-1 text-xs">
                <div className="flex justify-between text-slate-400">
                  <span>Split Ratio (Train / Val / Test)</span>
                  <span className="font-mono text-slate-200">{ds.splitRatio.train}% / {ds.splitRatio.val}% / {ds.splitRatio.test}%</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden flex">
                  <div className="bg-amber-500 h-full" style={{ width: `${ds.splitRatio.train}%` }} />
                  <div className="bg-blue-500 h-full" style={{ width: `${ds.splitRatio.val}%` }} />
                  <div className="bg-purple-500 h-full" style={{ width: `${ds.splitRatio.test}%` }} />
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800 flex justify-between items-center">
              <span className="text-xs text-slate-400">Missing Labels: 0</span>
              <button
                onClick={() => setActiveTab("training")}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-400 border border-slate-700 text-xs font-medium flex items-center gap-1.5 cursor-pointer transition-colors"
              >
                <span>Train Model on Dataset</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
