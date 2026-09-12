import torch

from database.fetch import get_user_history

from database.insert import (
    insert_transaction,
    insert_flagged_transaction
)

from database.metrics import update_daily_metrics

from preprocessing.feature_engineering import (
    build_feature_vector
)

from realtime.anomaly_detector import anomaly_score

from realtime.risk_score import get_risk_score

from realtime.hold_transaction import (
    should_hold_transaction
)


def fraud_probability(
    anomaly,
    risk
):
    """
    Convert Autoencoder reconstruction error
    into a 0-1 anomaly risk and combine it
    with the GNN risk score.
    """

    # Convert reconstruction error to 0-1 range.
    # Higher reconstruction error = higher anomaly risk.
    anomaly_risk = 1.0 - torch.exp(
    torch.tensor(-float(anomaly))
    ).item()

    # Keep GNN output safely inside 0-1.
    risk = max(
        0.0,
        min(float(risk), 1.0)
    )

    # Combine Autoencoder + GNN
    probability = (
        0.6 * anomaly_risk
        + 0.4 * risk
    )

    return max(
        0.0,
        min(float(probability), 1.0)
    )


def process_transaction(transaction):

    history = get_user_history(
        transaction["user_id"]
    )

    features = build_feature_vector(
        transaction,
        history
    )

    feature_vector = [

        features["amount"],
        features["average_spending"],
        features["geo_speed"],
        features["unknown_merchant"],
        features["unusual_amount"],
        features["geo_velocity_spike"]

    ]

    anomaly = anomaly_score(
        feature_vector
    )

    edge_index = torch.tensor(
        [[0], [0]],
        dtype=torch.long
    )

    risk = get_risk_score(
        [feature_vector],
        edge_index
    )

    if isinstance(risk, list):
        risk = risk[0]

    print(
    f"DEBUG → Anomaly Score: {anomaly:.6f}"
    )

    print(
    f"DEBUG → GNN Risk Score: {float(risk):.6f}"
    )

    probability = fraud_probability(
        anomaly,
        risk
    )

    hold = should_hold_transaction(
        probability
    )

    reason = []

    if features["unusual_amount"]:
        reason.append("Unusual Amount")

    if features["unknown_merchant"]:
        reason.append("Unknown Merchant")

    if features["geo_velocity_spike"]:
        reason.append("Geo Velocity Spike")

    if hold and not reason:
     reason.append("ML Anomaly Detection")

    if not reason:
        reason.append("Normal")

    result = {

        "transaction_id":
        transaction["transaction_id"],

        "user_id":
        transaction["user_id"],

        "amount":
        transaction["amount"],

        "risk_score":
        float(risk),

        "fraud_probability":
        float(probability),

        "hold_flag":
        hold,

        "reason":
        ", ".join(reason),

        "feature_vector":
        feature_vector,

        "timestamp":
        transaction["timestamp"]

    }

    insert_transaction(transaction)

    if hold:

        insert_flagged_transaction(result)

        update_daily_metrics(
            transaction["timestamp"][:10],
            transaction["amount"]
        )

    return result