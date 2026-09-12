import sqlite3
import os

DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "metrics.db"
)

DB_PATH = os.path.abspath(DB_PATH)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():

    conn = get_connection()
    cur = conn.cursor()

    # ----------------------------
    # All Transactions
    # ----------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions(

        transaction_id INTEGER PRIMARY KEY,

        user_id TEXT,

        amount REAL,

        merchant TEXT,

        latitude REAL,

        longitude REAL,

        timestamp TEXT

    )
    """)

    # ----------------------------
    # Flagged Transactions
    # ----------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS flagged_transactions(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        transaction_id INTEGER,

        user_id TEXT,

        amount REAL,

        risk_score REAL,

        fraud_probability REAL,

        hold_flag INTEGER,

        reason TEXT,

        feature_vector TEXT,

        timestamp TEXT

    )
    """)

    # ----------------------------
    # Daily Metrics
    # ----------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS daily_metrics(

        date TEXT PRIMARY KEY,

        total_transactions INTEGER,

        fraud_transactions INTEGER,

        prevented_loss REAL

    )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    initialize_database()
    print("Database Created Successfully")