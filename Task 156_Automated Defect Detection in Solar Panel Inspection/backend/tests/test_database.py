import unittest
import os
import tempfile
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database.sqlite_db import init_db
from backend.database.repository import InspectionRepository


class TestDatabaseRepository(unittest.TestCase):
    def setUp(self):
        # Create isolated temporary database file
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.repo = InspectionRepository(db_path=self.temp_db_path)

    def tearDown(self):
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)

    def test_database_initialization(self):
        """Verify database schema initializes cleanly in an isolated test database."""
        # Database should be initialized by constructor
        history = self.repo.get_history()
        self.assertEqual(len(history), 0)

    def test_save_and_retrieve_inspection(self):
        """Verify inserting inspection, detections, and tickets, then retrieving history."""
        inspection = {
            "inspection_id": "test_run_999",
            "image_id": "test_panel.jpg",
            "model": "best.pt",
            "device": "cpu",
            "input_resolution": "640x640",
            "inference_time_ms": 105.4,
            "count": 1
        }

        detections = [
            {
                "detection_id": 1,
                "class_id": 2,
                "class_name": "MultiHotSpot",
                "confidence": 0.812,
                "bbox": [120.0, 80.0, 350.0, 290.0],
                "severity_score": 81.2,
                "severity_level": "HIGH",
                "recommended_action": "MAINTENANCE_REQUIRED",
                "ticket_id": "SL-TEST-001",
                "crop_path": "test_run_999/defects/detection_001.jpg"
            }
        ]

        tickets = [
            {
                "ticket_id": "SL-TEST-001",
                "inspection_id": "test_run_999",
                "detection_id": 1,
                "class_name": "MultiHotSpot",
                "confidence": 0.812,
                "severity_score": 81.2,
                "severity_level": "HIGH",
                "priority": "HIGH",
                "recommended_action": "MAINTENANCE_REQUIRED",
                "status": "OPEN",
                "reason": "HIGH severity MultiHotSpot anomaly detected",
                "created_at": "2026-08-09T23:30:00Z"
            }
        ]

        success = self.repo.save_inspection(inspection, detections, tickets)
        self.assertTrue(success)

        # Retrieve history
        history = self.repo.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["inspection_id"], "test_run_999")

        # Retrieve tickets
        fetched_tickets = self.repo.get_tickets()
        self.assertEqual(len(fetched_tickets), 1)
        self.assertEqual(fetched_tickets[0]["ticket_id"], "SL-TEST-001")
        self.assertEqual(fetched_tickets[0]["status"], "OPEN")

    def test_ticket_status_transition(self):
        """Verify ticket status updates (OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED)."""
        inspection = {"inspection_id": "insp_status_test", "image_id": "img.jpg", "model": "best.pt", "count": 1, "inference_time_ms": 50.0}
        tickets = [{
            "ticket_id": "SL-STATUS-101",
            "inspection_id": "insp_status_test",
            "detection_id": 1,
            "class_name": "SingleDiode",
            "confidence": 0.9,
            "severity_score": 90.0,
            "severity_level": "CRITICAL",
            "priority": "CRITICAL",
            "recommended_action": "PRIORITY_MAINTENANCE",
            "status": "OPEN",
            "reason": "Critical defect",
            "created_at": "2026-08-09T23:30:00Z"
        }]

        self.repo.save_inspection(inspection, [], tickets)

        # Transition: OPEN -> IN_PROGRESS
        res1 = self.repo.update_ticket_status("SL-STATUS-101", "IN_PROGRESS")
        self.assertTrue(res1)
        t1 = self.repo.get_tickets()[0]
        self.assertEqual(t1["status"], "IN_PROGRESS")

        # Transition: IN_PROGRESS -> RESOLVED
        res2 = self.repo.update_ticket_status("SL-STATUS-101", "RESOLVED")
        self.assertTrue(res2)
        t2 = self.repo.get_tickets()[0]
        self.assertEqual(t2["status"], "RESOLVED")

        # Transition: RESOLVED -> CLOSED
        res3 = self.repo.update_ticket_status("SL-STATUS-101", "CLOSED")
        self.assertTrue(res3)
        t3 = self.repo.get_tickets()[0]
        self.assertEqual(t3["status"], "CLOSED")


if __name__ == "__main__":
    unittest.main()
