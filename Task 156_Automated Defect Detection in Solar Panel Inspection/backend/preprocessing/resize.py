import numpy as np
import cv2
from backend.utils.logger import setup_logger

logger = setup_logger("resize")

class Resizer:
    def __init__(self, target_width: int = 1024, target_height: int = 1024, interpolation=cv2.INTER_LINEAR):
        self.target_width = target_width
        self.target_height = target_height
        self.interpolation = interpolation

    def apply(self, image: np.ndarray) -> np.ndarray:
        """
        Resize solar inspection image to standard model input dimensions
        while preserving aspect ratio or fitting target bounding box.
        """
        logger.info(f"Resizing image to {self.target_width}x{self.target_height}...")
        return cv2.resize(image, (self.target_width, self.target_height), interpolation=self.interpolation)
