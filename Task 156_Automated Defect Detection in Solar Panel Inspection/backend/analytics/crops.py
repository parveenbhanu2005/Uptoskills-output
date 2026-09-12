import os
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.utils.logger import setup_logger

logger = setup_logger("crops")


class DefectCropExtractor:
    """
    SolarLens Defect Evidence Cropper.
    
    Extracts defect regions from original (unannotated) images using clamped bounding box coordinates.
    Saves defect crop thumbnails inside the inspection outputs directory.
    """

    @staticmethod
    def clamp_bbox(bbox: List[float], img_width: int, img_height: int) -> List[int]:
        """
        Safely clamp floating-point bounding box coordinates [xmin, ymin, xmax, ymax]
        to valid integer pixel bounds within [0, img_width] and [0, img_height].
        Guarantees non-negative, ordered coordinates.
        """
        if len(bbox) < 4:
            return [0, 0, min(10, img_width), min(10, img_height)]

        xmin, ymin, xmax, ymax = bbox[:4]

        # Clamp to [0, boundary]
        c_xmin = max(0, min(img_width - 1, int(round(xmin))))
        c_ymin = max(0, min(img_height - 1, int(round(ymin))))
        c_xmax = max(0, min(img_width, int(round(xmax))))
        c_ymax = max(0, min(img_height, int(round(ymax))))

        # Ensure xmin < xmax and ymin < ymax with minimum size 2px
        if c_xmax <= c_xmin:
            c_xmax = min(img_width, c_xmin + 2)
            c_xmin = max(0, c_xmax - 2)

        if c_ymax <= c_ymin:
            c_ymax = min(img_height, c_ymin + 2)
            c_ymin = max(0, c_ymax - 2)

        return [c_xmin, c_ymin, c_xmax, c_ymax]

    def crop_defect(self, original_image: np.ndarray, bbox: List[float]) -> np.ndarray:
        """
        Extract cropped region of defect from original image array.
        Handles coordinate clamping safely without throwing errors.
        """
        if original_image is None or original_image.size == 0:
            raise ValueError("Invalid original image array provided for cropping.")

        h, w = original_image.shape[:2]
        c_xmin, c_ymin, c_xmax, c_ymax = self.clamp_bbox(bbox, w, h)

        crop = original_image[c_ymin:c_ymax, c_xmin:c_xmax]

        if crop.size == 0:
            # Emergency fallback: minimum 10x10 patch around center
            cx, cy = w // 2, h // 2
            crop = original_image[max(0, cy - 5):min(h, cy + 5), max(0, cx - 5):min(w, cx + 5)]

        return crop

    def extract_and_save_crops(self, original_image: np.ndarray, 
                               detections: List[Dict[str, Any]], 
                               run_dir: Path) -> List[Dict[str, Any]]:
        """
        Extract defect crops for all detections in an inspection and save under <run_dir>/defects/.
        Updates detections with crop_path relative property.
        """
        defects_dir = run_dir / "defects"
        defects_dir.mkdir(parents=True, exist_ok=True)

        updated_detections = []
        for det in detections:
            det_copy = dict(det)
            det_id = det_copy.get("detection_id", 1)
            bbox = det_copy.get("bbox", [0, 0, 10, 10])

            try:
                crop = self.crop_defect(original_image, bbox)
                filename = f"detection_{det_id:03d}.jpg"
                crop_path_abs = defects_dir / filename
                cv2.imwrite(str(crop_path_abs), crop)

                # Relative path from run_dir.parent (outputs/)
                rel_crop_path = f"{run_dir.name}/defects/{filename}"
                det_copy["crop_path"] = rel_crop_path
            except Exception as e:
                logger.error(f"Failed to generate crop for detection {det_id}: {str(e)}")
                det_copy["crop_path"] = None

            updated_detections.append(det_copy)

        return updated_detections
