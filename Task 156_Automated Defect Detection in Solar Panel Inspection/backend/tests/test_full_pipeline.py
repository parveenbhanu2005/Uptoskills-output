import os
import sys
import unittest
import tempfile
import cv2
import numpy as np
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.inference.pipeline import InspectionPipeline
from backend.database.repository import InspectionRepository


class TestFullPipelineIntegration(unittest.TestCase):
    def setUp(self):
        # Create isolated DB for full pipeline test
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.pipeline = InspectionPipeline(db_path=self.temp_db_path)

    def tearDown(self):
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)

    def test_end_to_end_pipeline_execution(self):
        """Test full end-to-end inspection pipeline with synthetic panel image."""
        # Create synthetic test panel image (640x640)
        img = np.zeros((640, 640, 3), dtype=np.uint8)
        img[200:300, 200:300] = [128, 128, 255] # synthetic highlight

        res = self.pipeline.run(img, image_id="synthetic_panel.jpg")

        # 1. Best.pt loaded & YOLO executed
        self.assertEqual(res["status"], "success")
        self.assertIn("inspection_id", res)
        self.assertIn("time_ms", res)
        self.assertIn("count", res)

        # 2. Output paths verification
        out_base = PROJECT_ROOT / "backend" / "outputs" / res["inspection_id"]
        self.assertTrue((out_base / "original.jpg").exists())
        self.assertTrue((out_base / "annotated.jpg").exists())
        self.assertTrue((out_base / "detections.csv").exists())
        self.assertTrue((out_base / "detections.json").exists())
        self.assertTrue((out_base / "report.pdf").exists())

        # 3. Analytics verification
        self.assertIn("severity_summary", res)
        self.assertIn("maintenance_summary", res)
        self.assertIn("tickets", res)
        self.assertIn("normalized_detections", res)

        # 4. Database verification
        repo = InspectionRepository(db_path=self.temp_db_path)
        history = repo.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["inspection_id"], res["inspection_id"])


if __name__ == "__main__":
    unittest.main()
