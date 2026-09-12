import os
import json
import csv
from datetime import datetime

import matplotlib.pyplot as plt


ALERT_DIR = "reports/alerts"
VISUALIZATION_DIR = "reports/visualizations"
CSV_PATH = "reports/flagged_transactions.csv"


def create_directories():

    os.makedirs(
        ALERT_DIR,
        exist_ok=True
    )

    os.makedirs(
        VISUALIZATION_DIR,
        exist_ok=True
    )

    os.makedirs(
        "reports",
        exist_ok=True
    )


def get_next_alert_number():

    create_directories()

    existing_files = [
        file
        for file in os.listdir(ALERT_DIR)
        if file.startswith("alert_")
        and file.endswith(".json")
    ]

    numbers = []

    for file in existing_files:

        try:

            number = int(
                file.replace(
                    "alert_",
                    ""
                ).replace(
                    ".json",
                    ""
                )
            )

            numbers.append(number)

        except ValueError:

            continue

    if not numbers:
        return 1

    return max(numbers) + 1


def generate_json_alert(
    result,
    alert_number
):

    alert = {

        "transaction_id":
        result["transaction_id"],

        "user_id":
        result["user_id"],

        "amount":
        result["amount"],

        "risk_score":
        round(
            float(result["risk_score"]),
            4
        ),

        "fraud_probability":
        round(
            float(result["fraud_probability"]),
            4
        ),

        # Instant hold flag
        "hold_flag":
        True,

        # Action for fraud prevention team
        "action":
        "TRANSACTION_HELD",

        "decision":
        "HOLD",

        "decision_trigger":
        result["reason"],

        "timestamp":
        result["timestamp"],

        "alert_generated_at":
        datetime.now().isoformat()
    }

    file_path = os.path.join(
        ALERT_DIR,
        f"alert_{alert_number}.json"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            alert,
            file,
            indent=4
        )

    return file_path


def generate_feature_visualization(
    result,
    alert_number
):

    features = result.get(
        "feature_vector",
        []
    )

    feature_names = [
        "Amount",
        "Average Spending",
        "Geo Speed",
        "Unknown Merchant",
        "Unusual Amount",
        "Geo Velocity Spike"
    ]

    features = features[:6]

    names = feature_names[:len(features)]

    plt.figure(
        figsize=(10, 6)
    )

    plt.bar(
        names,
        features
    )

    plt.title(
        "Fraud Risk Feature Breakdown"
    )

    plt.ylabel(
        "Feature Value"
    )

    plt.xticks(
        rotation=30,
        ha="right"
    )

    plt.tight_layout()

    file_path = os.path.join(
        VISUALIZATION_DIR,
        f"transaction_{result['transaction_id']}.png"
    )

    plt.savefig(
        file_path,
        dpi=150
    )

    plt.close()

    return file_path


def update_csv(result):

    create_directories()

    fieldnames = [
        "transaction_id",
        "risk_score",
        "fraud_probability",
        "decision_trigger"
    ]

    existing_rows = {}

    if os.path.exists(CSV_PATH):

        with open(
            CSV_PATH,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                existing_rows[
                    str(row["transaction_id"])
                ] = row

    transaction_id = str(
        result["transaction_id"]
    )

    existing_rows[transaction_id] = {

        "transaction_id":
        transaction_id,

        "risk_score":
        f"{float(result['risk_score']):.4f}",

        "fraud_probability":
        f"{float(result['fraud_probability']):.4f}",

        "decision_trigger":
        result["reason"]
    }

    with open(
        CSV_PATH,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(
            existing_rows.values()
        )


def generate_alert(result):

    # Generate alert only when
    # transaction must be held.

    if not result.get(
        "hold_flag",
        False
    ):

        return

    create_directories()

    alert_number = get_next_alert_number()

    generate_json_alert(
        result,
        alert_number
    )

    generate_feature_visualization(
        result,
        alert_number
    )

    update_csv(
        result
    )

    # Instant hold notification
    print()
    print("🚨 INSTANT TRANSACTION HOLD FLAG 🚨")
    print("------------------------------------")
    print(
        f"Transaction ID : "
        f"{result['transaction_id']}"
    )

    print(
        f"User           : "
        f"{result['user_id']}"
    )

    print(
        f"Risk Score     : "
        f"{float(result['risk_score']):.2f}"
    )

    print(
        f"Fraud Probability : "
        f"{float(result['fraud_probability']):.2f}"
    )

    print(
        "Hold Flag      : TRUE"
    )

    print(
        "Action         : TRANSACTION HELD"
    )

    print(
        f"Trigger        : "
        f"{result['reason']}"
    )

    print(
        "Alert sent to fraud prevention workflow."
    )

    print("------------------------------------")

    print(
        f"JSON → reports/alerts/"
        f"alert_{alert_number}.json"
    )

    print(
        f"PNG  → reports/visualizations/"
        f"transaction_{result['transaction_id']}.png"
    )

    print(
        "CSV  → reports/flagged_transactions.csv"
    )