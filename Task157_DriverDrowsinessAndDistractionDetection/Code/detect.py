import os
import sys
import cv2
import argparse
import time
import json
import torch
import numpy as np
import pandas as pd
import mediapipe as mp

# PyTorch safety patch
try:
    _orig_load = torch.load
    def _patched_load(*args, **kwargs):
        kwargs['weights_only'] = False
        return _orig_load(*args, **kwargs)
    torch.load = _patched_load
except Exception:
    pass

from ultralytics import YOLO

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import (
    video_frame_generator,
    calculate_ear,
    calculate_mar,
    estimate_gaze,
    estimate_head_pose,
    EventClipSaver,
    log_incident,
    display_drowsiness_dashboard
)

try:
    import winsound
    def play_beep(severity):
        if severity == "CRITICAL":
            winsound.Beep(2200, 350)
        elif severity == "WARNING":
            winsound.Beep(1200, 150)
except ImportError:
    def play_beep(severity):
        pass

def parse_args():
    parser = argparse.ArgumentParser(description="AI-Based Driver Drowsiness and Distraction Detection")
    parser.add_argument(
        "--video",
        type=str,
        required=True,
        help="Path to the input video file or webcam index (e.g. 0)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Path to save the annotated output video. Defaults to Outputs/."
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Models", "yolov8n.pt")),
        help="Path to the YOLOv8 model weight file for phone detection."
    )
    parser.add_argument(
        "--conf_threshold",
        type=float,
        default=0.25,
        help="YOLOv8 cell phone confidence threshold."
    )
    parser.add_argument(
        "--ear_threshold",
        type=float,
        default=0.21,
        help="EAR threshold representing closed eyes."
    )
    parser.add_argument(
        "--mar_threshold",
        type=float,
        default=0.55,
        help="MAR threshold representing yawning."
    )
    parser.add_argument(
        "--head_tilt_threshold",
        type=float,
        default=18.0,
        help="Head Pitch/Roll threshold in degrees representing distraction/nodding."
    )
    parser.add_argument(
        "--gaze_time_limit",
        type=float,
        default=1.5,
        help="Maximum duration in seconds looking away before warning."
    )
    parser.add_argument(
        "--eyes_closed_time_limit",
        type=float,
        default=1.0,
        help="Maximum duration in seconds eyes closed before critical alert (micro-sleep)."
    )
    parser.add_argument(
        "--simulate_speed",
        type=bool,
        default=True,
        help="Simulate driver speed during the run."
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    code_dir = os.path.dirname(os.path.abspath(__file__))
    outputs_dir = os.path.abspath(os.path.join(code_dir, "..", "Outputs"))
    evidence_dir = os.path.join(outputs_dir, "evidence_frames")
    inspect_dir = os.path.join(outputs_dir, "inspect_frames")
    
    os.makedirs(outputs_dir, exist_ok=True)
    os.makedirs(evidence_dir, exist_ok=True)
    os.makedirs(inspect_dir, exist_ok=True)
    
    # Resolve input path
    video_source = args.video
    if not video_source.isdigit() and not os.path.exists(video_source):
        print(f"[ERROR] Input video path does not exist: {video_source}")
        sys.exit(1)
        
    # Setup output paths
    if video_source.isdigit():
        video_filename = f"webcam_{video_source}"
        video_name_only = f"webcam_{video_source}"
    else:
        video_filename = os.path.basename(video_source.rstrip('/\\'))
        video_name_only, _ = os.path.splitext(video_filename)
        
    output_video_path = args.output if args.output else os.path.join(outputs_dir, f"{video_name_only}_annotated.mp4")
    
    print(f"\n[INFO] Initializing Driver Drowsiness and Distraction Monitoring Pipeline")
    print(f" - Input Path:           {video_source}")
    print(f" - Output Video Path:      {output_video_path}")
    print(f" - YOLOv8 Model:           {args.model}")
    print(f" - EAR Threshold:          {args.ear_threshold}")
    print(f" - MAR Threshold:          {args.mar_threshold}")
    print(f" - Head Pose Threshold:    {args.head_tilt_threshold} deg")
    
    # Load YOLO model
    if not os.path.exists(args.model):
        print(f"[ERROR] Model weights file not found at: {args.model}")
        sys.exit(1)
    print("Loading YOLOv8 model...")
    yolo_model = YOLO(args.model)
    
    # Load MediaPipe FaceMesh
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,  # Crucial for iris tracking
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    print("[OK] Models loaded successfully.\n")
    
    start_time = time.time()
    processed_frames = 0
    incident_logs = []
    
    # Rolling state variables
    drowsiness_score = 0.0  # Range 0 - 100
    eyes_closed_frames = 0
    yawn_frames = 0
    gaze_away_frames = 0
    head_tilt_frames = 0
    missing_face_frames = 0
    
    # Blink detection state variables
    blink_count = 0
    eyes_closed_blink_state = False
    
    # Cooldown states
    last_yawn_time = 0
    last_gaze_time = 0
    last_tilt_time = 0
    last_phone_time = 0
    last_missing_time = 0
    
    # Initialize clip saver
    clip_saver = None
    
    # Camera calibration parameters for SolvePnP (will be updated once resolution is known)
    camera_matrix = None
    dist_coeffs = np.zeros((4, 1))
    
    try:
        frame_generator = video_frame_generator(video_source)
        out_writer = None
        
        for frame, frame_idx, fps, frame_count, width, height in frame_generator:
            if out_writer is None:
                # Use avc1 for H.264 video encoding to ensure WhatsApp playability
                fourcc = cv2.VideoWriter_fourcc(*'avc1')
                out_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
                clip_saver = EventClipSaver(outputs_dir, fps=fps, pre_seconds=3, post_seconds=2)
                
                print(f"Video specs: {width}x{height} pixels | {fps:.2f} FPS | {frame_count} total frames")
                print("Processing frames...")
                
                # Approximate camera matrix
                focal_length = width
                center = (width / 2, height / 2)
                camera_matrix = np.array([
                    [focal_length, 0, center[0]],
                    [0, focal_length, center[1]],
                    [0, 0, 1]
                ], dtype=np.float32)
                
            # Simulate vehicle speed (e.g. cruising around 85 km/h, fluctuating slightly)
            speed = 85.0
            if args.simulate_speed:
                speed = round(80.0 + 5.0 * np.sin(frame_idx / 30.0) + np.random.uniform(-1.0, 1.0), 1)
                
            # Copy frame for annotation
            annotated_frame = frame.copy()
            
            # --- 1. YOLOv8 Cell Phone Detection ---
            yolo_results = yolo_model.predict(frame, conf=args.conf_threshold, verbose=False)
            yolo_boxes = yolo_results[0].boxes
            
            phone_detected = False
            phone_box = None
            
            if yolo_boxes is not None and len(yolo_boxes) > 0:
                xyxy = yolo_boxes.xyxy.cpu().numpy()
                cls = yolo_boxes.cls.cpu().numpy()
                conf = yolo_boxes.conf.cpu().numpy()
                names = yolo_results[0].names
                
                for idx in range(len(xyxy)):
                    cls_name = names[int(cls[idx])].lower()
                    if cls_name == "cell phone":
                        phone_detected = True
                        phone_box = list(map(int, xyxy[idx]))
                        
                        # Draw phone bounding box
                        cv2.rectangle(annotated_frame, (phone_box[0], phone_box[1]), (phone_box[2], phone_box[3]), (0, 0, 255), 2)
                        cv2.putText(annotated_frame, f"Phone: {conf[idx]:.2f}", (phone_box[0], phone_box[1] - 8),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                                    
            # --- 2. MediaPipe Face Mesh Landmark Tracking ---
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            fm_results = face_mesh.process(rgb_frame)
            
            face_detected = False
            ear = 0.3
            mar = 0.15
            gaze_direction = "LOOKING_CENTER"
            gaze_ratio = 0.5
            pitch, yaw, roll = 0.0, 0.0, 0.0
            
            active_warnings = []
            active_criticals = []
            
            if fm_results.multi_face_landmarks:
                face_detected = True
                missing_face_frames = 0
                landmarks = fm_results.multi_face_landmarks[0].landmark
                
                # Compute EAR and MAR
                ear, _, _ = calculate_ear(landmarks, width, height)
                mar = calculate_mar(landmarks, width, height)
                
                # Compute Gaze Direction
                gaze_direction, gaze_ratio = estimate_gaze(landmarks, width, height)
                
                # Compute Head Pose (Pitch, Yaw, Roll)
                pitch, yaw, roll = estimate_head_pose(landmarks, width, height)
                
                # Draw facial landmark points
                # Select a few major landmarks to overlay (eyebrows, outline, irises)
                for lm_idx in [33, 133, 362, 263, 13, 14, 78, 308]:  # Major contours
                    lm = landmarks[lm_idx]
                    cx, cy = int(lm.x * width), int(lm.y * height)
                    cv2.circle(annotated_frame, (cx, cy), 2, (0, 255, 0), -1)
                    
                # Highlight Irises (landmarks 468, 473)
                for iris_idx, color in [(468, (0, 242, 255)), (473, (0, 242, 255))]:
                    lm = landmarks[iris_idx]
                    cx, cy = int(lm.x * width), int(lm.y * height)
                    cv2.circle(annotated_frame, (cx, cy), 3, color, -1)
                    
                # Draw Head Pose Axes Vector
                # Keypoints: Nose tip 4, Yaw/Pitch coordinates projection
                p4 = landmarks[4]
                nose_tip_2d = (int(p4.x * width), int(p4.y * height))
                
                # Build 3D canonical rotation and project axes onto image
                # Standard rotation projection
                axis_3d = np.array([
                    (0.0, 0.0, 0.0),       # Origin (Nose tip)
                    (40.0, 0.0, 0.0),      # X axis (Right - red)
                    (0.0, 40.0, 0.0),      # Y axis (Down - green)
                    (0.0, 0.0, 40.0)       # Z axis (Forward - blue)
                ], dtype=np.float32)
                
                # Recompute solvePnP specifically for vector drawing
                image_points = np.array([
                    [landmarks[4].x * width, landmarks[4].y * height],
                    [landmarks[152].x * width, landmarks[152].y * height],
                    [landmarks[33].x * width, landmarks[33].y * height],
                    [landmarks[263].x * width, landmarks[263].y * height],
                    [landmarks[61].x * width, landmarks[61].y * height],
                    [landmarks[291].x * width, landmarks[291].y * height]
                ], dtype=np.float32)
                
                model_points = np.array([
                    (0.0, 0.0, 0.0),
                    (0.0, -330.0, -65.0),
                    (-225.0, 170.0, -135.0),
                    (225.0, 170.0, -135.0),
                    (-150.0, -150.0, -125.0),
                    (150.0, -150.0, -125.0)
                ], dtype=np.float32)
                
                success, rvec, tvec = cv2.solvePnP(
                    model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
                )
                
                if success:
                    projected_points, _ = cv2.projectPoints(axis_3d, rvec, tvec, camera_matrix, dist_coeffs)
                    pt_origin = tuple(projected_points[0].ravel().astype(int))
                    pt_x = tuple(projected_points[1].ravel().astype(int))
                    pt_y = tuple(projected_points[2].ravel().astype(int))
                    pt_z = tuple(projected_points[3].ravel().astype(int))
                    
                    cv2.line(annotated_frame, pt_origin, pt_x, (0, 0, 255), 2, cv2.LINE_AA) # X
                    cv2.line(annotated_frame, pt_origin, pt_y, (0, 255, 0), 2, cv2.LINE_AA) # Y
                    cv2.line(annotated_frame, pt_origin, pt_z, (255, 0, 0), 2, cv2.LINE_AA) # Z
                    
            else:
                # Driver face missing
                missing_face_frames += 1
                
            # --- 3. Distraction and Drowsiness Temporal Evaluation ---
            current_time = time.time()
            
            # A. Phone usage (Instant severe violation)
            if phone_detected:
                active_criticals.append("PHONE_USAGE")
                if current_time - last_phone_time > 4.0:
                    clip_name = clip_saver.trigger_recording("PHONE_USAGE", width, height)
                    log_incident(
                        frame=annotated_frame,
                        frame_idx=frame_idx,
                        event_type="PHONE_USAGE",
                        severity="CRITICAL",
                        score=drowsiness_score,
                        speed=speed,
                        clip_name=clip_name,
                        details="Driver detected holding cell phone.",
                        evidence_dir=evidence_dir,
                        log_list=incident_logs
                    )
                    last_phone_time = current_time
                    play_beep("CRITICAL")
                    
            # B. Face missing evaluation
            if not face_detected:
                if missing_face_frames > int(fps * 2.0):
                    active_criticals.append("DRIVER_MISSING")
                    if current_time - last_missing_time > 5.0:
                        clip_name = clip_saver.trigger_recording("DRIVER_MISSING", width, height)
                        log_incident(
                            frame=annotated_frame,
                            frame_idx=frame_idx,
                            event_type="DRIVER_MISSING",
                            severity="CRITICAL",
                            score=drowsiness_score,
                            speed=speed,
                            clip_name=clip_name,
                            details="Driver's face missing/not detected for > 2 seconds.",
                            evidence_dir=evidence_dir,
                            log_list=incident_logs
                        )
                        last_missing_time = current_time
                        play_beep("CRITICAL")
                else:
                    active_warnings.append("FACE_UNTRACKED")
                    
            # C. Eyes closed (Drowsiness/Micro-sleep) & Blink Counting
            if face_detected:
                if ear < args.ear_threshold:
                    eyes_closed_frames += 1
                    # Detect transition to closed for blink counting
                    if not eyes_closed_blink_state:
                        eyes_closed_blink_state = True
                    
                    # Increment drowsiness score quickly when eyes are closed
                    drowsiness_score = min(drowsiness_score + 1.8, 100.0)
                    
                    # Check micro-sleep duration: trigger faster if head is also tilted/nodding
                    duration_closed = eyes_closed_frames / fps
                    is_head_tilted = abs(pitch) > args.head_tilt_threshold or abs(roll) > args.head_tilt_threshold
                    required_time = 0.5 if is_head_tilted else args.eyes_closed_time_limit
                    
                    if duration_closed >= required_time:
                        active_criticals.append("MICRO_SLEEP")
                        if duration_closed == required_time or int(eyes_closed_frames) % int(fps) == 0:
                            clip_name = clip_saver.trigger_recording("MICRO_SLEEP", width, height)
                            log_incident(
                                frame=annotated_frame,
                                frame_idx=frame_idx,
                                event_type="MICRO_SLEEP",
                                severity="CRITICAL",
                                score=drowsiness_score,
                                speed=speed,
                                clip_name=clip_name,
                                details=f"Eyes closed for {duration_closed:.1f}s. Severe fatigue detected.",
                                evidence_dir=evidence_dir,
                                log_list=incident_logs
                            )
                            play_beep("CRITICAL")
                else:
                    # Eyes are now open
                    if eyes_closed_blink_state:
                        if eyes_closed_frames >= 1:  # Closed for at least 1 frame
                            blink_count += 1
                        eyes_closed_blink_state = False
                        
                    eyes_closed_frames = 0
                    # Decay drowsiness score slowly when alert
                    drowsiness_score = max(drowsiness_score - 0.4, 0.0)
                    
                # D. Yawning (MAR)
                if mar > args.mar_threshold:
                    yawn_frames += 1
                    if yawn_frames >= int(fps * 1.2):  # Yawn active for 1.2s
                        active_warnings.append("YAWNING")
                        drowsiness_score = min(drowsiness_score + 15.0, 100.0)  # Heavy fatigue penalty
                        if current_time - last_yawn_time > 8.0:
                            clip_name = clip_saver.trigger_recording("YAWNING", width, height)
                            log_incident(
                                frame=annotated_frame,
                                frame_idx=frame_idx,
                                event_type="YAWNING",
                                severity="WARNING",
                                score=drowsiness_score,
                                speed=speed,
                                clip_name=clip_name,
                                details=f"Yawning detected (MAR: {mar:.2f}).",
                                evidence_dir=evidence_dir,
                                log_list=incident_logs
                            )
                            last_yawn_time = current_time
                            play_beep("WARNING")
                else:
                    yawn_frames = 0
                    
                # E. Gaze distraction
                if gaze_direction in ["LOOKING_LEFT", "LOOKING_RIGHT"]:
                    gaze_away_frames += 1
                    duration_gaze_away = gaze_away_frames / fps
                    if duration_gaze_away >= args.gaze_time_limit:
                        active_warnings.append("GAZE_DISTRACTED")
                        if int(gaze_away_frames) % int(fps) == 0:
                            clip_name = clip_saver.trigger_recording("GAZE_DISTRACTED", width, height)
                            log_incident(
                                frame=annotated_frame,
                                frame_idx=frame_idx,
                                event_type="GAZE_DISTRACTED",
                                severity="WARNING",
                                score=drowsiness_score,
                                speed=speed,
                                clip_name=clip_name,
                                details=f"Driver looking away for {duration_gaze_away:.1f}s ({gaze_direction}).",
                                evidence_dir=evidence_dir,
                                log_list=incident_logs
                            )
                            play_beep("WARNING")
                else:
                    gaze_away_frames = 0
                    
                # F. Head pose tilt (Nodding / Looking down)
                # Pitch (negative values look down) or Roll (tilting sideways)
                if abs(pitch) > args.head_tilt_threshold or abs(roll) > args.head_tilt_threshold or yaw > 25.0 or yaw < -25.0:
                    head_tilt_frames += 1
                    duration_tilt = head_tilt_frames / fps
                    if duration_tilt >= 1.5:
                        active_warnings.append("HEAD_POSE_TILT")
                        if int(head_tilt_frames) % int(fps) == 0:
                            clip_name = clip_saver.trigger_recording("HEAD_POSE_TILT", width, height)
                            log_incident(
                                frame=annotated_frame,
                                frame_idx=frame_idx,
                                event_type="HEAD_POSE_TILT",
                                severity="WARNING",
                                score=drowsiness_score,
                                speed=speed,
                                clip_name=clip_name,
                                details=f"Driver head tilt/distraction: pitch={pitch:.1f}, roll={roll:.1f}, yaw={yaw:.1f}",
                                evidence_dir=evidence_dir,
                                log_list=incident_logs
                            )
                            play_beep("WARNING")
                else:
                    head_tilt_frames = 0
                    
            # G. High Fatigue Alert
            if drowsiness_score >= 70.0:
                active_warnings.append("HIGH_FATIGUE")
                
            # --- 4. Draw HUD Elements (Visual Overlays) ---
            # Semi-transparent overlay block for status HUD
            hud_overlay = annotated_frame.copy()
            cv2.rectangle(hud_overlay, (0, 0), (280, 200), (30, 30, 30), -1)
            cv2.addWeighted(hud_overlay, 0.4, annotated_frame, 0.6, 0, annotated_frame)
            
            # Print state indicators
            cv2.putText(annotated_frame, "IN-CABIN DRIVER MONITOR", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 242, 255), 2)
            cv2.putText(annotated_frame, f"Blinks: {blink_count}", (width - 140, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2, cv2.LINE_AA)
            cv2.putText(annotated_frame, f"Speed: {speed} km/h", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
            cv2.putText(annotated_frame, f"EAR (Eyes): {ear:.2f}", (15, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
            cv2.putText(annotated_frame, f"MAR (Mouth): {mar:.2f}", (15, 94), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
            cv2.putText(annotated_frame, f"Gaze: {gaze_direction}", (15, 116), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
            cv2.putText(annotated_frame, f"Pose: P:{pitch:.1f} Y:{yaw:.1f} R:{roll:.1f}", (15, 138), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 255), 1)
            
            # Draw Drowsiness Score bar
            cv2.putText(annotated_frame, f"Drowsiness: {drowsiness_score:.1f}%", (15, 162), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
            # Draw empty bar border
            cv2.rectangle(annotated_frame, (15, 172), (200, 185), (80, 80, 80), 1)
            # Bar color changes based on drowsiness score: Green -> Yellow -> Red
            bar_color = (0, 255, 100) if drowsiness_score < 30 else ((0, 230, 255) if drowsiness_score < 60 else (0, 0, 255))
            filled_width = int(15 + (185 * (drowsiness_score / 100.0)))
            cv2.rectangle(annotated_frame, (15, 172), (filled_width, 185), bar_color, -1)
            
            # Alert HUD banner if criticals or warnings exist
            if active_criticals:
                cv2.rectangle(annotated_frame, (0, height - 50), (width, height), (0, 0, 240), -1)
                critical_msg = f"CRITICAL ALERT: " + " | ".join(active_criticals)
                cv2.putText(annotated_frame, critical_msg, (20, height - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
            elif active_warnings:
                cv2.rectangle(annotated_frame, (0, height - 50), (width, height), (0, 180, 255), -1)
                warning_msg = f"WARNING ALERT: " + " | ".join(active_warnings)
                cv2.putText(annotated_frame, warning_msg, (20, height - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
            else:
                # Green banner for normal driving/gesture
                cv2.rectangle(annotated_frame, (0, height - 50), (width, height), (0, 180, 0), -1)
                cv2.putText(annotated_frame, "STATUS: NORMAL DRIVING", (20, height - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
                
            # Write to output clip stream
            clip_saver.add_frame(annotated_frame)
            
            # Write frame to output video
            out_writer.write(annotated_frame)
            
            # Save periodic inspect frames for reporting
            if frame_idx in [0, 50, 100, 150, 200, 250, 300, 400, 500]:
                inspect_img_path = os.path.join(inspect_dir, f"frame_{frame_idx}.jpg")
                cv2.imwrite(inspect_img_path, annotated_frame)
                
            processed_frames += 1
            if processed_frames % 50 == 0 or processed_frames == frame_count:
                progress = (processed_frames / frame_count) * 100
                print(f" [INFO] Processed {processed_frames}/{frame_count} frames ({progress:.1f}%)")
                
        # Close streams
        if out_writer is not None:
            out_writer.release()
        if clip_saver is not None:
            clip_saver.stop_recording()
            
        if processed_frames == 0:
            print("[ERROR] Processing completed but no frames were loaded. Verify video file.")
            sys.exit(1)
            
        # Export CSV log
        log_cols = ["timestamp", "event_id", "event_type", "severity", "drowsiness_score", "speed", "frame_number", "evidence_filename", "clip_filename", "details"]
        log_df = pd.DataFrame(incident_logs, columns=log_cols)
        csv_path = os.path.join(outputs_dir, "incident_log.csv")
        
        # Merge with existing logs to keep history
        if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
            try:
                existing_df = pd.read_csv(csv_path)
                log_df = pd.concat([existing_df, log_df], ignore_index=True)
                log_df = log_df.drop_duplicates(subset=["timestamp", "event_id"])
            except Exception:
                pass
                
        log_df.to_csv(csv_path, index=False)
        print(f"[INFO] Incident log CSV written/updated: {csv_path}")
        
        # Timing Stats
        elapsed = time.time() - start_time
        avg_fps = processed_frames / elapsed
        
        # Compile stats JSON
        summary_stats = {
            "total_frames": processed_frames,
            "processing_time_sec": round(elapsed, 2),
            "average_fps": round(avg_fps, 2),
            "total_incidents_logged": len(incident_logs),
            "incidents_by_severity": {
                "CRITICAL": sum(1 for e in incident_logs if e["severity"] == "CRITICAL"),
                "WARNING": sum(1 for e in incident_logs if e["severity"] == "WARNING")
            }
        }
        stats_path = os.path.join(outputs_dir, "summary_stats.json")
        with open(stats_path, "w") as f:
            json.dump(summary_stats, f, indent=2)
        print(f"[INFO] Summary statistics JSON written: {stats_path}")
        
        print("\n" + "="*60)
        print("[SUCCESS] DRIVER DROWSINESS & DISTRACTION DETECTION PIPELINE COMPLETED")
        print("="*60)
        print(f"Total Processing Time: {elapsed:.2f} seconds")
        print(f"Average FPS Achieved:  {avg_fps:.2f} FPS")
        print(f"Annotated Video Saved: {output_video_path}")
        print("="*60 + "\n")
        
        # Generate dashboard plot
        display_drowsiness_dashboard(outputs_dir, save_plot=True)
        
    except Exception as e:
        print(f"[ERROR] Critical pipeline failure: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
