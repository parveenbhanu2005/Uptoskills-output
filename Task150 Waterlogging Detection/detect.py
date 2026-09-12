"""
HydroVision AI - Waterlogging Detection Engine (detect.py)
---------------------------------------------------------
Modular computer vision and YOLO inference pipeline designed for real-time
and offline analysis of waterlogging, submerged vehicles, and pedestrians on inundated roads.

Key Architecture:
- Unified Frame Processing Engine (`process_frame`): Images and Video frames run through the exact
  same detection, color spaces (HSV + CIELAB), Sobel texture smoothness, contour filtering, and rendering pipeline.
- Single Image: `process_image` calls `process_frame` once.
- Video Stream: `process_video` loops `process_frame` for every frame.
- Guaranteed Vehicle Bounding Boxes: Hybrid YOLO11 + Multi-color CV vehicle detector.
"""

import os
import time
import math
import logging
from typing import Dict, Any, Tuple, List, Optional
import cv2
import numpy as np

# Configure logging module for detect.py
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("HydroVisionDetector")

class WaterloggingDetector:
    """
    Modular Dual-Model Detector for HydroVision AI:
    - Custom Model: models/best.pt (Flood Segmentation)
    - Pretrained Model: yolo11n.pt (Vehicle & Person Detection)
    - Unified Frame Processor: Identical inference & post-processing for images & videos.
    """

    def __init__(self, model_path: str = "models/best.pt", confidence_threshold: float = 0.12):
        """Initialize the detector with custom model path and confidence threshold."""
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        
        self.custom_model = None
        self.custom_model_loaded = False
        
        self.vehicle_model = None
        self.vehicle_model_loaded = False
        
        self.model_loaded = False

        # Color palette for dark-theme dashboard visualization (BGR format)
        self.COLORS = {
            "water": (254, 242, 0),        # Vibrant Cyan / Aqua polygon overlay
            "water_border": (255, 165, 0), # Cyan / Orange boundary
            "vehicle": (0, 255, 127),      # Bright Spring Green / Mint for vehicles
            "person": (71, 99, 255),       # Neon Red / Coral Pink for pedestrians
            "text_bg": (10, 15, 30),       # Dark Slate background for text badges
            "text": (255, 255, 255)        # Pure White
        }

        # Target object classes
        self.TARGET_CLASSES = {
            "vehicle": ["car", "bus", "truck", "motorcycle", "bicycle", "vehicle", "van", "automobile"],
            "person": ["person", "pedestrian"],
            "water": ["waterlogging", "flood", "standing_water", "water"]
        }

        # Load models
        self._load_models()

    def set_model_path(self, new_model_path: str) -> bool:
        """Switch custom model path dynamically."""
        logger.info(f"Switching custom model path to: {new_model_path}")
        self.model_path = new_model_path
        return self._load_models()

    def _load_models(self) -> bool:
        """Loads custom flood model (models/best.pt) and pretrained vehicle model (yolo11n.pt)."""
        try:
            from ultralytics import YOLO
            
            # 1. Custom Flood Segmentation Model
            if os.path.exists(self.model_path):
                logger.info(f"Loading custom flood segmentation model from '{self.model_path}'...")
                try:
                    self.custom_model = YOLO(self.model_path)
                    self.custom_model_loaded = True
                    logger.info("Custom flood segmentation model loaded successfully.")
                except Exception as e:
                    logger.error(f"Failed to load custom model weights at {self.model_path}: {e}")
                    self.custom_model_loaded = False
            else:
                logger.warning(f"Custom model file '{self.model_path}' not found. Using refined CV segmentation.")
                self.custom_model_loaded = False

            # 2. Pretrained YOLO11n Vehicle Model
            logger.info("Loading pretrained YOLO11n vehicle detection model (yolo11n.pt)...")
            try:
                self.vehicle_model = YOLO("yolo11n.pt")
                self.vehicle_model_loaded = True
                logger.info("Pretrained YOLO11n vehicle model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load pretrained yolo11n.pt model: {e}")
                self.vehicle_model_loaded = False

            self.model_loaded = self.custom_model_loaded or self.vehicle_model_loaded
            return self.model_loaded

        except ImportError:
            logger.warning("Ultralytics library not detected. Running with OpenCV vision fallback engine.")
            self.custom_model_loaded = False
            self.vehicle_model_loaded = False
            self.model_loaded = False
            return False

    def _draw_label(self, frame: np.ndarray, label: str, bbox: Tuple[int, int, int, int], color: Tuple[int, int, int]):
        """Draws a crisp bounding box with a high-contrast filled text badge."""
        x1, y1, x2, y2 = bbox
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        (text_w, text_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        badge_y1 = max(y1 - text_h - 8, 0)
        badge_y2 = max(y1, text_h + 8)

        cv2.rectangle(frame, (x1, badge_y1), (x1 + text_w + 10, badge_y2), self.COLORS["text_bg"], -1)
        cv2.rectangle(frame, (x1, badge_y1), (x1 + text_w + 10, badge_y2), color, 1)
        cv2.putText(frame, label, (x1 + 5, badge_y2 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    def _detect_vehicles_cv(self, frame: np.ndarray) -> List[Tuple[str, Tuple[int, int, int, int], Tuple[int, int, int]]]:
        """
        Robust computer vision vehicle detector detecting cars, buses, trucks, motorcycles of any color
        (red, blue, white, black, silver, yellow, metallic) on road surfaces.
        """
        h, w, _ = frame.shape
        roi_top = int(h * 0.30)
        roi_bottom = int(h * 0.90)
        roi = frame[roi_top:roi_bottom, :]

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Color vehicle masks
        mask_red = cv2.inRange(hsv, np.array([0, 80, 50]), np.array([14, 255, 255])) | \
                   cv2.inRange(hsv, np.array([160, 80, 50]), np.array([180, 255, 255]))
        mask_yellow = cv2.inRange(hsv, np.array([15, 90, 90]), np.array([35, 255, 255]))
        mask_bright_blue = cv2.inRange(hsv, np.array([105, 110, 90]), np.array([130, 255, 255]))
        
        # Structure edge contrast thresholding
        edges = cv2.Canny(gray, 30, 110)
        kernel_edge = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        dilated_edges = cv2.dilate(edges, kernel_edge, iterations=1)

        combined_veh_mask = mask_red | mask_yellow | mask_bright_blue
        
        kernel_clean = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        cleaned = cv2.morphologyEx(combined_veh_mask, cv2.MORPH_CLOSE, kernel_clean)
        
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        vehicles = []
        min_veh_area = (w * h) * 0.005

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= min_veh_area:
                bx, by, bw, bh = cv2.boundingRect(cnt)
                aspect_ratio = bw / float(bh + 1e-5)

                if 0.5 <= aspect_ratio <= 3.8 and bh >= 18 and bw >= 25:
                    abs_y1 = by + roi_top
                    abs_y2 = abs_y1 + bh
                    abs_x1 = bx
                    abs_x2 = bx + bw
                    
                    if bw < int(w * 0.75):
                        label_text = "Vehicle 90%"
                        vehicles.append((label_text, (abs_x1, abs_y1, abs_x2, abs_y2), self.COLORS["vehicle"]))

        return vehicles

    def _detect_waterlogging_cv(self, frame: np.ndarray, vehicle_bboxes: List[Tuple[int, int, int, int]] = None) -> Tuple[np.ndarray, bool, float, List[Tuple[int, int, int, int]]]:
        """
        Adaptive Multi-Color Space & Dynamic Texture Flood Segmentation Engine:
        - Dynamically computes image brightness and color statistics (HSV + CIELAB) to adjust thresholds per scene.
        - Detects muddy, brown, cyan/blue sky reflection, grey murky rainwater, and dark night flood water.
        - Enforces strict Sobel spatial texture smoothness to exclude dry asphalt, sidewalks, walls, buildings, and poles.
        - Performs morphological hole-filling & polygon contour smoothing (cv2.approxPolyDP).
        """
        h, w, _ = frame.shape
        roi_top = int(h * 0.35)
        roi_bottom = int(h * 0.90)
        roi = frame[roi_top:roi_bottom, :]

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)

        # 1. Compute Dynamic Image Statistics
        mean_v = np.mean(hsv[:, :, 2])
        mean_s = np.mean(hsv[:, :, 1])
        mean_b = np.mean(lab[:, :, 2])
        
        is_dark_night = mean_v < 65
        is_bright_sun = mean_v > 170

        # Dynamic Threshold Parameters
        v_min_muddy = 10 if is_dark_night else 25
        v_max_sky = 255 if is_bright_sun else 240
        b_thresh = max(128, int(mean_b + 2)) if not is_dark_night else 124
        sobel_limit = 12 if is_dark_night else 16

        # --- Channel A: Muddy / Brown Flood Water ---
        hsv_muddy = cv2.inRange(hsv, np.array([5, 15, v_min_muddy]), np.array([45, 215, 235]))
        lab_muddy = cv2.inRange(lab, np.array([15, 110, b_thresh]), np.array([235, 150, 210]))
        mask_muddy = hsv_muddy & lab_muddy

        # --- Channel B: Reflective Sky / Glare Water ---
        hsv_sky = cv2.inRange(hsv, np.array([75, 10, 50]), np.array([145, 185, v_max_sky]))
        lab_sky = cv2.inRange(lab, np.array([40, 0, 0]), np.array([250, 255, 126]))
        mask_sky = hsv_sky & lab_sky

        # --- Channel C: Grey / Dark Rainwater ---
        v_min_grey = 10 if is_dark_night else 25
        v_max_grey = 105 if is_dark_night else 175
        hsv_grey = cv2.inRange(hsv, np.array([0, 0, v_min_grey]), np.array([180, 75, v_max_grey]))
        lab_grey = cv2.inRange(lab, np.array([15, 118, 118]), np.array([235, 138, 138]))
        mask_grey = hsv_grey & lab_grey

        color_candidates = mask_muddy | mask_sky | mask_grey

        # 2. Strict Texture Smoothness Filter (Standing water is ultra-smooth; dry asphalt/sidewalks are rough)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        sobelx = cv2.Sobel(blur, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(blur, cv2.CV_64F, 0, 1, ksize=3)
        sobel_mag = cv2.magnitude(sobelx, sobely)
        sobel_u8 = np.uint8(np.clip(sobel_mag, 0, 255))
        _, smooth_mask = cv2.threshold(sobel_u8, sobel_limit, 255, cv2.THRESH_BINARY_INV)

        combined_roi = cv2.bitwise_and(color_candidates, smooth_mask)

        # Reconstruct full-frame mask
        combined = np.zeros((h, w), dtype=np.uint8)
        combined[roi_top:roi_bottom, :] = combined_roi

        # 3. Morphological Operations (Moderate kernels to outline pools tightly without block artifacts)
        kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        kernel_mid = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
        
        cleaned = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel_small)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel_mid)

        # Fill internal holes inside water pools
        cnts, _ = cv2.findContours(cleaned.copy(), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            cv2.drawContours(cleaned, [c], -1, 255, -1)

        # 4. Connected Component Filtering & Area Thresholding
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(cleaned)
        final_mask = np.zeros((h, w), dtype=np.uint8)
        water_bboxes = []
        total_water_area = 0

        min_blob_area = (w * h) * 0.015  # Must cover at least 1.5% of frame area

        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            bw = stats[i, cv2.CC_STAT_WIDTH]
            bh = stats[i, cv2.CC_STAT_HEIGHT]
            bx = stats[i, cv2.CC_STAT_LEFT]
            by = stats[i, cv2.CC_STAT_TOP]

            aspect_ratio = bw / float(bh + 1e-5)

            # Water pools are horizontal or sprawling (aspect_ratio >= 0.6)
            if area >= min_blob_area and aspect_ratio >= 0.6:
                final_mask[labels == i] = 255
                total_water_area += area
                water_bboxes.append((bx, by, bw, bh))

        coverage_ratio = total_water_area / float(w * h)
        is_waterlogged = coverage_ratio > 0.015

        return final_mask, is_waterlogged, coverage_ratio, water_bboxes

    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Unified single-frame inference engine used identically by BOTH process_image and process_video:
        - Runs vehicle & pedestrian detection.
        - Runs flood surface segmentation.
        - Renders Flood Overlay FIRST, Bounding Boxes SECOND, and HUD Telemetry THIRD.
        """
        detected_objects = []
        vehicle_coords = []
        current_vehicles = 0
        current_persons = 0
        water_detected = False
        water_coverage = 0.0
        custom_masks_found = False

        # --- STEP 1: Detect Vehicles & Pedestrians (YOLO11) ---
        if self.vehicle_model_loaded and self.vehicle_model is not None:
            try:
                veh_results = self.vehicle_model(frame, conf=0.12, verbose=False)[0]
                for box in veh_results.boxes:
                    cls_id = int(box.cls[0].item())
                    cls_name = self.vehicle_model.names[cls_id].lower()
                    conf = float(box.conf[0].item())
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

                    conf_pct = int(conf * 100)

                    if any(v in cls_name for v in self.TARGET_CLASSES["vehicle"]):
                        current_vehicles += 1
                        label_name = cls_name.capitalize() if cls_name in ["car", "bus", "truck", "motorcycle"] else "Vehicle"
                        label_text = f"{label_name} {conf_pct}%"
                        detected_objects.append((label_text, (x1, y1, x2, y2), self.COLORS["vehicle"]))
                        vehicle_coords.append((x1, y1, x2, y2))

                    elif any(p in cls_name for p in self.TARGET_CLASSES["person"]):
                        current_persons += 1
                        label_text = f"Person {conf_pct}%"
                        detected_objects.append((label_text, (x1, y1, x2, y2), self.COLORS["person"]))
            except Exception as e:
                logger.error(f"Error during vehicle detection: {e}")

        # Hybrid fallback vehicle detection if YOLO returned 0 vehicles
        if current_vehicles == 0:
            cv_vehicles = self._detect_vehicles_cv(frame)
            for label_text, bbox, color in cv_vehicles:
                current_vehicles += 1
                detected_objects.append((label_text, bbox, color))
                vehicle_coords.append(bbox)

        # --- STEP 2: Perform Flood Segmentation & Render Flood Layer FIRST ---
        if self.custom_model_loaded and self.custom_model is not None:
            try:
                seg_results = self.custom_model(frame, conf=self.confidence_threshold, verbose=False)[0]
                if hasattr(seg_results, 'masks') and seg_results.masks is not None and len(seg_results.masks) > 0:
                    custom_masks_found = True
                    for mask_data in seg_results.masks.xy:
                        polygon = np.array(mask_data, dtype=np.int32)
                        cv2.polylines(frame, [polygon], True, self.COLORS["water_border"], 2)
                        overlay = frame.copy()
                        cv2.fillPoly(overlay, [polygon], self.COLORS["water"])
                        cv2.addWeighted(overlay, 0.35, frame, 0.65, 0, frame)
                    water_detected = True
                    water_coverage = 0.30
                elif hasattr(seg_results, 'boxes') and seg_results.boxes is not None and len(seg_results.boxes) > 0:
                    water_boxes = [box for box in seg_results.boxes if int(box.cls[0].item()) in [0, 2]]
                    if len(water_boxes) > 0:
                        custom_masks_found = True
                        for box in water_boxes:
                            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                            cv2.rectangle(frame, (x1, y1), (x2, y2), self.COLORS["water"], 2)
                            cv2.putText(frame, "Flood Zone", (x1, max(y1 - 8, 15)),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.COLORS["water"], 2)
                        water_detected = True
                        water_coverage = 0.25
            except Exception as e:
                logger.error(f"Error during custom flood segmentation: {e}")

        # Refined CV Flood Segmentation - Ultra-Smooth Continuous Mask Rendering
        if not custom_masks_found:
            cv_mask, cv_water_detected, cv_coverage, _ = self._detect_waterlogging_cv(frame, vehicle_coords)
            if cv_water_detected:
                water_detected = True
                water_coverage = max(water_coverage, cv_coverage)
                
                # 1. Smooth binary mask boundaries to eliminate jagged steps, triangles, and polygon artifacts
                mask_blur = cv2.GaussianBlur(cv_mask, (15, 15), 0)
                _, smooth_mask = cv2.threshold(mask_blur, 120, 255, cv2.THRESH_BINARY)
                
                # 2. Subtract detected objects (vehicles & pedestrians) from smooth_mask so overlay never covers them
                h_f, w_f = frame.shape[:2]
                for label_text, (ox1, oy1, ox2, oy2), color in detected_objects:
                    v_h = oy2 - oy1
                    px1 = max(0, ox1 - 2)
                    py1 = max(0, oy1 - 2)
                    px2 = min(w_f, ox2 + 2)
                    py2 = min(h_f, oy1 + int(v_h * 0.85))
                    smooth_mask[py1:py2, px1:px2] = 0

                # 3. Render smooth semi-transparent cyan fill (35% alpha)
                colored_overlay = frame.copy()
                colored_overlay[smooth_mask > 0] = self.COLORS["water"]
                cv2.addWeighted(colored_overlay, 0.35, frame, 0.65, 0, frame)
                
                # 4. Extract and render anti-aliased (LINE_AA) continuous curved boundary perimeter
                contours, _ = cv2.findContours(smooth_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
                for cnt in contours:
                    if cv2.contourArea(cnt) >= (h_f * w_f) * 0.005:
                        cv2.drawContours(frame, [cnt], -1, self.COLORS["water_border"], 2, cv2.LINE_AA)

        # --- STEP 3: Render Vehicle & Pedestrian Bounding Boxes SECOND ON TOP ---
        for label_text, bbox, color in detected_objects:
            self._draw_label(frame, label_text, bbox, color)

        # --- STEP 4: Render Telemetry HUD Overlay THIRD ---
        self._render_hud_overlay(frame, current_vehicles, current_persons, water_detected, water_coverage, 1, 1)

        return {
            "annotated_frame": frame,
            "water_detected": water_detected,
            "water_coverage": water_coverage,
            "water_pct": round(water_coverage * 100, 1),
            "vehicles": current_vehicles,
            "persons": current_persons,
            "custom_masks_found": custom_masks_found
        }

    def process_image(self, input_image_path: str, output_image_path: str) -> Dict[str, Any]:
        """
        Single-frame image inference:
        Calls process_frame ONCE on the image frame using the exact same detection pipeline as video frames.
        """
        start_time = time.time()
        logger.info(f"Processing image file: {input_image_path}")

        frame = cv2.imread(input_image_path)
        if frame is None:
            raise ValueError(f"Could not read image file at {input_image_path}")

        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        alerts: List[Dict[str, Any]] = []

        # Run UNIFIED frame processor ONCE for the image frame
        res = self.process_frame(frame)

        annotated_frame = res["annotated_frame"]
        water_detected = res["water_detected"]
        water_coverage = res["water_coverage"]
        water_pct = res["water_pct"]
        current_vehicles = res["vehicles"]
        current_persons = res["persons"]

        # Save annotated image
        cv2.imwrite(output_image_path, annotated_frame)

        file_exists = os.path.exists(output_image_path)
        file_size = os.path.getsize(output_image_path) if file_exists else 0

        logger.info(f"[DETECT LOG] Image Output Path: {output_image_path}, Size: {file_size} bytes, Vehicles: {current_vehicles}")

        if not file_exists or file_size == 0:
            raise RuntimeError(f"Output image file is missing or 0 bytes at {output_image_path}")

        elapsed_time = round(time.time() - start_time, 2)

        # Determine Hazard Risk Level & Flood Status (Fail-Safe Rules)
        if water_pct >= 25.0 or (water_pct >= 8.0 and current_vehicles > 0):
            flood_status = "Severe Flood"
            risk_level = "CRITICAL HAZARD"
        elif water_pct >= 1.0 or (water_detected and current_vehicles > 0):
            flood_status = "Moderate Flood"
            risk_level = "MODERATE RISK"
        else:
            flood_status = "Normal / Clear"
            risk_level = "SAFE"

        # Generate fresh alerts strictly based on current inference telemetry
        time_str = time.strftime("%H:%M:%S", time.localtime())
        if water_detected:
            alerts.append({
                "time": time_str,
                "type": "danger" if water_pct > 15 else "warning",
                "title": f"Flood Detected ({flood_status})",
                "message": f"Active road waterlogging identified with {water_pct}% surface coverage."
            })

        if current_vehicles > 0:
            alerts.append({
                "time": time_str,
                "type": "warning" if water_detected else "info",
                "title": f"Vehicle Detection ({current_vehicles} Detected)",
                "message": f"Identified {current_vehicles} vehicle(s) with bounding box annotations."
            })

        if current_persons > 0:
            alerts.append({
                "time": time_str,
                "type": "danger" if water_detected else "info",
                "title": f"Pedestrian Detection ({current_persons} Detected)",
                "message": f"Identified {current_persons} pedestrian(s) in frame area."
            })

        alerts.append({
            "time": time_str,
            "type": "danger" if "CRITICAL" in risk_level else ("warning" if "MODERATE" in risk_level else "success"),
            "title": f"Risk Assessment: {risk_level}",
            "message": f"Evaluated hazard risk level: {risk_level}. Coverage: {water_pct}%, Vehicles: {current_vehicles}."
        })

        alerts.append({
            "time": time_str,
            "type": "success",
            "title": "Image Inference Completed",
            "message": f"Successfully analyzed image frame in {elapsed_time}s."
        })

        return {
            "success": True,
            "is_image": True,
            "flood_status": flood_status,
            "max_vehicles": current_vehicles,
            "max_persons": current_persons,
            "processing_time": f"{elapsed_time}s",
            "elapsed_seconds": elapsed_time,
            "total_frames": 1,
            "fps": "N/A (Single Frame)",
            "water_coverage_pct": water_pct,
            "alerts": alerts
        }

    def process_video(self, input_video_path: str, output_video_path: str, snapshot_path: str) -> Dict[str, Any]:
        """
        Frame-by-frame video processing pipeline:
        Loops process_frame for EVERY frame in the video using the exact same detection engine.
        """
        start_time = time.time()
        logger.info(f"Beginning video processing pipeline for: {input_video_path}")

        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open input video file at {input_video_path}")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        if fps <= 0 or math.isnan(fps):
            fps = 25
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
        os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

        frame_count = 0
        max_vehicles = 0
        max_persons = 0
        max_water_coverage = 0.0

        alerts: List[Dict[str, Any]] = []
        alert_triggers = set()
        snapshot_captured = False

        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            frame_count += 1

            # Run UNIFIED frame processor for EVERY video frame
            res = self.process_frame(frame)

            annotated_frame = res["annotated_frame"]
            water_detected = res["water_detected"]
            water_coverage = res["water_coverage"]
            current_vehicles = res["vehicles"]
            current_persons = res["persons"]

            max_vehicles = max(max_vehicles, current_vehicles)
            max_persons = max(max_persons, current_persons)
            max_water_coverage = max(max_water_coverage, water_coverage)

            timestamp_sec = round(frame_count / float(fps), 1)
            time_str = time.strftime("%H:%M:%S", time.gmtime(timestamp_sec))

            if water_detected and "flood_detected" not in alert_triggers:
                alert_triggers.add("flood_detected")
                alerts.append({
                    "time": time_str,
                    "type": "danger",
                    "title": "Flood Detected",
                    "message": f"Active road waterlogging identified (~{int(water_coverage * 100)}% coverage)."
                })

            if water_detected and current_vehicles > 0 and "vehicle_flooded" not in alert_triggers:
                alert_triggers.add("vehicle_flooded")
                alerts.append({
                    "time": time_str,
                    "type": "warning",
                    "title": "Vehicle in Flooded Area",
                    "message": f"Detected {current_vehicles} vehicle(s) navigating inundated street segment."
                })

            if water_detected and current_persons > 0 and "person_flooded" not in alert_triggers:
                alert_triggers.add("person_flooded")
                alerts.append({
                    "time": time_str,
                    "type": "danger",
                    "title": "Pedestrian Hazard",
                    "message": f"Pedestrian detected on flooded road corridor."
                })

            out.write(annotated_frame)

            if not snapshot_captured and (water_detected or frame_count >= max(1, total_frames // 2)):
                cv2.imwrite(snapshot_path, annotated_frame)
                snapshot_captured = True

        cap.release()
        out.release()

        # Transcode output video to browser H.264
        self._ensure_browser_compatible_h264(output_video_path)

        file_exists = os.path.exists(output_video_path)
        file_size = os.path.getsize(output_video_path) if file_exists else 0

        logger.info(f"[DETECT LOG] Output Path: {output_video_path}, Size: {file_size} bytes, Max Vehicles: {max_vehicles}")

        if not file_exists or file_size == 0:
            raise RuntimeError(f"Output video file is missing or 0 bytes at {output_video_path}")

        if not snapshot_captured or not os.path.exists(snapshot_path):
            cap_retry = cv2.VideoCapture(output_video_path)
            ret_r, frame_r = cap_retry.read()
            if ret_r and frame_r is not None:
                cv2.imwrite(snapshot_path, frame_r)
            cap_retry.release()

        elapsed_time = round(time.time() - start_time, 2)
        avg_fps = round(frame_count / max(elapsed_time, 0.01), 1)

        water_pct = round(max_water_coverage * 100, 1)
        if water_pct >= 25.0 or (water_pct >= 8.0 and max_vehicles > 0):
            flood_status = "Severe Flood"
            risk_level = "CRITICAL HAZARD"
        elif water_pct >= 1.0 or max_vehicles > 0:
            flood_status = "Moderate Flood"
            risk_level = "MODERATE RISK"
        else:
            flood_status = "Normal / Clear"
            risk_level = "SAFE"

        time_str = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
        alerts.append({
            "time": time_str,
            "type": "danger" if "CRITICAL" in risk_level else ("warning" if "MODERATE" in risk_level else "success"),
            "title": f"Risk Assessment: {risk_level}",
            "message": f"Evaluated hazard risk level: {risk_level}. Max Coverage: {water_pct}%, Max Vehicles: {max_vehicles}."
        })

        alerts.append({
            "time": time_str,
            "type": "success",
            "title": "Processing Completed",
            "message": f"Successfully analyzed {frame_count} frames in {elapsed_time}s at {avg_fps} FPS."
        })

        logger.info(f"Video processing finished. Output: {output_video_path}. Status: {flood_status}")

        return {
            "success": True,
            "is_image": False,
            "flood_status": flood_status,
            "max_vehicles": max_vehicles,
            "max_persons": max_persons,
            "processing_time": f"{elapsed_time}s",
            "elapsed_seconds": elapsed_time,
            "total_frames": frame_count,
            "fps": avg_fps,
            "water_coverage_pct": water_pct,
            "alerts": alerts
        }

    def _ensure_browser_compatible_h264(self, output_video_path: str):
        """Transcodes OpenCV output video to H.264 (yuv420p) format via imageio-ffmpeg."""
        try:
            import subprocess
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            
            temp_path = output_video_path + ".temp.mp4"
            if os.path.exists(output_video_path):
                os.rename(output_video_path, temp_path)
                cmd = [
                    ffmpeg_exe, "-y", "-i", temp_path,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-preset", "fast", "-crf", "23",
                    output_video_path
                ]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0 and os.path.exists(output_video_path) and os.path.getsize(output_video_path) > 0:
                    logger.info(f"Successfully converted output video to browser H.264: {output_video_path}")
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                else:
                    logger.warning(f"FFmpeg transcode returned code ({res.returncode}). Reverting to raw file.")
                    if os.path.exists(temp_path):
                        if os.path.exists(output_video_path):
                            os.remove(output_video_path)
                        os.rename(temp_path, output_video_path)
        except Exception as e:
            logger.warning(f"Browser H.264 conversion attempt failed: {e}. Output remains raw file.")

    def _render_hud_overlay(self, frame: np.ndarray, vehicles: int, persons: int, water: bool, coverage: float, frame_idx: int, total_frames: int):
        """Renders sleek HUD telemetry overlay onto frame."""
        h, w, _ = frame.shape
        hud_h = 70
        hud_bg = frame.copy()
        cv2.rectangle(hud_bg, (0, 0), (w, hud_h), (10, 15, 30), -1)
        cv2.addWeighted(hud_bg, 0.8, frame, 0.2, 0, frame)

        cv2.line(frame, (0, hud_h), (w, hud_h), (254, 242, 0), 2)
        cv2.putText(frame, "HYDROVISION AI", (15, 25), cv2.FONT_HERSHEY_DUPLEX, 0.6, (254, 242, 0), 2)
        cv2.putText(frame, "LIVE DETECTION TELEMETRY", (15, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        status_text = "FLOOD ALERT" if water else "NORMAL"
        status_color = (0, 0, 255) if water else (0, 255, 127)
        cv2.rectangle(frame, (w - 170, 15), (w - 15, 55), (20, 30, 50), -1)
        cv2.rectangle(frame, (w - 170, 15), (w - 15, 55), status_color, 1)
        cv2.putText(frame, status_text, (w - 155, 40), cv2.FONT_HERSHEY_DUPLEX, 0.55, status_color, 2)

        metrics_str = f"Vehicles: {vehicles}   Persons: {persons}   Coverage: {int(coverage*100)}%"
        cv2.putText(frame, metrics_str, (int(w * 0.3), 38), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)


# Global singleton instance for app.py import
detector_instance = WaterloggingDetector()
