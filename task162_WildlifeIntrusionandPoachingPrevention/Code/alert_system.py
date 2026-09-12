import os
from datetime import datetime

class AlertSystem:
    def __init__(self, data_manager):
        self.dm = data_manager
        self.logs_dir = self.dm.logs_dir
        self.alert_log_file = os.path.join(self.logs_dir, "alerts_sent.log")
        
    def trigger_alert(self, category, count, severity, perimeter_status, gps_coords):
        """
        Triggers SMS or Satellite transmission based on severity level.
        Low: No Alert (just logged).
        Medium: SMS Alert to Ranger Station.
        Critical: Both SMS and Satellite Alerts.
        """
        config = self.dm.get_config()
        node_id = config.get("node_id", "EDGE_NODE_01")
        recipient = config.get("alert_recipient_sms", "+919876543210")
        
        sms_sent = False
        sat_sent = False
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Determine and send alerts
        if severity == "CRITICAL":
            sms_sent = self._send_sms(node_id, recipient, category, count, severity, perimeter_status, gps_coords, timestamp)
            sat_sent = self._send_satellite(node_id, category, count, severity, perimeter_status, gps_coords, timestamp)
        elif severity == "MEDIUM":
            sms_sent = self._send_sms(node_id, recipient, category, count, severity, perimeter_status, gps_coords, timestamp)
            
        # Log to file for ranger audit
        self._log_alert_to_file(node_id, category, count, severity, perimeter_status, gps_coords, timestamp, sms_sent, sat_sent)
        
        return sms_sent, sat_sent
        
    def _send_sms(self, node_id, recipient, category, count, severity, perimeter_status, gps_coords, timestamp):
        """Simulates GSM/SMS transmission."""
        msg = (
            f"\n🚨 [EDGE SMS ALERT - {node_id}]\n"
            f"⚠️ Severity: {severity}\n"
            f"🔍 Detected: {count}x {category.upper()}\n"
            f"📍 Location: Lat {gps_coords[0]:.6f}, Lon {gps_coords[1]:.6f}\n"
            f"🚧 Perimeter Status: {perimeter_status.upper()}\n"
            f"🕒 Time: {timestamp}\n"
            f"📲 Sent to Ranger Station: {recipient}\n"
        )
        print(msg)
        return True
        
    def _send_satellite(self, node_id, category, count, severity, perimeter_status, gps_coords, timestamp):
        """Simulates SATELLITE transmission (used for off-grid remote reserves)."""
        # Compressed satellite payload format to optimize bandwidth
        sat_payload = (
            f"SATMSG-{node_id}|SEV={severity}|OBJ={category}:{count}|"
            f"GPS={gps_coords[0]:.5f},{gps_coords[1]:.5f}|PERIM={perimeter_status[:4].upper()}|TS={timestamp}"
        )
        msg = (
            f"\n📡 [SAT-COM LINK - UPLINK SUCCESSFUL]\n"
            f"📨 Channel: L-Band Orbit Satellite\n"
            f"📦 Payload: {sat_payload}\n"
            f"✅ Dispatch status: Route Broadcast to Central Ranger Command\n"
        )
        print(msg)
        return True
        
    def _log_alert_to_file(self, node_id, category, count, severity, perimeter_status, gps_coords, timestamp, sms, sat):
        """Logs alert dispatch metadata."""
        log_entry = (
            f"[{timestamp}] NODE={node_id} | SEVERITY={severity} | OBJECT={category}({count}) | "
            f"GPS={gps_coords[0]:.6f},{gps_coords[1]:.6f} | PERIMETER={perimeter_status} | "
            f"SMS_DISPATCH={'SUCCESS' if sms else 'NONE'} | SAT_DISPATCH={'SUCCESS' if sat else 'NONE'}\n"
        )
        with open(self.alert_log_file, 'a') as f:
            f.write(log_entry)
            
    def log_throttled_alert(self, category, count, severity, perimeter_status, gps_coords):
        """Logs a throttled alert quietly to the log file for auditing."""
        config = self.dm.get_config()
        node_id = config.get("node_id", "EDGE_NODE_01")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = (
            f"[{timestamp}] NODE={node_id} | SEVERITY={severity} | OBJECT={category}({count}) | "
            f"GPS={gps_coords[0]:.6f},{gps_coords[1]:.6f} | PERIMETER={perimeter_status} | "
            f"SMS_DISPATCH=THROTTLED | SAT_DISPATCH=THROTTLED\n"
        )
        with open(self.alert_log_file, 'a') as f:
            f.write(log_entry)
