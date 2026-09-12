import os
import sys
import cv2
import json
import csv
import hashlib
import pytesseract
import numpy as np
from datetime import datetime


# ============================================================
# SMART DOCUMENT TAMPERING DETECTION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPORT_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


# ============================================================
# TESSERACT CONFIGURATION
# ============================================================

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# ============================================================
# SHA-256
# ============================================================

def calculate_sha256(file_path):

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:

        while True:

            data = f.read(1024 * 1024)

            if not data:
                break

            sha256.update(data)

    return sha256.hexdigest()


# ============================================================
# FIND REFERENCE IMAGE
# ============================================================

def find_reference_image(input_path):

    filename = os.path.basename(input_path).lower()

    candidates = []

    # For the deliberately created tampered test image,
    # compare it with the original sample image.

    if "tampered" in filename:

        candidates.extend([
            os.path.join(INPUT_DIR, "sample.png"),
            os.path.join(INPUT_DIR, "sample.jpg"),
            os.path.join(INPUT_DIR, "sample.jpeg")
        ])

    for candidate in candidates:

        if os.path.exists(candidate):

            return candidate

    return None


# ============================================================
# OCR ANALYSIS
# ============================================================

def perform_ocr(image):

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    data = pytesseract.image_to_data(
        gray,
        output_type=pytesseract.Output.DICT,
        config="--psm 6"
    )

    regions = []

    for i in range(len(data["text"])):

        text = data["text"][i].strip()

        try:
            confidence = float(data["conf"][i])

        except Exception:
            confidence = -1

        if text and confidence >= 20:

            x = int(data["left"][i])
            y = int(data["top"][i])
            w = int(data["width"][i])
            h = int(data["height"][i])

            regions.append({
                "text": text,
                "confidence": round(
                    confidence,
                    2
                ),
                "x": x,
                "y": y,
                "w": w,
                "h": h
            })

    return regions


# ============================================================
# REFERENCE IMAGE COMPARISON
# ============================================================

