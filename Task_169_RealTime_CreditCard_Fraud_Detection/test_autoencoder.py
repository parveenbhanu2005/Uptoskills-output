import torch
import numpy as np

from models.autoencoder import AutoEncoder

model = AutoEncoder()

model.load_state_dict(
    torch.load(
        "saved_models/autoencoder.pth",
        map_location="cpu"
    )
)

model.eval()

sample = np.array([
    200,
    28.61,
    77.20,
    5,
    10,
    7
],dtype=np.float32)

sample = torch.tensor(
    sample
).unsqueeze(0)

with torch.no_grad():

    reconstructed = model(sample)

error = torch.mean(
    (sample-reconstructed)**2
).item()

print("Reconstruction Error =",error)