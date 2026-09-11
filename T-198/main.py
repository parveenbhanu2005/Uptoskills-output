# main.py

import cv2
import numpy as np
import os
import urllib.request
from config import YUNET_MODEL_PATH, YUNET_DOWNLOAD_URL, BUFFER_SIZE
from data_logger import AlertLogger
from signal_processing import RPPGExtractor

class CrowdSurveillanceSystem:
    def __init__(self):
        self.face_buffers = {}
        self.face_bpms = {}     
        self.next_face_id = 0
        self.tracked_centers = {} 
        
        self.setup_yunet()
        self.logger = AlertLogger()
        self.rppg = RPPGExtractor()

    def setup_yunet(self):
        if not os.path.exists(YUNET_MODEL_PATH):
            print(f"Downloading {YUNET_MODEL_PATH}...")
            urllib.request.urlretrieve(YUNET_DOWNLOAD_URL, YUNET_MODEL_PATH)
            
        self.detector = cv2.FaceDetectorYN.create(
            model=YUNET_MODEL_PATH, config="", input_size=(320, 320),
            score_threshold=0.6, nms_threshold=0.3, top_k=5000
        )

    def get_face_id(self, x, y, w, h):
        center_x, center_y = x + w // 2, y + h // 2
        closest_id, min_dist = None, float('inf')
        
        for face_id, (cx, cy) in self.tracked_centers.items():
            dist = np.sqrt((center_x - cx)**2 + (center_y - cy)**2)
            if dist < 50 and dist < min_dist:
                min_dist, closest_id = dist, face_id
                
        if closest_id is not None:
            self.tracked_centers[closest_id] = (center_x, center_y)
            return closest_id
            
        new_id = self.next_face_id
        self.tracked_centers[new_id] = (center_x, center_y)
        self.face_buffers[new_id] = []
        self.face_bpms[new_id] = "Calc..."
        self.next_face_id += 1
        return new_id

    def run(self, video_path):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Error: Could not open video.")
            return

        width, height = int(cap.get(3)), int(cap.get(4))
        self.detector.setInputSize((width, height))
        print("Starting video processing stream...")

        while cap.isOpened():
            success, frame = cap.read()
            if not success: break

            _, faces = self.detector.detect(frame)
            current_frame_ids = []

            if faces is not None:
                for face in faces:
                    x, y, w, h = list(map(int, face[:4]))
                    x, y = max(0, x), max(0, y)
                    face_roi = frame[y:y+h, x:x+w]
                    
                    if face_roi.size == 0: continue
                        
                    face_id = self.get_face_id(x, y, w, h)
                    current_frame_ids.append(face_id)
                    
                    self.face_buffers[face_id].append(face_roi)
                    
                    if len(self.face_buffers[face_id]) == BUFFER_SIZE:
                        calculated_bpm = self.rppg.process_tensor(self.face_buffers[face_id])
                        self.face_bpms[face_id] = calculated_bpm
                        self.face_buffers[face_id] = self.face_buffers[face_id][15:]
                    
                    bpm_display = self.face_bpms.get(face_id, "Calc...")
                    is_panic = False
                    
                    if isinstance(bpm_display, int):
                        is_panic = self.logger.evaluate_and_log(bpm_display, face_id)
                        
                    color = (0, 0, 255) if is_panic else (0, 255, 0)
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                    cv2.putText(frame, f"ID:{face_id} BPM:{bpm_display}", (x, y - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            lost_ids = set(self.tracked_centers.keys()) - set(current_frame_ids)
            for lost_id in lost_ids: del self.tracked_centers[lost_id]

            cv2.imshow('Modular Architecture Active', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    system = CrowdSurveillanceSystem()
    # Replace with your local video file
    system.run("raw data\\crowd.mp4")