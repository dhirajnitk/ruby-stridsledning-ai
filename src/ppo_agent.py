import torch
import torch.nn as nn
import numpy as np
import math

class ResBlock(nn.Module):
    def __init__(self, size):
        super().__init__()
        self.fc1 = nn.Linear(size, size); self.fc2 = nn.Linear(size, size)
    def forward(self, x): return torch.relu(self.fc2(torch.relu(self.fc1(x))) + x)

class BorealDirectEngine(nn.Module):
    """Elite/Supreme direct-action policy network.
    Input : (Batch, 15) theater feature vector
    Output: (policy (Batch, output_dim), value (Batch, 1)) tuple
    """
    def __init__(self, input_dim=15, output_dim=11):
        super().__init__()
        self.embed = nn.Linear(input_dim, 128)
        self.attn = nn.MultiheadAttention(128, 4, batch_first=True)
        self.res = ResBlock(128)
        self.head = nn.Linear(128, output_dim)        # policy
        self.value_head = nn.Linear(128, 1)           # FIX B1: added value head

    def forward(self, x):
        if len(x.shape) == 1: x = x.unsqueeze(0)
        x = torch.relu(self.embed(x)).unsqueeze(1)
        x, _ = self.attn(x, x, x)
        x = self.res(x.squeeze(1))
        policy = torch.sigmoid(self.head(x))
        value  = self.value_head(x)                   # FIX B1: return value alongside policy
        return policy, value

class BorealValueNetwork(nn.Module):
    """Hybrid RL critic — returns scalar value only."""
    def __init__(self, input_dim=15):
        super().__init__()
        self.input = nn.Linear(input_dim, 128)
        self.res1 = ResBlock(128)
        self.head = nn.Linear(128, 1)
    def forward(self, x):
        x = torch.relu(self.input(x))
        x = self.res1(x)
        return self.head(x)

# BorealTwinEngine: backward-compat alias
class BorealTwinEngine(BorealDirectEngine):
    pass


# ---------------------------------------------------------------------------
# FIX B2 — ActorCriticDirect and extract_direct_features (used by marathon
# trainer for per-unit bipartite matching — DIFFERENT from the 15-D model).
# ---------------------------------------------------------------------------

class ActorCriticDirect(nn.Module):
    """Cross-attention assignment network for per-unit training.
    Inputs : eff  (N_eff, EFF_FEAT)  — per-effector feature rows
             thr  (N_thr, THR_FEAT)  — per-threat feature rows
    Outputs: affinity (N_eff, N_thr) logits, value scalar
    """
    EFF_FEAT = 8
    THR_FEAT = 6

    def __init__(self, hidden=64):
        super().__init__()
        self.eff_proj  = nn.Linear(self.EFF_FEAT, hidden)
        self.thr_proj  = nn.Linear(self.THR_FEAT, hidden)
        self.value_head = nn.Sequential(nn.Linear(hidden, 32), nn.ReLU(), nn.Linear(32, 1))

    def forward(self, eff, thr):
        e = torch.relu(self.eff_proj(eff))    # (N_eff, hidden)
        t = torch.relu(self.thr_proj(thr))    # (N_thr, hidden)
        affinity = e @ t.T                     # (N_eff, N_thr)
        value    = self.value_head(e.mean(0))  # scalar
        return affinity, value


# Effector type → index for feature encoding
_EFF_TYPE_IDX = {
    "patriot-pac3": 0, "thaad": 1, "nasams": 2,
    "helws": 3, "coyote-block2": 4, "iris-t-sls": 5,
    "meteor": 6, "saab-nimbrix": 7, "lids-ew": 8,
}
_THR_TYPE_IDX = {
    "ballistic": 0, "hypersonic": 1, "cruise": 2,
    "drone": 3, "fighter": 4, "loiter": 3,
}
# Average Pk lookup (used in feature encoding)
_EFF_PK_AVG = {
    "patriot-pac3": 0.88, "thaad": 0.73, "nasams": 0.88,
    "helws": 0.95, "coyote-block2": 0.63, "iris-t-sls": 0.88,
    "meteor": 0.88, "saab-nimbrix": 0.97, "lids-ew": 0.85,
}
_EFF_RANGE = {
    "patriot-pac3": 5000, "thaad": 7200, "nasams": 3200,
    "helws": 999, "coyote-block2": 800, "iris-t-sls": 3500,
    "meteor": 4900, "saab-nimbrix": 200, "lids-ew": 300000,
}


def extract_direct_features(state, threats):
    """Extract per-effector (N_eff, 8) and per-threat (N_thr, 6) feature tensors.

    Returns (eff_tensor, thr_tensor, eff_meta, thr_meta) or
            (None, None, None, None) if no valid effectors or threats.
    """
    effector_rows, effector_meta = [], []
    for base in state.bases:
        for eff_name, count in base.inventory.items():
            if count <= 0:
                continue
            key = eff_name.lower()
            pk_avg  = _EFF_PK_AVG.get(key, 0.5)
            range_n = _EFF_RANGE.get(key, 1000) / 10000.0
            type_n  = _EFF_TYPE_IDX.get(key, len(_EFF_TYPE_IDX)) / len(_EFF_TYPE_IDX)
            row = [
                base.x  / 1000.0,   # normalised x
                base.y  / 1000.0,   # normalised y
                range_n,             # normalised range
                min(count / 50.0, 1.0),  # ammo level
                pk_avg,              # average Pk
                type_n,              # effector type encoding
                1.0,                 # availability flag
                0.5,                 # doctrine affinity (neutral)
            ]
            effector_rows.append(row)
            effector_meta.append({"base": base.name, "type": eff_name})

    threat_rows, threat_meta = [], []
    n_thr_types = len(_THR_TYPE_IDX) + 1
    for t in threats:
        ttype = t.estimated_type.lower().split("-")[0]
        type_n = _THR_TYPE_IDX.get(ttype, len(_THR_TYPE_IDX)) / n_thr_types
        row = [
            t.x           / 1000.0,
            t.y           / 1000.0,
            t.speed_kmh   / 10000.0,
            t.threat_value / 500.0,
            type_n,
            1.0,   # active flag
        ]
        threat_rows.append(row)
        threat_meta.append(t)

    if not effector_rows or not threat_rows:
        return None, None, None, None

    return (
        torch.tensor(effector_rows, dtype=torch.float32),
        torch.tensor(threat_rows,   dtype=torch.float32),
        effector_meta,
        threat_meta,
    )
