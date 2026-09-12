from database.database import get_connection
import json


def insert_transaction(transaction):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""

INSERT OR IGNORE INTO transactions
VALUES (?,?,?,?,?,?,?)

""", (
    transaction["transaction_id"],
    transaction["user_id"],
    transaction["amount"],
    transaction["merchant"],
    transaction["latitude"],
    transaction["longitude"],
    transaction["timestamp"]
))

    conn.commit()
    conn.close()


def insert_flagged_transaction(data):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""

    INSERT INTO flagged_transactions(

        transaction_id,
        user_id,
        amount,
        risk_score,
        fraud_probability,
        hold_flag,
        reason,
        feature_vector,
        timestamp

    )

    VALUES(?,?,?,?,?,?,?,?,?)

    """, (

        data["transaction_id"],
        data["user_id"],
        data["amount"],
        data["risk_score"],
        data["fraud_probability"],
        data["hold_flag"],
        data["reason"],
        json.dumps(data["feature_vector"]),
        data["timestamp"]

    ))

    conn.commit()
    conn.close()