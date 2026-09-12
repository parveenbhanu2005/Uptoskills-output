"""
HydroVision AI - Flask Application Server (app.py)
---------------------------------------------------
Main application backend providing HTTP API endpoints, dashboard rendering,
secure file uploads (Videos & Images), asynchronous media processing delegation
to detect.py, and file downloads.
"""

import os
import time
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from werkzeug.utils import secure_filename

# Import custom detection engine
from detect import detector_instance

# Initialize Flask Application
app = Flask(__name__, template_folder="templates", static_folder="static")

# Configuration & Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")
SNAPSHOT_FOLDER = os.path.join(BASE_DIR, "snapshots")
LOG_FOLDER = os.path.join(BASE_DIR, "logs")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config["SNAPSHOT_FOLDER"] = SNAPSHOT_FOLDER
app.config["LOG_FOLDER"] = LOG_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB max upload size

# File type definitions (Image & Video support)
IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}
VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "webm"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

# Ensure required directories exist
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, SNAPSHOT_FOLDER, LOG_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Configure logging
log_file_path = os.path.join(LOG_FOLDER, "app.log")
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("HydroVisionApp")

def allowed_file(filename: str) -> bool:
    """Check if uploaded file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def is_image_file(filename: str) -> bool:
    """Check if filename is an image."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in IMAGE_EXTENSIONS

# Session state store (in-memory for simple dashboard session management)
session_state = {
    "uploaded_filename": None,
    "processed_filename": None,
    "snapshot_filename": None,
    "stats": None
}

@app.route("/")
def index():
    """
    GET /
    Renders main HydroVision AI Dashboard interface.
    """
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    """
    POST /upload
    Handles image & video file uploads from drag-and-drop or file input.
    Stores raw file in uploads/ and returns media URL for immediate web preview.
    """
    try:
        file = request.files.get("video") or request.files.get("file") or request.files.get("image")
        if not file or file.filename == "":
            return jsonify({"success": False, "error": "No file selected or provided in request."}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"upload_{timestamp}_{filename}"
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
            
            file.save(save_path)
            session_state["uploaded_filename"] = unique_filename
            session_state["processed_filename"] = None
            session_state["stats"] = None

            is_image = is_image_file(unique_filename)
            logger.info(f"Successfully uploaded {'image' if is_image else 'video'}: {unique_filename}")

            return jsonify({
                "success": True,
                "message": f"{'Image' if is_image else 'Video'} uploaded successfully.",
                "filename": unique_filename,
                "is_image": is_image,
                "file_type": "image" if is_image else "video",
                "file_url": f"/uploads/{unique_filename}",
                "video_url": f"/uploads/{unique_filename}"
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Invalid file type. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            }), 400

    except Exception as e:
        logger.error(f"Error during file upload: {str(e)}")
        return jsonify({"success": False, "error": f"Upload failed: {str(e)}"}), 500

@app.route("/process", methods=["POST"])
def process_media():
    """
    POST /process
    Triggers YOLO11 detection pipeline on currently uploaded image or video.
    Saves processed file into outputs/ and returns telemetry & real-time alerts.
    """
    try:
        data = request.get_json(silent=True) or {}
        filename = data.get("filename") or session_state.get("uploaded_filename")

        if not filename:
            return jsonify({"success": False, "error": "No file available for processing. Upload a file first."}), 400

        input_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        if not os.path.exists(input_path):
            return jsonify({"success": False, "error": f"File '{filename}' not found in uploads directory."}), 404

        output_filename = f"output_{filename}"
        output_path = os.path.join(app.config["OUTPUT_FOLDER"], output_filename)
        
        is_image = is_image_file(filename)
        snapshot_filename = filename if is_image else f"snapshot_{os.path.splitext(filename)[0]}.jpg"
        snapshot_path = os.path.join(app.config["SNAPSHOT_FOLDER"], snapshot_filename)

        logger.info(f"Starting detection processing for {'image' if is_image else 'video'} file: {filename}")

        # Invoke appropriate detect.py processing method
        if is_image:
            results = detector_instance.process_image(input_path, output_path)
        else:
            results = detector_instance.process_video(input_path, output_path, snapshot_path)

        # Output verification & logging
        output_exists = os.path.exists(output_path)
        output_size = os.path.getsize(output_path) if output_exists else 0

        logger.info(f"[APP LOG] Processed Output File Path: {output_path}")
        logger.info(f"[APP LOG] Processed Output Filename: {output_filename}")
        logger.info(f"[APP LOG] Output File Exists: {output_exists}")
        logger.info(f"[APP LOG] Output File Size: {output_size} bytes")

        if not output_exists or output_size == 0:
            logger.error(f"Output file generation failed or resulted in 0 bytes at '{output_path}'")
            return jsonify({
                "success": False,
                "error": f"Failed to generate valid processed file (0 bytes or missing file)."
            }), 500

        # Update session state
        session_state["processed_filename"] = output_filename
        session_state["snapshot_filename"] = snapshot_filename
        session_state["stats"] = results

        # Log session event into log file
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "input": filename,
            "output": output_filename,
            "is_image": is_image,
            "results": results
        }
        with open(os.path.join(LOG_FOLDER, "detection_history.jsonl"), "a") as lf:
            lf.write(json.dumps(log_entry) + "\n")

        return jsonify({
            "success": True,
            "message": f"{'Image' if is_image else 'Video'} processed successfully.",
            "output_filename": output_filename,
            "is_image": is_image,
            "file_type": "image" if is_image else "video",
            "output_file_url": f"/outputs/{output_filename}",
            "output_video_url": f"/outputs/{output_filename}",
            "snapshot_url": f"/snapshots/{snapshot_filename}",
            "download_url": f"/download/{output_filename}",
            "stats": {
                "flood_status": results["flood_status"],
                "max_vehicles": results["max_vehicles"],
                "max_persons": results["max_persons"],
                "processing_time": results["processing_time"],
                "fps": results["fps"],
                "total_frames": results["total_frames"],
                "water_coverage_pct": results["water_coverage_pct"]
            },
            "alerts": results["alerts"]
        })

    except Exception as e:
        logger.error(f"Error during media detection processing: {str(e)}")
        return jsonify({"success": False, "error": f"Detection processing failed: {str(e)}"}), 500

