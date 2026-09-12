import torch
import torch.nn.functional as F

from torch_geometric.nn import GCNConv


class FraudGNN(torch.nn.Module):

    def __init__(self,
                 input_dim=6,
                 hidden_dim=32):

        super().__init__()

        self.conv1 = GCNConv(
            input_dim,
            hidden_dim
        )

        self.conv2 = GCNConv(
            hidden_dim,
            16
        )

        self.output = torch.nn.Linear(
            16,
            1
        )

    def forward(
        self,
        x,
        edge_index
    ):

        x = self.conv1(
            x,
            edge_index
        )

        x = F.relu(x)

        x = self.conv2(
            x,
            edge_index
        )

        x = F.relu(x)

        risk = self.output(x)

        return torch.sigmoid(risk)
    