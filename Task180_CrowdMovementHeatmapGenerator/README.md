# Crowd Movement Heatmap Generator (AI-Based Crowd Surveillance System)

An AI-based crowd surveillance system that processes video feeds, detects and tracks individuals, generates dynamic crowd density and trajectory heatmaps, triggers configurable alerts, and stores analysis statistics in CSV logs.

This directory implements the Crowd Movement Heatmap Generator (Task ID 180).
 
## 🚀 Key Features

1. **Pedestrian Tracking:** Uses a pre-trained YOLOv8 object detection model (`yolov8n.pt`) with native `ByteTrack` tracking to identify and track individual pedestrians (Class ID 0) frame-by-frame.
2. **Dynamic Decay Heatmap:** Accumulates person center-points over time and decays older frames to create a dynamic motion-fade heatmap. Smoothed with a 2D Gaussian filter and overlaid as a colormap on the frame.
3. **Trajectory Visualization:** Displays historical paths of tracked pedestrians, color-coded by velocity to show direction and speed.
4. **Resolution-Independent speed metrics:** Normalizes speeds as a percentage of the frame width per second ($width/sec$) instead of raw pixels per frame, ensuring calibration across different video resolutions.
5. **Boundary Filtering:** Ignores velocity jitter near video boundaries (within 5% of margins) to prevent false alerts.
6. **Multiplicative Threat Model:** Evaluates a hybrid threat risk: `Risk = 0.4 * Density + 0.3 * Speed + 0.3 * (Density * Speed)`.
7. **Codec Fallback:** Attempts H.264 (`avc1`) first for browser-compatible streaming, falling back to MPEG-4 (`mp4v`) if necessary.

---

## 📁 Repository Structure

```
Task180_CrowdMovementHeatmapGenerator/
├── Code/
│   ├── crowd_heatmap_generator.ipynb  <-- Single comprehensive Jupyter Notebook
│   └── Models/yolov8n.pt              <-- Pre-trained weights (downloaded automatically)
├── Inputs/
│   ├── classroom.mp4                  <-- Indoor classroom surveillance video
│   ├── people_detection.mp4           <-- Outdoor street pedestrian video
│   └── street_crowd.mp4               <-- Urban street video
└── Outputs/
    ├── classroom_heatmap.mp4          <-- Processed Video 1 (H.264 format)
    ├── classroom_log.csv              <-- Bounding box & event analysis logs
    ├── classroom_summary.png          <-- Matplotlib crowd statistics plots
    ├── people_detection_heatmap.mp4   <-- Processed Video 2 (H.264 format)
    ├── people_detection_log.csv       <-- Bounding box & event analysis logs
    ├── people_detection_summary.png   <-- Matplotlib crowd statistics plots
    ├── street_crowd_heatmap.mp4       <-- Processed Video 3 (H.264 format)
    ├── street_crowd_log.csv           <-- Bounding box & event analysis logs
    └── street_crowd_summary.png       <-- Matplotlib crowd statistics plots
```

---

## 🛠️ Setup & Running

To run this project:
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install ultralytics opencv-python pandas matplotlib torch
   ```
3. Open and run the Jupyter notebook `Code/crowd_heatmap_generator.ipynb`. It will verify folder setup, download the sample videos, run tracking, and output the heatmaps, logs, and plots.
