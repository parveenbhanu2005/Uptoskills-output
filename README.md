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
@'
# Smart Document Tampering Detection

## 1. Project Overview

Smart Document Tampering Detection is a Python-based digital forensic analysis system designed to identify possible modifications in document images.

The system uses OCR, image processing, forensic analysis, reference-image comparison, suspicious-region detection, evidence highlighting, heatmap generation, and JSON/CSV reporting.

A Flask web application provides a simple interface for uploading documents and viewing analysis results.

## 2. Objectives

1. Detect possible modifications in document images.
2. Extract document text using OCR.
3. Analyze text and document layout.
4. Perform visual forensic analysis.
5. Compare documents with a reference image when available.
6. Identify suspicious visual regions.
7. Generate tampering confidence.
8. Classify document risk level.
9. Highlight suspicious evidence.
10. Generate JSON and CSV reports.

## 3. Technologies Used

### Programming Language

- Python 3.10

### Framework

- Flask

### Libraries

- OpenCV
- PyTesseract
- NumPy
- Pillow
- scikit-image

### OCR Engine

- Tesseract OCR 5.x

### Frontend

- HTML
- CSS
- Jinja2

## 4. System Workflow

Document Upload
      |
      v
Image Validation
      |
      v
OCR Analysis
      |
      v
Text/Layout Analysis
      |
      v
Visual Forensic Analysis
      |
      v
Reference Image Comparison
      |
      v
Suspicious Region Detection
      |
      v
Evidence Highlighting
      |
      v
Tampering Confidence
      |
      +-------------------+
      |                   |
      v                   v
   Heatmap          JSON / CSV Reports
      |                   |
      +---------+---------+
                |
                v
           Web Result

## 5. Project Structure

tampering-detection/
|
├── app.py
├── detect.py
├── create_tampered.py
├── requirements.txt
├── README.md
|
├── input/
│   ├── sample.png
│   └── tampered_sample.png
|
├── output/
│   ├── sample_result.png
│   ├── sample_heatmap.png
│   ├── tampered_sample_result.png
│   └── tampered_sample_heatmap.png
|
├── reports/
│   ├── sample_report.json
│   ├── sample_report.csv
│   ├── tampered_sample_report.json
│   └── tampered_sample_report.csv
|
└── templates/
    ├── index.html
    └── result.html

## 6. Installation

Check Python:

python --version

Install dependencies:

pip install -r requirements.txt

Verify libraries:

python -c "import flask, cv2, pytesseract, numpy, PIL, skimage; print('ALL PROJECT DEPENDENCIES OK')"

## 7. Tesseract OCR

Tesseract OCR is required for document text extraction.

Development path:

C:\Program Files\Tesseract-OCR\tesseract.exe

Verify Tesseract:

& "C:\Program Files\Tesseract-OCR\tesseract.exe" --version

## 8. Command-Line Usage

Analyze the original document:

python detect.py input/sample.png

Analyze the tampered document:

python detect.py input/tampered_sample.png

The system generates:

- Highlighted evidence image
- Tampering heatmap
- JSON report
- CSV report

## 9. Web Application

Start the Flask application:

python app.py

Open the application:

http://127.0.0.1:5000

The web application allows users to:

1. Upload a document.
2. Start forensic analysis.
3. View tampering confidence.
4. View risk level.
5. View suspicious regions.
6. View highlighted evidence.
7. View the forensic heatmap.
8. Open the JSON report.
9. Open the CSV report.
10. Analyze another document.

## 10. Test Documents

Original/reference document:

input/sample.png

Tampered test document:

input/tampered_sample.png

A tampered test image can also be generated using:

python create_tampered.py

## 11. Test Results

### Original Document

Input: sample.png

Tampering Confidence : 0.00%
Risk Level           : LOW
OCR Regions          : 141
Visual Anomalies     : 0
Suspicious Regions   : 0

### Tampered Document

Input: tampered_sample.png

Tampering Confidence : 35.00%
Risk Level           : MEDIUM
OCR Regions          : 110
Visual Anomalies     : 5
Changed Image Area   : 0.3805%
Suspicious Regions   : 5

These results demonstrate the current prototype's ability to distinguish the original test document from the generated tampered test document using the implemented forensic evidence.

## 12. Output Files

Highlighted evidence:

output/tampered_sample_result.png

Tampering heatmap:

output/tampered_sample_heatmap.png

JSON report:

reports/tampered_sample_report.json

CSV report:

reports/tampered_sample_report.csv

## 13. Confidence Score

The tampering confidence is the score generated by the implemented detection algorithm.

For example, a result of 35.00% represents the algorithm's confidence based on detected forensic evidence.

It does not mean that 35% of the physical document was modified.

## 14. Risk Levels

The system provides three risk categories:

- LOW
- MEDIUM
- HIGH

The risk level is an initial forensic indicator and should not be treated as legal proof of document fraud.

## 15. Limitations

The current system is a prototype.

Limitations include:

- Performance depends on image quality.
- OCR errors can affect analysis.
- Reference comparison requires a suitable reference image.
- Very small modifications may be difficult to detect.
- The confidence score is algorithm-specific.
- More genuine and tampered documents are required for comprehensive evaluation.

## 16. Future Enhancements

Possible improvements include:

1. Machine-learning based classification.
2. Deep-learning based forgery detection.
3. PDF support.
4. Multiple reference templates.
5. Improved font analysis.
6. Metadata analysis.
7. Database storage.
8. User authentication.
9. Cloud deployment.
10. REST API support.
11. Larger benchmark dataset evaluation.
12. Advanced forensic visualization.

## 17. Conclusion

Smart Document Tampering Detection combines OCR, image processing, forensic analysis, reference comparison, suspicious-region detection, evidence visualization, and web-based reporting.

The current prototype successfully demonstrates document upload, OCR processing, forensic analysis, suspicious-region identification, confidence calculation, evidence highlighting, heatmap generation, and JSON/CSV report generation.

The system provides a foundation for future improvements using larger datasets and machine-learning or deep-learning based detection techniques.

## Important Note

The current results demonstrate the prototype using the available original and tampered test images. Further evaluation with a larger genuine/tampered document dataset is recommended before real-world deployment.
'@ | Set-Content .\README.md -Encoding UTF8
