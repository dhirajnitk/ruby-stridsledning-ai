import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import sys
import os

sys.path.insert(0, 'src')
from core.inference import TransformerResNet

data = np.load('data/training/strategic_mega_corpus/marv_mirv_eval.npz')
X = torch.tensor(data['features'], dtype=torch.float32)
Y = torch.tensor(data['weights'], dtype=torch.float32)

model = TransformerResNet(18, 11)
opt = optim.Adam(model.parameters(), lr=1e-3)
crit = nn.BCELoss()

print("Training Elite V3.5 for 200 epochs...")
for epoch in range(200):
    opt.zero_grad()
    loss = crit(model(X), Y)
    loss.backward()
    opt.step()
    if epoch % 50 == 0: 
        print(f'Epoch {epoch} Loss: {loss.item()}')
        sys.stdout.flush()

torch.save(model.state_dict(), 'models/elite_v3_5.pth')
print("Saved models/elite_v3_5.pth")

import benchmark_marv_mirv_models
benchmark_marv_mirv_models.benchmark()
