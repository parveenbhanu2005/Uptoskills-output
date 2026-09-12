import os
import cv2
import numpy as np

def draw_pedestrian_sprite(img, x, y, color=(50, 50, 50)):
    """
    Draw a clean, isolated pedestrian silhouette with crisp boundary.
    """
    x, y = int(x), int(y)
    
    # Draw head
    cv2.circle(img, (x, y - 28), 7, (220, 200, 180), -1)
    cv2.circle(img, (x, y - 28), 7, (10, 10, 10), 1)

    # Draw body / torso
    cv2.rectangle(img, (x - 10, y - 20), (x + 10, y - 5), color, -1)
    cv2.rectangle(img, (x - 10, y - 20), (x + 10, y - 5), (10, 10, 10), 1)

    # Draw legs
    cv2.rectangle(img, (x - 8, y - 5), (x - 2, y + 12), (80, 60, 40), -1)
    cv2.rectangle(img, (x + 2, y - 5), (x + 8, y + 12), (80, 60, 40), -1)
    cv2.rectangle(img, (x - 8, y - 5), (x - 2, y + 12), (10, 10, 10), 1)
    cv2.rectangle(img, (x + 2, y - 5), (x + 8, y + 12), (10, 10, 10), 1)


def generate_synthetic_surveillance_video(output_path, num_frames=300, width=1280, height=720, fps=30):
    """
    Generates synthetic surveillance video with clearly distinguishable walking pedestrians.
    Scenario:
    - Phase 1 (Frames 0..90): Group A (3 peds) and Group B (3 peds) walk towards center from left and right.
    - Phase 2 (Frames 91..200): Group A and Group B merge into a single large cluster in center plaza.
    - Phase 3 (Frames 201..300): The cluster splits back into two separate groups moving apart.
    - Plus 2 solo background pedestrians.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print(f"[Video Generator] Generating synthetic surveillance video at: {output_path} ({num_frames} frames)...", flush=True)

    # Base background (plaza grid)
    bg = np.ones((height, width, 3), dtype=np.uint8) * 225
    for grid_x in range(0, width, 80):
        cv2.line(bg, (grid_x, 0), (grid_x, height), (210, 210, 210), 1)
    for grid_y in range(0, height, 80):
        cv2.line(bg, (0, grid_y), (width, grid_y), (210, 210, 210), 1)

    # Offset patterns for Group A and Group B members (spaced 60px apart so contours never merge)
    offset_A = [(-55, -40), (55, -40), (0, 40)]
    offset_B = [(-55, 40), (55, 40), (0, -40)]

    for frame_idx in range(num_frames):
        frame = bg.copy()
        
        # Camera HUD overlay
        cv2.putText(frame, f"CAM-01 SURVEILLANCE PLAZA | FRAME {frame_idx:04d}", (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 50, 50), 2)

        # Calculate centroids for Group A and Group B
        if frame_idx <= 90:
            # Phase 1: Moving towards center (Group A from left, Group B from right)
            t = frame_idx / 90.0
            cx_A = 180 + t * (480 - 180)  # 180 -> 480
            cy_A = 360
            cx_B = 1080 - t * (1080 - 720) # 1080 -> 720
            cy_B = 360
        elif frame_idx <= 200:
            # Phase 2: Merged in center (Group A & Group B close together at ~570 and ~640)
            t = (frame_idx - 90) / 110.0
            cx_A = 480 + t * (570 - 480)
            cy_A = 360 + t * (380 - 360)
            cx_B = 720 - t * (720 - 640)
            cy_B = 360 + t * (380 - 360)
        else:
            # Phase 3: Splitting (Group A moves Up-Left, Group B moves Down-Right)
            t = (frame_idx - 200) / 100.0
            cx_A = 570 - t * (570 - 250)
            cy_A = 380 - t * (380 - 180)
            cx_B = 640 + t * (980 - 640)
            cy_B = 380 + t * (580 - 380)

        # Draw Group A Pedestrians (Red shirts)
        for dx, dy in offset_A:
            draw_pedestrian_sprite(frame, cx_A + dx, cy_A + dy, color=(180, 50, 50))

        # Draw Group B Pedestrians (Blue shirts)
        for dx, dy in offset_B:
            draw_pedestrian_sprite(frame, cx_B + dx, cy_B + dy, color=(50, 50, 180))

        # Draw Solo Pedestrian 1 (top plaza)
        solo1_x = 100 + (frame_idx * 3.2) % 1080
        solo1_y = 100
        draw_pedestrian_sprite(frame, solo1_x, solo1_y, color=(50, 160, 50))

        # Draw Solo Pedestrian 2 (bottom plaza)
        solo2_x = 1180 - (frame_idx * 2.5) % 1080
        solo2_y = 650
        draw_pedestrian_sprite(frame, solo2_x, solo2_y, color=(160, 160, 50))

        out.write(frame)

    out.release()
    print(f"[Video Generator] Synthetic video successfully generated: {output_path}", flush=True)
    return output_path

if __name__ == "__main__":
    generate_synthetic_surveillance_video("data/input_video.mp4")
