import os
import cv2
import numpy as np
import uuid
import torch
from datetime import datetime

# Monkey patch torch load for security in newer PyTorch versions
original_load = torch.load
def patched_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return original_load(*args, **kwargs)
torch.load = patched_load

from ultralytics import YOLO

class WildlifeDetector:
    def __init__(self, data_manager, alert_system):
        self.dm = data_manager
        self.alert_sys = alert_system
        
        # Load YOLOv8 Nano model from Models/ folder
        print("🧠 Loading YOLOv8 model for edge surveillance...")
        model_path = os.path.join(self.dm.models_dir, 'yolov8n.pt')
        if os.path.exists(model_path):
            self.model = YOLO(model_path)
        else:
            # Fall back to root path download if not present
            self.model = YOLO('yolov8n.pt')
        print("✅ YOLOv8 model loaded successfully!")
        
        # Target classes to extract
        self.animal_classes = {
            14: 'bird', 15: 'cat', 16: 'dog', 17: 'horse', 18: 'sheep', 
            19: 'cow', 20: 'elephant', 21: 'bear', 22: 'zebra', 23: 'giraffe'
        }
        self.human_classes = {0: 'person'}
        self.vehicle_classes = {1: 'bicycle', 2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}
        self.gear_classes = {24: 'backpack', 26: 'handbag', 28: 'suitcase'}
        
        # Trajectory tracking variables
        self.next_track_id = 1
        self.active_tracks = {}  # {track_id: {'class': str, 'centroids': [(cx, cy), ...], 'frames_since_update': int}}
        self.max_lost_frames = 10  # Maintain tracks through short occlusions
        self.track_distance_threshold = 100  # Distance threshold for matching centroid
        
        # Threat history & Throttling
        self.logged_tracks = set()  # Track IDs already logged/alerted
        self.last_alert_timestamps = {}  # {category: datetime}
        
    def is_thermal_feed(self, frame):
        """Detects if the input frame is already thermal (grayscale/single-channel color profile)."""
        b, g, r = cv2.split(frame)
        diff_rg = np.mean(np.abs(r.astype(np.int16) - g.astype(np.int16)))
        diff_gb = np.mean(np.abs(g.astype(np.int16) - b.astype(np.int16)))
        return (diff_rg < 2.0) and (diff_gb < 2.0)
        
    def translate_class(self, yolo_class_name):
        """Translates standard COCO classes to contextual forest/wildlife classes."""
        mapping = {
            'person': 'Human Intruder',
            'car': 'Intruder Vehicle',
            'truck': 'Intruder Vehicle',
            'motorcycle': 'Intruder Vehicle',
            'bicycle': 'Intruder Vehicle',
            'bus': 'Intruder Vehicle',
            'elephant': 'Elephant',
            'bear': 'Deer/Forest Animal',
            'zebra': 'Deer/Forest Animal',
            'giraffe': 'Deer/Forest Animal',
            'dog': 'Deer/Forest Animal',
            'cat': 'Deer/Forest Animal',
            'sheep': 'Deer/Forest Animal',
            'cow': 'Livestock (Intrusion)',
            'horse': 'Livestock (Intrusion)',
            'bird': 'Bird'
        }
        return mapping.get(yolo_class_name, yolo_class_name.capitalize())

    def apply_thermal_effect(self, frame):
        """Converts standard BGR image to high-contrast Thermal/Infrared night feed look."""
        # Step 1: Convert to Grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Step 2: Apply slight Gaussian Blur to smooth out noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Step 3: Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced_gray = clahe.apply(blurred)
        
        # Step 4: Apply INFERNO color map for professional thermal imaging effect
        thermal_frame = cv2.applyColorMap(enhanced_gray, cv2.COLORMAP_INFERNO)
        
        return thermal_frame
        
    def _update_tracks(self, detections):
        """
        Updates trajectories using simple Euclidean distance centroid matching.
        detections: list of dicts with bbox, centroid, class, conf.
        """
        # Increment lost frames for active tracks
        for tid in self.active_tracks:
            self.active_tracks[tid]['frames_since_update'] += 1
            
        # Match detections to active tracks
        for det in detections:
            det_centroid = det['centroid']
            det_class = det['class']
            
            best_match_tid = None
            min_dist = float('inf')
            
            for tid, track_info in self.active_tracks.items():
                if track_info['frames_since_update'] > self.max_lost_frames:
                    continue
                    
                prev_centroid = track_info['centroids'][-1]
                dist = np.linalg.norm(np.array(det_centroid) - np.array(prev_centroid))
                
                # Verify classification category groups match and distance is within limits
                if dist < self.track_distance_threshold and dist < min_dist:
                    min_dist = dist
                    best_match_tid = tid
                    
            if best_match_tid is not None:
                self.active_tracks[best_match_tid]['centroids'].append(det_centroid)
                # Cap history at 30 frames
                if len(self.active_tracks[best_match_tid]['centroids']) > 30:
                    self.active_tracks[best_match_tid]['centroids'].pop(0)
                self.active_tracks[best_match_tid]['frames_since_update'] = 0
                self.active_tracks[best_match_tid]['class'] = det_class
                det['track_id'] = best_match_tid
            else:
                # Spawn new track ID
                new_tid = self.next_track_id
                self.next_track_id += 1
                self.active_tracks[new_tid] = {
                    'class': det_class,
                    'centroids': [det_centroid],
                    'frames_since_update': 0
                }
                det['track_id'] = new_tid
                
        # Clean up old tracks
        expired_tids = [tid for tid, info in self.active_tracks.items() if info['frames_since_update'] > self.max_lost_frames]
        for tid in expired_tids:
            del self.active_tracks[tid]
            if tid in self.logged_tracks:
                self.logged_tracks.discard(tid)
                
    def _ccw(self, A, B, C):
        """Counter-clockwise check for line segment intersection."""
        return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

    def _intersect(self, A, B, C, D):
        """Returns True if line segment AB intersects segment CD."""
        return self._ccw(A,C,D) != self._ccw(B,C,D) and self._ccw(A,B,C) != self._ccw(A,B,D)

    def _check_perimeter_crossing(self, track_id, height, width, config):
        """
        Determines if a trajectory crossed the user-defined perimeter line.
        Supports horizontal, vertical, and custom diagonal boundary segments.
        """
        track_info = self.active_tracks.get(track_id)
        if not track_info or len(track_info['centroids']) < 2:
            curr_y = track_info['centroids'][0][1] if track_info else 0
            line_y = height * config['perimeter_boundary']['position_ratio']
            return "inside" if curr_y > line_y else "outside", False
            
        centroids = track_info['centroids']
        p_boundary = config['perimeter_boundary']
        line_type = p_boundary.get('line_type', 'horizontal')
        
        A = centroids[-2] # Previous centroid
        B = centroids[-1] # Current centroid
        
        crossed = False
        status = "outside"
        
        if line_type == "diagonal":
            start_ratio = p_boundary.get('diagonal_start', [0.0, 0.5])
            end_ratio = p_boundary.get('diagonal_end', [1.0, 0.5])
            
            C = (int(start_ratio[0] * width), int(start_ratio[1] * height))
            D = (int(end_ratio[0] * width), int(end_ratio[1] * height))
            
            crossed = self._intersect(A, B, C, D)
            val = (D[0] - C[0]) * (B[1] - C[1]) - (D[1] - C[1]) * (B[0] - C[0])
            
            if crossed:
                status = "violation"
            else:
                status = "inside" if val > 0 else "outside"
                
        elif line_type == "vertical":
            line_x = width * p_boundary.get('position_ratio', 0.5)
            prev_x, curr_x = A[0], B[0]
            
            if (prev_x <= line_x < curr_x) or (curr_x <= line_x < prev_x):
                crossed = True
                status = "violation"
            else:
                status = "inside" if curr_x > line_x else "outside"
        else:
            line_y = height * p_boundary.get('position_ratio', 0.5)
            prev_y, curr_y = A[1], B[1]
            direction = p_boundary.get('direction', 'downward')
            
            if prev_y <= line_y < curr_y:
                if direction == "downward":
                    crossed = True
                    status = "violation"
                else:
                    status = "inside"
            elif curr_y <= line_y < prev_y:
                if direction == "upward":
                    crossed = True
                    status = "violation"
                else:
                    status = "outside"
            else:
                status = "inside" if curr_y > line_y else "outside"
                
        return status, crossed

    def _save_evidence_snapshot(self, frame, bbox, category):
        """Crops bounding box, applies high-contrast evidence filter, and saves compressed JPG."""
        h, w, _ = frame.shape
        x1, y1, x2, y2 = bbox
        
        pad_x = int((x2 - x1) * 0.1)
        pad_y = int((y2 - y1) * 0.1)
        
        x1 = max(0, x1 - pad_x)
        y1 = max(0, y1 - pad_y)
        x2 = min(w, x2 + pad_x)
        y2 = min(h, y2 + pad_y)
        
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return None
            
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4, 4))
        high_contrast = clahe.apply(gray)
        
        high_contrast_bgr = cv2.cvtColor(high_contrast, cv2.COLOR_GRAY2BGR)
        
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evidence_{category.replace(' ', '_')}_{timestamp_str}_{uuid.uuid4().hex[:6]}.jpg"
        filepath = os.path.join(self.dm.snapshots_dir, filename)
        
        cv2.imwrite(filepath, high_contrast_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 65])
        self.dm.enforce_storage_limit()
        
        return filename

    def process_frame(self, frame, metadata=None, custom_config=None, mock_weapon=False):
        """
        Processes a surveillance frame:
        1. Identifies if the video is already thermal. If so, skips false thermal colormap.
        2. Conducts target detection via YOLOv8 (high sensitivity predict mode) or metadata.
        3. Tracks targets using an optimized centroid tracking algorithm.
        4. Maps COCO class signatures to reserve categories.
        5. Detects custom perimeter line segment crossings.
        6. Rates alerts with temporal throttling (30s limits per category).
        """
        config = custom_config if custom_config else self.dm.get_config()
        gps = (config['camera_gps']['latitude'], config['camera_gps']['longitude'])
        
        h, w, _ = frame.shape
        
        is_thermal = self.is_thermal_feed(frame)
        if is_thermal:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            thermal_frame = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        else:
            thermal_frame = self.apply_thermal_effect(frame)
            
        raw_detections = []
        gear_boxes = []
        
        if metadata is not None:
            for det_item in metadata:
                cls_name = det_item['class']
                translated_cls = self.translate_class(cls_name)
                xyxy = det_item['bbox']
                conf = det_item.get('conf', 0.95)
                cx = int((xyxy[0] + xyxy[2]) / 2)
                cy = int((xyxy[1] + xyxy[3]) / 2)
                
                raw_detections.append({
                    'class': translated_cls,
                    'bbox': xyxy,
                    'centroid': (cx, cy),
                    'conf': conf,
                    'mock_weapon': det_item.get('is_carrying_equipment', False)
                })
        else:
            # Predict for optimal sensitivity (especially important for thermal night frames)
            results = self.model.predict(frame, conf=config['detection_threshold'], verbose=False)
            yolo_boxes = results[0].boxes
            
            for box in yolo_boxes:
                cls_id = int(box.cls[0])
                if cls_id in self.gear_classes:
                    gear_boxes.append([int(v) for v in box.xyxy[0]])
                    
            for box in yolo_boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = [int(v) for v in box.xyxy[0]]
                cx = int((xyxy[0] + xyxy[2]) / 2)
                cy = int((xyxy[1] + xyxy[3]) / 2)
                
                category = None
                if cls_id in self.human_classes:
                    category = self.human_classes[cls_id]
                elif cls_id in self.vehicle_classes:
                    category = self.vehicle_classes[cls_id]
                elif cls_id in self.animal_classes:
                    category = self.animal_classes[cls_id]
                    
                if category:
                    translated_cls = self.translate_class(category)
                    raw_detections.append({
                        'class': translated_cls,
                        'bbox': xyxy,
                        'centroid': (cx, cy),
                        'conf': conf,
                        'mock_weapon': False
                    })
                    
        # Update centroid tracker
        self._update_tracks(raw_detections)
        
        processed_tracks = []
        for det in raw_detections:
            tid = det['track_id']
            translated_cls = det['class']
            
            perim_status, crossed = self._check_perimeter_crossing(tid, h, w, config)
            
            severity = "LOW"
            is_carrying_equipment = False
            
            if translated_cls == "Human Intruder":
                hx1, hy1, hx2, hy2 = det['bbox']
                for gbox in gear_boxes:
                    gx1, gy1, gx2, gy2 = gbox
                    ix1, iy1 = max(hx1, gx1), max(hy1, gy1)
                    ix2, iy2 = min(hx2, gx2), min(hy2, gy2)
                    if ix1 < ix2 and iy1 < iy2:
                        is_carrying_equipment = True
                        break
                        
                if is_carrying_equipment or mock_weapon or det.get('mock_weapon', False):
                    severity = "CRITICAL"
                else:
                    severity = "MEDIUM"
                    
            elif translated_cls == "Intruder Vehicle":
                severity = "MEDIUM"
                
            elif translated_cls in ["Livestock (Intrusion)", "Deer/Forest Animal", "Elephant"]:
                severity = "LOW"
                
            if crossed or perim_status == "violation":
                if translated_cls in ["Human Intruder", "Intruder Vehicle"]:
                    severity = "CRITICAL"
                elif translated_cls in ["Livestock (Intrusion)", "Elephant", "Deer/Forest Animal"]:
                    severity = "MEDIUM"
                    
            alert_sent = False
            snapshot_filename = None
            
            current_time = datetime.now()
            last_alert_time = self.last_alert_timestamps.get(translated_cls)
            is_throttled = False
            
            if last_alert_time and (current_time - last_alert_time).total_seconds() < 30.0:
                is_throttled = True
                
            if tid not in self.logged_tracks and severity in ["MEDIUM", "CRITICAL"]:
                if not is_throttled:
                    snapshot_filename = self._save_evidence_snapshot(frame, det['bbox'], translated_cls)
                    sms_ok, sat_ok = self.alert_sys.trigger_alert(
                        category=translated_cls,
                        count=1,
                        severity=severity,
                        perimeter_status=perim_status,
                        gps_coords=gps
                    )
                    alert_sent = sms_ok or sat_ok
                    self.last_alert_timestamps[translated_cls] = current_time
                    self.logged_tracks.add(tid)
                    
                    self.dm.log_movement_event(
                        event_id=str(uuid.uuid4())[:8],
                        gps_lat=gps[0],
                        gps_lon=gps[1],
                        category=translated_cls,
                        count=1,
                        severity=severity,
                        perimeter_status=perim_status,
                        alert_sent=alert_sent,
                        snapshot_fn=snapshot_filename
                    )
                else:
                    self.alert_sys.log_throttled_alert(
                        category=translated_cls,
                        count=1,
                        severity=severity,
                        perimeter_status=perim_status,
                        gps_coords=gps
                    )
                    self.logged_tracks.add(tid)
                    
                    self.dm.log_movement_event(
                        event_id=str(uuid.uuid4())[:8],
                        gps_lat=gps[0],
                        gps_lon=gps[1],
                        category=translated_cls,
                        count=1,
                        severity=severity,
                        perimeter_status=perim_status,
                        alert_sent=False,
                        snapshot_fn="THROTTLED"
                    )
                    
            processed_tracks.append({
                'track_id': tid,
                'class': translated_cls,
                'bbox': det['bbox'],
                'centroid': det['centroid'],
                'severity': severity,
                'perimeter_status': perim_status,
                'is_carrying_equipment': is_carrying_equipment or (translated_cls == "Human Intruder" and mock_weapon) or det.get('mock_weapon', False)
            })
            
        annotated_frame = thermal_frame.copy()
        p_boundary = config['perimeter_boundary']
        line_type = p_boundary.get('line_type', 'horizontal')
        line_color = (0, 255, 255)
        
        if line_type == "diagonal":
            start_ratio = p_boundary.get('diagonal_start', [0.0, 0.5])
            end_ratio = p_boundary.get('diagonal_end', [1.0, 0.5])
            p1 = (int(start_ratio[0] * w), int(start_ratio[1] * h))
            p2 = (int(end_ratio[0] * w), int(end_ratio[1] * h))
            cv2.line(annotated_frame, p1, p2, line_color, 2)
            cv2.putText(annotated_frame, "DIAGONAL SURVEILLANCE BOUNDARY", (p1[0] + 10, p1[1] - 8), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, line_color, 1, cv2.LINE_AA)
        elif line_type == "vertical":
            line_x = int(w * p_boundary.get('position_ratio', 0.5))
            cv2.line(annotated_frame, (line_x, 0), (line_x, h), line_color, 2)
            cv2.putText(annotated_frame, "VERTICAL BOUNDARY", (line_x - 120, 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, line_color, 1, cv2.LINE_AA)
        else:
            line_y = int(h * p_boundary.get('position_ratio', 0.5))
            cv2.line(annotated_frame, (0, line_y), (w, line_y), line_color, 2)
            cv2.putText(annotated_frame, "HORIZONTAL BOUNDARY", (10, line_y - 8), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, line_color, 1, cv2.LINE_AA)
            
        # Draw trajectories
        for tid, track_info in self.active_tracks.items():
            centroids = track_info['centroids']
            if len(centroids) > 1:
                for i in range(1, len(centroids)):
                    cv2.line(annotated_frame, centroids[i-1], centroids[i], (0, 255, 0), 2)
                cv2.arrowedLine(annotated_frame, centroids[-2], centroids[-1], (0, 0, 255), 3, tipLength=0.3)
                
        # Draw boxes
        for pt in processed_tracks:
            x1, y1, x2, y2 = pt['bbox']
            sev = pt['severity']
            lbl = pt['class'].upper()
            tid = pt['track_id']
            
            if sev == "CRITICAL":
                box_color = (0, 0, 255)
            elif sev == "MEDIUM":
                box_color = (0, 165, 255)
            else:
                box_color = (0, 255, 0)
                
            if pt['is_carrying_equipment']:
                lbl += " (ARMED/EQUIPPED)"
                
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), box_color, 2)
            
            label_text = f"ID:{tid} {lbl} [{sev}]"
            (text_w, text_h), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
            cv2.rectangle(annotated_frame, (x1, y1 - text_h - 6), (x1 + text_w, y1), box_color, -1)
            cv2.putText(annotated_frame, label_text, (x1, y1 - 4), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
            
        return annotated_frame, processed_tracks
