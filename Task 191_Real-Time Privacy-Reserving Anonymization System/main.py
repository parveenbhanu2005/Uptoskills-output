import cv2
import csv
from datetime import datetime
from ultralytics import YOLO

# 1. Load the YOLO-Pose model
model = YOLO('yolov8n-pose.pt')
video_name = 'data\\02.avi'
cap = cv2.VideoCapture(video_name)

# 2. Setup CSV report
csv_filename = 'surveillance_log.csv'
with open(csv_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Timestamp', 'Location', 'Track_ID', 'Detected Condition', 'Confidence Score', 'Risk Level'])

CONFIDENCE_THRESHOLD = 0.60
unique_footfall_ids = set()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
        
    # Enable tracking to assign anonymous consistent IDs across frames
    results = model.track(frame, persist=True, stream=True, verbose=False)
    
    for r in results:
        boxes = r.boxes
        
        if r.keypoints is not None and boxes is not None:
            keypoints = r.keypoints.xy.cpu().numpy()
            
            for i, (kp, box) in enumerate(zip(keypoints, boxes)):
                # Anonymous tracking ID
                track_id = int(box.id[0]) if box.id is not None else -1
                if track_id != -1:
                    unique_footfall_ids.add(track_id)
                
                conf_score = round(float(box.conf[0]), 2)
                bx1, by1, bx2, by2 = map(int, box.xyxy[0])
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Extract keypoints: Face (0-4), Shoulders (5-6), Hips (11-12)
                face_pts = kp[0:5]
                valid_face_pts = [pt for pt in face_pts if pt[0] > 0 and pt[1] > 0]
                
                # --- 1. Face Masking & Fail-Safe Logic ---
                if len(valid_face_pts) >= 2:
                    fx_coords = [pt[0] for pt in valid_face_pts]
                    fy_coords = [pt[1] for pt in valid_face_pts]
                    
                    fx1 = max(0, int(min(fx_coords)) - 25)
                    fy1 = max(0, int(min(fy_coords)) - 45)
                    fx2 = min(frame.shape[1], int(max(fx_coords)) + 25)
                    fy2 = min(frame.shape[0], int(max(fy_coords)) + 25)
                    
                    face_roi = frame[fy1:fy2, fx1:fx2]
                    if face_roi.shape[0] > 0 and face_roi.shape[1] > 0:
                        frame[fy1:fy2, fx1:fx2] = cv2.GaussianBlur(face_roi, (99, 99), 30)
                        
                    if conf_score >= CONFIDENCE_THRESHOLD:
                        condition = "Face & Credentials Masked"
                        risk_level = "LOW"
                    else:
                        condition = "Low Confidence Mask"
                        risk_level = "MEDIUM"
                else:
                    condition = "EXPOSURE RISK: Face Landmarks Missed"
                    risk_level = "HIGH"
                    
                    # Fallback upper-body blur
                    head_h = int((by2 - by1) * 0.35)
                    fallback_roi = frame[by1:by1 + head_h, bx1:bx2]
                    if fallback_roi.shape[0] > 0 and fallback_roi.shape[1] > 0:
                        frame[by1:by1 + head_h, bx1:bx2] = cv2.GaussianBlur(fallback_roi, (99, 99), 30)
                    
                    # On-screen warning
                    cv2.putText(frame, "ALERT: Unmasked Exposure Risk!", (30, 80),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # --- 2. ID Badge / Credential Area Masking ---
                l_shoulder, r_shoulder = kp[5], kp[6]
                if l_shoulder[0] > 0 and r_shoulder[0] > 0:
                    chest_x1 = max(0, int(min(l_shoulder[0], r_shoulder[0])) - 15)
                    chest_x2 = min(frame.shape[1], int(max(l_shoulder[0], r_shoulder[0])) + 15)
                    chest_y1 = max(0, int(min(l_shoulder[1], r_shoulder[1])))
                    
                    # Badge zone spans roughly 35% down the torso from shoulders
                    chest_height = int((by2 - by1) * 0.35)
                    chest_y2 = min(frame.shape[0], chest_y1 + chest_height)
                    
                    chest_roi = frame[chest_y1:chest_y2, chest_x1:chest_x2]
                    if chest_roi.shape[0] > 0 and chest_roi.shape[1] > 0:
                        # Pixelate/blur chest ID badge zone
                        frame[chest_y1:chest_y2, chest_x1:chest_x2] = cv2.GaussianBlur(chest_roi, (51, 51), 20)

                # Log row to CSV
                with open(csv_filename, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([current_time, 'Camera_Entrance_01', f"Person_{track_id}", condition, conf_score, risk_level])

    # --- 3. On-Screen Live Footfall Counter ---
    total_footfall = len(unique_footfall_ids)
    cv2.rectangle(frame, (20, 15), (280, 55), (0, 0, 0), -1)
    cv2.putText(frame, f"Footfall Count: {total_footfall}", (30, 42),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow('Privacy-Preserving CCTV Anonymization System', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()