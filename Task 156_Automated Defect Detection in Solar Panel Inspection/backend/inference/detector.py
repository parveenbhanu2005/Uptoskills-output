import os
import time
import numpy as np
import torch
import cv2
from typing import Dict, List, Any, Union, Optional
from pathlib import Path
from ultralytics import YOLO
from backend.utils.logger import setup_logger

logger = setup_logger("detector")

class YOLOv11Detector:
    def __init__(self, model_path: str = None, conf_threshold: float = 0.25, iou_threshold: float = 0.45, imgsz: int = 640):
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.imgsz = imgsz
        self.model = None
        self.loaded = False
        self.last_results = None
        self.last_inference_time_ms: float = 0.0
        
        # Determine fallback device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"YOLOv11 Detector initialized. Target device: {self.device}")
        
        # Resolve default model path if not specified
        if model_path is None:
            base_dir = Path(__file__).resolve().parent.parent
            model_path = str(base_dir / "models" / "best.pt")
            
        self.model_path = model_path
        
        # Proactively load weights if model file exists
        if os.path.exists(self.model_path):
            self.load_weights(self.model_path)
        else:
            logger.warning(f"Model weights file not found at {self.model_path}. Awaiting model load.")

    def load_weights(self, path: str):
        logger.info(f"Loading YOLO weights from {path} on device {self.device}...")
        try:
            self.model_path = path
            # Load Ultralytics YOLO model
            self.model = YOLO(path)
            self.model.to(self.device)
            self.loaded = True
            logger.info(f"YOLO weights successfully loaded from {path}.")
            
            # Model warm-up
            logger.info("Starting model warm-up...")
            warmup_img = np.zeros((self.imgsz, self.imgsz, 3), dtype=np.uint8)
            _ = self.model.predict(warmup_img, imgsz=self.imgsz, verbose=False)
            logger.info("Model warm-up completed successfully.")
        except Exception as e:
            self.loaded = False
            self.model = None
            logger.error(f"Failed to load YOLO model weights from {path}: {str(e)}")
            raise e

    def get_model_filename(self) -> str:
        """Return the basename of the currently loaded model weights file."""
        if self.model_path:
            return os.path.basename(self.model_path)
        return "None"

    def get_model_info(self) -> Dict[str, Any]:
        """Return detailed info about the loaded model."""
        return {
            "filename": self.get_model_filename(),
            "path": self.model_path,
            "loaded": self.loaded,
            "device": self.device,
            "imgsz": self.imgsz,
            "conf_threshold": self.conf_threshold,
            "iou_threshold": self.iou_threshold,
        }

    def detect(self, image_data: Union[np.ndarray, str, Path], 
               conf_threshold: float = None, 
               iou_threshold: float = None, 
               imgsz: int = None) -> List[Dict[str, Any]]:
        """
        Execute object detection for solar panel anomalies using the loaded YOLO model.
        Accepts numpy.ndarray or image filepath.
        Returns bounding boxes, class names, confidence and class IDs.
        """
        logger.info("Running YOLO object detection inference...")
        if not self.loaded or self.model is None:
            # Attempt to reload from default path
            if os.path.exists(self.model_path):
                self.load_weights(self.model_path)
            else:
                logger.error("Inference aborted. No model weights loaded.")
                raise RuntimeError("No model weights loaded. Please load weights first.")

        # Determine parameters
        iou = iou_threshold if iou_threshold is not None else self.iou_threshold
        sz = imgsz if imgsz is not None else self.imgsz

        # If string/path, load image via OpenCV
        if isinstance(image_data, (str, Path)):
            image_path = str(image_data)
            logger.info(f"Loading image from filepath: {image_path}")
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Failed to read image at path: {image_path}")
        else:
            img = image_data

        # Print stats of image passed to detect()
        print(f"[YOLO_DETECT_INPUT] img shape: {img.shape} | dtype: {img.dtype} | min: {img.min()} | max: {img.max()}")
        logger.info(f"[YOLO_DETECT_INPUT] img shape: {img.shape} | dtype: {img.dtype} | min: {img.min()} | max: {img.max()}")

        # Expose confidence threshold as a configurable parameter (default to 0.10)
        target_conf = conf_threshold if conf_threshold is not None else 0.10
        print(f"[YOLO_CONF] confidence threshold passed into model.predict(): {target_conf}")
        logger.info(f"[YOLO_CONF] confidence threshold passed into model.predict(): {target_conf}")

        start_time = time.time()
        # Run YOLO with target_conf, iou=0.5, verbose=True
        results = self.model.predict(
            img, 
            conf=target_conf, 
            iou=0.5 if iou is None else iou, 
            imgsz=sz, 
            device=self.device, 
            verbose=True
        )
        # Store prediction object internally
        self.last_results = results
        
        inference_time = (time.time() - start_time) * 1000
        self.last_inference_time_ms = round(inference_time, 2)
        logger.info(f"YOLO inference completed in {inference_time:.2f} ms.")

        # 1. Print the complete raw YOLO detections immediately after model.predict
        print("Raw YOLO boxes:", len(results[0].boxes))
        for i, box in enumerate(results[0].boxes):
            cls_id = int(box.cls[0])
            print(f"Detection {i}")
            print("Class ID:", cls_id)
            print("Class Name:", results[0].names[cls_id])
            print("Confidence:", float(box.conf[0]))
            print("BBox:", box.xyxy.tolist())

        # 2. Print stage-by-stage counts and actual detections
        print("\n=========================")
        print("RAW YOLO")
        print("=========================")
        print()
        print(f"{len(results[0].boxes)} detections")
        print()
        for i, box in enumerate(results[0].boxes):
            cls_id = int(box.cls[0])
            name = self.model.names[cls_id]
            conf = float(box.conf[0])
            bbox = [round(coord, 2) for coord in box.xyxy[0].tolist()]
            print(i)
            print(name)
            print(conf)
            print(bbox)
            print()

        # Stage 2: CONFIDENCE FILTER
        confidence_filtered_boxes = []
        for i, box in enumerate(results[0].boxes):
            confidence = float(box.conf[0])
            if confidence < target_conf:
                # Print every filtering condition for removed detection
                print("Detection removed")
                print()
                print("File:")
                print("detector.py")
                print()
                print("Function:")
                print("detect()")
                print()
                print("Line:")
                print("175")
                print()
                print("Reason:")
                print("confidence < threshold")
                print()
                print("Confidence:")
                print(confidence)
                print()
                print("Threshold:")
                print(target_conf)
                print()
            else:
                confidence_filtered_boxes.append(box)

        print("=========================")
        print("AFTER CONFIDENCE FILTER")
        print("=========================")
        print()
        print(f"{len(confidence_filtered_boxes)} detections")
        print()
        for i, box in enumerate(confidence_filtered_boxes):
            cls_id = int(box.cls[0])
            name = self.model.names[cls_id]
            conf = float(box.conf[0])
            bbox = [round(coord, 2) for coord in box.xyxy[0].tolist()]
            print(i)
            print(name)
            print(conf)
            print(bbox)
            print()

        # Stage 3: AFTER CLASS FILTER
        class_filtered_boxes = []
        for i, box in enumerate(confidence_filtered_boxes):
            # No class filtering currently exists, so we retain all
            class_filtered_boxes.append(box)

        print("=========================")
        print("AFTER CLASS FILTER")
        print("=========================")
        print()
        print(f"{len(class_filtered_boxes)} detections")
        print()
        for i, box in enumerate(class_filtered_boxes):
            cls_id = int(box.cls[0])
            name = self.model.names[cls_id]
            conf = float(box.conf[0])
            bbox = [round(coord, 2) for coord in box.xyxy[0].tolist()]
            print(i)
            print(name)
            print(conf)
            print(bbox)
            print()

        # Stage 4: AFTER SERIALIZATION
        detections = []
        for i, box in enumerate(class_filtered_boxes):
            xyxy = box.xyxy[0].tolist()
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = self.model.names[class_id]
            
            detections.append({
                "detection_id": i + 1,
                "class_id": class_id,
                "class_name": class_name,
                "confidence": round(confidence, 4),
                "bbox": [round(coord, 2) for coord in xyxy]
            })

        print("=========================")
        print("AFTER SERIALIZATION")
        print("=========================")
        print()
        print(f"{len(detections)} detections")
        print()
        for i, det in enumerate(detections):
            print(i)
            print(det["class_name"])
            print(det["confidence"])
            print(det["bbox"])
            print()

        print(f"API detections object id: {id(detections)}")
        print()

        # Stage 5: RETURNED BY API
        print("=========================")
        print("RETURNED BY API")
        print("=========================")
        print()
        print(f"{len(detections)} detections")
        print()
        for i, det in enumerate(detections):
            print(i)
            print(det["class_name"])
            print(det["confidence"])
            print(det["bbox"])
            print()

        print(f"API response uses detections object id: {id(detections)}")
        print()

        return detections

    def generate_annotated_image(self, output_path: str) -> Optional[str]:
        """
        Generate an annotated image using results[0].plot() and save it to disk.
        Returns the output path on success, None on failure.
        """
        if self.last_results is None or len(self.last_results) == 0:
            logger.warning("No inference results available for annotation.")
            return None

        try:
            result = self.last_results[0]
            print(f"[DEBUG_PLOT] Before plot(), box count: {len(result.boxes)}")
            logger.info(f"[DEBUG_PLOT] Before plot(), box count: {len(result.boxes)}")
            for idx, box in enumerate(result.boxes):
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                print(f"  [PLOT_BOX] Box {idx+1}: Class ID={cls_id}, Confidence={conf:.4f}")
                logger.info(f"  [PLOT_BOX] Box {idx+1}: Class ID={cls_id}, Confidence={conf:.4f}")
                
            print("Boxes drawn:")
            print(len(result.boxes))
            annotated = result.plot()
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            cv2.imwrite(output_path, annotated)
            logger.info(f"Annotated image saved to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to generate annotated image: {str(e)}")
            return None
