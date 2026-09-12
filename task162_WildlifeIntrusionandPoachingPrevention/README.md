# Wildlife Intrusion & Poaching Prevention System
### AI-Based Edge Camera Surveillance System

This repository contains a localized AI-based edge camera surveillance system designed to detect wildlife movement and unauthorized human intruders in protected forest reserves.

---

## 📌 Project Structure

The project has been restructured as follows:
```
├── Code/
│   ├── Wildlife_Detection_Notebook.ipynb  # Interactive Jupyter Notebook step-by-step
│   ├── test_model.py                      # Standalone command-line testing script
│   ├── detector.py                        # Detection, tracking, & thermal simulation engine
│   ├── alert_system.py                    # SMS/Satellite dispatch logic
│   ├── data_manager.py                    # Directory, config, and CSV log manager
│   └── simulator.py                       # Synthetic night feed generator
│
├── Inputs/
│   ├── demo.mp4                           # Perimeter test video
│   ├── busy_mall.mp4                      # Crowded pedestrian walkway video
│   └── highway.mp4                        # Vehicle corridor video
│
├── Models/
│   └── yolov8n.pt                         # YOLOv8 model weights
│
├── Outputs/                               # Processed results
│   ├── annotated_demo.mp4                 # Processed video for demo.mp4
│   ├── annotated_busy_mall.mp4            # Processed video for busy_mall.mp4
│   ├── annotated_highway.mp4              # Processed video for highway.mp4
│   ├── threat_detection_timeline.png      # Threat timeline scatter chart
│   ├── config.json                        # Camera node configurations
│   ├── logs/
│   │   ├── wildlife_movement_log.csv      # Ecological CSV movement logs
│   │   └── alerts_sent.log                # Mock transmission audit logs
│   └── snapshots/                         # High-contrast cropped evidence images
│
├── notes.md                               # Real-world video validation results
└── README.md                              # Setup & execution guide
```

---

## 🛠️ Setup & Installation

Ensure you have Python 3.8+ installed. You can install all dependencies via pip:

```bash
pip install opencv-python ultralytics matplotlib pandas numpy pillow torch torchvision
```

---

## 🚀 Running the Standalone CLI Testing Script (`test_model.py`)

To run the testing engine, navigate to the `Code` directory:
```bash
cd Code
```

### 1. Run the Out-of-the-Box Synthetic Simulation
If no video file is provided, the script automatically generates a synthetic nighttime forest feed featuring moving wildlife, patrol vehicles, and an armed poacher inside `/Inputs`:
```bash
python test_model.py
```

### 2. Run on a Real-World Input Video
Run the script specifying any video present in the `/Inputs` folder:
```bash
python test_model.py -i demo.mp4
python test_model.py -i busy_mall.mp4
python test_model.py -i highway.mp4
```

### 3. Override Bounding Box Confidence Threshold
Specify the threshold (e.g., `0.45` for noisy night feeds):
```bash
python test_model.py -i demo.mp4 --conf 0.45
```

### 4. Manually Inject a Poacher Threat
Force human detections to trigger poaching/armed intruder critical alarms:
```bash
python test_model.py -i demo.mp4 --mock-poacher
```

---

## 📓 Running the Interactive Jupyter Notebook (`Wildlife_Detection_Notebook.ipynb`)

For a step-by-step visual demonstration:

1. Navigate to the `Code` directory and launch Jupyter:
   ```bash
   cd Code
   jupyter notebook Wildlife_Detection_Notebook.ipynb
   ```
   *(Or open the notebook directly inside VS Code).*
2. Run cells sequentially to:
   - Initialize managers and load dependencies.
   - Generate and examine the synthetic nighttime video.
   - Run the surveillance vision pipeline.
   - View high-contrast evidence crops directly inside the notebook.
   - Load and analyze CSV ecological logs using Pandas.
   - Graph the threat timeline scatter plot.
   - Test your own custom video files using the customized testing cell.
