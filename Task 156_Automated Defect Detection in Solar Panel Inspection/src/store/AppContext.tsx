import React, { createContext, useContext, useState, useEffect } from "react";
import { UploadedImage, ValidationResult, PreprocessingConfig, ModelsState, LogEntry, InferenceResult, MaintenanceTicket, TicketStatus } from "../types";

interface AppContextType {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  images: UploadedImage[];
  setImages: React.Dispatch<React.SetStateAction<UploadedImage[]>>;
  activeImage: UploadedImage | null;
  setActiveImage: (img: UploadedImage | null) => void;
  validationResult: ValidationResult | null;
  setValidationResult: React.Dispatch<React.SetStateAction<ValidationResult | null>>;
  preprocessingConfig: PreprocessingConfig;
  setPreprocessingConfig: React.Dispatch<React.SetStateAction<PreprocessingConfig>>;
  preprocessedImageUrl: string | null;
  setPreprocessedImageUrl: (url: string | null) => void;
  models: ModelsState;
  logs: LogEntry[];
  addLog: (category: LogEntry["category"], message: string, level?: LogEntry["level"]) => void;
  loadModel: (modelId: string, filename: string, framework?: any, version?: string) => Promise<void>;
  unloadModel: (modelId: string) => Promise<void>;
  inferenceComplete: boolean;
  setInferenceComplete: (val: boolean) => void;
  isProcessing: boolean;
  setIsProcessing: (val: boolean) => void;
  runPipelineInference: () => Promise<boolean>;
  inferenceResult: InferenceResult | null;
  tickets: MaintenanceTicket[];
  fetchTickets: () => Promise<void>;
  updateTicketStatus: (ticketId: string, status: TicketStatus) => Promise<boolean>;
}