@app.route("/download", methods=["GET"])
@app.route("/download/<filename>", methods=["GET"])
def download_file(filename=None):
    """
    GET /download or GET /download/<filename>
    Serves the processed file for user download.
    """
    try:
        target_filename = filename or session_state.get("processed_filename")
        if not target_filename:
            return jsonify({"success": False, "error": "No processed file available to download."}), 404

        file_path = os.path.join(app.config["OUTPUT_FOLDER"], target_filename)
        if not os.path.exists(file_path):
            return jsonify({"success": False, "error": f"File '{target_filename}' not found in outputs directory."}), 404

        is_img = is_image_file(target_filename)
        mimetype = "image/jpeg" if target_filename.lower().endswith((".jpg", ".jpeg")) else ("image/png" if target_filename.lower().endswith(".png") else "video/mp4")

        return send_file(
            file_path,
            as_attachment=True,
            download_name=target_filename,
            mimetype=mimetype
        )
    except Exception as e:
        logger.error(f"Error serving download file: {str(e)}")
        return jsonify({"success": False, "error": f"Download failed: {str(e)}"}), 500

@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    """Serve uploaded image or video files."""
    mimetype = None
    if is_image_file(filename):
        ext = filename.rsplit(".", 1)[1].lower()
        mimetype = f"image/{'jpeg' if ext in ['jpg', 'jpeg'] else 'png'}"
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, mimetype=mimetype)

@app.route("/outputs/<path:filename>")
def serve_output(filename):
    """Serve processed output image or video files."""
    mimetype = None
    if is_image_file(filename):
        ext = filename.rsplit(".", 1)[1].lower()
        mimetype = f"image/{'jpeg' if ext in ['jpg', 'jpeg'] else 'png'}"
    else:
        mimetype = "video/mp4"
    return send_from_directory(app.config["OUTPUT_FOLDER"], filename, mimetype=mimetype)

@app.route("/snapshots/<path:filename>")
def serve_snapshot(filename):
    """Serve snapshot thumbnail images."""
    return send_from_directory(app.config["SNAPSHOT_FOLDER"], filename)

@app.route("/reset", methods=["POST"])
def reset_dashboard():
    """
    POST /reset
    Resets dashboard session state.
    """
    session_state["uploaded_filename"] = None
    session_state["processed_filename"] = None
    session_state["snapshot_filename"] = None
    session_state["stats"] = None
    logger.info("Dashboard state reset by user.")
    return jsonify({"success": True, "message": "Dashboard reset successfully."})

@app.route("/health", methods=["GET"])
def health_check():
    """System health check endpoint."""
    return jsonify({
        "status": "online",
        "system": "HydroVision AI",
        "yolo_model_loaded": detector_instance.model_loaded,
        "model_path": detector_instance.model_path,
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    logger.info("Launching HydroVision AI Server on http://127.0.0.1:5000 ...")
    app.run(host="0.0.0.0", port=5000, debug=True)
