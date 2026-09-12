def is_unknown_merchant(user_history, merchant):
    """
    Returns True if merchant has never been used before.
    """

    previous_merchants = {
        row["merchant"]
        for row in user_history
    }

    return merchant not in previous_merchants