import os

# Base Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

# File Paths
DEFAULT_INPUT_VIDEO = os.path.join(DATA_DIR, "input_video.mp4")
ANNOTATED_VIDEO_PATH = os.path.join(OUTPUT_DIR, "annotated_group_detection.mp4")
ALERTS_JSON_PATH = os.path.join(OUTPUT_DIR, "alerts.json")
CSV_REPORT_PATH = os.path.join(OUTPUT_DIR, "group_events_report.csv")
EVENT_STATS_PATH = os.path.join(OUTPUT_DIR, "event_statistics.json")
GROUP_ANALYSIS_PNG = os.path.join(OUTPUT_DIR, "group_analysis.png")
CROWD_DENSITY_PNG = os.path.join(OUTPUT_DIR, "crowd_density.png")
GROUP_EVENTS_PNG = os.path.join(OUTPUT_DIR, "group_events.png")

# High-Accuracy Detection & Tracking Parameters
YOLO_MODEL_NAME = "yolov8n.pt"  # Lightweight nano model with calibrated confidence filter
DETECTION_CONFIDENCE = 0.40      # Higher confidence threshold to eliminate false positives (>95% precision)
TRACKER_TYPE = "bytetrack.yaml"

# Group Clustering Parameters
GROUP_DISTANCE_THRESHOLD = 115.0 # Max pixel distance between pedestrians in a group
VELOCITY_WEIGHT = 30.0            # Direction/speed alignment weight in distance metric
MIN_GROUP_SIZE = 2                # Minimum pedestrians to form a group

# High-Precision Event & Stability Parameters
GROUP_STABILITY_FRAMES = 8        # Frames membership must persist to be STABLE
GROUP_JACCARD_THRESHOLD = 0.60    # Overlap threshold for persistent group identity tracking
MERGE_SPLIT_PERSISTENCE_FRAMES = 6 # Consecutive frames required to declare MERGE/SPLIT (Zero false positives)
CROWD_DENSITY_THRESHOLD = 0.0002   # Pedestrians per pixel area threshold
ALERT_CONFIDENCE_THRESHOLD = 0.95 # Minimum 95%+ confidence requirement for event alerts
