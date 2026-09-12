from flask import Flask, render_template, request, send_from_directory
import os
import subprocess
import sys
import re

app = Flask(__name__)

# ============================================================
# PROJECT DIRECTORIES
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


# ============================================================
# ALLOWED FILE TYPES
# ============================================================

ALLOWED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".tif",
    ".tiff"
}


def allowed_file(filename):
    extension = os.path.splitext(filename)[1].lower()
    return extension in ALLOWED_EXTENSIONS


# ============================================================
# EXTRACT DETECTION RESULTS
# ============================================================

def extract_metrics(text):

    metrics = {
        "confidence": "N/A",
        "risk": "N/A",
        "ocr_regions": "N/A",
        "visual_anomalies": "N/A",
        "text_anomalies": "N/A",
        "font_anomalies": "N/A",
        "spacing_anomalies": "N/A",
        "changed_area": "N/A",
        "suspicious_regions": "N/A",
        "ela_score": "N/A"
    }

    # Tampering confidence
    match = re.search(
        r"Tampering confidence\s*:\s*([0-9.]+%)",
        text,
        re.IGNORECASE
    )
    if match:
        metrics["confidence"] = match.group(1)

    # Risk level
    match = re.search(
        r"Risk level\s*:\s*([A-Za-z]+)",
        text,
        re.IGNORECASE
    )
    if match:
        metrics["risk"] = match.group(1).upper()

    # OCR regions
    match = re.search(
        r"OCR regions(?:\s+detected)?\s*:\s*(\d+)",
        text,
        re.IGNORECASE
    )
    if match:
        metrics["ocr_regions"] = match.group(1)

    # Visual anomalies
    match = re.search(
        r"Visual anomalies(?:\s+detected)?\s*:\s*(\d+)",
        text,
        re.IGNORECASE
    )
    if match:
        metrics["visual_anomalies"] = match.group(1)

    # Text/layout anomalies
    match = re.search(
        r"(?:Text/layout anomalies|Text anomalies)\s*:\s*(\d+)",
        text,
        re.IGNORECASE
    )
    if match:
        metrics["text_anomalies"] = match.group(1)

    # Font/layout anomalies
    match = re.search(
        r"(?:Font/layout anomalies|Font anomalies)\s*:\s*(\d+)",
        text,
        re.IGNORECASE
    )
    if match:
        metrics["font_anomalies"] = match.group(1)

    # Spacing anomalies
    match = re.search(
        r"Spacing anomalies\s*:\s*(\d+)",
        text,
        re.IGNORECASE
    )
    if match:
        metrics["spacing_anomalies"] = match.group(1)

    # Changed image area
    match = re.search(
        r"Changed image area\s*:\s*([0-9.]+\s*%)",
        text,
        re.IGNORECASE
    )
    if match:
        metrics["changed_area"] = match.group(1)

    # Suspicious regions
    match = re.search(
        r"Suspicious regions\s*:\s*(\d+)",
        text,
        re.IGNORECASE
    )
    if match:
        metrics["suspicious_regions"] = match.group(1)

    # ELA score
    match = re.search(
        r"ELA forensic score\s*:\s*([0-9.]+)",
        text,
        re.IGNORECASE
    )
    if match:
        metrics["ela_score"] = match.group(1)

    return metrics


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


# ============================================================
# ANALYZE DOCUMENT
# ============================================================

@app.route("/analyze", methods=["POST"])
def analyze():

    if "document" not in request.files:
        return "No document uploaded.", 400

    file = request.files["document"]

    if file.filename == "":
        return "Please select a document.", 400

    filename = os.path.basename(file.filename)

    if not allowed_file(filename):
        return (
            "Unsupported file type. "
            "Please upload PNG, JPG, JPEG, BMP, TIF or TIFF."
        ), 400

    input_path = os.path.join(INPUT_DIR, filename)

    # Save uploaded file
    file.save(input_path)

    try:

        # Run detection program
        result = subprocess.run(
            [
                sys.executable,
                "detect.py",
                input_path
            ],
            capture_output=True,
            text=True,
            cwd=BASE_DIR
        )

        # Detection failed
        if result.returncode != 0:

            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Detection Error</title>
                <style>
                    body {{
                        font-family: Arial;
                        background: #f4f6f8;
                        padding: 40px;
                    }}
                    .error {{
                        background: white;
                        padding: 30px;
                        border-radius: 12px;
                        max-width: 900px;
                        margin: auto;
                    }}
                    pre {{
                        background: #111827;
                        color: white;
                        padding: 20px;
                        overflow-x: auto;
                    }}
                </style>
            </head>
            <body>
                <div class="error">
                    <h2>Detection Error</h2>
                    <pre>{result.stderr}</pre>
                </div>
            </body>
            </html>
            """, 500

        # ====================================================
        # OUTPUT FILE NAMES
        # ====================================================

        output_name = os.path.splitext(filename)[0]

        result_image = f"{output_name}_result.png"
        heatmap_image = f"{output_name}_heatmap.png"

        json_report = f"{output_name}_report.json"
        csv_report = f"{output_name}_report.csv"

        # ====================================================
        # EXTRACT METRICS
        # ====================================================

        metrics = extract_metrics(result.stdout)

        # ====================================================
        # RISK CLASS
        # ====================================================

        risk = metrics["risk"]

        if risk == "HIGH":
            risk_class = "high"
        elif risk == "MEDIUM":
            risk_class = "medium"
        else:
            risk_class = "low"

        # ====================================================
        # RESULT PAGE
        # ====================================================

        return render_template(
            "result.html",

            filename=filename,

            result=result.stdout,

            metrics=metrics,

            risk_class=risk_class,

            result_image=result_image,

            heatmap_image=heatmap_image,

            json_report=json_report,

            csv_report=csv_report
        )

    except Exception as e:

        return f"""
        <h2>Application Error</h2>
        <pre>{e}</pre>
        """, 500


# ============================================================
# SERVE INPUT IMAGE
# ============================================================

@app.route("/input/<filename>")
def input_file(filename):

    return send_from_directory(
        INPUT_DIR,
        filename
    )


# ============================================================
# SERVE OUTPUT IMAGE
# ============================================================

@app.route("/output/<filename>")
def output_file(filename):

    return send_from_directory(
        OUTPUT_DIR,
        filename
    )


# ============================================================
# SERVE REPORT FILES
# ============================================================

@app.route("/reports/<filename>")
def report_file(filename):

    return send_from_directory(
        REPORTS_DIR,
        filename
    )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("SMART DOCUMENT TAMPERING DETECTION")
    print("Web application starting...")
    print("Open: http://127.0.0.1:5000")
    print("=" * 70)

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )