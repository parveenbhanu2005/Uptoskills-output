def should_hold_transaction(
    fraud_probability,
    threshold=0.75
):
    """
    Returns True when the fraud probability
    reaches the transaction hold threshold.
    """

    return fraud_probability >= threshold