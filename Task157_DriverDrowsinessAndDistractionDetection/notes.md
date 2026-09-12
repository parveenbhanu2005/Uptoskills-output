# Task 157: AI-Based Driver Drowsiness and Distraction Detection

## Task Overview

This project implements a state-of-the-art, **AI-Based Driver Drowsiness and Distraction Detection System** (In-Cabin Monitoring System) to monitor driver safety in real-time, preventing accidents caused by fatigue, drowsiness, cell phone usage, or gaze distractions. It integrates:
1. **MediaPipe Face Mesh**: For high-precision 3D facial landmarks (468 points + 10 iris tracking points) at high frame rates.
2. **Eye Aspect Ratio (EAR)**: Computes eye closure over frames to detect fatigue and micro-sleeps.
3. **Mouth Aspect Ratio (MAR)**: Monitors yawning frequency.
4. **Head Pose Estimation**: Computes 3D head pitch (nodding), yaw (turning), and roll (tilting) via PnP solvers.
5. **Gaze Direction Tracker**: Estimates horizontal pupil offsets to track gaze directions.
6. **Phone Usage Detection**: Leverages YOLOv8 to detect `cell phone` objects held by the driver.
7. **Rolling Drowsiness Score (0-100%)**: Tracks fatigue levels dynamically over time.
8. **Event Clip Buffering**: A frame buffer queue automatically captures 5-second video clips (3s pre-event, 2s post-event) of severe incidents.
9. **Alerts & Logging**: Generates Windows audio warnings using `winsound`, saves JPG evidence snapshots, and logs events to CSV and JSON.

---

## Folder Architecture & Alignment

The project is structured inside the workspace as follows:

```text
Task157_DriverDrowsinessAndDistractionDetection/
├── Code/
│   ├── detect.py                   # Main executable CLI pipeline script
│   ├── utils.py                    # Helper utilities (geometry, calculations, dashboards)
│   └── driver_drowsiness_detection.ipynb # Jupyter Notebook for visualization
├── Models/
│   └── yolov8n.pt                  # Pre-trained YOLOv8 weights (6.2 MB)
└── Outputs/
    ├── event_clips/                # Event clips of severe distraction triggers
    ├── evidence_frames/            # Full-resolution JPG alert snapshots
    ├── incident_log.csv            # Structured CSV log database
    ├── summary_stats.json          # Compiled summary metrics JSON
    └── analytics_dashboard.png     # Matplotlib dashboard plots
```

---

## Verification & Execution Outcomes

The pipeline was verified on **3 separate, highly relevant video inputs** representing drowsiness, yawning, and cell phone texting distractions:

### 1. Video 1: Driver Drowsiness Test (`drowsiness_0.mp4`)
*   **Properties**: 576x480 | 60.02 FPS | 660 frames
*   **Execution Command**:
    ```bash
    python Task157_DriverDrowsinessAndDistractionDetection/Code/detect.py --video "Task157_DriverDrowsinessAndDistractionDetection/Inputs/drowsiness_0.mp4"
    ```
*   **Outcome**: Successfully detected driver eye closures and nodding head tilts. Logged **2 critical Micro-sleep alerts** (eyes closed for >= 2.0s and 3.0s) and multiple **head pose tilt warnings** (pitch/roll thresholds exceeded). Saved 5-second video clips of severe triggers to outputs.
*   **Performance**: ~12.08 FPS average processing speed (total time: 54.61 seconds).

### 2. Video 2: Driver Yawning Video (`drowsiness_1.mp4`)
*   **Properties**: 588x360 | 30.00 FPS | 588 frames
*   **Execution Command**:
    ```bash
    python Task157_DriverDrowsinessAndDistractionDetection/Code/detect.py --video "Task157_DriverDrowsinessAndDistractionDetection/Inputs/drowsiness_1.mp4"
    ```
*   **Outcome**: Tracked profile changes. Correctly triggered **Driver Missing alerts** when the driver rotated completely out of face mesh range or during camera transition.
*   **Performance**: ~14.32 FPS average processing speed (total time: 41.06 seconds).

### 3. Video 3: Distracted Texting Video (`drowsiness_2.mp4`)
*   **Properties**: 640x360 (approx) | 14.79 FPS | 1798 frames
*   **Execution Command**:
    ```bash
    python Task157_DriverDrowsinessAndDistractionDetection/Code/detect.py --video "Task157_DriverDrowsinessAndDistractionDetection/Inputs/drowsiness_2.mp4"
    ```
*   **Outcome**: Successfully detected mobile phone distraction using YOLOv8, alongside head tilts. Logged **49 incidents** (18 CRITICAL, 31 WARNING) including multiple **Phone Usage critical events** (driver holding phone) and head nodding tilt alerts. Compiled rolling drowsiness stats and saved incident clips.
*   **Performance**: ~14.79 FPS average processing speed (total time: 121.55 seconds).

---

## How to Run

### Standalone CLI Execution
To execute the pipeline:
```bash
# Process a video with default settings
python Task157_DriverDrowsinessAndDistractionDetection/Code/detect.py --video <path_to_video>

# Process a video with custom sensitivity thresholds
python Task157_DriverDrowsinessAndDistractionDetection/Code/detect.py --video input.mp4 --ear_threshold 0.20 --mar_threshold 0.60
```

### Jupyter Notebook
Open `Task157_DriverDrowsinessAndDistractionDetection/Code/driver_drowsiness_detection.ipynb` in Jupyter Notebook/Lab, or upload to Google Colab, and execute all cells.
