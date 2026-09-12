import unittest
import sys
import numpy as np
import cv2
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.analytics.crops import DefectCropExtractor


class TestDefectCropExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = DefectCropExtractor()
        # Synthetic 640x640 BGR image
        self.test_img = np.zeros((640, 640, 3), dtype=np.uint8)
        self.test_img[100:200, 100:200] = [0, 255, 0] # green patch

    def test_normal_bounding_box(self):
        """Test normal inside-bounds bounding box."""
        crop = self.extractor.crop_defect(self.test_img, [100.0, 100.0, 200.0, 200.0])
        self.assertEqual(crop.shape, (100, 100, 3))
        self.assertGreater(crop.size, 0)

    def test_boundary_touching_box(self):
        """Test box touching boundary (0, 0, 640, 640)."""
        crop = self.extractor.crop_defect(self.test_img, [0.0, 0.0, 640.0, 640.0])
        self.assertEqual(crop.shape, (640, 640, 3))

    def test_out_of_bounds_box(self):
        """Test box extending outside image boundary (-50, -50, 800, 800)."""
        crop = self.extractor.crop_defect(self.test_img, [-50.0, -50.0, 800.0, 800.0])
        self.assertEqual(crop.shape, (640, 640, 3))
        self.assertGreater(crop.size, 0)

    def test_very_small_box(self):
        """Test degenerate/very small bounding box (100, 100, 100, 100)."""
        crop = self.extractor.crop_defect(self.test_img, [100.0, 100.0, 100.0, 100.0])
        self.assertGreaterEqual(crop.shape[0], 2)
        self.assertGreaterEqual(crop.shape[1], 2)

    def test_clamping_helper(self):
        """Verify clamp_bbox helper method."""
        clamped = DefectCropExtractor.clamp_bbox([-10, -20, 1000, 1000], 640, 640)
        self.assertEqual(clamped, [0, 0, 640, 640])


if __name__ == "__main__":
    unittest.main()
