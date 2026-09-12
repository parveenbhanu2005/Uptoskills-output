import numpy as np


def average_spending(history):

    if len(history) == 0:
        return 0

    amounts = [
        row["amount"]
        for row in history
    ]

    return float(np.mean(amounts))


def spending_std(history):

    if len(history) == 0:
        return 0

    amounts = [
        row["amount"]
        for row in history
    ]

    return float(np.std(amounts))


def unusual_amount(amount, history, multiplier=3):

    avg = average_spending(history)

    std = spending_std(history)

    if std == 0:
        return False

    return amount > avg + multiplier * std


def spending_window(history, window=10):

    return history[-window:]