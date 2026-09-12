import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import fs from "fs";

interface ModelConfig {
  id: string;
  name: string;
  type: "detection" | "segmentation" | "classification";
  framework: string;
  version: string;
  inputResolution: string;
  loaded: boolean;
  filename?: string;
  loadedAt?: string;
}

interface DatasetItem {
  id: string;
  name: string;
  imageCount: number;
  annotatedCount: number;
  classes: string[];
  splitRatio: { train: number; val: number; test: number };
  status: "Ready" | "Partitioned" | "Training";
  createdAt: string;
}

interface LogEntry {
  id: string;
  timestamp: string;
  category: "UPLOAD" | "VALIDATION" | "PREPROCESS" | "MODEL" | "INFERENCE" | "ERROR" | "EXPORT" | "TRAINING";
  message: string;
  level: "INFO" | "WARN" | "SUCCESS" | "ERROR";
}

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json({ limit: "50mb" }));
  app.use(express.urlencoded({ extended: true, limit: "50mb" }));

  let models: Record<string, ModelConfig> = {
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
  };

  let datasets: DatasetItem[] = [
    {
      id: "ds-1",
      name: "Solar_EL_Inspection_Batch_2026_Q1",
      imageCount: 1250,
      annotatedCount: 1250,
      classes: ["Micro Cracks", "Broken Glass", "Delamination", "Burn Marks", "Soiling"],
      splitRatio: { train: 80, val: 10, test: 10 },
      status: "Partitioned",
      createdAt: "2026-03-15"
    },
    {
      id: "ds-2",
      name: "Infrared_Thermography_Rooftop_Array",
      imageCount: 640,
      annotatedCount: 610,
      classes: ["Hotspot", "Diode Failure", "String Disconnection"],
      splitRatio: { train: 75, val: 15, test: 10 },
      status: "Ready",
      createdAt: "2026-04-02"
    }
  ];

  const logs: LogEntry[] = [
    {
      id: "log-1",
      timestamp: new Date().toISOString(),
      category: "MODEL",
      message: "System initialized. Waiting for trained model weights to be loaded.",
      level: "INFO"
    }
  ];

  const addLog = (category: LogEntry["category"], message: string, level: LogEntry["level"] = "INFO") => {
    const entry: LogEntry = {
      id: `log-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
      timestamp: new Date().toLocaleTimeString(),
      category,
      message,
      level
    };
    logs.unshift(entry);
    if (logs.length > 250) logs.pop();
  };

  // Fetch live model info from FastAPI backend
  const fetchFastAPIModelInfo = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/health");
      if (response.ok) {
        return await response.json();
      }
    } catch (err) {
      // FastAPI not running
    }
    return null;
  };

  // API Routes
  app.get("/api/health", (req, res) => {
    res.json({ status: "ok", timestamp: new Date().toISOString() });
  });

  // FastAPI Health & Inference Bridge Endpoints
  app.get("/api/fastapi/health", async (req, res) => {
    try {
      const response = await fetch("http://localhost:8000/api/health");
      if (response.ok) {
        const data = await response.json();
        return res.json({ status: "connected", fastapi: data });
      } else {
        return res.json({ status: "disconnected", error: "FastAPI responded with error status" });
      }
    } catch (err) {
      return res.json({ status: "offline", message: "FastAPI service not currently running on port 8000." });
    }
  });

  app.get("/api/models", (req, res) => {
    res.json({ models });
  });

  // Model Verification & Load
  const handleModelLoad = async (req: express.Request, res: express.Response) => {
    const { modelId, filename, framework, version } = req.body;
    if (!models[modelId]) {
      addLog("MODEL", `Failed to verify unknown model ID: ${modelId}`, "ERROR");
      return res.status(400).json({ error: "Invalid model ID" });
    }

    // For the detection model, get live info from FastAPI
    let actualFilename = filename;
    if (modelId === "detection") {
      const fastApiInfo = await fetchFastAPIModelInfo();
      if (fastApiInfo && fastApiInfo.model_loaded) {
        actualFilename = fastApiInfo.model_name || filename;
      }
    }

    addLog("MODEL", `Loading weights: ${actualFilename} for ${models[modelId].name}...`, "INFO");

    models[modelId].loaded = true;
    models[modelId].filename = actualFilename;
    if (framework) models[modelId].framework = framework;
    if (version) models[modelId].version = version;
    models[modelId].loadedAt = new Date().toLocaleTimeString();

    addLog("MODEL", `Successfully loaded weights for ${models[modelId].name}: ${actualFilename}`, "SUCCESS");
    res.json({ success: true, models });
  };

  app.post("/api/models/verify-and-load", handleModelLoad);
  app.post("/api/models/load", handleModelLoad);

  app.post("/api/models/unload", (req, res) => {
    const { modelId } = req.body;
    if (!models[modelId]) {
      return res.status(400).json({ error: "Invalid model ID" });
    }

    models[modelId].loaded = false;
    delete models[modelId].filename;
    delete models[modelId].loadedAt;

    addLog("MODEL", `Unloaded model weights for ${models[modelId].name}`, "WARN");
    res.json({ success: true, models });
  });

  // Dataset Endpoints
  app.get("/api/datasets", (req, res) => {
    res.json({ datasets });
  });

  app.post("/api/datasets/create", (req, res) => {
    const { name, imageCount, classes, splitRatio } = req.body;
    const newDs: DatasetItem = {
      id: `ds-${Date.now()}`,
      name: name || "New_Inspection_Dataset",
      imageCount: imageCount || 100,
      annotatedCount: imageCount || 100,
      classes: classes || ["Micro Cracks", "Broken Glass", "Delamination"],
      splitRatio: splitRatio || { train: 80, val: 10, test: 10 },
      status: "Partitioned",
      createdAt: new Date().toLocaleDateString()
    };
    datasets.unshift(newDs);
    addLog("UPLOAD", `Created and partitioned dataset: ${newDs.name} (${newDs.imageCount} images)`, "SUCCESS");
    res.json({ success: true, datasets });
  });

  // GPU Telemetry Endpoint — query from FastAPI if available
  app.get("/api/gpu/telemetry", async (req, res) => {
    const fastApiInfo = await fetchFastAPIModelInfo();
    res.json({
      device: fastApiInfo?.device || "cpu",
      cudaAvailable: fastApiInfo?.device === "cuda",
      torchVersion: fastApiInfo?.torch_version || "unknown",
      ultralyticsVersion: fastApiInfo?.ultralytics_version || "unknown",
    });
  });

  app.get("/api/logs", (req, res) => {
    res.json({ logs });
  });

  app.post("/api/logs", (req, res) => {
    const { category, message, level } = req.body;
    addLog(category || "INFERENCE", message || "", level || "INFO");
    res.json({ success: true });
  });

  // Ticket Management & History Gateway Endpoints (Proxy to FastAPI)
  app.get("/api/tickets", async (req, res) => {
    try {
      const queryStr = req.query.status ? `?status=${req.query.status}` : "";
      const response = await fetch(`http://localhost:8000/api/tickets${queryStr}`);
      const data = await response.json();
      return res.status(response.status).json(data);
    } catch (err) {
      return res.status(503).json({ error: "FastAPI service unavailable", details: String(err) });
    }
  });

  app.patch("/api/tickets/:id/status", async (req, res) => {
    try {
      const response = await fetch(`http://localhost:8000/api/tickets/${req.params.id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req.body)
      });
      const data = await response.json();
      return res.status(response.status).json(data);
    } catch (err) {
      return res.status(503).json({ error: "FastAPI service unavailable", details: String(err) });
    }
  });

  app.get("/api/history", async (req, res) => {
    try {
      const limit = req.query.limit || 50;
      const response = await fetch(`http://localhost:8000/api/history?limit=${limit}`);
      const data = await response.json();
      return res.status(response.status).json(data);
    } catch (err) {
      return res.status(503).json({ error: "FastAPI service unavailable", details: String(err) });
    }
  });

  // Validation API
  app.post("/api/validate", (req, res) => {
    const { filename, size, type, width, height } = req.body;
    addLog("VALIDATION", `Validating image: ${filename} (${type}, ${(size / 1024 / 1024).toFixed(2)} MB)`, "INFO");

    const errors: string[] = [];
    const warnings: string[] = [];

    const validTypes = ["image/jpeg", "image/png", "image/tiff", "image/jpg"];
    if (!validTypes.includes(type) && !filename?.match(/\.(jpg|jpeg|png|tiff|tif)$/i)) {
      errors.push("Unsupported file format. Only JPG, PNG, and TIFF are supported.");
    }

    if (width && height) {
      if (width < 512 || height < 512) {
        warnings.push("Resolution is below recommended 1024x1024 for optimal defect detection.");
      }
    }

    if (errors.length > 0) {
      addLog("VALIDATION", `Validation failed for ${filename}: ${errors.join(", ")}`, "ERROR");
      return res.json({ valid: false, errors, warnings });
    }

    addLog("VALIDATION", `Validation passed successfully for ${filename}`, "SUCCESS");
    res.json({ valid: true, errors: [], warnings });
  });

  // Inference Execution Pipeline API — forwards to FastAPI backend
  app.post("/api/inference/run", express.raw({ type: "image/*", limit: "50mb" }), async (req, res) => {
    if (!Buffer.isBuffer(req.body) || req.body.length === 0) {
      addLog("INFERENCE", "No image data received in request body.", "ERROR");
      return res.status(400).json({ error: "No image data received." });
    }

    const filename = (req.headers['x-filename'] as string) || 'image.jpg';
    const preprocessingConfigStr = (req.headers['x-preprocessing-config'] as string) || '{}';

    const detectionLoaded = models.detection.loaded;

    if (!detectionLoaded) {
      addLog("INFERENCE", "Inference aborted. Detection model not loaded. Please load weights first.", "ERROR");
      return res.status(400).json({
        error: "No trained model loaded. Please load detection weights before running inference.",
        missingModels: ["Detection Model"]
      });
    }

    addLog("INFERENCE", `Executing inference pipeline on ${filename}...`, "INFO");

    try {
      const blob = new Blob([req.body], { type: (req.headers['content-type'] as string) || 'image/jpeg' });
      const formData = new FormData();
      formData.append('file', blob, filename);
      formData.append('preprocessing_config', preprocessingConfigStr);

      const response = await fetch("http://localhost:8000/api/infer", {
        method: "POST",
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        addLog("INFERENCE", `Pipeline completed: ${result.count || 0} detections in ${result.time_ms || 0}ms using model ${result.model || 'unknown'}.`, "SUCCESS");
        return res.json({
          success: true,
          timestamp: new Date().toISOString(),
          data: result,
          message: "Inference completed successfully."
        });
      } else {
        const errText = await response.text();
        addLog("INFERENCE", `FastAPI inference execution failed: ${errText}`, "ERROR");
        return res.status(500).json({ error: "FastAPI inference execution failed", details: errText });
      }
    } catch (err) {
      addLog("INFERENCE", `FastAPI service unavailable: ${err}`, "ERROR");
      return res.status(503).json({ error: "FastAPI service unavailable.", details: String(err) });
    }
  });

  // Proxy outputs/ directory to FastAPI static files
  app.use("/outputs", async (req, res) => {
    const targetUrl = `http://localhost:8000/outputs${req.url}`;
    console.log(`[PROXY_DEBUG] Request received for: ${req.originalUrl}, req.url: ${req.url}, targetUrl: ${targetUrl}`);
    try {
      const response = await fetch(targetUrl);
      console.log(`[PROXY_DEBUG] FastAPI response status: ${response.status}, Content-Type: ${response.headers.get("content-type")}`);
      if (response.ok) {
        const contentType = response.headers.get("content-type");
        if (contentType) {
          res.setHeader("Content-Type", contentType);
        }
        const buffer = await response.arrayBuffer();
        console.log(`[PROXY_DEBUG] Sending ${buffer.byteLength} bytes to client`);
        return res.send(Buffer.from(buffer));
      } else {
        console.log(`[PROXY_DEBUG] FastAPI returned non-200. Sending file not found.`);
        return res.status(response.status).send("File not found");
      }
    } catch (err) {
      console.error(`[PROXY_DEBUG] Fetch error:`, err);
      return res.status(503).send("FastAPI outputs service unavailable");
    }
  });

  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*all", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Solar Panel Inspection Platform server running on http://localhost:${PORT}`);
  });
}

startServer();