const defaultPreprocessing: PreprocessingConfig = {
  resizeWidth: 1024,
  resizeHeight: 1024,
  noiseRemoval: true,
  histogramEqualization: false,
  clahe: true,
  contrastEnhancement: 15,
  imageSharpening: true,
  perspectiveCorrection: false,
  colorNormalization: true,
  confidenceThreshold: 0.10,
};

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [activeTab, setActiveTab] = useState<string>("dashboard");
  const [images, setImages] = useState<UploadedImage[]>([]);
  const [activeImage, setActiveImage] = useState<UploadedImage | null>(null);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [preprocessingConfig, setPreprocessingConfig] = useState<PreprocessingConfig>(defaultPreprocessing);
  const [preprocessedImageUrl, setPreprocessedImageUrl] = useState<string | null>(null);
  
  const [models, setModels] = useState<ModelsState>({
    detection: {
      id: "detection",
      name: "Solar Panel Object Detector",
      type: "detection",
      framework: "YOLO",
      version: "auto-detected",
      inputResolution: "640x640",
      loaded: false
    },
    segmentation: {
      id: "segmentation",
      name: "Panel Mask Segmenter",
      type: "segmentation",
      framework: "SAM2",
      version: "stub",
      inputResolution: "1024x1024",
      loaded: false
    },
    classification: {
      id: "classification",
      name: "Defect Classifier & Severity Estimator",
      type: "classification",
      framework: "EfficientNet",
      version: "stub",
      inputResolution: "384x384",
      loaded: false
    }
  });

  const [logs, setLogs] = useState<LogEntry[]>([
    {
      id: "log-init",
      timestamp: new Date().toLocaleTimeString(),
      category: "MODEL",
      message: "Platform initialized. Load detection model weights to begin inference.",
      level: "INFO"
    }
  ]);

  const [inferenceComplete, setInferenceComplete] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [inferenceResult, setInferenceResult] = useState<InferenceResult | null>(null);
  const [tickets, setTickets] = useState<MaintenanceTicket[]>([]);

  const addLog = (category: LogEntry["category"], message: string, level: LogEntry["level"] = "INFO") => {
    const newEntry: LogEntry = {
      id: `log-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
      timestamp: new Date().toLocaleTimeString(),
      category,
      message,
      level
    };
    setLogs(prev => [newEntry, ...prev]);

    fetch("/api/logs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ category, message, level })
    }).catch(() => {});
  };

  const fetchTickets = async () => {
    try {
      const res = await fetch("/api/tickets");
      if (res.ok) {
        const data = await res.json();
        if (data.tickets) {
          setTickets(data.tickets);
        }
      }
    } catch (err) {
      console.error("Error fetching tickets:", err);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, []);

  const updateTicketStatus = async (ticketId: string, status: TicketStatus): Promise<boolean> => {
    try {
      const res = await fetch(`/api/tickets/${ticketId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status })
      });
      if (res.ok) {
        addLog("INFERENCE", `Updated ticket ${ticketId} status to ${status}`, "SUCCESS");
        await fetchTickets();
        return true;
      }
      return false;
    } catch (err) {
      addLog("ERROR", `Failed to update ticket ${ticketId}: ${err}`, "ERROR");
      return false;
    }
  };

  const loadModel = async (modelId: string, filename: string, framework?: any, version?: string) => {
    try {
      const res = await fetch("/api/models/load", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ modelId, filename, framework, version })
      });
      const data = await res.json();
      if (data.success) {
        setModels(data.models);
        addLog("MODEL", `Loaded weights file '${data.models[modelId]?.filename || filename}' for ${models[modelId]?.name || modelId}`, "SUCCESS");
      }
    } catch (err) {
      addLog("MODEL", `Error loading model ${modelId}: ${err}`, "ERROR");
    }
  };

  const unloadModel = async (modelId: string) => {
    try {
      const res = await fetch("/api/models/unload", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ modelId })
      });
      const data = await res.json();
      if (data.success) {
        setModels(data.models);
        setInferenceComplete(false);
        setInferenceResult(null);
        addLog("MODEL", `Unloaded model ${models[modelId]?.name || modelId}`, "WARN");
      }
    } catch (err) {
      addLog("MODEL", `Error unloading model ${modelId}: ${err}`, "ERROR");
    }
  };

  const runPipelineInference = async (): Promise<boolean> => {
    setIsProcessing(true);
    addLog("INFERENCE", "Starting inspection pipeline...", "INFO");

    if (!activeImage || !activeImage.file) {
      setIsProcessing(false);
      addLog("INFERENCE", "No active image file available for inference.", "ERROR");
      alert("Please upload an image first.");
      return false;
    }

    try {
      const res = await fetch("/api/inference/run", {
        method: "POST",
        headers: {
          "Content-Type": activeImage.file.type,
          "X-Filename": activeImage.filename,
          "X-Preprocessing-Config": JSON.stringify(preprocessingConfig)
        },
        body: activeImage.file
      });

      const data = await res.json();
      if (!res.ok) {
        setIsProcessing(false);
        addLog("INFERENCE", data.error || "Inference failed.", "ERROR");
        alert(data.error || "No trained model loaded. Please load detection weights before running inference.");
        return false;
      }

      const result: InferenceResult = data.data;
      setInferenceResult(result);
      setIsProcessing(false);
      setInferenceComplete(true);
      
      await fetchTickets();

      addLog(
        "INFERENCE",
        `Pipeline completed: ${result.count} detections in ${result.time_ms}ms using ${result.model}`,
        "SUCCESS"
      );
      return true;
    } catch (err) {
      setIsProcessing(false);
      addLog("INFERENCE", `Pipeline execution error: ${err}`, "ERROR");
      return false;
    }
  };

  return (
    <AppContext.Provider
      value={{
        activeTab,
        setActiveTab,
        images,
        setImages,
        activeImage,
        setActiveImage,
        validationResult,
        setValidationResult,
        preprocessingConfig,
        setPreprocessingConfig,
        preprocessedImageUrl,
        setPreprocessedImageUrl,
        models,
        logs,
        addLog,
        loadModel,
        unloadModel,
        inferenceComplete,
        setInferenceComplete,
        isProcessing,
        setIsProcessing,
        runPipelineInference,
        inferenceResult,
        tickets,
        fetchTickets,
        updateTicketStatus
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
}
