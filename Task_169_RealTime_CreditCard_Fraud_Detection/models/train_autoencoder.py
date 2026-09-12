import os
import torch
import pandas as pd
import numpy as np

from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from models.autoencoder import AutoEncoder
from preprocessing.feature_engineering import build_feature_vector
from preprocessing.scaler import FeatureScaler


MODEL_DIR = "saved_models"
MODEL_PATH = os.path.join(
    MODEL_DIR,
    "autoencoder.pth"
)


def load_training_data():

    df = pd.read_csv("data/transactions.csv")

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df = df.sort_values(
        ["user_id", "timestamp"]
    )

    all_features = []

    histories = {}

    for _, row in df.iterrows():

        transaction = {
            "transaction_id": row["transaction_id"],
            "user_id": row["user_id"],
            "amount": float(row["amount"]),
            "merchant": row["merchant"],
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "timestamp": row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        }

        user_id = transaction["user_id"]

        history = histories.get(
            user_id,
            []
        )

        features = build_feature_vector(
            transaction,
            history
        )

        vector = [
            features["amount"],
            features["average_spending"],
            features["geo_speed"],
            features["unknown_merchant"],
            features["unusual_amount"],
            features["geo_velocity_spike"]
        ]

        all_features.append(vector)

        history.append(transaction)

        histories[user_id] = history

    return np.array(
        all_features,
        dtype=np.float32
    )


def train():

    X = load_training_data()

    print(
        f"Training samples: {len(X)}"
    )

    print(
        f"Feature shape: {X.shape}"
    )

    # -----------------------------
    # SCALE FEATURES
    # -----------------------------

    scaler = FeatureScaler()

    X_scaled = scaler.fit_transform(X)

    scaler.save()

    print(
        "Feature scaler saved."
    )

    # -----------------------------
    # DATASET
    # -----------------------------

    dataset = TensorDataset(
        torch.tensor(
            X_scaled,
            dtype=torch.float32
        )
    )

    loader = DataLoader(
        dataset,
        batch_size=32,
        shuffle=True
    )

    # -----------------------------
    # MODEL
    # -----------------------------

    model = AutoEncoder(
        input_dim=X.shape[1]
    )

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=0.001
    )

    criterion = nn.MSELoss()

    epochs = 50

    # -----------------------------
    # TRAIN
    # -----------------------------

    for epoch in range(epochs):

        total_loss = 0.0

        for batch in loader:

            x = batch[0]

            output = model(x)

            loss = criterion(
                output,
                x
            )

            optimizer.zero_grad()

            loss.backward()

            optimizer.step()

            total_loss += loss.item()

        print(
            f"Epoch {epoch + 1}/{epochs} "
            f"Loss={total_loss:.6f}"
        )

    # -----------------------------
    # SAVE MODEL
    # -----------------------------

    os.makedirs(
        MODEL_DIR,
        exist_ok=True
    )

    torch.save(
        model.state_dict(),
        MODEL_PATH
    )

    print(
        "\nAutoencoder Saved Successfully"
    )


if __name__ == "__main__":
    train()