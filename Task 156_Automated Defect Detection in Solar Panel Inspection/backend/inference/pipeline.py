import os
import time
import csv
import json
import cv2
import numpy as np
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from backend.inference.detector import YOLOv11Detector
from backend.inference.segmenter import SAM2Segmenter
from backend.inference.classifier import EfficientNetClassifier
from backend.inference.severity import SeverityAnalyzer
from backend.preprocessing.clahe import CLAHEPreprocessor
from backend.preprocessing.normalize import Normalizer
from backend.preprocessing.resize import Resizer
from backend.utils.logger import setup_logger
from backend.utils.pdf_generator import generate_pdf_report

# Phase 2 Analytics & Persistence Imports
from backend.analytics.severity import SeverityEngine, get_severity_summary
from backend.analytics.maintenance import MaintenanceEngine
from backend.analytics.crops import DefectCropExtractor
from backend.database.repository import InspectionRepository

logger = setup_logger("pipeline")

# Resolve the project-level outputs directory
OUTPUTS_BASE = Path(__file__).resolve().parent.parent / "outputs"


class InspectionPipeline:
    def __init__(self, db_path: str = None):
        self.detector = YOLOv11Detector()
        self.segmenter = SAM2Segmenter()
        self.classifier = EfficientNetClassifier()
        self.severity_analyzer = SeverityAnalyzer()
        
        # Phase 2 Components
        self.severity_engine = SeverityEngine()
        self.maintenance_engine = MaintenanceEngine()
        self.crop_extractor = DefectCropExtractor()
        self.repo = InspectionRepository(db_path=db_path)
        
        logger.info("Complete Inspection Pipeline with Phase 2 Analytics initialized successfully.")

    def run(self, image: np.ndarray, image_id: str = "img-default",
            preprocessing_config: Dict[str, Any] = None,
            original_image_bytes: bytes = None) -> Dict[str, Any]:
        start_time = time.time()

        if preprocessing_config is None:
            preprocessing_config = {}

        logger.info(f"Starting end-to-end inference pipeline for image_id: {image_id}")
        logger.info(f"Preprocessing config: {preprocessing_config}")

        # --- Create timestamped output directory ---
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        safe_image_id = "".join(c if c.isalnum() or c in "._-" else "_" for c in image_id)
        run_dir_name = f"{timestamp_str}_{safe_image_id}"
        run_dir = OUTPUTS_BASE / run_dir_name
        run_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {run_dir}")

        # --- Save original image ---
        original_path = run_dir / "original.jpg"
        if original_image_bytes:
            original_path.write_bytes(original_image_bytes)
            original_img = cv2.imdecode(np.frombuffer(original_image_bytes, np.uint8), cv2.IMREAD_COLOR)
        else:
            original_img = image.copy()
            cv2.imwrite(str(original_path), original_img)
        logger.info(f"Original image saved to {original_path}")

        # --- Preprocessing ---
        processed_image = image.copy()

        # 1. Resize (always enabled)
        resize_width = preprocessing_config.get("resizeWidth", 640)
        resize_height = preprocessing_config.get("resizeHeight", 640)
        resizer = Resizer(target_width=resize_width, target_height=resize_height)
        processed_image = resizer.apply(processed_image)

        # 2. CLAHE (configurable)
        if preprocessing_config.get("clahe", False):
            clip_limit = preprocessing_config.get("contrastEnhancement", 20) / 10.0
            if clip_limit <= 0:
                clip_limit = 2.0
            clahe_preprocessor = CLAHEPreprocessor(clip_limit=clip_limit)
            processed_image = clahe_preprocessor.apply(processed_image)

        # Keep a copy of the preprocessed image sent to YOLO (WITHOUT NORMALIZATION!)
        yolo_input_img = processed_image.copy()
        yolo_input_path = run_dir / "image_sent_to_yolo.jpg"
        cv2.imwrite(str(yolo_input_path), yolo_input_img)

        # --- Execute raw detection stage (FROZEN BACKBONE & YOLO INFERENCE) ---
        conf_threshold = preprocessing_config.get("confidenceThreshold", None)
        # Pass non-normalized BGR uint8 image to detect!
        detections = self.detector.detect(yolo_input_img, conf_threshold=conf_threshold)

        inference_time_ms = self.detector.last_inference_time_ms
        model_filename = self.detector.get_model_filename()
        model_info = self.detector.get_model_info()

        # Save results_plot.jpg
        last_res = self.detector.last_results[0]
        results_plot_img = last_res.plot()
        results_plot_path = run_dir / "results_plot.jpg"
        cv2.imwrite(str(results_plot_path), results_plot_img)

        # --- Generate annotated image (annotated.jpg) ---
        annotated_filename = "annotated.jpg"
        annotated_path = str(run_dir / annotated_filename)
        self.detector.generate_annotated_image(annotated_path)

        # Load annotated_saved back from disk to verify
        annotated_saved_img = cv2.imread(annotated_path)

        # =========================================================================
        # PHASE 2: DEFECT NORMALIZATION, SEVERITY, MAINTENANCE & EVIDENCE CROPS
        # =========================================================================
        
        # 1. Defect Severity Scoring
        detections_with_severity = self.severity_engine.process_detections(detections)
        severity_summary = get_severity_summary(detections_with_severity)

        # 2. Maintenance Decision Engine
        maint_result = self.maintenance_engine.process_detections(run_dir_name, detections_with_severity)
        normalized_detections = maint_result["detections"]
        tickets = maint_result["tickets"]
        maintenance_summary = maint_result["summary"]

        # 3. Defect Evidence Crops (extracted from original_img, NOT annotated)
        normalized_detections = self.crop_extractor.extract_and_save_crops(
            original_image=original_img,
            detections=normalized_detections,
            run_dir=run_dir
        )

        # --- Relative file paths ---
        original_rel = f"{run_dir_name}/{original_path.name}"
        annotated_rel = f"{run_dir_name}/{annotated_filename}"
        csv_filename = "detections.csv"
        csv_rel = f"{run_dir_name}/{csv_filename}"
        pdf_filename = "report.pdf"
        pdf_rel = f"{run_dir_name}/{pdf_filename}"
        json_rel = f"{run_dir_name}/detections.json"
        csv_path = str(run_dir / csv_filename)
        pdf_path = str(run_dir / pdf_filename)
        json_path = str(run_dir / "detections.json")

        # 4. Inspection History Database Persistence
        inspection_record = {
            "inspection_id": run_dir_name,
            "image_id": image_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model": model_filename,
            "device": model_info["device"],
            "input_resolution": f"{resize_width}x{resize_height}",
            "inference_time_ms": inference_time_ms,
            "count": len(detections),
            "annotated_image": annotated_rel,
            "original_image": original_rel,
            "pdf": pdf_rel,
            "csv": csv_rel,
            "detections_json": json_rel
        }
        self.repo.save_inspection(inspection_record, normalized_detections, tickets)

        # --- Generate CSV with Extended Fields ---
        self._write_csv(normalized_detections, csv_path)

        # --- Compute statistics ---
        stats = self._compute_stats(detections, inference_time_ms, model_info, image)

        # --- Save Extended JSON ---
        json_payload = {
            "inspection_id": run_dir_name,
            "image_id": image_id,
            "model": model_filename,
            "device": model_info["device"],
            "input_resolution": f"{resize_width}x{resize_height}",
            "inference_time_ms": inference_time_ms,
            "count": len(detections),
            "detections": detections,  # Frozen raw YOLO detections
            "normalized_detections": normalized_detections,
            "severity_summary": severity_summary,
            "maintenance_summary": maintenance_summary,
            "tickets": tickets,
            "statistics": stats,
            "output_paths": {
                "original_image": original_rel,
                "annotated_image": annotated_rel,
                "csv": csv_rel,
                "pdf": pdf_rel,
                "detections_json": json_rel
            }
        }
        with open(json_path, "w") as f:
            json.dump(json_payload, f, indent=2)
        logger.info(f"Detections JSON saved to {json_path}")

        # --- Generate Certified PDF Engineering Report ---
        generate_pdf_report(
            pdf_path=pdf_path,
            original_img_path=str(original_path),
            annotated_img_path=annotated_path,
            detections=normalized_detections,
            stats=stats,
            severity_summary=severity_summary,
            maintenance_summary=maintenance_summary,
            tickets=tickets,
            run_dir=run_dir
        )

        processing_time = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Pipeline executed successfully in {processing_time} ms.")

        return {
            "inspection_id": run_dir_name,
            "image_id": image_id,
            "model": model_filename,
            "device": model_info["device"],
            "input_resolution": f"{resize_width}x{resize_height}",
            "original_image": original_rel,
            "annotated_image": annotated_rel,
            "csv": csv_rel,
            "pdf": pdf_rel,
            "detections_json": json_rel,
            "detections": detections,
            "normalized_detections": normalized_detections,
            "severity_summary": severity_summary,
            "maintenance_summary": maintenance_summary,
            "tickets": tickets,
            "count": len(detections),
            "time_ms": inference_time_ms,
            "processing_time_ms": processing_time,
            "statistics": stats,
            "masks": [],
            "classifications": {},
            "severity_scores": {},
            "status": "success"
        }

    def _write_csv(self, detections: List[Dict[str, Any]], csv_path: str):
        """Write normalized detections to a CSV file with extended Phase 2 fields."""
        fieldnames = [
            "DetectionID", "Class", "Confidence", "Xmin", "Ymin", "Xmax", "Ymax",
            "SeverityScore", "SeverityLevel", "MaintenanceAction", "TicketID"
        ]
        try:
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for det in detections:
                    bbox = det.get("bbox", [0, 0, 0, 0])
                    if isinstance(bbox, dict):
                        xmin = bbox.get("xmin", 0)
                        ymin = bbox.get("ymin", 0)
                        xmax = bbox.get("xmax", 0)
                        ymax = bbox.get("ymax", 0)
                    else:
                        xmin = bbox[0] if len(bbox) > 0 else 0
                        ymin = bbox[1] if len(bbox) > 1 else 0
                        xmax = bbox[2] if len(bbox) > 2 else 0
                        ymax = bbox[3] if len(bbox) > 3 else 0

                    writer.writerow({
                        "DetectionID": det.get("detection_id", 0),
                        "Class": det.get("class_name", "Unknown"),
                        "Confidence": det.get("confidence", 0),
                        "Xmin": xmin,
                        "Ymin": ymin,
                        "Xmax": xmax,
                        "Ymax": ymax,
                        "SeverityScore": det.get("severity_score", 0.0),
                        "SeverityLevel": det.get("severity_level", "LOW"),
                        "MaintenanceAction": det.get("recommended_action", "MONITOR"),
                        "TicketID": det.get("ticket_id") or "N/A"
                    })
            logger.info(f"CSV saved to {csv_path} with {len(detections)} rows.")
        except Exception as e:
            logger.error(f"Failed to write CSV: {str(e)}")

    def _compute_stats(self, detections: List[Dict[str, Any]], inference_time_ms: float,
                       model_info: Dict[str, Any], image: np.ndarray) -> Dict[str, Any]:
        """Compute inspection statistics from raw detections."""
        total = len(detections)

        if total == 0:
            return {
                "total_detections": 0,
                "class_distribution": {},
                "average_confidence": 0,
                "highest_confidence": 0,
                "lowest_confidence": 0,
                "inference_time_ms": inference_time_ms,
                "model_filename": model_info.get("filename", "None"),
                "device": model_info.get("device", "cpu"),
                "input_resolution": f"{image.shape[1]}x{image.shape[0]}",
            }

        confidences = [d["confidence"] for d in detections]
        class_dist: Dict[str, int] = {}
        for d in detections:
            cls = d.get("class_name", "Unknown")
            class_dist[cls] = class_dist.get(cls, 0) + 1

        return {
            "total_detections": total,
            "class_distribution": class_dist,
            "average_confidence": round(sum(confidences) / total, 4),
            "highest_confidence": round(max(confidences), 4),
            "lowest_confidence": round(min(confidences), 4),
            "inference_time_ms": inference_time_ms,
            "model_filename": model_info.get("filename", "None"),
            "device": model_info.get("device", "cpu"),
            "input_resolution": f"{image.shape[1]}x{image.shape[0]}",
        }
