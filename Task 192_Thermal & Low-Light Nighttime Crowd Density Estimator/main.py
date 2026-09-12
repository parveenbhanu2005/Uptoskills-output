import cv2
import csv
import numpy as np
from datetime import datetime
from ultralytics import YOLO

# 1. Configuration Setup
MODEL_WEIGHTS = 'runs/detect/train-2/weights/best.pt'
VIDEO_SOURCE = 'data/1.mp4'  # Replace with your video file
CSV_FILE = 'nighttime_crowd_log.csv'
CROWD_LIMIT = 5
LOCATION_ID = "Zone_A_North"

model = YOLO(MODEL_WEIGHTS)
cap = cv2.VideoCapture(VIDEO_SOURCE)

# Create a resizable display window
cv2.namedWindow('Thermal Density Estimator', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Thermal Density Estimator', 960, 540)

with open(CSV_FILE, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Timestamp', 'Location', 'Detected Condition', 'Confidence Score', 'Count'])

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, conf=0.45, iou=0.45, verbose=False)
    
    current_count = 0
    confidence_sum = 0
    
    # Initialize a blank grayscale mask for the heatmap
    heatmap_mask = np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)
    
    for r in results:
        for box in r.boxes:
            current_count += 1
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            confidence_sum += conf
            
            centroid_x, centroid_y = int((x1 + x2) / 2), int((y1 + y2) / 2)
            
            # Draw bounding boxes and centroids
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(heatmap_mask, (centroid_x, centroid_y), radius=40, color=50, thickness=-1)

    # Process and Apply Density Map
    if current_count > 0:
        heatmap_mask = cv2.GaussianBlur(heatmap_mask, (71, 71), 0)
        heatmap_mask = cv2.normalize(heatmap_mask, None, 0, 255, cv2.NORM_MINMAX)
        color_heatmap = cv2.applyColorMap(heatmap_mask, cv2.COLORMAP_JET)
        
        mask_boolean = heatmap_mask > 5
        frame[mask_boolean] = cv2.addWeighted(frame, 0.6, color_heatmap, 0.4, 0)[mask_boolean]

        # Log Data
        avg_conf = round(confidence_sum / current_count, 2)
        condition = "Threshold Breached" if current_count > CROWD_LIMIT else "Normal"
        
        with open(CSV_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), LOCATION_ID, condition, avg_conf, current_count])
            
        # Draw Alert Banner
        alert_color = (0, 0, 255) if condition == "Threshold Breached" else (0, 255, 0)
        cv2.rectangle(frame, (10, 10), (450, 70), alert_color, -1)
        cv2.putText(frame, f"Density Count: {current_count} | {condition}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    cv2.imshow('Thermal Density Estimator', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()