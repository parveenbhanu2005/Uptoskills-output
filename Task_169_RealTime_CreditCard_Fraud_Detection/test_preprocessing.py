from preprocessing.feature_engineering import build_feature_vector
from database.fetch import get_user_history

history = get_user_history("U101")

transaction = {
    "transaction_id": 100,
    "user_id": "U101",
    "amount": 15000,
    "merchant": "Apple",
    "latitude": 19.0760,
    "longitude": 72.8777,
    "timestamp": "2026-08-07 12:30:00"
}

features = build_feature_vector(transaction, history)

print(features)