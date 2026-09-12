# ☀️ SolarLens AI Inspector

<p align="center">
  <b>Industrial Solar Panel Defect Detection & Engineering Inspection Platform</b>
</p>

<p align="center">
Built with <b>YOLOv11</b>, <b>FastAPI</b>, <b>React</b>, <b>Express</b>, and <b>TypeScript</b>.
</p>

---

## 📌 Overview

SolarLens AI Inspector is an industrial-grade inspection platform designed for automated solar panel defect detection using deep learning.

The platform enables users to upload solar panel images, perform real-time YOLO-based inference, visualize detected defects, and automatically generate engineering reports in multiple formats.

---

# ✨ Features

- ✅ Real YOLOv11 defect detection
- ✅ Industrial inspection workflow
- ✅ Annotated image generation
- ✅ CSV detection reports
- ✅ JSON telemetry export
- ✅ Engineering PDF reports
- ✅ Interactive React dashboard
- ✅ Model Management interface
- ✅ Inspection statistics
- ✅ FastAPI inference backend
- ✅ Express proxy server
- ✅ Modern TypeScript frontend

---

# 🏗 Project Structure

```text
SolarLens/
│
├── backend/
│   ├── api/
│   ├── inference/
│   ├── models/
│   │     └── best.pt
│   ├── utils/
│   ├── outputs/
│   └── main.py
│
├── src/
│   ├── components/
│   ├── store/
│   └── types.ts
│
├── server.ts
├── package.json
├── run.bat
└── README.md
```

---

# 🛠 Prerequisites

Install the following before running the project.

- Python 3.11+
- Node.js 18+
- npm
- Git

Verify installation:

```bash
python --version
node --version
npm --version
git --version
```

---

# 📥 Clone Repository

```bash
git clone https://github.com/shounak2006/SolarLens.git

cd SolarLens
```

---

# 🐍 Backend Setup

## Step 1 — Create a Virtual Environment

Windows

```bash
python -m venv venv
```

---

## Step 2 — Activate the Virtual Environment

PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

Command Prompt

```cmd
venv\Scripts\activate
```

---

## Step 3 — Install Python Dependencies

```bash
pip install -r backend/requirements.txt
```

---

## Step 4 — Configure Environment Variables

Create a `.env` file in the project root.

Example:

```env
HOST=0.0.0.0
PORT=8000

MODEL_PATH=backend/models/best.pt
```

> **Note:** Add any additional environment variables required by your project.

---

# 🌐 Frontend Setup

Install all frontend dependencies.

```bash
npm install
```

---

# 🤖 Model Setup

Place your trained YOLO weights inside:

```text
backend/models/
```

Example:

```text
backend/models/
    best.pt
```

The detection pipeline automatically loads this model.

---

# 🚀 Running the Project

## Option 1 (Recommended)

Simply double-click

```text
run.bat
```

The script automatically:

- Starts the FastAPI backend
- Starts the React frontend
- Opens the application

---

## Option 2 (Manual)

### Terminal 1

Start FastAPI

```bash
python backend/main.py
```

Backend URL

```
http://localhost:8000
```

---

### Terminal 2

Start Frontend

```bash
npm run dev
```

Frontend URL

```
http://localhost:3000
```

---

# 📖 Using the Application

## Step 1

Open

```
http://localhost:3000
```

---

## Step 2

Navigate to

```
Image Upload
```

Upload a solar panel image.

---

## Step 3

Navigate to

```
Model Management
```

Load

```
best.pt
```

---

## Step 4

Navigate to

```
Inspection Pipeline
```

Click

```
Execute Full Pipeline
```

---

## Step 5

The pipeline performs

- Image preprocessing
- YOLO inference
- Bounding box generation
- Detection serialization
- Statistics computation
- Annotated image generation
- CSV generation
- JSON telemetry generation
- Engineering PDF generation

---

## Step 6

Navigate to

```
Engineering Reports
```

View

- Original image
- Annotated image
- Detection table
- Detection statistics
- Confidence scores
- Inference time
- Model information

---

## Step 7

Download

- Annotated Image
- CSV Report
- JSON Telemetry
- Engineering PDF

---

# 📂 Output Directory

Every inference creates a timestamped directory inside

```text
backend/outputs/
```

Example

```text
backend/outputs/

20260731_152209/

│── original.jpg
│── annotated.jpg
│── detections.csv
│── detections.json
└── report.pdf
```

---

# 📊 Generated Reports

The platform automatically generates

### Annotated Image

Contains all detected defects with bounding boxes.

---

### CSV Report

Contains

| Detection ID | Class | Confidence | Xmin | Ymin | Xmax | Ymax |
|--------------|--------|------------|------|------|------|------|

---

### JSON Report

Contains complete inference telemetry including

- model filename
- inference time
- detections
- statistics
- confidence scores

---

### Engineering PDF

Includes

- Original Image
- Annotated Image
- Detection Summary
- Statistics
- Model Metadata
- Engineering Report

---

# 🧠 Detection Model

Current detection model

```
YOLOv11
```

Weights

```
backend/models/best.pt
```

> **Note**
>
> Currently only the YOLO detection model performs real inference.
>
> Segmentation and classification modules are interface placeholders and do not yet execute inference.

---

# ⚙ Technology Stack

## Frontend

- React
- TypeScript
- Vite

## Backend

- FastAPI
- Express
- Node.js

## AI

- Ultralytics YOLO
- OpenCV
- NumPy

## Reporting

- ReportLab

---

# 🛠 Troubleshooting

## No detections

Verify that

```
backend/models/best.pt
```

exists and has been loaded successfully from **Model Management**.

---

## Backend doesn't start

Run

```bash
pip install -r backend/requirements.txt
```

---

## Frontend doesn't start

Run

```bash
npm install
```

---

## Blank annotated image

Check that

- the uploaded image actually contains detectable defects
- `best.pt` is the correct trained model
- the detection model is shown as **Loaded** inside Model Management

---

## Ports already in use

Backend

```
8000
```

Frontend

```
3000
```

Stop any process already using these ports or modify the configuration.

---

# 📌 Files Not Included in Git

The following files are intentionally excluded:

```text
node_modules/
venv/
.venv/
__pycache__/
backend/outputs/
backend/scratch/
.env
```

---

# 🚧 Future Improvements

- SAM2 segmentation
- EfficientNet classification
- Batch inference
- Live camera support
- GPU inference
- Docker deployment
- Cloud deployment
- Continuous model retraining

---



# ⭐ Support

If you found this project useful, consider giving it a ⭐ on GitHub!
