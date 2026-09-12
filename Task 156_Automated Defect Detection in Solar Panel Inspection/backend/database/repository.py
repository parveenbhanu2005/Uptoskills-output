import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.database.sqlite_db import get_connection, init_db
from backend.utils.logger import setup_logger

logger = setup_logger("repository")


class InspectionRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def save_inspection(self, inspection: Dict[str, Any], 
                        detections: List[Dict[str, Any]], 
                        tickets: List[Dict[str, Any]]) -> bool:
        """
        Atomically insert an inspection record, its associated detections, and maintenance tickets.
        """
        conn = get_connection(self.db_path)
        try:
            with conn:
                # 1. Insert inspection record
                conn.execute("""
                INSERT OR REPLACE INTO inspections (
                    inspection_id, image_id, timestamp, model, device, input_resolution,
                    inference_time_ms, detection_count, annotated_image, original_image,
                    pdf_report, csv_report, json_report
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    inspection.get("inspection_id"),
                    inspection.get("image_id"),
                    inspection.get("timestamp", datetime.utcnow().isoformat() + "Z"),
                    inspection.get("model"),
                    inspection.get("device", "cpu"),
                    inspection.get("input_resolution", "640x640"),
                    float(inspection.get("inference_time_ms", 0.0)),
                    int(inspection.get("count", len(detections))),
                    inspection.get("annotated_image"),
                    inspection.get("original_image"),
                    inspection.get("pdf"),
                    inspection.get("csv"),
                    inspection.get("detections_json")
                ))

                # 2. Insert detections
                for det in detections:
                    bbox_str = json.dumps(det.get("bbox", []))
                    conn.execute("""
                    INSERT INTO detections (
                        detection_id, inspection_id, class_id, class_name, confidence,
                        bbox, severity_score, severity_level, recommended_action, ticket_id, crop_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        int(det.get("detection_id", 1)),
                        inspection.get("inspection_id"),
                        int(det.get("class_id", 0)),
                        det.get("class_name", "Unknown"),
                        float(det.get("confidence", 0.0)),
                        bbox_str,
                        float(det.get("severity_score", 0.0)),
                        det.get("severity_level", "LOW"),
                        det.get("recommended_action", "MONITOR"),
                        det.get("ticket_id"),
                        det.get("crop_path")
                    ))

                # 3. Insert maintenance tickets
                for ticket in tickets:
                    conn.execute("""
                    INSERT OR REPLACE INTO maintenance_tickets (
                        ticket_id, inspection_id, detection_id, class_name, confidence,
                        severity_score, severity_level, priority, recommended_action, status, reason, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ticket.get("ticket_id"),
                        ticket.get("inspection_id"),
                        int(ticket.get("detection_id", 1)),
                        ticket.get("class_name"),
                        float(ticket.get("confidence", 0.0)),
                        float(ticket.get("severity_score", 0.0)),
                        ticket.get("severity_level"),
                        ticket.get("priority"),
                        ticket.get("recommended_action"),
                        ticket.get("status", "OPEN"),
                        ticket.get("reason"),
                        ticket.get("created_at", datetime.utcnow().isoformat() + "Z")
                    ))

            logger.info(f"Successfully saved inspection {inspection.get('inspection_id')} with {len(detections)} detections and {len(tickets)} tickets.")
            return True
        except Exception as e:
            logger.error(f"Failed to save inspection: {str(e)}")
            return False
        finally:
            conn.close()

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent inspection records."""
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM inspections ORDER BY timestamp DESC LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_tickets(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve maintenance tickets, optionally filtered by status."""
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            if status:
                cursor.execute("""
                SELECT * FROM maintenance_tickets WHERE UPPER(status) = UPPER(?) ORDER BY created_at DESC
                """, (status,))
            else:
                cursor.execute("""
                SELECT * FROM maintenance_tickets ORDER BY created_at DESC
                """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def update_ticket_status(self, ticket_id: str, status: str) -> bool:
        """Update status of a maintenance ticket ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED')."""
        valid_statuses = ["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"]
        target_status = status.upper().strip()

        if target_status not in valid_statuses:
            raise ValueError(f"Invalid ticket status '{status}'. Must be one of {valid_statuses}")

        now_iso = datetime.utcnow().isoformat() + "Z"
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.execute("""
                UPDATE maintenance_tickets
                SET status = ?, updated_at = ?
                WHERE ticket_id = ?
                """, (target_status, now_iso, ticket_id))

                if cursor.rowcount == 0:
                    logger.warning(f"No ticket found with ticket_id: {ticket_id}")
                    return False

            logger.info(f"Updated ticket {ticket_id} status to {target_status}")
            return True
        except Exception as e:
            logger.error(f"Failed to update ticket status: {str(e)}")
            return False
        finally:
            conn.close()
