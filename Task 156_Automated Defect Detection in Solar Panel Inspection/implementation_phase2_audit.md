# SolarLens Phase 2 Audit & Architectural Baseline

## 1. Executive Summary
This document completes **Phase 0 (Audit Before Coding)** for Phase 2 of SolarLens. It establishes the exact runtime state, model specifications, protected core pipeline components, and proposed additive architectural changes for severity scoring, maintenance decision automation, defect evidence cropping, SQLite inspection history, extended reporting, and updated UI.

---

## 2. Current Architecture & Inference Flow

### System Components:
1. **Frontend**: React 18 + Vite SPA with `AppContext.tsx` managing state, `InspectionPipelineView.tsx` driving inference, `ReportsView.tsx` rendering output, and `ModelManagementView.tsx` tracking model weights status.
2. **Gateway Server**: Express.js (`server.ts` on port 3000) bridging frontend requests to FastAPI backend and proxying static output artifacts (`/outputs/...`).
3. **Backend Service**: Python FastAPI (`backend/main.py` on port 8000).
4. **Inference Pipeline**: `backend/inference/pipeline.py` executing `YOLOv11Detector` (`backend/inference/detector.py`).
5. **Model Weights**: `backend/models/best.pt` (PyTorch / Ultralytics YOLOv11 detector).

### Current Execution Flow:
```
User Image Upload (Frontend)
    ↓
AppContext.runPipelineInference()
    ↓
POST /api/inference/run (Express Server :3000)
    ↓
POST /api/infer (FastAPI Service :8000)
    ↓
InspectionPipeline.run() (backend/inference/pipeline.py)
    ↓
YOLOv11Detector.detect() (backend/inference/detector.py)
    ↓
backend/models/best.pt (Ultralytics YOLO inference)
    ↓
YOLO Detections List & results[0].plot() Annotated Image
    ↓
Output Directory Creation (backend/outputs/<timestamp>_<image_id>/)
    - original.jpg
    - annotated.jpg
    - detections.csv
    - detections.json
    - report.pdf
    ↓
JSON Response to Express → React State Update (InferenceResult)
    ↓
Frontend Rendering (InspectionPipelineView & ReportsView)
```

---

## 3. Frozen Backbone & Model Inspection Details

In accordance with Primary Non-Negotiable Constraint #1, `backend/models/best.pt` was inspected and verified via Python runtime introspection.

### Verified Model Metadata:
- **Model Path**: `backend/models/best.pt`
- **Model Task**: `detect` (Ultralytics YOLO object detection)
- **Total Classes**: 8
- **Class Map**:
  - `0`: `MultiByPassed`
  - `1`: `MultiDiode`
  - `2`: `MultiHotSpot`
  - `3`: `SingleByPassed`
  - `4`: `SingleDiode`
  - `5`: `SingleHotSpot`
  - `6`: `StringOpenCircuit`
  - `7`: `StringReversedPolarity`
- **Default Confidence Threshold**: `0.10` (passed via `preprocessing_config` / default parameter)
- **Expected Input Shape**: `(640, 640, 3)` BGR Image Array

> **Note on Supported Defects**: The model detects specific solar PV anomalies listed above (e.g. `MultiHotSpot`, `SingleDiode`, `StringOpenCircuit`). It does NOT detect unlisted categories such as micro-cracks or surface soiling. No fake or unlisted defect classes will be introduced.

---

## 4. Protected Files & Functions

The following files and functions constitute the core black-box detection engine and MUST REMAIN FROZEN:

| Protected Resource | File / Location | Protection Policy |
| :--- | :--- | :--- |
| **Model Weights** | `backend/models/best.pt` | FROZEN. No retraining, replacement, or modification. |
| **YOLO Model Instance** | `backend/inference/detector.py` | FROZEN. Model loading, `model.predict()` parameters, and weight initialization remain unchanged. |
| **Plot / Annotation Logic** | `detector.generate_annotated_image` | FROZEN. Uses Ultralytics `results[0].plot()`. |
| **Preprocessing Stream** | `backend/preprocessing/*` | FROZEN. Original image bytes passed to YOLO intact without normalization mutations. |
| **Gateway Routing** | `server.ts` & `AppContext.tsx` | FROZEN. Base `/api/inference/run` endpoint contract and binary image transmission preserved. |

---

## 5. Current vs. Extended Output Schema

### Current Output JSON Schema:
```json
{
  "image_id": "test_panel.jpg",
  "model": "best.pt",
  "device": "cpu",
  "input_resolution": "640x640",
  "original_image": "<dir>/original.jpg",
  "annotated_image": "<dir>/annotated.jpg",
  "csv": "<dir>/detections.csv",
  "pdf": "<dir>/report.pdf",
  "detections_json": "<dir>/detections.json",
  "detections": [
    {
      "detection_id": 1,
      "class_id": 2,
      "class_name": "MultiHotSpot",
      "confidence": 0.812,
      "bbox": [120.0, 80.0, 350.0, 290.0]
    }
  ],
  "count": 1,
  "time_ms": 115.59,
  "processing_time_ms": 377.62,
  "statistics": { ... },
  "status": "success"
}
```

