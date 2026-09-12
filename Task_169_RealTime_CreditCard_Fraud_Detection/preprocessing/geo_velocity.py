from geopy.distance import geodesic
from datetime import datetime


def calculate_velocity(previous_transaction, current_transaction):
    """
    Returns travel speed in km/h between two transactions.
    """

    if previous_transaction is None:
        return 0

    previous_location = (
        previous_transaction["latitude"],
        previous_transaction["longitude"]
    )

    current_location = (
        current_transaction["latitude"],
        current_transaction["longitude"]
    )

    distance = geodesic(
        previous_location,
        current_location
    ).km

    t1 = datetime.strptime(
        previous_transaction["timestamp"],
        "%Y-%m-%d %H:%M:%S"
    )

    t2 = datetime.strptime(
        current_transaction["timestamp"],
        "%Y-%m-%d %H:%M:%S"
    )

    hours = (t2 - t1).total_seconds() / 3600

    if hours <= 0:
        return 0

    return distance / hours


def geo_velocity_spike(speed, threshold=900):

    return speed > threshold