from preprocessing.geo_velocity import (
    calculate_velocity,
    geo_velocity_spike
)

from preprocessing.merchant_features import (
    is_unknown_merchant
)

from preprocessing.spending_history import (
    average_spending,
    unusual_amount
)


def build_feature_vector(
        transaction,
        history
):
    """
    Creates a feature vector for Autoencoder/GNN.
    """

    previous = history[-1] if len(history) else None

    speed = calculate_velocity(
        previous,
        transaction
    )

    amount = transaction["amount"]

    avg = average_spending(history)

    unknown = is_unknown_merchant(
        history,
        transaction["merchant"]
    )

    amount_flag = unusual_amount(
        amount,
        history
    )

    geo_flag = geo_velocity_spike(
        speed
    )

    feature_vector = {

        "amount": amount,

        "average_spending": avg,

        "geo_speed": speed,

        "unknown_merchant": int(unknown),

        "unusual_amount": int(amount_flag),

        "geo_velocity_spike": int(geo_flag)

    }

    return feature_vector