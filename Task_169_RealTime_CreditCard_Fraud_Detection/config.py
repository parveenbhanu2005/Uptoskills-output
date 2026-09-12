import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FOLDER = os.path.join(BASE_DIR, "data")

DATABASE = os.path.join(DATA_FOLDER, "metrics.db")

TRANSACTION_FILE = os.path.join(DATA_FOLDER, "transactions.csv")

FLAGGED_FILE = os.path.join(DATA_FOLDER, "flagged_transactions.csv")

MODEL_FOLDER = os.path.join(BASE_DIR, "saved_models")

AUTOENCODER_MODEL = os.path.join(
    MODEL_FOLDER,
    "autoencoder.pth"
)

GNN_MODEL = os.path.join(
    MODEL_FOLDER,
    "gnn_model.pth"
)

RISK_THRESHOLD = 0.70

AUTOENCODER_THRESHOLD = 0.05

WINDOW_SIZE = 10

MAX_GEO_SPEED = 900

SECRET_KEY = "FraudDetection2026"

DEBUG = True