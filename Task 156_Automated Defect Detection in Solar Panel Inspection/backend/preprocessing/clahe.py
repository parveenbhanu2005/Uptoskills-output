import numpy as np
import cv2
from backend.utils.logger import setup_logger

logger = setup_logger("clahe")

class CLAHEPreprocessor:
    def __init__(self, clip_limit: float = 2.0, tile_grid_size: tuple = (8, 8)):
        self.clip_limit = clip_limit
        self.tile_grid_size = tile_grid_size
        self.clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)

    def apply(self, image: np.ndarray) -> np.ndarray:
        """
        Apply Contrast Limited Adaptive Histogram Equalization (CLAHE)
        to enhance EL / infrared solar panel inspection images.
        """
        logger.info("Applying CLAHE contrast enhancement...")
        if len(image.shape) == 3:
            # Convert to LAB color space, apply to L channel, convert back
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            l_eq = self.clahe.apply(l)
            lab_eq = cv2.merge((l_eq, a, b))
            return cv2.cvtColor(lab_eq, cv2.COLOR_LAB2BGR)
        else:
            return self.clahe.apply(image)
