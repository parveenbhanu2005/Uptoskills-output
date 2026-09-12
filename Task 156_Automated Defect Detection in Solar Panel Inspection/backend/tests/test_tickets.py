import unittest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.analytics.maintenance import MaintenanceEngine, VALID_STATUSES


class TestMaintenanceTickets(unittest.TestCase):
    def setUp(self):
        self.maint_engine = MaintenanceEngine()

    def test_deterministic_ticket_ids(self):
        """Verify ticket IDs are deterministic and avoid duplicates within an inspection."""
        id1 = self.maint_engine.generate_ticket_id("insp_2026_001", 1)
        id2 = self.maint_engine.generate_ticket_id("insp_2026_001", 1)
        id3 = self.maint_engine.generate_ticket_id("insp_2026_001", 2)

        self.assertEqual(id1, id2, "Same inspection and detection ID must yield identical ticket ID.")
        self.assertNotEqual(id1, id3, "Different detection IDs must yield distinct ticket IDs.")

    def test_ticket_attributes(self):
        """Test initial status, severity, priority, and detection association on generated tickets."""
        detections = [
            {
                "detection_id": 10,
                "class_name": "MultiHotSpot",
                "confidence": 0.82,
                "severity_score": 82.0,
                "severity_level": "HIGH"
            },
            {
                "detection_id": 11,
                "class_name": "StringReversedPolarity",
                "confidence": 0.95,
                "severity_score": 95.0,
                "severity_level": "CRITICAL"
            }
        ]

        result = self.maint_engine.process_detections("insp_test_abc", detections)
        tickets = result["tickets"]

        self.assertEqual(len(tickets), 2)

        t1 = tickets[0]
        self.assertEqual(t1["detection_id"], 10)
        self.assertEqual(t1["priority"], "HIGH")
        self.assertEqual(t1["status"], "OPEN")
        self.assertIn("SL-", t1["ticket_id"])

        t2 = tickets[1]
        self.assertEqual(t2["detection_id"], 11)
        self.assertEqual(t2["priority"], "CRITICAL")
        self.assertEqual(t2["status"], "OPEN")

    def test_valid_statuses(self):
        """Verify valid status definitions."""
        self.assertEqual(VALID_STATUSES, ["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"])


if __name__ == "__main__":
    unittest.main()
