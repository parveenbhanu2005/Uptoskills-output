export interface UploadedImage {
  id: string;
  filename: string;
  url: string;
  size: number;
  type: string;
  width: number;
  height: number;
  uploadedAt: string;
  file?: File;
  metadata?: {
    droneAltitude?: string;
    cameraModel?: string;
    sensorType?: "RGB" | "Thermal" | "Electroluminescence (EL)";
  };
}

export interface DatasetItem {
  id: string;
  name: string;
  imageCount: number;
  annotatedCount: number;
  classes: string[];
  splitRatio: { train: number; val: number; test: number };
  status: "Ready" | "Partitioned" | "Training";
  createdAt: string;
}

export interface TrainingJob {
  jobId: string;
  modelName: string;
  framework: string;
  epoch: number;
  maxEpochs: number;
  loss: number;
  mAP: number;
  status: "Idle" | "Training" | "Completed" | "Failed";
}

export interface GPUTelemetry {
  device: string;
  cudaAvailable: boolean;
  cudaVersion: string;
  gpuName: string;
  vramTotalMB: number;
  vramUsedMB: number;
  temperatureC: number;
  utilizationPercent: number;
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface PreprocessingConfig {
  resizeWidth: number;
  resizeHeight: number;
  noiseRemoval: boolean;
  histogramEqualization: boolean;
  clahe: boolean;
  contrastEnhancement: number; // 0 to 100
  imageSharpening: boolean;
  perspectiveCorrection: boolean;
  colorNormalization: boolean;
  confidenceThreshold: number;
}

export type ModelType = "detection" | "segmentation" | "classification";

export type FrameworkType = string;

export interface ModelConfig {
  id: string;
  name: string;
  type: ModelType;
  framework: FrameworkType;
  version: string;
  inputResolution: string;
  loaded: boolean;
  filename?: string;
  loadedAt?: string;
}

export interface ModelsState {
  detection: ModelConfig;
  segmentation: ModelConfig;
  classification: ModelConfig;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  category: "UPLOAD" | "VALIDATION" | "PREPROCESS" | "MODEL" | "INFERENCE" | "ERROR" | "EXPORT";
  message: string;
  level: "INFO" | "WARN" | "SUCCESS" | "ERROR";
}

export type PipelineStep =
  | "upload"
  | "validation"
  | "preprocessing"
  | "detection"
  | "segmentation"
  | "classification"
  | "severity"
  | "visualization"
  | "report";

export type SeverityLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type MaintenanceAction =
  | "MONITOR"
  | "REVIEW"
  | "MAINTENANCE_REQUIRED"
  | "PRIORITY_MAINTENANCE";

export type TicketStatus = "OPEN" | "IN_PROGRESS" | "RESOLVED" | "CLOSED";

export interface DetectionItem {
  detection_id: number;
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: number[] | { xmin: number; ymin: number; xmax: number; ymax: number };
  severity_score?: number;
  severity_level?: SeverityLevel;
  recommended_action?: MaintenanceAction;
  ticket_id?: string | null;
  crop_path?: string | null;
}

export interface MaintenanceTicket {
  ticket_id: string;
  inspection_id: string;
  detection_id: number;
  class_name: string;
  confidence: number;
  severity_score: number;
  severity_level: SeverityLevel;
  priority: "HIGH" | "CRITICAL";
  recommended_action: MaintenanceAction;
  status: TicketStatus;
  reason: string;
  created_at: string;
}

export interface SeveritySummary {
  total_detections: number;
  low: number;
  medium: number;
  high: number;
  critical: number;
}

export interface MaintenanceSummary {
  monitor_count: number;
  review_count: number;
  maintenance_required_count: number;
  priority_maintenance_count: number;
  total_tickets: number;
}

export interface InferenceStatistics {
  total_detections: number;
  class_distribution: Record<string, number>;
  average_confidence: number;
  highest_confidence: number;
  lowest_confidence: number;
  inference_time_ms: number;
  model_filename: string;
  device: string;
  input_resolution: string;
}

export interface InferenceResult {
  inspection_id?: string;
  image_id: string;
  model: string;
  device: string;
  input_resolution: string;
  original_image: string;
  annotated_image: string;
  csv: string;
  pdf: string;
  detections_json: string;
  detections: DetectionItem[];
  normalized_detections?: DetectionItem[];
  severity_summary?: SeveritySummary;
  maintenance_summary?: MaintenanceSummary;
  tickets?: MaintenanceTicket[];
  count: number;
  time_ms: number;
  processing_time_ms: number;
  statistics: InferenceStatistics;
  masks: any[];
  classifications: Record<string, any>;
  severity_scores: Record<string, any>;
  status: string;
}

export interface InspectionReportData {
  inspectionId: string;
  timestamp: string;
  imageFilename: string;
  imageResolution: string;
  modelsUsed: {
    detection: string;
    segmentation: string;
    classification: string;
  };
  preprocessingApplied: string[];
  status: string;
  summary: string;
}
