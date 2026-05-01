import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import os, json


MODEL_NAME_ALIASES = {
    "elite": "elite_v3_5",
    "elite_v3_5": "elite_v3_5",
    "supreme3": "supreme_v3_1",
    "supreme_v3_1": "supreme_v3_1",
    "supreme2": "supreme_v2",
    "supreme_v2": "supreme_v2",
    "titan": "titan",
    "titan12": "titan",
    "titan_12": "titan",
    "titan-12": "titan",
    "supreme4": "supreme4",
    "supreme_v4": "supreme4",
    "supreme_v4_25d": "supreme4",
    "chronos4": "chronos4",
    "chronos_4": "chronos4",
    "chronos-4": "chronos4",
    "vanguard": "vanguard",
    "twinoracle": "twinOracle",
    "twin_oracle": "twinOracle",
    "twin-oracle": "twinOracle",
    "guardian": "guardian",
    "hybrid": "hybrid_rl",
    "hybrid_rl": "hybrid_rl",
    "gene10": "generalist_e10",
    "generalist_e10": "generalist_e10",
    "heuristic": "heuristic",
    "hbase": "heuristic",
    "random": "heuristic",
    "supreme_v4": "supreme_v4",
}


MODEL_SPECS = {
    "elite_v3_5": {"arch": "elite18", "path": "models/elite_v3_5.pth", "input_dim": 18, "output_dim": 11},
    "supreme_v3_1": {"arch": "chronos18", "path": "models/supreme_v3_1.pth", "input_dim": 18, "output_dim": 11},
    "supreme_v2": {"arch": "resnet18", "path": "models/supreme_v2.pth", "input_dim": 18, "output_dim": 11},
    "supreme4": {"arch": "direct25", "path": "models/ppo_strategic_v4_25d.pth", "input_dim": 25, "output_dim": 24},
    "titan": {"arch": "titan25", "path": "models/titan.pth", "input_dim": 25, "output_dim": 24},
    "chronos4": {"arch": "chronos25", "path": "models/chronos_v4_25d.pth", "input_dim": 25, "output_dim": 24},
    "vanguard": {"arch": "direct25", "path": "models/vanguard.pth", "input_dim": 25, "output_dim": 24},
    "twinOracle": {"arch": "direct25", "path": "models/twin_oracle.pth", "input_dim": 25, "output_dim": 24},
    "guardian": {"arch": "direct25", "path": "models/guardian.pth", "input_dim": 25, "output_dim": 24},
    "hybrid_rl": {"arch": "resnet18", "path": "models/hybrid_rl.pth", "input_dim": 18, "output_dim": 11},
    "generalist_e10": {"arch": "mlp18", "path": "models/generalist_e10.pth", "input_dim": 18, "output_dim": 11},
    "heuristic": {"arch": "heuristic", "path": None, "input_dim": 18, "output_dim": 11},
}


def resolve_model_name(model_name="elite_v3_5", default="elite_v3_5"):
    if not model_name:
        return default
    normalized = str(model_name).strip().lower().replace(" ", "_").replace("-", "_")
    if normalized in MODEL_NAME_ALIASES:
        return MODEL_NAME_ALIASES[normalized]
    if normalized in MODEL_NAME_ALIASES.values():
        return normalized
    return default

# --- 1. ARCHITECTURES ---
class ResBlock(nn.Module):
    def __init__(self, size):
        super().__init__()
        self.fc1 = nn.Linear(size, size); self.fc2 = nn.Linear(size, size)
    def forward(self, x): return torch.relu(self.fc2(torch.relu(self.fc1(x))) + x)

class TransformerResNet(nn.Module):
    """Elite V3.5 / default: 18 features treated as sequence → 11"""
    def __init__(self, in_dim=18, out_dim=11):
        super().__init__()
        self.feature_embed = nn.Parameter(torch.randn(1, in_dim, 64))
        self.attn = nn.MultiheadAttention(64, 4, batch_first=True)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.head = nn.Sequential(
            nn.Linear(64, 128), nn.ReLU(),
            nn.Linear(128, out_dim)
        )
    def forward(self, x):
        x_val = x.unsqueeze(-1)
        x_emb = self.feature_embed * x_val
        x_attn, _ = self.attn(x_emb, x_emb, x_emb)
        x_pool = self.pool(x_attn.transpose(1, 2)).squeeze(-1)
        return torch.sigmoid(self.head(x_pool))

