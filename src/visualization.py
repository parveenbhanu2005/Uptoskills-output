import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
import config

# Color Palette for distinct visual group differentiation
GROUP_COLORS = [
    (255, 50, 50),    # Bright Blue (BGR)
    (50, 200, 50),    # Bright Green
    (50, 50, 255),    # Bright Red
    (200, 50, 200),   # Purple
    (50, 200, 200),   # Yellow
    (200, 150, 50),   # Cyan
    (255, 100, 0),    # Deep Blue
    (0, 165, 255),    # Orange
]

def get_group_color(group_id_str):
    if not group_id_str or group_id_str == "NONE":
        return (180, 180, 180)  # Neutral Gray for ungrouped individuals
    try:
        idx = int(group_id_str.replace("G", ""))
        return GROUP_COLORS[idx % len(GROUP_COLORS)]
    except:
        return (100, 255, 100)

def draw_hud(frame, frame_idx, total_frames, num_peds, num_groups, density, active_alerts, fps=30):
    """
    Draw a clean, professional surveillance HUD overlay on the frame.
    """
    h, w, _ = frame.shape
    
    # Top HUD Banner Background
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 80), (15, 15, 15), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    # HUD Metrics
    title_text = f"CROWD SURVEILLANCE & GROUP DETECTOR | FPS: {fps:.1f}"
    cv2.putText(frame, title_text, (20, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    stats_text = f"FRAME: {frame_idx}/{total_frames}  |  PEDESTRIANS: {num_peds}  |  GROUPS: {num_groups}  |  DENSITY: {density:.4f}"
    cv2.putText(frame, stats_text, (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 230, 255), 2)

    # Display real-time alert banner at bottom if recent alert exists
    if len(active_alerts) > 0:
        latest = active_alerts[-1]
        banner_color = (0, 0, 220) if latest['event_type'] == 'GROUP_MERGED' else (
            (0, 140, 255) if latest['event_type'] == 'GROUP_SPLIT' else (0, 180, 0)
        )
        
        banner_overlay = frame.copy()
        cv2.rectangle(banner_overlay, (0, h - 50), (w, h), banner_color, -1)
        cv2.addWeighted(banner_overlay, 0.85, frame, 0.15, 0, frame)
        
        cv2.putText(frame, f"EVENT ALERT: {latest['event_type']} — {latest['message']}",
                    (20, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

def annotate_frame(frame, tracked_pedestrians, groups, frame_idx, total_frames, density, recent_alerts, fps=30):
    """
    Annotate frame with pedestrian bboxes, person IDs, group IDs, convex hulls, and HUD.
    """
    annotated = frame.copy()
    
    # Map track_id to group_id
    track_to_group = {}
    for g in groups:
        gid = g['group_id']
        for tid in g['member_track_ids']:
            track_to_group[tid] = gid

    # Draw Group Region Hulls / Ellipses
    for g in groups:
        peds = g['pedestrians']
        if len(peds) >= 2:
            pts = np.array([p['bottom_center'] for p in peds], dtype=np.int32)
            color = get_group_color(g['group_id'])
            
            if len(pts) >= 3:
                hull = cv2.convexHull(pts)
                # Draw translucent group polygon
                poly_mask = annotated.copy()
                cv2.fillPoly(poly_mask, [hull], color)
                cv2.addWeighted(poly_mask, 0.25, annotated, 0.75, 0, annotated)
                cv2.polylines(annotated, [hull], True, color, 2)
            else:
                # 2 points -> draw line / ellipse
                pt1, pt2 = tuple(pts[0]), tuple(pts[1])
                cv2.line(annotated, pt1, pt2, color, 2)

            # Group Label Centroid
            cx, cy = int(g['center'][0]), int(g['center'][1])
            status_str = "STABLE GROUP" if g['is_stable'] else "FORMING"
            group_label = f"Group: {g['group_id']} ({len(peds)} peds) [{status_str}]"
            
            # Label background box
            (lw, lh), _ = cv2.getTextSize(group_label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(annotated, (cx - lw//2 - 5, cy - 20), (cx + lw//2 + 5, cy), (20, 20, 20), -1)
            cv2.putText(annotated, group_label, (cx - lw//2, cy - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # Draw Pedestrian Bounding Boxes and Labels
    for ped in tracked_pedestrians:
        tid = ped['track_id']
        x1, y1, x2, y2 = map(int, ped['bbox'])
        gid = track_to_group.get(tid, "NONE")
        color = get_group_color(gid)

        # Draw bounding box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

        # Draw trajectory history
        hist = ped.get('history', [])
        if len(hist) > 1:
            pts = np.array(hist, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(annotated, [pts], False, color, 1)

        # Pedestrian Tag Box
        tag_text = f"Person ID: {tid} | Group ID: {gid}"
        (tw, th), _ = cv2.getTextSize(tag_text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
        cv2.rectangle(annotated, (x1, max(0, y1 - 18)), (x1 + tw + 6, max(18, y1)), color, -1)
        cv2.putText(annotated, tag_text, (x1 + 3, max(12, y1 - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    # Draw HUD Overlay
    draw_hud(annotated, frame_idx, total_frames, len(tracked_pedestrians), len(groups), density, recent_alerts, fps)

    return annotated


def generate_visualization_plots(csv_records, alerts, output_dir=config.OUTPUT_DIR):
    """
    Generate meaningful analysis charts (PNG plots) from processing results:
    1. outputs/group_analysis.png
    2. outputs/crowd_density.png
    3. outputs/group_events.png
    """
    os.makedirs(output_dir, exist_ok=True)
    
    frames = [r['frame_number'] for r in csv_records]
    ped_counts = [r['pedestrian_count'] for r in csv_records]
    group_counts = [r['group_count'] for r in csv_records]
    densities = [r['pedestrian_count'] / 100.0 for r in csv_records]  # scaled density metric

    # PLOT 1: Group Analysis
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.set_title("Pedestrian & Group Dynamics Over Time", fontsize=14, fontweight='bold')
    ax1.plot(frames, ped_counts, label="Total Pedestrians", color="blue", linewidth=2)
    ax1.set_xlabel("Frame Number")
    ax1.set_ylabel("Pedestrian Count", color="blue")
    ax1.tick_params(axis='y', labelcolor="blue")
    ax1.grid(True, linestyle="--", alpha=0.5)

    ax2 = ax1.twinx()
    ax2.plot(frames, group_counts, label="Active Groups", color="green", linewidth=2, linestyle="--")
    ax2.set_ylabel("Group Count", color="green")
    ax2.tick_params(axis='y', labelcolor="green")

    fig.tight_layout()
    plot1_path = os.path.join(output_dir, "group_analysis.png")
    plt.savefig(plot1_path, dpi=200)
    plt.close()

    # PLOT 2: Crowd Density Trend
    plt.figure(figsize=(10, 5))
    plt.plot(frames, densities, color="purple", linewidth=2, label="Crowd Density Metric")
    plt.axhline(y=config.CROWD_DENSITY_THRESHOLD * 10000, color="red", linestyle=":", label="High Density Threshold")
    plt.title("Crowd Density Over Video Duration", fontsize=14, fontweight='bold')
    plt.xlabel("Frame Number")
    plt.ylabel("Density Metric (Pedestrians / Unit Area)")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plot2_path = os.path.join(output_dir, "crowd_density.png")
    plt.savefig(plot2_path, dpi=200)
    plt.close()

    # PLOT 3: Group Events Timeline
    plt.figure(figsize=(10, 5))
    merge_frames = [a['frame_number'] for a in alerts if a['event_type'] == 'GROUP_MERGED']
    split_frames = [a['frame_number'] for a in alerts if a['event_type'] == 'GROUP_SPLIT']
    stable_frames = [a['frame_number'] for a in alerts if a['event_type'] == 'STABLE_GROUP']

    plt.scatter(merge_frames, [2]*len(merge_frames), color="red", s=120, label="Group Merged", zorder=3)
    plt.scatter(split_frames, [1]*len(split_frames), color="orange", s=120, label="Group Split", zorder=3)
    plt.scatter(stable_frames, [0]*len(stable_frames), color="green", s=100, label="Stable Group", zorder=3)

    plt.yticks([0, 1, 2], ["STABLE_GROUP", "GROUP_SPLIT", "GROUP_MERGED"])
    plt.title("Surveillance Event Timeline (Merge & Split Events)", fontsize=14, fontweight='bold')
    plt.xlabel("Frame Number")
    plt.xlim(0, max(frames) if len(frames) > 0 else 100)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(loc="upper right")
    plt.tight_layout()
    plot3_path = os.path.join(output_dir, "group_events.png")
    plt.savefig(plot3_path, dpi=200)
    plt.close()

    print(f"[Visualization] PNG plots successfully saved to {output_dir}")
