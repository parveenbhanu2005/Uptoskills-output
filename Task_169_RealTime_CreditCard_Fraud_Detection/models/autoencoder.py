import torch
import torch.nn as nn


class AutoEncoder(nn.Module):

    def __init__(self, input_dim=6):

        super().__init__()

        self.encoder = nn.Sequential(

            nn.Linear(input_dim, 16),
            nn.ReLU(),

            nn.Linear(16, 8),
            nn.ReLU(),

            nn.Linear(8, 4)

        )

        self.decoder = nn.Sequential(

            nn.Linear(4, 8),
            nn.ReLU(),

            nn.Linear(8, 16),
            nn.ReLU(),

            nn.Linear(16, input_dim)

        )

    def forward(self, x):

        latent = self.encoder(x)

        reconstructed = self.decoder(latent)

        return reconstructed