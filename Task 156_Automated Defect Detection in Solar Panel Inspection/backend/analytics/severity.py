from typing import Dict, Any, List
from backend.utils.logger import setup_logger

logger = setup_logger("severity_engine")

# Configurable constants for severity thresholds
SEVERITY_BAND_LOW_MAX = 39.0
SEVERITY_BAND_MEDIUM_MAX = 69.0
SEVERITY_BAND_HIGH_MAX = 84.0


class SeverityEngine:
    """
    SolarLens Severity Scoring Engine.
    
    Decision-support heuristic based on model detection confidence.
    Calculates severity AFTER YOLO object detection.
    
    Bands:
      0.0 - 39.0  : LOW
      40.0 - 69.0 : MEDIUM
      70.0 - 84.0 : HIGH
      85.0 - 100.0: CRITICAL
    """
    def __init__(self, low_max: float = SEVERITY_BAND_LOW_MAX, 
                 medium_max: float = SEVERITY_BAND_MEDIUM_MAX, 
                 high_max: float = SEVERITY_BAND_HIGH_MAX):
        self.low_max = low_max
        self.medium_max = medium_max
        self.high_max = high_max

    def score_detection(self, confidence: float) -> Dict[str, Any]:
        """
        Calculate severity score and level for a single detection confidence.
        Confidence is expected as a float between 0.0 and 1.0 (or 0-100).
        Returns dict with severity_score (0-100) and severity_level (LOW|MEDIUM|HIGH|CRITICAL).
        """
        # Clamp confidence to [0.0, 1.0] if needed
        conf_val = max(0.0, min(1.0, float(confidence)))
        score = round(conf_val * 100.0, 2)

        if score <= self.low_max:
            level = "LOW"
        elif score <= self.medium_max:
            level = "MEDIUM"
        elif score <= self.high_max:
            level = "HIGH"
        else:
            level = "CRITICAL"

        return {
            "severity_score": score,
            "severity_level": level
        }

    def process_detections(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich normalized detection items with severity analysis without altering raw properties.
        """
        enriched = []
        for det in detections:
            conf = det.get("confidence", 0.0)
            sev_info = self.score_detection(conf)
            det_copy = dict(det)
            det_copy["severity_score"] = sev_info["severity_score"]
            det_copy["severity_level"] = sev_info["severity_level"]
            enriched.append(det_copy)
        return enriched


def get_severity_summary(detections_with_severity: List[Dict[str, Any]]) -> Dict[str, int]:
    """Return counts of LOW, MEDIUM, HIGH, CRITICAL detections."""
    summary = {"total_detections": len(detections_with_severity), "low": 0, "medium": 0, "high": 0, "critical": 0}
    for det in detections_with_severity:
        lvl = str(det.get("severity_level", "")).upper()
        if lvl == "LOW":
            summary["low"] += 1
        elif lvl == "MEDIUM":
            summary["medium"] += 1
        elif lvl == "HIGH":
            summary["high"] += 1
        elif lvl == "CRITICAL":
            summary["critical"] += 1
    return summary
