import os
import csv
import json
from datetime import datetime

class DataManager:
    def __init__(self, base_dir=None):
        if base_dir is None:
            # If running inside the Code directory, resolve base_dir as the parent project root
            self.code_dir = os.path.dirname(os.path.abspath(__file__))
            self.base_dir = os.path.dirname(self.code_dir)
        else:
            self.base_dir = base_dir
            
        self.inputs_dir = os.path.join(self.base_dir, "Inputs")
        self.outputs_dir = os.path.join(self.base_dir, "Outputs")
        self.output_dir = self.outputs_dir
        self.models_dir = os.path.join(self.base_dir, "Models")
        
        self.logs_dir = os.path.join(self.outputs_dir, "logs")
        self.snapshots_dir = os.path.join(self.outputs_dir, "snapshots")
        
        # Paths
        self.log_file = os.path.join(self.logs_dir, "wildlife_movement_log.csv")
        self.config_file = os.path.join(self.outputs_dir, "config.json")
        
        # Initialize structure
        self._setup_directories()
        self._init_config()
        self._init_log_csv()
        
    def _setup_directories(self):
        """Create project directories if they don't exist."""
        os.makedirs(self.inputs_dir, exist_ok=True)
        os.makedirs(self.outputs_dir, exist_ok=True)
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.snapshots_dir, exist_ok=True)
        
    def _init_config(self):
        """Creates default configurations for the camera node."""
        if not os.path.exists(self.config_file):
            default_config = {
                "node_id": "EDGE_NODE_01",
                "camera_gps": {
                    "latitude": 29.9792,  # Near Rajaji National Park, India
                    "longitude": 78.4348
                },
                "detection_threshold": 0.30,  # Lower threshold for security verification
                "perimeter_boundary": {
                    "line_type": "horizontal",  # 'horizontal', 'vertical', 'diagonal'
                    "position_ratio": 0.5,      # 50% height
                    "direction": "downward",    # crossing top to bottom is a violation
                    "diagonal_start": [0.0, 0.5], # [x_ratio, y_ratio]
                    "diagonal_end": [1.0, 0.5]    # [x_ratio, y_ratio]
                },
                "alert_recipient_sms": "+919876543210",
                "storage_max_size_mb": 50.0   # Max snapshots folder capacity
            }
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
                
    def get_config(self):
        """Loads and returns config."""
        with open(self.config_file, 'r') as f:
            return json.load(f)
            
    def update_config(self, key, value):
        """Updates a specific key in config."""
        config = self.get_config()
        config[key] = value
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
            
    def _init_log_csv(self):
        """Initializes the CSV movement log with correct headers if it doesn't exist."""
        if not os.path.exists(self.log_file):
            headers = [
                "timestamp",
                "event_id",
                "gps_latitude",
                "gps_longitude",
                "detected_category",
                "count",
                "severity_level",
                "perimeter_status",
                "alert_sent",
                "snapshot_filename"
            ]
            with open(self.log_file, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                
    def log_movement_event(self, event_id, gps_lat, gps_lon, category, count, severity, perimeter_status, alert_sent, snapshot_fn):
        """Logs a movement event to the ecological CSV tracker."""
        timestamp = datetime.now().isoformat()
        row = [
            timestamp,
            event_id,
            f"{gps_lat:.6f}",
            f"{gps_lon:.6f}",
            category,
            count,
            severity,
            perimeter_status,
            "YES" if alert_sent else "NO",
            snapshot_fn or "N/A"
        ]
        with open(self.log_file, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
        return timestamp
        
    def enforce_storage_limit(self):
        """
        Enforces maximum directory size for snapshots.
        If snapshots directory exceeds storage_max_size_mb, deletes oldest JPG files (FIFO).
        """
        config = self.get_config()
        max_size_bytes = config.get("storage_max_size_mb", 50.0) * 1024 * 1024
        
        # Get all snapshot files sorted by modification time (oldest first)
        snapshot_files = []
        total_size = 0
        for entry in os.scandir(self.snapshots_dir):
            if entry.is_file() and entry.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                stat = entry.stat()
                snapshot_files.append((entry.path, stat.st_size, stat.st_mtime))
                total_size += stat.st_size
                
        # Sort oldest first
        snapshot_files.sort(key=lambda x: x[2])
        
        deleted_count = 0
        deleted_bytes = 0
        
        # FIFO cleanup
        for path, size, _ in snapshot_files:
            if total_size <= max_size_bytes:
                break
            try:
                os.remove(path)
                total_size -= size
                deleted_bytes += size
                deleted_count += 1
            except Exception as e:
                print(f"⚠️ Error cleaning up snapshot {path}: {e}")
                
        if deleted_count > 0:
            print(f"🧹 Edge Storage Cleanup: Deleted {deleted_count} oldest snapshot(s) ({deleted_bytes / (1024*1024):.2f} MB freed) due to storage limit.")
