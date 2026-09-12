import sqlite3
import json
from pathlib import Path
from typing import Optional
from backend.utils.logger import setup_logger

logger = setup_logger("database")

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "solarlens.db"


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Get a SQLite database connection with row factory enabled."""
    target_path = str(db_path) if db_path else str(DEFAULT_DB_PATH)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None):
    """
    Initialize SolarLens database schema.
    Creates inspections, detections, and maintenance_tickets tables if they do not exist.
    """
    target_path = str(db_path) if db_path else str(DEFAULT_DB_PATH)
    logger.info(f"Initializing SolarLens database schema at: {target_path}")

    conn = get_connection(target_path)
    try:
        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS inspections (
                inspection_id TEXT PRIMARY KEY,
                image_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                model TEXT NOT NULL,
                device TEXT NOT NULL,
                input_resolution TEXT NOT NULL,
                inference_time_ms REAL NOT NULL,
                detection_count INTEGER NOT NULL,
                annotated_image TEXT,
                original_image TEXT,
                pdf_report TEXT,
                csv_report TEXT,
                json_report TEXT
            );
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detection_id INTEGER NOT NULL,
                inspection_id TEXT NOT NULL,
                class_id INTEGER NOT NULL,
                class_name TEXT NOT NULL,
                confidence REAL NOT NULL,
                bbox TEXT NOT NULL,
                severity_score REAL NOT NULL,
                severity_level TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                ticket_id TEXT,
                crop_path TEXT,
                FOREIGN KEY (inspection_id) REFERENCES inspections(inspection_id) ON DELETE CASCADE
            );
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_tickets (
                ticket_id TEXT PRIMARY KEY,
                inspection_id TEXT NOT NULL,
                detection_id INTEGER NOT NULL,
                class_name TEXT NOT NULL,
                confidence REAL NOT NULL,
                severity_score REAL NOT NULL,
                severity_level TEXT NOT NULL,
                priority TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED')),
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                FOREIGN KEY (inspection_id) REFERENCES inspections(inspection_id) ON DELETE CASCADE
            );
            """)
        logger.info("SolarLens database schema successfully initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise e
    finally:
        conn.close()
