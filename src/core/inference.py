import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import os, json

# --- 1. ARCHITECTURES ---
class ResBlock(nn.Module):
    def __init__(self, size):
        super().__init__()
        self.fc1 = nn.Linear(size, size); self.fc2 = nn.Linear(size, size)
    def forward(self, x): return torch.relu(self.fc2(torch.relu(self.fc1(x))) + x)

class TransformerResNet(nn.Module):
    def __init__(self, in_dim=15, out_dim=11):
        super().__init__()
        self.embed = nn.Linear(in_dim, 128)
        self.attn = nn.MultiheadAttention(128, 4, batch_first=True)
        self.res = ResBlock(128); self.head = nn.Linear(128, out_dim)
    def forward(self, x):
        x = torch.relu(self.embed(x)).unsqueeze(1)
        x, _ = self.attn(x, x, x)
        x = self.res(x.squeeze(1))
        return torch.sigmoid(self.head(x))

class ChronosGRU(nn.Module):
    def __init__(self, in_dim=15, out_dim=11):
        super().__init__()
        self.gru = nn.GRU(in_dim, 128, num_layers=2, batch_first=True)
        self.head = nn.Linear(128, out_dim)
    def forward(self, x):
        _, h = self.gru(x.unsqueeze(1)); return torch.sigmoid(self.head(h[-1]))

class StandardResNet(nn.Module):
    def __init__(self, in_dim=15, out_dim=11, width=64):
        super().__init__()
        self.input = nn.Linear(in_dim, width); self.res1 = ResBlock(width); self.head = nn.Linear(width, out_dim)
    def forward(self, x):
        x = torch.relu(self.input(x)); x = self.res1(x); return torch.sigmoid(self.head(x))

class BorealInference:
    def __init__(self, model_name="elite_v3_5", device="cpu"):
        self.device = torch.device(device)
        self.model_name = model_name.lower().replace(" ", "_")
        
        # Load Scalers for Normalization
        self.mean = np.zeros(15)
        self.scale = np.ones(15)
        params_path = "models/policy_network_params.json"
        if os.path.exists(params_path):
            with open(params_path, "r") as f:
                p = json.load(f)
                self.mean = np.array(p["scaler_mean"][:15])
                self.scale = np.array(p["scaler_scale"][:15])
        
        # Architecture mapping
        if "supreme_v3_1" in self.model_name:
            self.model = ChronosGRU(15, 11)
        elif "supreme_v2" in self.model_name:
            self.model = StandardResNet(15, 11, width=64)
        else:
            self.model = TransformerResNet(15, 11)
            
        model_path = f"models/{self.model_name}.pth"
        if os.path.exists(model_path):
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        
        self.model.to(self.device).eval()
        
    def predict(self, features):
        # Apply Normalization (Essential for Accuracy)
        norm_features = (np.array(features) - self.mean) / (self.scale + 1e-6)
        with torch.no_grad():
            # BUG FIX: Add batch dimension [1, 15] so sequential models 
            # (GRU/Transformer) don't interpret features as timesteps.
            t_feat = torch.tensor(norm_features, dtype=torch.float32).unsqueeze(0).to(self.device)
            out = self.model(t_feat)
            # Squeeze out the batch dimension from the result
            return out.squeeze(0).cpu().numpy().flatten()