### Proposed Additive Schema (Phase 2):
```json
{
  ...existing_fields...,
  "panel_id": "PANEL-001",
  "normalized_detections": [
    {
      "detection_id": 1,
      "class_id": 2,
      "class_name": "MultiHotSpot",
      "confidence": 0.812,
      "bbox": { "xmin": 120.0, "ymin": 80.0, "xmax": 350.0, "ymax": 290.0 },
      "severity_score": 81.2,
      "severity_level": "HIGH",
      "recommended_action": "MAINTENANCE_REQUIRED",
      "ticket_id": "SL-000001",
      "crop_image": "<dir>/defects/detection_001.jpg"
    }
  ],
  "severity_summary": {
    "total_detections": 1,
    "low": 0,
    "medium": 0,
    "high": 1,
    "critical": 0
  },
  "maintenance_summary": {
    "maintenance_required": 1,
    "priority_maintenance": 0,
    "open_tickets": 1
  },
  "tickets": [
    {
      "ticket_id": "SL-000001",
      "inspection_id": "<run_dir_name>",
      "detection_id": 1,
      "priority": "HIGH",
      "status": "OPEN",
      "reason": "High-severity MultiHotSpot detection",
      "severity_score": 81.2,
      "confidence": 0.812,
      "created_at": "2026-08-09T23:28:03Z"
    }
  ]
}
```

---

## 6. Proposed Additive Architecture

To extend SolarLens without modifying the core YOLO detector, the new components will sit downstream of YOLO detection:

```
[ YOLO Detections ]
         ↓
Phase 1: Defect Normalization (backend/analytics/normalization.py)
         ↓
Phase 2: Severity Engine (backend/analytics/severity.py)
         ↓
Phase 3: Maintenance Decision Engine (backend/analytics/maintenance.py)
         ↓
Phase 4: Defect Evidence Cropper (backend/analytics/crops.py)
         ↓
Phase 5: Inspection History DB (backend/database/sqlite_db.py)
         ↓
Phase 6: Extended PDF / CSV / JSON Generators
         ↓
Phase 7: Frontend Visualization & Ticket Management UI
```

### Module Blueprint:
1. **Defect Normalization (`backend/analytics/normalization.py`)**:
   - Converts raw YOLO detections into structured objects with `panel_id` (inferred e.g. `PANEL-001` or `IMAGE-<inspection_id>`).
2. **Severity Engine (`backend/analytics/severity.py`)**:
   - Computes `severity_score = confidence * 100`.
   - Categorizes into `LOW` (0-39), `MEDIUM` (40-69), `HIGH` (70-84), `CRITICAL` (85-100).
   - Configurable constants; decision-support heuristic.
3. **Maintenance Decision Engine (`backend/analytics/maintenance.py`)**:
   - Maps severity to actions: `MONITOR`, `REVIEW`, `MAINTENANCE_REQUIRED`, `PRIORITY_MAINTENANCE`.
   - Automatically generates deterministic `ticket_id` (e.g. `SL-000001`) for `HIGH` and `CRITICAL` defects.
4. **Defect Evidence Cropper (`backend/analytics/crops.py`)**:
   - Crops bounding boxes from original image array with clamped coordinates.
   - Saves crops in `<run_dir>/defects/detection_<id>.jpg`.
5. **Database Layer (`backend/database/sqlite_db.py`)**:
   - SQLite DB (`backend/database/solarlens.db`).
   - Tables: `inspections`, `detections`, `tickets`.
   - Supports ticket status updates (`OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`).
6. **API & Gateway Extensions**:
   - FastAPI `/api/tickets` GET & PATCH routes for ticket tracking.
   - Express `/api/tickets` proxy endpoints.
7. **Frontend Updates**:
   - Extended `InspectionPipelineView` & `ReportsView` with Severity badge, Maintenance Action, Ticket badges, Crop thumbnails, and Severity/Maintenance summaries.
   - New Maintenance Ticket section/card allowing inline status updates.

---

## 7. Risk Analysis & Mitigation

| Risk Area | Mitigation Strategy |
| :--- | :--- |
| **Raw Detection Regression** | Automated regression script will verify raw YOLO output parameters (class IDs, confidence, bboxes, count) match pre-Phase 2 output exactly. |
| **PDF Generation Breakage** | ReportLab flowable list extended additively; backwards compatibility maintained with existing stats layout. |
| **Image Cropping Out-of-Bounds** | Bounding box coordinates clamped strictly: `0 <= xmin < xmax <= width`, `0 <= ymin < ymax <= height`. |
| **DB Locking / Persistence Issues** | Use lightweight SQLite connection context helper with auto-commit and fallback initialization. |
| **Proxy / Download File Not Found** | Defects folder static mounting added to FastAPI and Express proxy handles nested output paths cleanly. |

---

## 8. Audit Verification Status
- [x] Repository fully inspected.
- [x] `backend/models/best.pt` inspected via Python script.
- [x] Model class names verified: 8 genuine solar PV anomaly classes documented.
- [x] Real image (`test_panel.jpg`) traced through pipeline.
- [x] Output paths, server proxy, and disk file creation verified.
- [x] Zero changes made to `best.pt` or YOLO detector code.
