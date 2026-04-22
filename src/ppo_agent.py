import torch
import torch.nn as nn
import numpy as np

class ResBlock(nn.Module):
    def __init__(self, size):
        super().__init__()
        self.fc1 = nn.Linear(size, size); self.fc2 = nn.Linear(size, size)
    def forward(self, x): return torch.relu(self.fc2(torch.relu(self.fc1(x))) + x)

class BorealDirectEngine(nn.Module):
    def __init__(self, input_dim=15, output_dim=11):
        super().__init__()
        self.embed = nn.Linear(input_dim, 128)
        self.attn = nn.MultiheadAttention(128, 4, batch_first=True)
        self.res = ResBlock(128)
        self.head = nn.Linear(128, output_dim)
        
    def forward(self, x):
        if len(x.shape) == 1: x = x.unsqueeze(0)
        x = torch.relu(self.embed(x)).unsqueeze(1)
        x, _ = self.attn(x, x, x)
        x = self.res(x.squeeze(1))
        return torch.sigmoid(self.head(x))

class BorealValueNetwork(nn.Module):
    def __init__(self, input_dim=15):
        super().__init__()
        self.input = nn.Linear(input_dim, 128)
        self.res1 = ResBlock(128)
        self.head = nn.Linear(128, 1)
    def forward(self, x):
        x = torch.relu(self.input(x))
        x = self.res1(x)
        return self.head(x)

# Placeholder for backward compatibility if other scripts still import it
class BorealTwinEngine(BorealDirectEngine):
    pass