class ChronosGRU(nn.Module):
    """Supreme V3.1: 18 → GRU(128, 2-layer) → 11"""
    def __init__(self, in_dim=18, out_dim=11):
        super().__init__()
        self.gru = nn.GRU(in_dim, 128, num_layers=2, batch_first=True)
        self.head = nn.Linear(128, out_dim)
    def forward(self, x):
        _, h = self.gru(x.unsqueeze(1)); return torch.sigmoid(self.head(h[-1]))

class StandardResNet(nn.Module):
    """Supreme V2: 18 → ResBlock(64) → 11"""
    def __init__(self, in_dim=18, out_dim=11, width=64):
        super().__init__()
        self.input = nn.Linear(in_dim, width); self.res1 = ResBlock(width); self.head = nn.Linear(width, out_dim)
    def forward(self, x):
        x = torch.relu(self.input(x)); x = self.res1(x); return torch.sigmoid(self.head(x))

class GeneralistMLP(nn.Module):
    """Generalist E10: 18 → MLP(256, 128) → 11  (FIX B6: was missing)"""
    def __init__(self, in_dim=18, out_dim=11):
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
        self.model_name = resolve_model_name(model_name)
        mn = self.model_name
        spec = MODEL_SPECS.get(mn, MODEL_SPECS["elite_v3_5"])
        
        # Load Scalers for Normalization
        self.mean = np.zeros(spec["input_dim"])
        self.scale = np.ones(spec["input_dim"])
        params_path = "models/policy_network_params.json"
        if os.path.exists(params_path):
            with open(params_path, "r") as f:
                p = json.load(f)
                # DYNAMIC DIMENSION CHECK: Support 18-D or 25-D scalers
                dim = spec["input_dim"]
                self.mean = np.array(p["scaler_mean"][:dim]) if len(p.get("scaler_mean",[])) >= dim else np.zeros(dim)
                self.scale = np.array(p["scaler_scale"][:dim]) if len(p.get("scaler_scale",[])) >= dim else np.ones(dim)
        
        # FIX B6: Proper per-model architecture mapping
        mn = self.model_name
        if mn == "supreme4":
            from ppo_agent import BorealDirectEngine
            self.model = BorealDirectEngine(input_dim=25, output_dim=24)
        elif mn == "supreme_v3_1":
            self.model = ChronosGRU(18, 11)
        elif mn == "supreme_v2":
            self.model = StandardResNet(18, 11, width=64)
        elif mn == "titan":
            # Titan uses deep transformer — import at runtime to avoid circular deps
            try:
                import sys, os as _os
                _src = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
                if _src not in sys.path: sys.path.insert(0, _src)
                from ppo_titan_transformer import BorealTitanEngine
                self.model = BorealTitanEngine(input_dim=25, output_dim=24)
            except Exception:
                self.model = TransformerResNet(25, 24)  # graceful fallback
        elif mn == "chronos4":
            self.model = ChronosGRU(25, 24)
        elif mn == "vanguard":
            self.model = BorealDirectEngine(input_dim=25, output_dim=24)
        elif mn == "twinOracle":
            self.model = BorealDirectEngine(input_dim=25, output_dim=24)
        elif mn == "guardian":
            self.model = BorealDirectEngine(input_dim=25, output_dim=24)
        elif mn == "generalist_e10":
            self.model = GeneralistMLP(18, 11)
        elif mn == "hybrid_rl":
            # Hybrid RL uses a standard ResNet with depth-2 residual blocks
            self.model = StandardResNet(18, 11, width=128)
        else:
            # elite_v3_5, heuristic, etc.
            self.model = TransformerResNet(18, 11)

        model_path = spec["path"]
        if model_path and os.path.exists(model_path):
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
                p, v = out
                return p.squeeze(0).cpu().numpy().flatten(), v.item()
            return out.squeeze(0).cpu().numpy().flatten(), 0.85

def run_elite_inference(features, model_name="supreme_v4"):
    """Global convenience wrapper for the strategic engine."""
    inf = BorealInference(model_name=model_name)
    return inf.predict(features)
