import os
import time
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import deque

def video_frame_generator(video_path):
    """
    Generator that opens a video file or webcam stream and yields frames
    along with frame indices and video properties.
    """
    # Check if video_path is a digit (webcam index)
    if isinstance(video_path, str) and video_path.isdigit():
        cap = cv2.VideoCapture(int(video_path))
    else:
        cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise IOError(f"Cannot open video source: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or np.isnan(fps):
        fps = 30.0  # Fallback FPS
        
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_count <= 0:
        frame_count = 99999  # Streaming/webcam fallback
        
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        yield frame, frame_idx, fps, frame_count, width, height
        frame_idx += 1
        
    cap.release()

def calculate_ear(landmarks, width, height):
    """
    Computes Eye Aspect Ratio (EAR) for left and right eyes using standard MediaPipe landmarks.
    """
    def pt(idx):
        lm = landmarks[idx]
        return np.array([lm.x * width, lm.y * height])
    
    try:
        # Left Eye (MediaPipe indices)
        # Corners: 33 (outer), 133 (inner)
        # Vertical: (160, 144), (158, 153)
        p33 = pt(33)
        p133 = pt(133)
        p160 = pt(160)
        p144 = pt(144)
        p158 = pt(158)
        p153 = pt(153)
        
        ear_left = (np.linalg.norm(p160 - p144) + np.linalg.norm(p158 - p153)) / (2.0 * np.linalg.norm(p33 - p133) + 1e-6)
        
        # Right Eye (MediaPipe indices)
        # Corners: 362 (inner), 263 (outer)
        # Vertical: (385, 380), (387, 373)
        p362 = pt(362)
        p263 = pt(263)
        p385 = pt(385)
        p380 = pt(380)
        p387 = pt(387)
        p373 = pt(373)
        
        ear_right = (np.linalg.norm(p385 - p380) + np.linalg.norm(p387 - p373)) / (2.0 * np.linalg.norm(p362 - p263) + 1e-6)
        
        avg_ear = (ear_left + ear_right) / 2.0
        return avg_ear, ear_left, ear_right
    except Exception:
        return 0.3, 0.3, 0.3 # Fallback

def calculate_mar(landmarks, width, height):
    """
    Computes Mouth Aspect Ratio (MAR) to detect open-mouth yawning.
    """
    def pt(idx):
        lm = landmarks[idx]
        return np.array([lm.x * width, lm.y * height])
    
    try:
        # Mouth landmarks
        # Corners: 78, 308
        # Inner lips vertical: 13 (top), 14 (bottom)
        p13 = pt(13)
        p14 = pt(14)
        p78 = pt(78)
        p308 = pt(308)
        
        mar = np.linalg.norm(p13 - p14) / (np.linalg.norm(p78 - p308) + 1e-6)
        return mar
    except Exception:
        return 0.15 # Fallback

def estimate_gaze(landmarks, width, height):
    """
    Estimates horizontal gaze direction by tracking iris centers relative to eye corners.
    Requires refine_landmarks=True in MediaPipe FaceMesh to return 478 landmarks.
    """
    def pt(idx):
        lm = landmarks[idx]
        return np.array([lm.x * width, lm.y * height])
    
    try:
        # Left Eye (from driver's side): corners 33 and 133, iris center 468
        p33 = pt(33)
        p133 = pt(133)
        p468 = pt(468)
        
        v_eye = p133 - p33
        v_iris = p468 - p33
        len_eye = np.linalg.norm(v_eye) + 1e-6
        ratio_left = np.dot(v_iris, v_eye) / (len_eye ** 2)
        
        # Right Eye (from driver's side): corners 362 and 263, iris center 473
        p362 = pt(362)
        p263 = pt(263)
        p473 = pt(473)
        
        v_eye_r = p263 - p362
        v_iris_r = p473 - p362
        len_eye_r = np.linalg.norm(v_eye_r) + 1e-6
        ratio_right = np.dot(v_iris_r, v_eye_r) / (len_eye_r ** 2)
        
        avg_ratio = (ratio_left + ratio_right) / 2.0
        
        # Ratio classifications (iris centered is ~0.5)
        # Since looking left shifts the iris toward the right side of the eye
        if avg_ratio < 0.40:
            direction = "LOOKING_RIGHT"
        elif avg_ratio > 0.60:
            direction = "LOOKING_LEFT"
        else:
            direction = "LOOKING_CENTER"
            
        return direction, avg_ratio
    except Exception:
        return "LOOKING_CENTER", 0.5

def estimate_head_pose(landmarks, width, height):
    """
    Estimates 3D head pose (Pitch, Yaw, Roll) using solvePnP and a canonical 3D face model.
    """
    def pt(idx):
        lm = landmarks[idx]
        return np.array([lm.x * width, lm.y * height])
    
    try:
        # 2D image coordinates of key points
        image_points = np.array([
            pt(4),     # Nose tip
            pt(152),   # Chin
            pt(33),    # Left eye corner
            pt(263),   # Right eye corner
            pt(61),    # Left mouth corner
            pt(291)    # Right mouth corner
        ], dtype=np.float32)
        
        # 3D canonical coordinates of these key points
        model_points = np.array([
            (0.0, 0.0, 0.0),             # Nose tip
            (0.0, -330.0, -65.0),        # Chin
            (-225.0, 170.0, -135.0),     # Left eye corner
            (225.0, 170.0, -135.0),      # Right eye corner
            (-150.0, -150.0, -125.0),    # Left mouth corner
            (150.0, -150.0, -125.0)      # Right mouth corner
        ], dtype=np.float32)
        
        focal_length = width
        center = (width / 2, height / 2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype=np.float32)
        
        dist_coeffs = np.zeros((4, 1))
        
        success, rotation_vector, translation_vector = cv2.solvePnP(
            model_points,
            image_points,
            camera_matrix,
            dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )
        
        if not success:
            return 0.0, 0.0, 0.0
            
        rmat, _ = cv2.Rodrigues(rotation_vector)
        proj_matrix = np.hstack((rmat, translation_vector))
        _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(proj_matrix)
        pitch, yaw, roll = euler_angles.flatten()
        
        return pitch, yaw, roll
    except Exception:
        return 0.0, 0.0, 0.0

class EventClipSaver:
    """
    Manages a circular frame buffer to record video segments containing
    pre-event and post-event frames whenever severe alerts are triggered.
    """
    def __init__(self, outputs_dir, fps=30.0, pre_seconds=3, post_seconds=2):
        self.outputs_dir = outputs_dir
        self.fps = fps
        self.pre_frames_count = int(fps * pre_seconds)
        self.post_frames_count = int(fps * post_seconds)
        self.frame_buffer = deque(maxlen=self.pre_frames_count)
        
        self.is_recording = False
        self.remaining_post_frames = 0
        self.current_writer = None
        self.current_filename = ""
        self.current_filepath = ""

    def add_frame(self, frame):
        """Adds a copy of the current frame to the buffer or active writer."""
        self.frame_buffer.append(frame.copy())
        
        if self.is_recording:
            self.current_writer.write(frame)
            self.remaining_post_frames -= 1
            if self.remaining_post_frames <= 0:
                self.stop_recording()

    def trigger_recording(self, event_type, width, height):
        """Starts writing the buffered pre-event frames and starts active recording."""
        if self.is_recording:
            return self.current_filename
            
        self.is_recording = True
        self.remaining_post_frames = self.post_frames_count
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.current_filename = f"event_{event_type}_{timestamp}.mp4"
        self.current_filepath = os.path.join(self.outputs_dir, "event_clips", self.current_filename)
        
        # Setup Video Writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.current_writer = cv2.VideoWriter(self.current_filepath, fourcc, self.fps, (width, height))
        
        # Write pre-event frames
        for f in self.frame_buffer:
            self.current_writer.write(f)
            
        print(f"[CLIP SAVER] Recording triggered: {self.current_filename}")
        return self.current_filename

    def stop_recording(self):
        """Finalizes the video writer."""
        if self.is_recording:
            self.is_recording = False
            if self.current_writer is not None:
                self.current_writer.release()
                self.current_writer = None
            print(f"[CLIP SAVER] Clip finalized: {self.current_filepath}")

def log_incident(frame, frame_idx, event_type, severity, score, speed, clip_name, details, evidence_dir, log_list):
    """
    Saves an evidence image, logs incident details to output memory, and prints alert.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    timestamp_fns = time.strftime("%Y%m%d_%H%M%S")
    
    # Save JPG evidence snapshot
    evidence_filename = f"evidence_{event_type}_{timestamp_fns}_frame_{frame_idx}.jpg"
    evidence_path = os.path.join(evidence_dir, evidence_filename)
    cv2.imwrite(evidence_path, frame)
    
    event_id = f"evt_{frame_idx}_{int(time.time() * 1000) % 10000}"
    
    # Console alert
    alert_color = "\033[91m" if severity == "CRITICAL" else "\033[93m"
    reset_color = "\033[0m"
    print(f"{alert_color}[ALERT] {severity} | {event_type} | Drowsiness: {score:.1f}% | Speed: {speed} km/h | Details: {details}{reset_color}")
    
    log_list.append({
        "timestamp": timestamp,
        "event_id": event_id,
        "event_type": event_type,
        "severity": severity,
        "drowsiness_score": round(score, 1),
        "speed": speed,
        "frame_number": frame_idx,
        "evidence_filename": evidence_filename,
        "clip_filename": clip_name,
        "details": details
    })

def display_drowsiness_dashboard(outputs_dir, save_plot=True):
    """
    Reads the incident logs and generates a premium matplotlib dashboard plot.
    """
    csv_path = os.path.join(outputs_dir, "incident_log.csv")
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
        print("[WARNING] No incident logs found to plot dashboard.")
        # Create a placeholder empty plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "No Driver Distraction Incidents Logged Yet", 
                horizontalalignment='center', verticalalignment='center', fontsize=14)
        plt.tight_layout()
        if save_plot:
            plt.savefig(os.path.join(outputs_dir, "analytics_dashboard.png"), dpi=150)
            plt.close()
        return

    try:
        df = pd.read_csv(csv_path)
        
        # Set styling
        plt.style.use('dark_background')
        fig = plt.figure(figsize=(14, 9))
        fig.suptitle("Fleet Safety Management - Driver Distraction & Fatigue Analytics", fontsize=18, color="#00e6ff", fontweight='bold')
        
        # Grid layout
        gs = fig.add_gridspec(2, 2, height_ratios=[1.2, 1.0], hspace=0.35, wspace=0.25)
        
        # Plot 1: Drowsiness Timeline
        ax_timeline = fig.add_subplot(gs[0, :])
        ax_timeline.set_title("Distraction Alerts & Severity Timeline", fontsize=12, color="white", fontweight='bold')
        
        # Map colors based on severity
        colors = df['severity'].map({'CRITICAL': '#ff0055', 'WARNING': '#ffcc00'})
        sizes = df['drowsiness_score'].map(lambda s: max(s * 3, 50))
        
        scatter = ax_timeline.scatter(df['frame_number'], df['drowsiness_score'], 
                                      s=sizes, c=colors, alpha=0.8, edgecolors='white', linewidths=0.5)
        
        # Add labels to points
        for i, row in df.iterrows():
            ax_timeline.text(row['frame_number'], row['drowsiness_score'] + 4, row['event_type'], 
                             color='white', fontsize=8, alpha=0.9, ha='center')
                             
        ax_timeline.set_xlabel("Video Frame Index", color="gray")
        ax_timeline.set_ylabel("Drowsiness Score (%)", color="gray")
        ax_timeline.set_ylim(-10, 110)
        ax_timeline.grid(True, linestyle='--', alpha=0.3)
        
        # Legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#ff0055', label='CRITICAL ALERT'),
            Patch(facecolor='#ffcc00', label='WARNING ALERT')
        ]
        ax_timeline.legend(handles=legend_elements, loc='upper right', framealpha=0.5)
        
        # Plot 2: Distraction Type Distribution
        ax_dist = fig.add_subplot(gs[1, 0])
        event_counts = df['event_type'].value_counts()
        colors_dist = ['#00e6ff', '#ff0055', '#ffcc00', '#00ff66', '#a100ff']
        event_counts.plot(kind='bar', ax=ax_dist, color=colors_dist[:len(event_counts)], edgecolor='white', width=0.6)
        
        ax_dist.set_title("Frequency of Distraction Triggers", fontsize=12, color="white", fontweight='bold')
        ax_dist.set_ylabel("Event Count", color="gray")
        ax_dist.tick_params(axis='x', rotation=30, labelsize=9)
        ax_dist.grid(axis='y', linestyle='--', alpha=0.3)
        
        # Plot 3: Speed vs Drowsiness
        ax_speed = fig.add_subplot(gs[1, 1])
        ax_speed.set_title("Drowsiness Score vs Vehicle Speed Correlation", fontsize=12, color="white", fontweight='bold')
        
        scatter_speed = ax_speed.scatter(df['speed'], df['drowsiness_score'], 
                                         c=colors, s=100, alpha=0.75, edgecolors='black')
                                         
        ax_speed.set_xlabel("Vehicle Speed (km/h)", color="gray")
        ax_speed.set_ylabel("Drowsiness Score (%)", color="gray")
        ax_speed.set_xlim(min(df['speed']) - 10, max(df['speed']) + 10)
        ax_speed.set_ylim(-10, 110)
        ax_speed.grid(True, linestyle='--', alpha=0.3)
        
        # Final formatting
        plt.tight_layout()
        if save_plot:
            dashboard_path = os.path.join(outputs_dir, "analytics_dashboard.png")
            plt.savefig(dashboard_path, dpi=150)
            plt.close()
            print(f"[INFO] Dashboard analytics plot saved to: {dashboard_path}")
            
    except Exception as e:
        print(f"[ERROR] Failed to generate dashboard: {e}")
        import traceback
        traceback.print_exc()
