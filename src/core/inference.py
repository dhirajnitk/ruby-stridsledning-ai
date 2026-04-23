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
    """Elite V3.5 / default: 15 → 128 (embed+attn+res) → 11"""
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
    """Supreme V3.1: 15 → GRU(128, 2-layer) → 11"""
    def __init__(self, in_dim=15, out_dim=11):
        super().__init__()
        self.gru = nn.GRU(in_dim, 128, num_layers=2, batch_first=True)
        self.head = nn.Linear(128, out_dim)
    def forward(self, x):
        _, h = self.gru(x.unsqueeze(1)); return torch.sigmoid(self.head(h[-1]))

class StandardResNet(nn.Module):
    """Supreme V2: 15 → ResBlock(64) → 11"""
    def __init__(self, in_dim=15, out_dim=11, width=64):
        super().__init__()
        self.input = nn.Linear(in_dim, width); self.res1 = ResBlock(width); self.head = nn.Linear(width, out_dim)
    def forward(self, x):
        x = torch.relu(self.input(x)); x = self.res1(x); return torch.sigmoid(self.head(x))

class GeneralistMLP(nn.Module):
    """Generalist E10: 15 → MLP(256, 128) → 11  (FIX B6: was missing)"""
    def __init__(self, in_dim=15, out_dim=11):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 256), nn.ReLU(),
            nn.Linear(256, 128),    nn.ReLU(),
            nn.Linear(128, out_dim), nn.Sigmoid()
        )
    def forward(self, x): return self.net(x)

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
        
        # FIX B6: Proper per-model architecture mapping
        mn = self.model_name
        if "supreme_v3_1" in mn or "chronos" in mn:
            self.model = ChronosGRU(15, 11)
        elif "supreme_v2" in mn:
            self.model = StandardResNet(15, 11, width=64)
        elif "titan" in mn:
            # Titan uses deep transformer — import at runtime to avoid circular deps
            try:
                import sys, os as _os
                _src = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
                if _src not in sys.path: sys.path.insert(0, _src)
                from ppo_titan_transformer import BorealTitanEngine
                self.model = BorealTitanEngine(input_dim=15, output_dim=11)
            except Exception:
                self.model = TransformerResNet(15, 11)  # graceful fallback
        elif "generalist" in mn:
            self.model = GeneralistMLP(15, 11)
        elif "hybrid" in mn:
            # Hybrid RL uses a standard ResNet with depth-2 residual blocks
            self.model = StandardResNet(15, 11, width=128)
        else:
            # elite_v3_5, heuristic, etc.
            self.model = TransformerResNet(15, 11)

        model_path = f"models/{self.model_name}.pth"
        if os.path.exists(model_path):
            try:
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            except RuntimeError as e:
                print(f"[INFERENCE WARNING] {self.model_name}: state_dict mismatch — {e}")
                print(f"[INFERENCE] Running {self.model_name} with randomly-initialised weights.")

        self.model.to(self.device).eval()

    def predict(self, features):
        # Apply Normalization (Essential for Accuracy)
        norm_features = (np.array(features) - self.mean) / (self.scale + 1e-6)
        with torch.no_grad():
            t_feat = torch.tensor(norm_features, dtype=torch.float32).unsqueeze(0).to(self.device)
            out = self.model(t_feat)
            # FIX B7: models may return (policy, value) tuple — extract policy only
            if isinstance(out, tuple):
                out = out[0]
            return out.squeeze(0).cpu().numpy().flatten()
