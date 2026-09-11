# Pedestrian Group Formation Detection — AI Crowd Surveillance System

An AI-based computer vision crowd surveillance system designed to process surveillance video, detect and track pedestrians, form spatial-temporal pedestrian groups, detect stable groups, and identify **GROUP MERGING** and **GROUP SPLITTING** events in real-time.

---

## Key Features

1. **Pedestrian Detection & Multi-Object Tracking**: Utilizes YOLOv8/YOLO11 combined with multi-object tracking to assign persistent `Person IDs`.
2. **Spatial & Motion Feature Extraction**: Extracts center positions, velocity vectors $(\Delta x, \Delta y)$, trajectory history, and crowd density.
3. **Pedestrian Group Formation**: Applies DBSCAN clustering on spatial proximity and velocity vector similarity metrics.
4. **Group Stability Tracking**: Monitors group member consistency over consecutive frames to detect `STABLE_GROUP` events.
5. **Group Merging Detection**: Detects when two or more distinct groups converge into a single unified group for consecutive frames (`GROUP_MERGED`).
6. **Group Splitting Detection**: Detects when a single group separates into multiple distinct sub-groups (`GROUP_SPLIT`).
7. **Real-Time HUD & Visual Annotations**: Generates an annotated output video with bounding boxes, person IDs, group IDs, convex polygon hulls, and dynamic HUD overlay.
8. **JSON Alerts & CSV Logging**: Stores real-time alert logs (`alerts.json`), frame-by-frame event records (`group_events_report.csv`), and summary metrics (`event_statistics.json`).
9. **Visual Analytics**: Produces plot visualizations (`group_analysis.png`, `crowd_density.png`, `group_events.png`).

---

## Project Structure

```
pedestrian_group_detection/
├── config.py                  # Global configurations & thresholds
├── data/
│   └── input_video.mp4        # Input surveillance video
├── src/
│   ├── __init__.py
│   ├── detector.py            # YOLO pedestrian detector
│   ├── tracker.py             # Multi-object tracker
│   ├── features.py            # Feature extraction (position, motion, density)
│   ├── group_detector.py      # Group formation & stability tracking
│   ├── event_detector.py      # Group Merging & Group Splitting detection
│   ├── visualization.py       # HUD overlay & matplotlib plot generator
│   ├── video_generator.py     # Synthetic video generator for validation
│   └── main.py                # Core pipeline runner
├── outputs/
│   ├── annotated_group_detection.mp4
│   ├── group_analysis.png
│   ├── crowd_density.png
│   ├── group_events.png
│   ├── alerts.json
│   ├── group_events_report.csv
│   └── event_statistics.json
├── requirements.txt
├── README.md
└── run.py                     # Command-line entry point
```

---

## Installation & Setup

```bash
pip install -r requirements.txt
```

---

## Running the Project

### Option A: Running with your own surveillance video
Place your MP4/AVI surveillance video at `data/input_video.mp4` and run:

```bash
python run.py --input data/input_video.mp4
```

### Option B: Running with Synthetic Benchmark Video
If no video is provided or for automated testing, generate synthetic surveillance footage with merging & splitting groups:

```bash
python run.py --generate-synthetic
```

---

## Configurable Thresholds (`config.py`)

- `GROUP_DISTANCE_THRESHOLD`: Max pixel distance between pedestrians in a group (default: 90.0)
- `VELOCITY_WEIGHT`: Directional similarity weight in clustering (default: 25.0)
- `GROUP_STABILITY_FRAMES`: Consecutive frames required for a stable group (default: 10)
- `MERGE_SPLIT_PERSISTENCE_FRAMES`: Consecutive frames required for merge/split events (default: 5)
- `CROWD_DENSITY_THRESHOLD`: Threshold for high crowd density alerts (default: 0.0002)

---

## Generated Output Files

1. `outputs/annotated_group_detection.mp4`: Annotated surveillance video with HUD and group boundary polygons.
2. `outputs/alerts.json`: Real-time timestamped event alert logs.
3. `outputs/group_events_report.csv`: Frame-by-frame log with timestamp, location, condition, event type, group IDs, counts, confidence, and risk score.
4. `outputs/event_statistics.json`: Aggregated summary statistics.
5. `outputs/group_analysis.png`: Timeline chart of pedestrians and active groups.
6. `outputs/crowd_density.png`: Density trend chart.
7. `outputs/group_events.png`: Event scatter timeline.
