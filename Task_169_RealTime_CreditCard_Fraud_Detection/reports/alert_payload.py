import json
import os


def create_alert_payload(result):

    payload = {
        "transaction_id": result["transaction_id"],
        "user_id": result["user_id"],
        "fraud_probability": round(
            float(result["fraud_probability"]), 4
        ),
        "risk_score": round(
            float(result["risk_score"]), 4
        ),
        "decision": (
            "HOLD"
            if result["hold_flag"]
            else "APPROVE"
        ),
        "decision_trigger": result["reason"],
        "timestamp": result["timestamp"]
    }

    os.makedirs(
        "reports/alerts",
        exist_ok=True
    )

    file_path = (
        f"reports/alerts/"
        f"alert_{result['transaction_id']}.json"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            payload,
            file,
            indent=4
        )

    return file_path