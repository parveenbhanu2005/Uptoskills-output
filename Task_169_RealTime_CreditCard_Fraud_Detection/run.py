from realtime.stream import transaction_stream

from models.fraud_pipeline import (
    process_transaction
)

from reports.alert_payload import (
    create_alert_payload
)

from reports.feature_breakdown import (
    create_feature_visualization
)

from reports.csv_report import (
    export_csv
)


def main():

    print(
        "Real-time fraud detection started..."
    )

    print()

    for transaction in transaction_stream(
        "data/transactions.csv"
    ):

        result = process_transaction(
            transaction
        )

        # 1. Generate JSON alert
        alert_file = create_alert_payload(
            result
        )

        # 2. Generate feature visualization
        visualization_file = (
            create_feature_visualization(
                result
            )
        )

        if result["hold_flag"]:

            print(
                f"Transaction "
                f"{result['transaction_id']} "
                f"→ HOLD"
            )

        else:

            print(
                f"Transaction "
                f"{result['transaction_id']} "
                f"→ APPROVE"
            )

        print(
            "Fraud Probability:",
            round(
                result["fraud_probability"],
                4
            )
        )

        print(
            "Alert payload generated."
        )

        print(
            "Feature visualization generated."
        )

        print()

    # 3. Generate final CSV report
    csv_file = export_csv()

    print(
        "CSV report updated."
    )

    print()

    print(
        "Detection completed."
    )

    print()
    print("Generated files:")
    print(
        f"Alert folder       : {alert_file}"
    )
    print(
        f"Visualization      : {visualization_file}"
    )
    print(
        f"CSV report         : {csv_file}"
    )


if __name__ == "__main__":

    main()