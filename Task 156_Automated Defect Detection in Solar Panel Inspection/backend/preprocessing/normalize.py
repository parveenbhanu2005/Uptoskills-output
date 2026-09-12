import numpy as np
from backend.utils.logger import setup_logger

logger = setup_logger("normalize")

class Normalizer:
    def __init__(self, mean: list = [0.485, 0.456, 0.406], std: list = [0.229, 0.224, 0.225]):
        self.mean = np.array(mean, dtype=np.float32)
        self.std = np.array(std, dtype=np.float32)

    def apply(self, image: np.ndarray) -> np.ndarray:
        """
        Normalize image tensor/array to zero mean and unit variance
        using ImageNet statistics or custom calibration parameters.
        """
        logger.info("Normalizing image array...")
        img_float = image.astype(np.float32) / 255.0
        return (img_float - self.mean) / self.std
