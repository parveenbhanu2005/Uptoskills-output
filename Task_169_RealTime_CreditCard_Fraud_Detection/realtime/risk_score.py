import torch

from models.gnn_model import FraudGNN
from preprocessing.scaler import FeatureScaler


MODEL_PATH = "saved_models/gnn_model.pth"


model = FraudGNN(
    input_dim=6
)

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


def get_risk_score(
    feature_vector,
    edge_index
):

    # Scale the feature vector
    scaled_vector = scaler.transform(
        feature_vector
    )

    x = torch.tensor(
        scaled_vector,
        dtype=torch.float32
    )

    with torch.no_grad():

        score = model(
            x,
            edge_index
        )

    return score.squeeze().tolist()