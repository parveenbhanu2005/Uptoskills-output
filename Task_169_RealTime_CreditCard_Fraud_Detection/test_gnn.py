import torch

from models.gnn_model import FraudGNN

model = FraudGNN()

model.load_state_dict(
    torch.load(
        "saved_models/gnn_model.pth",
        map_location="cpu"
    )
)

model.eval()

x = torch.tensor([

    [200,
     28.6,
     77.2,
     1,
     10,
     7],

    [5000,
     19.0,
     72.8,
     4,
     11,
     7]

],dtype=torch.float)

edge_index = torch.tensor(

[
[0,1],
[1,0]

],dtype=torch.long).t()

with torch.no_grad():

    score = model(
        x,
        edge_index
    )

print(score)