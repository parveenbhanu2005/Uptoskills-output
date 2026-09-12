import os
import cv2
import json
import time
import argparse
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

from data_manager import DataManager
from alert_system import AlertSystem
from detector import WildlifeDetector
from simulator import generate_synthetic_surveillance_feed

def parse_args():
    parser = argparse.ArgumentParser(description="Wildlife Intrusion & Poaching Prevention System - Testing Engine")
    parser.add_argument("--input", "-i", type=str, default=None,
                        help="Path to input video file (e.g. mp4, avi). If not provided, a synthetic surveillance feed will be generated.")
    parser.add_argument("--conf", "-c", type=float, default=None,
                        help="Detection confidence threshold override (default: 0.50).")
    parser.add_argument("--mock-poacher", action="store_true",
                        help="Manually inject a poacher threat (carrying weapons) during human detections.")
    parser.add_argument("--generate-synthetic", action="store_true",
                        help="Force generate the synthetic surveillance video and run tests on it.")
    return parser.parse_args()

def process_video_feed(video_path, metadata_path, conf_override, mock_poacher, dm, alert_sys, detector):
    print(f"\n📹 Starting Surveillance Feed Analysis: {video_path}")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Error: Could not open video file at {video_path}")
        return
        
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_secs = total_frames / fps if fps > 0 else 0
    
    print(f"   Resolution: {width}x{height} | FPS: {fps:.2f} | Frames: {total_frames} | Duration: {duration_secs:.2f}s")
    
    # Load metadata if exists
    frame_metadata = None
    if metadata_path and os.path.exists(metadata_path):
        print(f"   ℹ️ Loading frame simulation metadata from: {os.path.basename(metadata_path)}")
        with open(metadata_path, 'r') as mf:
            frame_metadata = json.load(mf)
            
    # Video Writer
    output_filename = f"annotated_{os.path.basename(video_path)}"
    output_video_path = os.path.join(dm.output_dir, output_filename)
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out_video = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    # Overwrite confidence in config if overridden
    config = dm.get_config()
    if conf_override is not None:
        config['detection_threshold'] = conf_override
        print(f"   ℹ️ Confidence threshold overridden to: {conf_override:.2f}")
        
    # Analysis Metrics
    frame_idx = 0
    inference_times = []
    detections_by_class = {}
    severity_distribution = {"LOW": 0, "MEDIUM": 0, "CRITICAL": 0}
    timeline_data = [] # List of dicts: {'timestamp': float, 'class': str, 'conf': float, 'severity': str}
    
    t_pipeline_start = time.time()
    
    print("🚀 Running vision pipeline...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Get simulation metadata for this frame if available
        current_metadata = None
        if frame_metadata and str(frame_idx) in frame_metadata:
            current_metadata = frame_metadata[str(frame_idx)]
            
        # Run detection
        t_inf_start = time.time()
        annotated_frame, tracked_objects = detector.process_frame(
            frame=frame,
            metadata=current_metadata,
            custom_config=config,
            mock_weapon=mock_poacher
        )
        t_inf_elapsed = time.time() - t_inf_start
        inference_times.append(t_inf_elapsed)
        
        # Write to annotated output video
        out_video.write(annotated_frame)
        
        # Collect statistics
        timestamp = frame_idx / fps
        for obj in tracked_objects:
            cls_name = obj['class']
            sev = obj['severity']
            
            # Update counts
            detections_by_class[cls_name] = detections_by_class.get(cls_name, 0) + 1
            severity_distribution[sev] += 1
            
            # Record for chart
            timeline_data.append({
                'timestamp': timestamp,
                'class': cls_name,
                'conf': 0.95 if current_metadata else 0.90, # default conf if simulated
                'severity': sev
            })
            
        frame_idx += 1
        if frame_idx % 30 == 0 or frame_idx == total_frames:
            pct = (frame_idx / total_frames) * 100
            print(f"   Processed {frame_idx}/{total_frames} frames ({pct:.1f}%)")
            
    cap.release()
    out_video.release()
    t_pipeline_elapsed = time.time() - t_pipeline_start
    
    # Calculations
    avg_latency_ms = np.mean(inference_times) * 1000 if inference_times else 0
    avg_fps = 1.0 / np.mean(inference_times) if inference_times else 0
    overall_pipeline_fps = total_frames / t_pipeline_elapsed if t_pipeline_elapsed > 0 else 0
    
    print(f"✅ Pipeline complete! Output video saved to: {output_video_path}")
    
    # ----------------------------------------------------
    # Generate Confidence & Threat Timeline Chart (Matplotlib)
    # ----------------------------------------------------
    chart_path = os.path.join(dm.output_dir, "threat_detection_timeline.png")
    generate_timeline_chart(timeline_data, duration_secs, chart_path)
    
    # ----------------------------------------------------
    # Print Edge Surveillance Performance & Ecological Report
    # ----------------------------------------------------
    print("\n" + "="*60)
    print("📊 EDGE CAMERA SURVEILLANCE PERFORMANCE & DETECTION REPORT")
    print("="*60)
    print(f"1. HARDWARE LATENCY & SPEED:")
    print(f"   - Average Model Inference Latency: {avg_latency_ms:.2f} ms")
    print(f"   - Average Model Inference FPS:     {avg_fps:.1f} FPS")
    print(f"   - Pipeline Throughput (w/ I/O):    {overall_pipeline_fps:.1f} FPS")
    print()
    print(f"2. ECOLOGICAL COUNT STATISTICS:")
    if detections_by_class:
        for cls_name, count in detections_by_class.items():
            print(f"   - {cls_name.capitalize():12s}: {count} total bounding boxes")
    else:
        print("   - No wildlife/objects detected in the feed.")
    print()
    print(f"3. THREAT SEVERITY ANALYSIS:")
    print(f"   - Low Severity (Wildlife logs):   {severity_distribution['LOW']}")
    print(f"   - Medium Severity (Intrusions):   {severity_distribution['MEDIUM']}")
    print(f"   - Critical Severity (Poaching):   {severity_distribution['CRITICAL']}")
    print()
    print(f"4. EDGE DEVICE STORAGE & LOGS:")
    log_size = len(open(dm.log_file).readlines()) - 1 if os.path.exists(dm.log_file) else 0
    snapshots_count = len([n for n in os.listdir(dm.snapshots_dir) if n.lower().endswith('.jpg')])
    print(f"   - Total movement entries in CSV log: {log_size}")
    print(f"   - Compressed evidence snapshots saved: {snapshots_count}")
    print(f"   - CSV Log Location: {dm.log_file}")
    print(f"   - Timeline Chart Location: {chart_path}")
    print("="*60 + "\n")

def generate_timeline_chart(timeline_data, duration_secs, chart_path):
    """Generates a premium dark-themed scatter plot showing detections over time colored by threat level."""
    if not timeline_data:
        print("⚠️ No detection data to generate chart timeline.")
        return
        
    # Styled Dark Theme
    fig, ax = plt.subplots(figsize=(12, 5), facecolor='#111827')
    ax.set_facecolor('#1F2937')
    
    # Extract data
    times = [d['timestamp'] for d in timeline_data]
    confs = [d['conf'] for d in timeline_data]
    severities = [d['severity'] for d in timeline_data]
    classes = [d['class'] for d in timeline_data]
    
    # Map severities to colors and sizes
    colors_map = {'LOW': '#10B981', 'MEDIUM': '#F59E0B', 'CRITICAL': '#EF4444'} # Green, Amber, Red
    sizes_map = {'LOW': 30, 'MEDIUM': 60, 'CRITICAL': 100}
    
    plotted_labels = set()
    
    for i in range(len(timeline_data)):
        t = times[i]
        c = confs[i]
        sev = severities[i]
        cls = classes[i]
        
        lbl = f"{cls.upper()} ({sev})"
        label_to_show = lbl if lbl not in plotted_labels else None
        plotted_labels.add(lbl)
        
        ax.scatter(t, c, color=colors_map[sev], s=sizes_map[sev], label=label_to_show, alpha=0.85, edgecolors='white', linewidths=0.5, zorder=3)
        
    # Standard labels and decorations
    ax.set_title("Wildlife Surveillance: Threat Detection Timeline", color='white', fontsize=14, pad=15)
    ax.set_xlabel("Video Time (seconds)", color='#9CA3AF', fontsize=11, labelpad=8)
    ax.set_ylabel("Inference Confidence / Severity Marker", color='#9CA3AF', fontsize=11, labelpad=8)
    ax.set_xlim(0, max(duration_secs, 1.0))
    ax.set_ylim(0.4, 1.05)
    
    ax.tick_params(colors='#6B7280', labelsize=10)
    ax.spines[:].set_color('#374151')
    ax.yaxis.grid(True, color='#374151', linestyle='-', linewidth=0.5, zorder=0)
    ax.xaxis.grid(True, color='#374151', linestyle=':', linewidth=0.5, zorder=0)
    
    # Add threat zones
    ax.axhspan(0.4, 0.6, color='#10B981', alpha=0.04, label='Safe Reserve Monitoring')
    ax.axhspan(0.6, 0.8, color='#F59E0B', alpha=0.04, label='Intrusion Alert Zone')
    ax.axhspan(0.8, 1.05, color='#EF4444', alpha=0.04, label='Critical Poaching Response Zone')
    
    # Dedup legend
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='lower left', facecolor='#374151', edgecolor='#4B5563', labelcolor='white', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(chart_path, dpi=150, facecolor='#111827')
    plt.close()
    print(f"   📈 Saved threat timeline chart: {chart_path}")

def main():
    args = parse_args()
    
    # Initialize Core Managers
    dm = DataManager()
    alert_sys = AlertSystem(dm)
    detector = WildlifeDetector(dm, alert_sys)
    
    video_path = args.input
    metadata_path = None
    
    # Handle Input Setup
    if args.generate_synthetic or not video_path:
        print("ℹ️ Preparing synthetic night surveillance video feed...")
        video_path, metadata_path = generate_synthetic_surveillance_feed(dm.inputs_dir)
    else:
        # Check if the video path exists directly or in the Inputs folder
        resolved_path = video_path
        if not os.path.exists(resolved_path):
            resolved_path = os.path.join(dm.inputs_dir, video_path)
            
        if os.path.exists(resolved_path):
            video_path = resolved_path
            # Check for synthetic video metadata
            if os.path.basename(video_path) == "synthetic_surveillance.mp4":
                metadata_path = os.path.join(os.path.dirname(video_path), "synthetic_surveillance_metadata.json")
        else:
            print(f"❌ Error: Video file not found at '{video_path}' or inside '{dm.inputs_dir}'")
            return
            
    # Process the feed
    process_video_feed(
        video_path=video_path,
        metadata_path=metadata_path,
        conf_override=args.conf,
        mock_poacher=args.mock_poacher,
        dm=dm,
        alert_sys=alert_sys,
        detector=detector
    )

if __name__ == "__main__":
    main()
