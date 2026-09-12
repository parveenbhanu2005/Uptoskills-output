import unittest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.analytics.severity import SeverityEngine, get_severity_summary
from backend.analytics.maintenance import (
    MaintenanceEngine, ACTION_MONITOR, ACTION_REVIEW,
    ACTION_MAINTENANCE_REQUIRED, ACTION_PRIORITY_MAINTENANCE
)


class TestSeverityAndMaintenance(unittest.TestCase):
    def setUp(self):
        self.sev_engine = SeverityEngine()
        self.maint_engine = MaintenanceEngine()

    def test_severity_boundary_values(self):
        """Test explicit boundary values for severity scoring bands."""
        # 0.39 -> 39.0 -> LOW
        res_39 = self.sev_engine.score_detection(0.39)
        self.assertEqual(res_39["severity_score"], 39.0)
        self.assertEqual(res_39["severity_level"], "LOW")

        # 0.40 -> 40.0 -> MEDIUM
        res_40 = self.sev_engine.score_detection(0.40)
        self.assertEqual(res_40["severity_score"], 40.0)
        self.assertEqual(res_40["severity_level"], "MEDIUM")

        # 0.69 -> 69.0 -> MEDIUM
        res_69 = self.sev_engine.score_detection(0.69)
        self.assertEqual(res_69["severity_score"], 69.0)
        self.assertEqual(res_69["severity_level"], "MEDIUM")

        # 0.70 -> 70.0 -> HIGH
        res_70 = self.sev_engine.score_detection(0.70)
        self.assertEqual(res_70["severity_score"], 70.0)
        self.assertEqual(res_70["severity_level"], "HIGH")

        # 0.84 -> 84.0 -> HIGH
        res_84 = self.sev_engine.score_detection(0.84)
        self.assertEqual(res_84["severity_score"], 84.0)
        self.assertEqual(res_84["severity_level"], "HIGH")

        # 0.85 -> 85.0 -> CRITICAL
        res_85 = self.sev_engine.score_detection(0.85)
        self.assertEqual(res_85["severity_score"], 85.0)
        self.assertEqual(res_85["severity_level"], "CRITICAL")

        # 1.00 -> 100.0 -> CRITICAL
        res_100 = self.sev_engine.score_detection(1.00)
        self.assertEqual(res_100["severity_score"], 100.0)
        self.assertEqual(res_100["severity_level"], "CRITICAL")

    def test_maintenance_action_mapping(self):
        """Test mapping from severity level to maintenance action."""
        self.assertEqual(self.maint_engine.determine_action("LOW"), ACTION_MONITOR)
        self.assertEqual(self.maint_engine.determine_action("MEDIUM"), ACTION_REVIEW)
        self.assertEqual(self.maint_engine.determine_action("HIGH"), ACTION_MAINTENANCE_REQUIRED)
        self.assertEqual(self.maint_engine.determine_action("CRITICAL"), ACTION_PRIORITY_MAINTENANCE)

    def test_ticket_creation_threshold(self):
        """Verify that only HIGH and CRITICAL severity detections produce maintenance tickets."""
        detections = [
            {"detection_id": 1, "class_name": "MultiHotSpot", "confidence": 0.35, "severity_level": "LOW"},
            {"detection_id": 2, "class_name": "SingleDiode", "confidence": 0.55, "severity_level": "MEDIUM"},
            {"detection_id": 3, "class_name": "MultiDiode", "confidence": 0.75, "severity_level": "HIGH"},
            {"detection_id": 4, "class_name": "StringOpenCircuit", "confidence": 0.90, "severity_level": "CRITICAL"},
        ]

        result = self.maint_engine.process_detections("test_insp_001", detections)
        tickets = result["tickets"]

        # Exactly 2 tickets created (for HIGH and CRITICAL)
        self.assertEqual(len(tickets), 2)
        ticket_det_ids = [t["detection_id"] for t in tickets]
        self.assertIn(3, ticket_det_ids)
        self.assertIn(4, ticket_det_ids)
        self.assertNotIn(1, ticket_det_ids)
        self.assertNotIn(2, ticket_det_ids)


if __name__ == "__main__":
    unittest.main()