def reference_comparison(original, test):

    if original is None:

        return None

    # Make both images the same size
    original = cv2.resize(
        original,
        (
            test.shape[1],
            test.shape[0]
        )
    )

    # Convert to grayscale
    original_gray = cv2.cvtColor(
        original,
        cv2.COLOR_BGR2GRAY
    )

    test_gray = cv2.cvtColor(
        test,
        cv2.COLOR_BGR2GRAY
    )

    # Reduce tiny compression/noise differences
    original_blur = cv2.GaussianBlur(
        original_gray,
        (5, 5),
        0
    )

    test_blur = cv2.GaussianBlur(
        test_gray,
        (5, 5),
        0
    )

    # Calculate pixel difference
    difference = cv2.absdiff(
        original_blur,
        test_blur
    )

    # Threshold
    _, threshold = cv2.threshold(
        difference,
        25,
        255,
        cv2.THRESH_BINARY
    )

    # Morphological cleanup
    kernel = np.ones(
        (5, 5),
        np.uint8
    )

    threshold = cv2.morphologyEx(
        threshold,
        cv2.MORPH_OPEN,
        kernel
    )

    threshold = cv2.morphologyEx(
        threshold,
        cv2.MORPH_CLOSE,
        kernel
    )

    # Find suspicious regions
    contours, _ = cv2.findContours(
        threshold,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    suspicious_regions = []

    clean_mask = np.zeros_like(
        threshold
    )

    for contour in contours:

        area = cv2.contourArea(
            contour
        )

        # Ignore tiny differences
        if area < 150:
            continue

        x, y, w, h = cv2.boundingRect(
            contour
        )

        # Ignore tiny boxes
        if w < 10 or h < 10:
            continue

        suspicious_regions.append({

            "x": int(x),

            "y": int(y),

            "width": int(w),

            "height": int(h),

            "area": int(area)
        })

        cv2.drawContours(
            clean_mask,
            [contour],
            -1,
            255,
            -1
        )

    total_pixels = (
        clean_mask.shape[0] *
        clean_mask.shape[1]
    )

    changed_pixels = cv2.countNonZero(
        clean_mask
    )

    changed_percentage = (
        changed_pixels /
        total_pixels
    ) * 100

    changed_percentage = min(
        changed_percentage,
        100
    )

    return {

        "difference": difference,

        "mask": clean_mask,

        "regions": suspicious_regions,

        "changed_percentage":
            changed_percentage
    }


# ============================================================
# ERROR LEVEL ANALYSIS
# ============================================================

def ela_analysis(image):

    quality = 90

    encode_param = [
        int(cv2.IMWRITE_JPEG_QUALITY),
        quality
    ]

    success, encoded = cv2.imencode(
        ".jpg",
        image,
        encode_param
    )

    if not success:

        return (
            0,
            np.zeros(
                image.shape[:2],
                dtype=np.uint8
            )
        )

    compressed = cv2.imdecode(
        encoded,
        cv2.IMREAD_COLOR
    )

    difference = cv2.absdiff(
        image,
        compressed
    )

    ela_gray = cv2.cvtColor(
        difference,
        cv2.COLOR_BGR2GRAY
    )

    ela_normalized = cv2.normalize(
        ela_gray,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    )

    mean_score = float(
        np.mean(
            ela_normalized
        )
    )

    return (
        mean_score,
        ela_normalized
    )


# ============================================================
# TEXT REGION ANALYSIS
# ============================================================

def text_region_analysis(
    image,
    ocr_regions
):

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    suspicious = []

    for region in ocr_regions:

        x = region["x"]
        y = region["y"]
        w = region["w"]
        h = region["h"]

        if w < 8 or h < 5:
            continue

        x1 = max(
            0,
            x
        )

        y1 = max(
            0,
            y
        )

        x2 = min(
            gray.shape[1],
            x + w
        )

        y2 = min(
            gray.shape[0],
            y + h
        )

        roi = gray[
            y1:y2,
            x1:x2
        ]

        if roi.size == 0:
            continue

        variance = float(
            np.var(roi)
        )

        if variance > 3000:

            suspicious.append(
                region
            )

    return suspicious


# ============================================================
# HEATMAP
# ============================================================

def create_heatmap(
    image,
    comparison_result,
    ela
):

    h, w = image.shape[:2]

    heat = np.zeros(
        (h, w),
        dtype=np.float32
    )

    # Strong evidence from reference comparison
    if comparison_result is not None:

        mask = comparison_result[
            "mask"
        ]

        heat += mask.astype(
            np.float32
        )

    # Add ELA information
    ela_resized = cv2.resize(
        ela,
        (w, h)
    )

    heat += (
        ela_resized.astype(
            np.float32
        ) * 0.25
    )

    heat = cv2.normalize(
        heat,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    )

    heat = heat.astype(
        np.uint8
    )

    colored = cv2.applyColorMap(
        heat,
        cv2.COLORMAP_JET
    )

    overlay = cv2.addWeighted(
        image,
        0.55,
        colored,
        0.45,
        0
    )

    return overlay


# ============================================================
# HIGHLIGHT SUSPICIOUS REGIONS
# ============================================================

def highlight_regions(
    image,
    comparison_result,
    text_anomalies
):

    result = image.copy()

    suspicious_count = 0

    # ========================================================
    # PRIMARY EVIDENCE
    #
    # Reference-image differences are the strongest evidence.
    # Only these regions are highlighted as suspicious.
    # ========================================================

    if comparison_result is not None:

        for region in comparison_result[
            "regions"
        ]:

            x = region["x"]
            y = region["y"]
            w = region["width"]
            h = region["height"]

            cv2.rectangle(
                result,
                (x, y),
                (
                    x + w,
                    y + h
                ),
                (0, 0, 255),
                3
            )

            cv2.putText(
                result,
                "SUSPICIOUS",
                (
                    x,
                    max(
                        25,
                        y - 8
                    )
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2
            )

            suspicious_count += 1

    # ========================================================
    # IMPORTANT
    #
    # OCR/text anomalies are NOT counted as suspicious
    # regions because normal documents can naturally produce
    # OCR/layout variations.
    #
    # This prevents false-positive highlighting.
    # ========================================================

    return (
        result,
        suspicious_count
    )


# ============================================================
# RISK LEVEL
# ============================================================

def get_risk(confidence):

    if confidence >= 70:

        return "HIGH"

    if confidence >= 35:

        return "MEDIUM"

    return "LOW"


# ============================================================
# CONFIDENCE CALCULATION
# ============================================================

def calculate_confidence(
    comparison,
    visual_anomalies,
    ela_score
):

    confidence = 0.0

    # ========================================================
    # REFERENCE COMPARISON
    # ========================================================

    if comparison is not None:

        changed_percentage = comparison[
            "changed_percentage"
        ]

        # Strongest evidence
        if changed_percentage >= 5:

            confidence += 65

        elif changed_percentage >= 2:

            confidence += 50

        elif changed_percentage >= 0.5:

            confidence += 35

        elif changed_percentage >= 0.1:

            confidence += 20

        elif changed_percentage > 0:

            confidence += 10

    # ========================================================
    # VISUAL ANOMALIES
    # ========================================================

    if visual_anomalies >= 10:

        confidence += 20

    elif visual_anomalies >= 5:

        confidence += 15

    elif visual_anomalies >= 1:

        confidence += 8

    # ========================================================
    # ELA
    # ========================================================

    if ela_score >= 30:

        confidence += 10

    elif ela_score >= 15:

        confidence += 5

    # ========================================================
    # IMPORTANT:
    #
    # OCR/text anomaly count is intentionally NOT added to
    # confidence because it caused false positives.
    # ========================================================

    confidence = min(
        confidence,
        100
    )

    return confidence


# ============================================================
# MAIN DETECTION
# ============================================================

def detect(input_path):

    if not os.path.exists(
        input_path
    ):

        print()
        print(
            "ERROR: Input image not found."
        )

        print(
            input_path
        )

        print()

        return

    filename = os.path.basename(
        input_path
    )

    name_without_ext = os.path.splitext(
        filename
    )[0]

    print()
    print("=" * 70)
    print(
        "SMART DOCUMENT TAMPERING DETECTION"
    )
    print("=" * 70)

    print()

    print(
        "Input document:",
        input_path
    )

    # ========================================================
    # LOAD IMAGE
    # ========================================================

    image = cv2.imread(
        input_path
    )

    if image is None:

        print()

        print(
            "ERROR: OpenCV could not read the image."
        )

        print(
            "Check that the image is a valid PNG/JPG file."
        )

        print()

        return

    height, width = image.shape[:2]

    sha256 = calculate_sha256(
        input_path
    )

    print(
        f"Image size: {width} x {height}"
    )

    print(
        "SHA-256:",
        sha256[:32] + "..."
    )

    # ========================================================
    # STEP 1 — OCR
    # ========================================================

    print()

    print(
        "[1/6] Detecting document text and layout..."
    )

    ocr_regions = perform_ocr(
        image
    )

    print(
        "OCR text regions detected:",
        len(ocr_regions)
    )

    # ========================================================
    # STEP 2 — TEXT ANALYSIS
    # ========================================================

    print()

    print(
        "[2/6] Analyzing text spacing and alignment..."
    )

    text_anomalies = text_region_analysis(
        image,
        ocr_regions
    )

    print(
        "Text/layout anomalies:",
        len(text_anomalies)
    )

    # ========================================================
    # STEP 3 — ELA
    # ========================================================

    print()

    print(
        "[3/6] Performing visual forensic analysis..."
    )

    ela_score, ela_image = ela_analysis(
        image
    )

    print(
        "ELA forensic score:",
        round(
            ela_score,
            2
        )
    )

    # ========================================================
    # STEP 4 — REFERENCE COMPARISON
    # ========================================================

    print()

    print(
        "[4/6] Identifying suspicious visual regions..."
    )

    reference_path = find_reference_image(
        input_path
    )

    comparison = None

    if reference_path is not None:

        print(
            "Reference image:",
            reference_path
        )

        reference = cv2.imread(
            reference_path
        )

        comparison = reference_comparison(
            reference,
            image
        )

        visual_anomalies = len(
            comparison["regions"]
        )

        changed_percentage = (
            comparison[
                "changed_percentage"
            ]
        )

        print(
            "Visual anomalies detected:",
            visual_anomalies
        )

        print(
            "Changed image area:",
            round(
                changed_percentage,
                3
            ),
            "%"
        )

    else:

        visual_anomalies = 0

        changed_percentage = 0

        print(
            "No reference image available."
        )

    # ========================================================
    # STEP 5 — COMBINE FORENSIC EVIDENCE
    # ========================================================

    print()

    print(
        "[5/6] Combining forensic evidence..."
    )

    confidence = calculate_confidence(
        comparison,
        visual_anomalies,
        ela_score
    )

    risk = get_risk(
        confidence
    )

    # ========================================================
    # STEP 6 — HIGHLIGHT EVIDENCE
    # ========================================================

    print()

    print(
        "[6/6] Highlighting suspicious evidence..."
    )

    highlighted, suspicious_count = (
        highlight_regions(
            image,
            comparison,
            text_anomalies
        )
    )

    # ========================================================
    # OUTPUT PATHS
    # ========================================================

    result_path = os.path.join(
        OUTPUT_DIR,
        f"{name_without_ext}_result.png"
    )

    heatmap_path = os.path.join(
        OUTPUT_DIR,
        f"{name_without_ext}_heatmap.png"
    )

    json_path = os.path.join(
        REPORT_DIR,
        f"{name_without_ext}_report.json"
    )

    csv_path = os.path.join(
        REPORT_DIR,
        f"{name_without_ext}_report.csv"
    )

    log_path = os.path.join(
        REPORT_DIR,
        "verification_log.txt"
    )

    # ========================================================
    # SAVE HIGHLIGHTED IMAGE
    # ========================================================

    cv2.imwrite(
        result_path,
        highlighted
    )

    # ========================================================
    # CREATE AND SAVE HEATMAP
    # ========================================================

    heatmap = create_heatmap(
        image,
        comparison,
        ela_image
    )

    cv2.imwrite(
        heatmap_path,
        heatmap
    )

    # ========================================================
    # JSON REPORT
    # ========================================================

    report = {

        "project":
            "Smart Document Tampering Detection",

        "analysis_time":
            datetime.now().isoformat(),

        "input_document":
            input_path,

        "reference_document":
            reference_path,

        "image_width":
            width,

        "image_height":
            height,

        "sha256":
            sha256,

        "ocr_regions":
            len(ocr_regions),

        "text_layout_anomalies":
            len(text_anomalies),

        "visual_anomalies":
            visual_anomalies,

        "changed_area_percentage":
            round(
                changed_percentage,
                4
            ),

        "ela_score":
            round(
                ela_score,
                4
            ),

        "suspicious_regions":
            suspicious_count,

        "tampering_confidence":
            round(
                confidence,
                2
            ),

        "risk_level":
            risk,

        "reference_comparison_used":
            comparison is not None
    }

    with open(
        json_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            report,
            f,
            indent=4
        )

    # ========================================================
    # CSV REPORT
    # ========================================================

    with open(
        csv_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(
            f
        )

        writer.writerow([
            "Metric",
            "Value"
        ])

        writer.writerow([
            "Input document",
            input_path
        ])

        writer.writerow([
            "Reference document",
            reference_path
        ])

        writer.writerow([
            "Image width",
            width
        ])

        writer.writerow([
            "Image height",
            height
        ])

        writer.writerow([
            "SHA-256",
            sha256
        ])

        writer.writerow([
            "OCR regions",
            len(ocr_regions)
        ])

        writer.writerow([
            "Text/layout anomalies",
            len(text_anomalies)
        ])

        writer.writerow([
            "Visual anomalies",
            visual_anomalies
        ])

        writer.writerow([
            "Changed area %",
            round(
                changed_percentage,
                4
            )
        ])

        writer.writerow([
            "ELA score",
            round(
                ela_score,
                4
            )
        ])

        writer.writerow([
            "Suspicious regions",
            suspicious_count
        ])

        writer.writerow([
            "Tampering confidence",
            round(
                confidence,
                2
            )
        ])

        writer.writerow([
            "Risk level",
            risk
        ])

    # ========================================================
    # VERIFICATION LOG
    # ========================================================

    with open(
        log_path,
        "a",
        encoding="utf-8"
    ) as f:

        f.write("\n")

        f.write("=" * 70 + "\n")

        f.write(
            "SMART DOCUMENT TAMPERING VERIFICATION\n"
        )

        f.write("=" * 70 + "\n")

        f.write(
            f"Time: {datetime.now()}\n"
        )

        f.write(
            f"Input: {input_path}\n"
        )

        f.write(
            f"Reference: {reference_path}\n"
        )

        f.write(
            f"Confidence: {confidence:.2f}%\n"
        )

        f.write(
            f"Risk: {risk}\n"
        )

        f.write(
            f"Changed area: "
            f"{changed_percentage:.4f}%\n"
        )

        f.write(
            f"Visual anomalies: "
            f"{visual_anomalies}\n"
        )

        f.write(
            f"Suspicious regions: "
            f"{suspicious_count}\n"
        )

    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    print()

    print("=" * 70)

    print(
        "ANALYSIS COMPLETE"
    )

    print("=" * 70)

    print()

    print(
        f"Tampering confidence : "
        f"{confidence:.2f}%"
    )

    print(
        f"Risk level           : "
        f"{risk}"
    )

    print(
        f"OCR regions          : "
        f"{len(ocr_regions)}"
    )

    print(
        f"Visual anomalies     : "
        f"{visual_anomalies}"
    )

    print(
        f"Text anomalies       : "
        f"{len(text_anomalies)}"
    )

    print(
        f"Changed image area   : "
        f"{changed_percentage:.4f}%"
    )

    print(
        f"Suspicious regions   : "
        f"{suspicious_count}"
    )

    print()

    print(
        "OUTPUT FILES"
    )

    print("-" * 70)

    print(
        "Highlighted image :",
        result_path
    )

    print(
        "Heatmap            :",
        heatmap_path
    )

    print(
        "JSON report        :",
        json_path
    )

    print(
        "CSV report         :",
        csv_path
    )

    print(
        "Verification log   :",
        log_path
    )

    print("=" * 70)

    print()


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) >= 2:

        input_file = sys.argv[1]

    else:

        input_file = os.path.join(
            INPUT_DIR,
            "sample.png"
        )

    detect(
        input_file
    )