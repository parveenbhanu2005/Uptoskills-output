import os
import matplotlib.pyplot as plt


def create_feature_visualization(result):

    features = {
        "Transaction Amount":
            float(result["feature_vector"][0]),

        "Average Spending":
            float(result["feature_vector"][1]),

        "Geo Velocity":
            float(result["feature_vector"][2]),

        "Unknown Merchant":
            float(result["feature_vector"][3]),

        "Unusual Amount":
            float(result["feature_vector"][4]),

        "Geo Velocity Spike":
            float(result["feature_vector"][5])
    }

    names = list(features.keys())
    values = list(features.values())

    # Normalize values so different feature scales
    # can be displayed together.
    max_value = max(
        abs(value) for value in values
    )

    if max_value == 0:
        normalized_values = [
            0 for value in values
        ]
    else:
        normalized_values = [
            abs(value) / max_value
            for value in values
        ]

    risk_labels = []

    for value in normalized_values:

        if value >= 0.70:
            risk_labels.append("HIGH")
        elif value >= 0.40:
            risk_labels.append("MEDIUM")
        else:
            risk_labels.append("LOW")

    os.makedirs(
        "reports/visualizations",
        exist_ok=True
    )

    transaction_id = result["transaction_id"]

    file_path = (
        f"reports/visualizations/"
        f"feature_breakdown_{transaction_id}.png"
    )

    plt.figure(figsize=(10, 6))

    bars = plt.bar(
        names,
        normalized_values
    )

    plt.title(
        f"Feature Risk Breakdown - "
        f"Transaction {transaction_id}"
    )

    plt.ylabel("Relative Risk Indicator")

    plt.ylim(0, 1.1)

    plt.xticks(
        rotation=30,
        ha="right"
    )

    for bar, label in zip(
        bars,
        risk_labels
    ):

        plt.text(
            bar.get_x() +
            bar.get_width() / 2,

            bar.get_height() + 0.03,

            label,

            ha="center"
        )

    plt.tight_layout()

    plt.savefig(
        file_path,
        dpi=150
    )

    plt.close()

    return file_path