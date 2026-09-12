import os
import cv2
import json
import numpy as np

def generate_synthetic_surveillance_feed(output_dir):
    """
    Generates:
    1. synthetic_surveillance.mp4: 15-second 640x480 night video of a forest with moving blobs.
    2. synthetic_surveillance_metadata.json: Bounding boxes and labels for each frame.
    """
    os.makedirs(output_dir, exist_ok=True)
    video_path = os.path.join(output_dir, "synthetic_surveillance.mp4")
    metadata_path = os.path.join(output_dir, "synthetic_surveillance_metadata.json")
    
    width, height = 640, 480
    fps = 20
    duration_secs = 15
    total_frames = fps * duration_secs  # 300 frames
    
    # Video Writer
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
    
    metadata = {}
    
    print("🎬 Generating synthetic night surveillance video...")
    
    for f in range(total_frames):
        # 1. Background: Dark night forest (very cool thermal signature)
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = (20, 15, 10)  # Very dark BGR
        
        # Add static environmental elements (cool trees/bushes - BGR (15, 30, 15))
        # Tree 1
        cv2.circle(frame, (100, 180), 50, (15, 35, 15), -1)
        cv2.rectangle(frame, (95, 180), (105, 260), (10, 20, 10), -1)
        # Tree 2
        cv2.circle(frame, (540, 150), 60, (12, 32, 12), -1)
        cv2.rectangle(frame, (535, 150), (545, 250), (10, 20, 10), -1)
        # Bush
        cv2.ellipse(frame, (300, 420), (80, 30), 0, 0, 360, (18, 40, 18), -1)
        
        frame_detections = []
        
        # 2. Moving Object 1: Elephant (Slow moving animal at the bottom)
        # Active: Frame 0 to 200
        if 0 <= f <= 200:
            # Centroid path: x starts at 50, goes to 380. y starts at 360, goes to 390.
            progress = f / 200.0
            cx = int(50 + progress * 330)
            cy = int(360 + progress * 30)
            
            # Draw Elephant (Warm grey body + head)
            body_w, body_h = 70, 45
            cv2.ellipse(frame, (cx, cy), (body_w // 2, body_h // 2), 0, 0, 360, (75, 80, 85), -1) # BGR
            cv2.circle(frame, (cx + 30, cy - 10), 18, (70, 75, 80), -1) # head
            cv2.rectangle(frame, (cx - 20, cy + 15), (cx - 10, cy + 30), (60, 65, 70), -1) # leg
            cv2.rectangle(frame, (cx + 10, cy + 15), (cx + 20, cy + 30), (60, 65, 70), -1) # leg
            
            # Bounding box
            x1, y1 = cx - 40, cy - 28
            x2, y2 = cx + 48, cy + 30
            frame_detections.append({
                'class': 'elephant',
                'bbox': [x1, y1, x2, y2],
                'conf': 0.92,
                'is_carrying_equipment': False
            })
            
        # 3. Moving Object 2: Ranger/Patrol Vehicle (Fast moving across)
        # Active: Frame 60 to 180
        if 60 <= f <= 180:
            progress = (f - 60) / 120.0
            cx = int(-80 + progress * (width + 160))
            cy = 270
            
            # Draw Vehicle (Hot white/yellow engine/wheels)
            cv2.rectangle(frame, (cx - 45, cy - 15), (cx + 45, cy + 15), (140, 140, 145), -1)
            cv2.circle(frame, (cx - 25, cy + 15), 10, (190, 190, 200), -1) # wheel (hot friction)
            cv2.circle(frame, (cx + 25, cy + 15), 10, (190, 190, 200), -1) # wheel
            cv2.rectangle(frame, (cx - 20, cy - 25), (cx + 20, cy - 15), (100, 100, 105), -1) # cabin
            
            x1, y1 = cx - 45, cy - 25
            x2, y2 = cx + 45, cy + 25
            frame_detections.append({
                'class': 'vehicle',
                'bbox': [x1, y1, x2, y2],
                'conf': 0.96,
                'is_carrying_equipment': False
            })
            
        # 4. Moving Object 3: Armed Poacher (Human walking top-to-bottom, crosses perimeter y=240 at f=220)
        # Active: Frame 130 to 300
        if 130 <= f <= 300:
            progress = (f - 130) / 170.0
            cx = 320
            # Walks from y=30 to y=380
            cy = int(30 + progress * 350)
            
            # Draw Human (Hot signature core, red/yellow)
            # Head
            cv2.circle(frame, (cx, cy - 25), 8, (60, 60, 210), -1)
            # Body
            cv2.ellipse(frame, (cx, cy), (10, 20), 0, 0, 360, (50, 55, 230), -1)
            # Legs
            cv2.line(frame, (cx - 5, cy + 20), (cx - 8, cy + 40), (40, 40, 190), 3)
            cv2.line(frame, (cx + 5, cy + 20), (cx + 8, cy + 40), (40, 40, 190), 3)
            # Weapon/Rifle carried (Thin white line representing rifle thermal signature)
            cv2.line(frame, (cx - 15, cy - 5), (cx + 10, cy - 15), (220, 220, 220), 2)
            
            x1, y1 = cx - 18, cy - 33
            x2, y2 = cx + 15, cy + 40
            frame_detections.append({
                'class': 'human',
                'bbox': [x1, y1, x2, y2],
                'conf': 0.89,
                'is_carrying_equipment': True # Armed poacher carrying rifle
            })
            
        # Write Frame to Video
        out.write(frame)
        
        # Save frame metadata (1-indexed to match video frame counts easily or 0-indexed)
        metadata[str(f)] = frame_detections
        
    out.release()
    
    # Save Metadata JSON
    with open(metadata_path, 'w') as jf:
        json.dump(metadata, jf, indent=4)
        
    print(f"✅ Generated synthetic video: {video_path}")
    print(f"✅ Generated synthetic metadata: {metadata_path}")
    
    return video_path, metadata_path

if __name__ == "__main__":
    import sys
    base_dir = os.path.dirname(os.path.abspath(__file__))
    generate_synthetic_surveillance_feed(os.path.join(base_dir, "data"))
