import numpy as np
from scipy.optimize import linear_sum_assignment
import config

def calculate_iou(box1, box2):
    """
    Calculate Intersection over Union (IoU) between two bounding boxes [x1, y1, x2, y2].
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[0])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[0])
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0

class Track:
    def __init__(self, track_id, bbox, confidence):
        self.track_id = track_id
        self.bbox = bbox
        self.confidence = confidence
        self.age = 1
        self.total_visible_count = 1
        self.consecutive_invisible_count = 0
        
        # Center coordinates
        self.center_x = (bbox[0] + bbox[2]) / 2.0
        self.center_y = (bbox[1] + bbox[3]) / 2.0
        self.vx = 0.0
        self.vy = 0.0
        self.history = [(self.center_x, self.center_y)]

    def update(self, bbox, confidence):
        new_cx = (bbox[0] + bbox[2]) / 2.0
        new_cy = (bbox[1] + bbox[3]) / 2.0
        
        # Update velocity with exponential moving average
        alpha = 0.6
        self.vx = alpha * (new_cx - self.center_x) + (1 - alpha) * self.vx
        self.vy = alpha * (new_cy - self.center_y) + (1 - alpha) * self.vy
        
        self.center_x = new_cx
        self.center_y = new_cy
        self.bbox = bbox
        self.confidence = confidence
        self.age += 1
        self.total_visible_count += 1
        self.consecutive_invisible_count = 0
        self.history.append((new_cx, new_cy))
        if len(self.history) > 30:
            self.history.pop(0)

    def predict(self):
        # Linear motion prediction during brief occlusion
        self.center_x += self.vx
        self.center_y += self.vy
        w = self.bbox[2] - self.bbox[0]
        h = self.bbox[3] - self.bbox[1]
        self.bbox = [self.center_x - w/2, self.center_y - h/2, self.center_x + w/2, self.center_y + h/2]
        self.consecutive_invisible_count += 1
        self.age += 1

class PedestrianTracker:
    def __init__(self, max_invisible_frames=10, min_iou=0.2):
        """
        Multi-Object Pedestrian Tracker with IoU and Spatial Distance Hungarian Matching.
        """
        self.next_id = 1
        self.tracks = []
        self.max_invisible_frames = max_invisible_frames
        self.min_iou = min_iou

    def update(self, detections):
        """
        Update active tracks with new frame detections.
        
        Args:
            detections (list of dict): List of detection dicts with 'bbox' and 'confidence'
        
        Returns:
            list of dict: Active tracked pedestrians with 'track_id', 'bbox', 'center', 'velocity'
        """
        # Predict positions for existing tracks
        for track in self.tracks:
            track.predict()

        if len(self.tracks) == 0:
            # First frame or reset: register all detections
            for det in detections:
                self.tracks.append(Track(self.next_id, det['bbox'], det['confidence']))
                self.next_id += 1
        else:
            # Build cost matrix between existing tracks and new detections
            cost_matrix = np.zeros((len(self.tracks), len(detections)), dtype=np.float32)
            for i, trk in enumerate(self.tracks):
                for j, det in enumerate(detections):
                    iou = calculate_iou(trk.bbox, det['bbox'])
                    
                    # Distance metric between predicted center and detection center
                    det_cx = (det['bbox'][0] + det['bbox'][2]) / 2.0
                    det_cy = (det['bbox'][1] + det['bbox'][3]) / 2.0
                    dist = np.hypot(trk.center_x - det_cx, trk.center_y - det_cy)
                    
                    # Combined cost (lower is better)
                    spatial_cost = min(dist / 150.0, 1.0)
                    cost = (1.0 - iou) * 0.7 + spatial_cost * 0.3
                    cost_matrix[i, j] = cost

            # Hungarian Algorithm assignment
            trk_indices, det_indices = linear_sum_assignment(cost_matrix)

            matched_tracks = set()
            matched_dets = set()

            for trk_idx, det_idx in zip(trk_indices, det_indices):
                if cost_matrix[trk_idx, det_idx] < 0.8:  # Matching threshold
                    self.tracks[trk_idx].update(detections[det_idx]['bbox'], detections[det_idx]['confidence'])
                    matched_tracks.add(trk_idx)
                    matched_dets.add(det_idx)

            # Unmatched detections -> create new tracks
            for j in range(len(detections)):
                if j not in matched_dets:
                    self.tracks.append(Track(self.next_id, detections[j]['bbox'], detections[j]['confidence']))
                    self.next_id += 1

        # Remove dead tracks that were invisible for too long
        self.tracks = [trk for trk in self.tracks if trk.consecutive_invisible_count <= self.max_invisible_frames]

        # Prepare tracked output
        tracked_pedestrians = []
        for trk in self.tracks:
            if trk.consecutive_invisible_count == 0:  # Currently visible
                tracked_pedestrians.append({
                    'track_id': trk.track_id,
                    'bbox': trk.bbox,
                    'confidence': trk.confidence,
                    'center_x': trk.center_x,
                    'center_y': trk.center_y,
                    'bottom_center': (trk.center_x, trk.bbox[3]),
                    'vx': trk.vx,
                    'vy': trk.vy,
                    'history': list(trk.history)
                })

        return tracked_pedestrians
