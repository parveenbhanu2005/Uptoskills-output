import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.utils.logger import setup_logger

logger = setup_logger("maintenance_engine")

ACTION_MONITOR = "MONITOR"
ACTION_REVIEW = "REVIEW"
ACTION_MAINTENANCE_REQUIRED = "MAINTENANCE_REQUIRED"
ACTION_PRIORITY_MAINTENANCE = "PRIORITY_MAINTENANCE"

VALID_STATUSES = ["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"]


class MaintenanceEngine:
    """
    SolarLens Maintenance Decision Engine.
    
    Determines maintenance recommendations based on severity level.
    Automatically generates maintenance tickets for HIGH and CRITICAL severity detections.
    """
    
    def determine_action(self, severity_level: str) -> str:
        """Map severity level to recommended maintenance action."""
        lvl = str(severity_level).upper()
        if lvl == "LOW":
            return ACTION_MONITOR
        elif lvl == "MEDIUM":
            return ACTION_REVIEW
        elif lvl == "HIGH":
            return ACTION_MAINTENANCE_REQUIRED
        elif lvl == "CRITICAL":
            return ACTION_PRIORITY_MAINTENANCE
        else:
            return ACTION_MONITOR

    def generate_ticket_id(self, inspection_id: str, detection_id: int) -> str:
        """
        Generate a deterministic ticket ID for a detection within an inspection.
        Prevents accidental duplication during re-runs of the same inspection.
        """
        # Create 6-character deterministic hash prefix from inspection_id
        hash_digest = hashlib.md5(str(inspection_id).encode("utf-8")).hexdigest()[:6].upper()
        return f"SL-{hash_digest}-{int(detection_id):03d}"

    def process_detections(self, inspection_id: str, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate detections, assign maintenance actions, and generate tickets for HIGH/CRITICAL defects.
        Returns tuple/dict containing enriched detections, generated tickets, and summary stats.
        """
        enriched_detections = []
        tickets = []
        now_iso = datetime.utcnow().isoformat() + "Z"

        for det in detections:
            det_copy = dict(det)
            sev_level = det_copy.get("severity_level", "LOW")
            action = self.determine_action(sev_level)
            det_copy["recommended_action"] = action
            
            # Create ticket only for HIGH or CRITICAL severity
            if sev_level.upper() in ["HIGH", "CRITICAL"]:
                ticket_id = self.generate_ticket_id(inspection_id, det_copy.get("detection_id", 1))
                priority = "CRITICAL" if sev_level.upper() == "CRITICAL" else "HIGH"
                class_name = det_copy.get("class_name", "Anomaly")
                
                ticket = {
                    "ticket_id": ticket_id,
                    "inspection_id": inspection_id,
                    "detection_id": det_copy.get("detection_id", 1),
                    "class_name": class_name,
                    "confidence": det_copy.get("confidence", 0.0),
                    "severity_score": det_copy.get("severity_score", 0.0),
                    "severity_level": sev_level.upper(),
                    "priority": priority,
                    "recommended_action": action,
                    "status": "OPEN",
                    "reason": f"{sev_level.upper()} severity {class_name} anomaly detected",
                    "created_at": now_iso
                }
                det_copy["ticket_id"] = ticket_id
                tickets.append(ticket)
            else:
                det_copy["ticket_id"] = None

            enriched_detections.append(det_copy)

        maintenance_summary = {
            "monitor_count": sum(1 for d in enriched_detections if d["recommended_action"] == ACTION_MONITOR),
            "review_count": sum(1 for d in enriched_detections if d["recommended_action"] == ACTION_REVIEW),
            "maintenance_required_count": sum(1 for d in enriched_detections if d["recommended_action"] == ACTION_MAINTENANCE_REQUIRED),
            "priority_maintenance_count": sum(1 for d in enriched_detections if d["recommended_action"] == ACTION_PRIORITY_MAINTENANCE),
            "total_tickets": len(tickets)
        }

        return {
            "detections": enriched_detections,
            "tickets": tickets,
            "summary": maintenance_summary
        }
