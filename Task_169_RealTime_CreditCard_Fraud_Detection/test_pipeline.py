from realtime.stream import transaction_stream

from models.fraud_pipeline import process_transaction

from realtime.alert_engine import generate_alert


for transaction in transaction_stream(
    "data/transactions.csv"
):

    result = process_transaction(
        transaction
    )

    generate_alert(result)