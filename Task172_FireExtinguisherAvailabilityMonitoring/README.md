# Smart Fire Extinguisher Availability Monitoring
### AI-Based Facility Safety Inspection System

This repository contains a standalone, production-ready facility safety inspection system that automatically monitors the presence and accessibility of wall-mounted fire extinguishers using Computer Vision and Deep Learning.

---

## Key Features
1. **Red Extinguisher Segmentation**: OpenCV HSV color space isolation combined with cylindrical aspect-ratio bounding box contour extraction.
2. **Standard Obstacle Detection**: Pre-trained YOLOv8 Nano model to capture standard dynamic blockages (people, chairs, luggage).
3. **Custom Obstacle Subtraction**: Adaptive thresholding and red-mask contour subtraction to detect arbitrary objects (cardboard boxes, crates).
4. **Depth-Aware Ground Contact Check**: Focuses on the ground contact base coordinates for moving people, eliminating occlusion false-positives when someone walks *behind* the unit.
5. **Auto-Calibration Mode**: Scans initial video frames programmatically to locate and register station coordinates automatically.
6. **Report Logging & Snapshots**: Writes a CSV log of safety state changes and captures photographic evidence of violations.

---

## Directory Structure
```
├── Code/
│   └── fire_extinguisher_monitor.ipynb   # Main Jupyter Notebook
├── Inputs/
│   ├── metadata.json                     # Ground truth annotations
│   ├── suite_00_synthetic_simulation.mp4 # Simulated video
│   ├── suite_01_office_hallway_clear.mp4
│   ├── suite_02_warehouse_blocked_boxes.mp4
│   └── suite_03_lobby_missing_inspection.mp4
├── Models/
│   └── yolov8n.pt                        # YOLOv8 weights (downloaded automatically)
└── Outputs/
    ├── suite_00_annotated.mp4            # Annotated video outputs
    ├── suite_01_annotated.mp4
    ├── suite_02_annotated.mp4
    ├── suite_03_annotated.mp4
    ├── suite_inspection_report.csv       # Consolidated inspection logs
    └── evidence_snapshots/               # Snapshot JPGs of violations
```

---

## Setup & Run Instructions
1. Open this workspace in **VS Code**.
2. Select your Python kernel (Python 3.10+ recommended) in the Jupyter extension interface.
3. Install required packages:
   ```bash
   pip install opencv-python numpy pandas matplotlib torch torchvision ultralytics
   ```
4. Run all cells in `Code/fire_extinguisher_monitor.ipynb`.
5. Press **'q'** on your keyboard to close the live OpenCV window during processing.
