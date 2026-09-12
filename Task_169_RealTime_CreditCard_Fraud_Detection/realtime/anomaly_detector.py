import torch
import numpy as np

from models.autoencoder import AutoEncoder
from preprocessing.scaler import FeatureScaler


MODEL_PATH = "saved_models/autoencoder.pth"

model = AutoEncoder(input_dim=6)

model.load_state_dict(
    torch.load(
        MODEL_PATH,
        map_location="cpu"
    )
)

model.eval()


# Load the SAME scaler used during training
scaler = FeatureScaler()
scaler.load()


def anomaly_score(feature_vector):

    # Scale using the saved training scaler
    scaled_vector = scaler.transform_single(
        feature_vector
    )

    vector = torch.tensor(
        scaled_vector,
        dtype=torch.float32
    )

    with torch.no_grad():

        reconstruction = model(
            vector
        )

    mse = torch.mean(
        (vector - reconstruction) ** 2
    ).item()

    return float(mse)