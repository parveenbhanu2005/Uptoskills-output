import os
import torch
import pandas as pd
import numpy as np

from torch_geometric.data import Data

from models.gnn_model import FraudGNN

from preprocessing.feature_engineering import build_feature_vector
from preprocessing.scaler import FeatureScaler


MODEL_DIR = "saved_models"

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "gnn_model.pth"
)


def load_graph():

    df = pd.read_csv(
        "data/transactions.csv"
    )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"]
    )

    df = df.sort_values(
        ["user_id", "timestamp"]
    )

    features = []
    labels = []

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

        feature = build_feature_vector(
            transaction,
            history
        )

        vector = [
            feature["amount"],
            feature["average_spending"],
            feature["geo_speed"],
            feature["unknown_merchant"],
            feature["unusual_amount"],
            feature["geo_velocity_spike"]
        ]

        features.append(vector)

        # --------------------------------
        # Weak supervision based on
        # task-defined suspicious behavior
        # --------------------------------

        suspicious = (
            feature["unknown_merchant"]
            or feature["unusual_amount"]
            or feature["geo_velocity_spike"]
        )

        labels.append(
            1.0 if suspicious else 0.0
        )

        history.append(transaction)

        histories[user_id] = history

    X = np.array(
        features,
        dtype=np.float32
    )

    y = np.array(
        labels,
        dtype=np.float32
    ).reshape(-1, 1)

    # --------------------------------
    # SAME SCALER AS AUTOENCODER
    # --------------------------------

    scaler = FeatureScaler()

    scaler.load()

    X_scaled = scaler.transform(X)

    x = torch.tensor(
        X_scaled,
        dtype=torch.float32
    )

    y = torch.tensor(
        y,
        dtype=torch.float32
    )

    # --------------------------------
    # TEMPORAL GRAPH
    # --------------------------------

    edge_index = []

    for i in range(len(df) - 1):

        edge_index.append(
            [i, i + 1]
        )

        edge_index.append(
            [i + 1, i]
        )

    edge_index = torch.tensor(
        edge_index,
        dtype=torch.long
    ).t().contiguous()

    return Data(
        x=x,
        edge_index=edge_index,
        y=y
    )


def train():

    graph = load_graph()

    print(
        f"Training nodes: {graph.x.shape[0]}"
    )

    print(
        f"Feature shape: {graph.x.shape}"
    )

    print(
        f"Suspicious nodes: "
        f"{int(graph.y.sum().item())}"
    )

    model = FraudGNN(
        input_dim=6
    )

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=0.001
    )

    criterion = torch.nn.BCELoss()

    epochs = 100

    for epoch in range(epochs):

        optimizer.zero_grad()

        prediction = model(
            graph.x,
            graph.edge_index
        )

        loss = criterion(
            prediction,
            graph.y
        )

        loss.backward()

        optimizer.step()

        if (
            epoch == 0
            or (epoch + 1) % 10 == 0
        ):

            print(
                f"Epoch {epoch + 1}/{epochs} "
                f"Loss={loss.item():.6f}"
            )

    os.makedirs(
        MODEL_DIR,
        exist_ok=True
    )

    torch.save(
        model.state_dict(),
        MODEL_PATH
    )

    print(
        "\nGNN Saved Successfully"
    )


if __name__ == "__main__":
    train()