# data_logger.py

import pandas as pd
import datetime
import os
from config import CSV_OUTPUT

class AlertLogger:
    def __init__(self):
        self.output_csv = CSV_OUTPUT
        self.setup_csv()

    def setup_csv(self):
        if not os.path.exists(self.output_csv):
            df = pd.DataFrame(columns=["Timestamp", "Location", "Face_ID", "Condition", "Confidence_Risk_Score"])
            df.to_csv(self.output_csv, index=False)

    def evaluate_and_log(self, bpm, face_id):
        from config import PANIC_THRESHOLD
        if bpm > PANIC_THRESHOLD:
            risk_score = min(100, (bpm / PANIC_THRESHOLD) * 80)
            self._log_event("Physiological Panic Detected", round(risk_score, 2), face_id)
            return True
        return False

    def _log_event(self, condition, risk_score, face_id):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_entry = pd.DataFrame({
            "Timestamp": [timestamp],
            "Location": ["Camera_Zone_Alpha"],
            "Face_ID": [face_id],
            "Condition": [condition],
            "Confidence_Risk_Score": [risk_score]
        })
        new_entry.to_csv(self.output_csv, mode='a', header=False, index=False)