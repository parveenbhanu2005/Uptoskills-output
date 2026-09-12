import os
import sys
import hashlib
import json
import cv2
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.inference.pipeline import InspectionPipeline

MODEL_PATH = PROJECT_ROOT / "backend" / "models" / "best.pt"
BASELINE_JSON_PATH = PROJECT_ROOT / "backend" / "tests" / "baseline_snapshot.json"
TEST_IMAGE_PATH = PROJECT_ROOT / "test_panel.jpg"


def get_file_sha256(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def capture_baseline(image_path: Path = TEST_IMAGE_PATH) -> dict:
    """Run working inference pipeline on test image and capture raw detection baseline."""
    print("==================================================")
    print("    SOLARLENS BASELINE CAPTURE & REGRESSION TEST  ")
    print("==================================================")
    
    # 1. Model integrity check
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file missing at: {MODEL_PATH}")
    
    model_size = os.path.getsize(MODEL_PATH)
    model_hash = get_file_sha256(MODEL_PATH)
    
    print(f"Model Path   : {MODEL_PATH}")
    print(f"Model Size   : {model_size} bytes")
    print(f"Model SHA256 : {model_hash}")
    
    # 2. Run current pipeline
    pipeline = InspectionPipeline()
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Failed to read image at {image_path}")

    # Standard default config
    config = {
        "resizeWidth": 640,
        "resizeHeight": 640,
        "confidenceThreshold": 0.10,
        "clahe": True,
        "colorNormalization": True
    }
    
    result = pipeline.run(img, image_id=image_path.name, preprocessing_config=config)
    
    # Extract raw detections
    raw_detections = result.get("detections", [])
    
    snapshot = {
        "model_filename": "best.pt",
        "model_sha256": model_hash,
        "model_size_bytes": model_size,
        "test_image": image_path.name,
        "detection_count": len(raw_detections),
        "raw_detections": raw_detections,
        "inference_time_ms": result.get("time_ms", 0.0),
        "statistics": result.get("statistics", {})
    }
    
    print(f"\nBaseline Capture Complete:")
    print(f"  Test Image       : {image_path.name}")
    print(f"  Raw Detections   : {len(raw_detections)}")
    for det in raw_detections:
        print(f"    - Det #{det.get('detection_id')}: {det.get('class_name')} ({det.get('confidence')}) BBox: {det.get('bbox')}")
    
    # Save snapshot
    os.makedirs(BASELINE_JSON_PATH.parent, exist_ok=True)
    with open(BASELINE_JSON_PATH, "w") as f:
        json.dump(snapshot, f, indent=2)
    print(f"\nSaved baseline snapshot to: {BASELINE_JSON_PATH}")
    
    return snapshot


def verify_against_baseline(image_path: Path = TEST_IMAGE_PATH) -> bool:
    """Verify that current inference matches baseline snapshot exactly."""
    if not BASELINE_JSON_PATH.exists():
        print(f"Baseline snapshot not found at {BASELINE_JSON_PATH}. Capturing baseline now...")
        capture_baseline(image_path)
        return True

    with open(BASELINE_JSON_PATH, "r") as f:
        baseline = json.load(f)
        
    print("\n--- Verifying Model Integrity ---")
    current_hash = get_file_sha256(MODEL_PATH)
    if current_hash != baseline["model_sha256"]:
        raise RuntimeError(f"REGRESSION FAILURE: best.pt SHA256 mismatch!\nExpected: {baseline['model_sha256']}\nGot     : {current_hash}")
    print("Model checksum matches baseline (best.pt is UNCHANGED).")
    
    print("\n--- Verifying Raw YOLO Detections ---")
    pipeline = InspectionPipeline()
    img = cv2.imread(str(image_path))
    config = {
        "resizeWidth": 640,
        "resizeHeight": 640,
        "confidenceThreshold": 0.10,
        "clahe": True,
        "colorNormalization": True
    }
    result = pipeline.run(img, image_id=image_path.name, preprocessing_config=config)
    current_detections = result.get("detections", [])
    
    if len(current_detections) != baseline["detection_count"]:
        raise RuntimeError(f"REGRESSION FAILURE: Detection count mismatch!\nExpected: {baseline['detection_count']}\nGot     : {len(current_detections)}")

    for idx, (expected_det, current_det) in enumerate(zip(baseline["raw_detections"], current_detections)):
        if expected_det["class_id"] != current_det["class_id"]:
            raise RuntimeError(f"REGRESSION FAILURE at index {idx}: Class ID mismatch!\nExpected: {expected_det['class_id']}\nGot     : {current_det['class_id']}")
        if expected_det["class_name"] != current_det["class_name"]:
            raise RuntimeError(f"REGRESSION FAILURE at index {idx}: Class Name mismatch!\nExpected: {expected_det['class_name']}\nGot     : {current_det['class_name']}")
        if abs(expected_det["confidence"] - current_det["confidence"]) > 1e-4:
            raise RuntimeError(f"REGRESSION FAILURE at index {idx}: Confidence mismatch!\nExpected: {expected_det['confidence']}\nGot     : {current_det['confidence']}")
        if expected_det["bbox"] != current_det["bbox"]:
            raise RuntimeError(f"REGRESSION FAILURE at index {idx}: Bounding box mismatch!\nExpected: {expected_det['bbox']}\nGot     : {current_det['bbox']}")

    print("ALL RAW YOLO DETECTIONS MATCH BASELINE EXACTLY (100% REGRESSION PASSED).")
    return True


if __name__ == "__main__":
    snapshot = capture_baseline()
    verify_against_baseline()
