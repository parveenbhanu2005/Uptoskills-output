import React, { useState, useRef } from "react";
import { useApp } from "../store/AppContext";
import { UploadCloud, Folder, FileImage, CheckCircle2, AlertTriangle, Trash2, ArrowRight } from "lucide-react";

export function UploadView() {
  const { images, setImages, activeImage, setActiveImage, validationResult, setValidationResult, addLog, setActiveTab } = useApp();
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = async (fileList: FileList | File[]) => {
    const filesArray = Array.from(fileList);
    for (const file of filesArray) {
      if (!file.type.startsWith("image/") && !file.name.match(/\.(tiff|tif)$/i)) {
        addLog("VALIDATION", `Rejected non-image file: ${file.name}`, "ERROR");
        continue;
      }

      const url = URL.createObjectURL(file);
      
      // Load image to get dimensions
      const img = new Image();
      img.src = url;
      await new Promise((resolve) => {
        img.onload = resolve;
        img.onerror = resolve;
      });

      const width = img.width || 1024;
      const height = img.height || 1024;

      const newImage = {
        id: `img-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
        filename: file.name,
        url,
        size: file.size,
        type: file.type || "image/tiff",
        width,
        height,
        uploadedAt: new Date().toLocaleTimeString(),
        file
      };

      // Validate via backend API
      try {
        const res = await fetch("/api/validate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            filename: file.name,
            size: file.size,
            type: file.type,
            width,
            height
          })
        });
        const valData = await res.json();
        setValidationResult(valData);
      } catch (e) {
        setValidationResult({ valid: true, errors: [], warnings: [] });
      }

      setImages(prev => [...prev, newImage]);
      setActiveImage(newImage);
      addLog("UPLOAD", `Successfully uploaded inspection image: ${file.name} (${width}x${height})`, "SUCCESS");
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Image Upload & Validation</h2>
          <p className="text-sm text-slate-400">Upload single EL/thermography images, batch files, or directories in JPG, PNG, or TIFF formats.</p>
        </div>
        {activeImage && (
          <button
            onClick={() => setActiveTab("preprocess")}
            className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-950 font-semibold text-sm flex items-center gap-2 cursor-pointer transition-colors"
          >
            <span>Proceed to Preprocessing</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload dropzone */}
        <div className="lg:col-span-2 space-y-6">
          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-2xl p-10 text-center flex flex-col items-center justify-center transition-all ${
              isDragging
                ? "border-amber-500 bg-amber-500/10"
                : "border-slate-700 bg-slate-900 hover:border-slate-600"
            }`}
          >
            <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 mb-4">
              <UploadCloud className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-1">Drag & Drop Solar Inspection Images</h3>
            <p className="text-sm text-slate-400 max-w-md mb-6">
              Support for high-resolution EL (Electroluminescence), RGB, and Thermography inspection files (.jpg, .png, .tiff, .tif).
            </p>

            <div className="flex items-center gap-4">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-sm border border-slate-700 transition-colors cursor-pointer flex items-center gap-2"
              >
                <FileImage className="w-4 h-4 text-amber-400" />
                <span>Browse Files</span>
              </button>
              <button
                onClick={() => folderInputRef.current?.click()}
                className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-sm border border-slate-700 transition-colors cursor-pointer flex items-center gap-2"
              >
                <Folder className="w-4 h-4 text-amber-400" />
                <span>Upload Folder</span>
              </button>
            </div>

            <input
              type="file"
              ref={fileInputRef}
              onChange={(e) => e.target.files && handleFiles(e.target.files)}
              multiple
              accept="image/jpeg,image/png,image/tiff,.tiff,.tif"
              className="hidden"
            />
            <input
              type="file"
              ref={folderInputRef}
              onChange={(e) => e.target.files && handleFiles(e.target.files)}
              {...({ webkitdirectory: "", directory: "" } as any)}
              className="hidden"
            />
          </div>

          {/* Uploaded Images List */}
          {images.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="font-semibold text-white">Loaded Inspection Queue ({images.length})</h4>
                <button
                  onClick={() => { setImages([]); setActiveImage(null); setValidationResult(null); }}
                  className="text-xs text-rose-400 hover:text-rose-300 flex items-center gap-1 cursor-pointer"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Clear All</span>
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-72 overflow-y-auto pr-2">
                {images.map(img => (
                  <div
                    key={img.id}
                    onClick={() => setActiveImage(img)}
                    className={`p-3 rounded-xl border flex items-center gap-3 cursor-pointer transition-all ${
                      activeImage?.id === img.id
                        ? "bg-amber-500/10 border-amber-500/50 text-white"
                        : "bg-slate-800/60 border-slate-700/60 text-slate-300 hover:bg-slate-800"
                    }`}
                  >
                    <img src={img.url} alt={img.filename} className="w-12 h-12 rounded-lg object-cover bg-slate-950 border border-slate-700" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate text-white">{img.filename}</p>
                      <p className="text-[11px] text-slate-400">{img.width}x{img.height} • {(img.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                    {activeImage?.id === img.id && (
                      <CheckCircle2 className="w-4 h-4 text-amber-400 shrink-0" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Validation & Preview Panel */}
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
            <h3 className="font-semibold text-white">Image Validation Module</h3>
            
            {activeImage ? (
              <div className="space-y-4">
                <div className="rounded-xl overflow-hidden border border-slate-700 bg-slate-950 aspect-video flex items-center justify-center relative">
                  <img src={activeImage.url} alt="Active preview" className="max-h-full max-w-full object-contain" />
                  <div className="absolute bottom-2 left-2 px-2 py-1 rounded bg-slate-950/80 text-[10px] text-slate-300 font-mono backdrop-blur-sm">
                    {activeImage.width} × {activeImage.height} px
                  </div>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">File Name:</span>
                    <span className="text-white font-mono truncate max-w-[160px]">{activeImage.filename}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">File Type:</span>
                    <span className="text-white font-mono">{activeImage.type || "image/tiff"}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">File Size:</span>
                    <span className="text-white font-mono">{(activeImage.size / 1024 / 1024).toFixed(2)} MB</span>
                  </div>
                </div>

                {validationResult && (
                  <div className={`p-4 rounded-xl border text-xs space-y-2 ${
                    validationResult.valid
                      ? "bg-emerald-950/20 border-emerald-800/40 text-emerald-300"
                      : "bg-rose-950/20 border-rose-800/40 text-rose-300"
                  }`}>
                    <div className="flex items-center gap-2 font-semibold">
                      {validationResult.valid ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <AlertTriangle className="w-4 h-4 text-rose-400" />}
                      <span>{validationResult.valid ? "Image Validation Passed" : "Validation Warnings/Errors"}</span>
                    </div>
                    {validationResult.warnings.map((w, idx) => (
                      <p key={idx} className="text-amber-300 text-[11px]">• {w}</p>
                    ))}
                    {validationResult.errors.map((e, idx) => (
                      <p key={idx} className="text-rose-300 text-[11px]">• {e}</p>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="py-16 text-center text-slate-500 text-sm">
                No active image selected. Upload an image to view validation telemetry.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
