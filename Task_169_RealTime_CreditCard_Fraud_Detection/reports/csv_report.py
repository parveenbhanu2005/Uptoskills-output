import csv
import os

from database.fetch import (
    get_flagged_transactions
)


def export_csv():

    rows = get_flagged_transactions()

    os.makedirs(
        "reports",
        exist_ok=True
    )

    output_file = (
        "reports/flagged_transactions.csv"
    )

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "transaction_id",
            "risk_score",
            "fraud_probability",
            "decision_trigger"
        ])

        for row in rows:

            writer.writerow([

                row["transaction_id"],

                round(
                    float(row["risk_score"]),
                    4
                ),

                round(
                    float(
                        row["fraud_probability"]
                    ),
                    4
                ),

                row["reason"]

            ])

    return output_file