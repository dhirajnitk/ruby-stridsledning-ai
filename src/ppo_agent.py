import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class ActorCriticDirect(nn.Module):
    """
    An Actor-Critic network that dynamically pairs effectors to threats using
    an embedding-based affinity matrix (Attention mechanism).
    This completely bypasses the Hungarian algorithm.
    """
    def __init__(self, effector_dim=6, threat_dim=6, embed_dim=64):
        super().__init__()
        
        # Effector Encoder (e.g. [x, y, speed, type_id, base_id, cost])
        self.effector_encoder = nn.Sequential(
            nn.Linear(effector_dim, 128),
            nn.ReLU(),
            nn.Linear(128, embed_dim)
        )
        
        # Threat Encoder (e.g. [x, y, speed, type_id, target_id, value])
        self.threat_encoder = nn.Sequential(
            nn.Linear(threat_dim, 128),
            nn.ReLU(),
            nn.Linear(128, embed_dim)
        )
        
        # Value Head (Critic) - uses the mean pooled embeddings to assess global state
        self.critic_head = nn.Sequential(
            nn.Linear(embed_dim * 2, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )

    def forward(self, effectors, threats):
        """
        effectors: Tensor of shape (num_effectors, effector_dim)
        threats: Tensor of shape (num_threats, threat_dim)
        Returns:
            affinity_matrix: (num_effectors, num_threats) representing assignment probabilities
            value: (1,) strategic consequence score estimation
        """
        if effectors.size(0) == 0 or threats.size(0) == 0:
            return torch.zeros((effectors.size(0), threats.size(0))), torch.tensor([0.0])

        # 1. Embed effectors and threats
        eff_emb = self.effector_encoder(effectors)  # (N, embed_dim)
        thr_emb = self.threat_encoder(threats)      # (M, embed_dim)
        
        # 2. Compute Affinity Matrix (N x M) via Dot Product Attention
        # scaled by sqrt(embed_dim) for stability
        affinity = torch.matmul(eff_emb, thr_emb.T) / (eff_emb.size(1) ** 0.5)
        
        # 3. Global State Pooling for Critic
        eff_pool = eff_emb.mean(dim=0)
        thr_pool = thr_emb.mean(dim=0)
        global_state = torch.cat([eff_pool, thr_pool], dim=0)
        value = self.critic_head(global_state)
        
        return affinity, value

# Helper to map string types to numeric IDs
TYPE_MAP = {"fighter": 0, "sam": 1, "drone": 2, "bomber": 3, "fast-mover": 4, "ghost": 5, "hypersonic": 6}

def extract_direct_features(state, threats):
    # Extract effectors
    eff_list = []
    eff_meta = []
    
    # Give bases numeric IDs
    base_ids = {b.name: float(i) for i, b in enumerate(state.bases)}
    
    for b in state.bases:
        for eff_type, count in b.inventory.items():
            eff_type = eff_type.lower()
            if count > 0:
                cost = 150 if eff_type == "fighter" else (50 if eff_type == "sam" else 15)
                speed = 2400 if eff_type == "fighter" else (3500 if eff_type == "sam" else 400)
                # Expand stack into individual available units up to a reasonable cap
                for _ in range(min(count, 50)): 
                    eff_list.append([
                        b.x / 3000.0, 
                        b.y / 3000.0, 
                        speed / 5000.0, 
                        TYPE_MAP.get(eff_type, 0.0), 
                        base_ids.get(b.name, 0.0), 
                        cost / 200.0
                    ])
                    eff_meta.append({"base": b.name, "type": eff_type, "cost": cost})
                    
    # Extract threats
    thr_list = []
    thr_meta = []
    for t in threats:
        thr_list.append([
            t.x / 3000.0,
            t.y / 3000.0,
            t.speed_kmh / 5000.0,
            TYPE_MAP.get(t.estimated_type.lower(), 0.0),
            base_ids.get(t.heading, -1.0),
            t.threat_value / 250.0
        ])
        thr_meta.append(t)
        
    if not eff_list or not thr_list:
        return None, None, eff_meta, thr_meta
        
    return torch.tensor(eff_list, dtype=torch.float32), torch.tensor(thr_list, dtype=torch.float32), eff_meta, thr_meta

def get_ppo_assignments(model, state, threats):
    eff_tensor, thr_tensor, eff_meta, thr_meta = extract_direct_features(state, threats)
    if eff_tensor is None:
        return []
        
    with torch.no_grad():
        affinity, _ = model(eff_tensor, thr_tensor)
        
    # Convert affinity to probabilities using Sigmoid
    probs = torch.sigmoid(affinity).numpy()
    
    assignments = []
    assigned_threats = set()
    assigned_effectors = set()
    
    # Greedy decoding: pick highest affinities first
    flat_indices = np.argsort(probs.flatten())[::-1]
    
    for idx in flat_indices:
        eff_idx = idx // probs.shape[1]
        thr_idx = idx % probs.shape[1]
        
        if eff_idx in assigned_effectors or thr_idx in assigned_threats:
            continue
            
        if probs[eff_idx, thr_idx] > 0.05: # Emergency aggression threshold for swarms
            a_meta = eff_meta[eff_idx]
            t_meta = thr_meta[thr_idx]
            assignments.append({
                "base": a_meta["base"],
                "effector": a_meta["type"],
                "threat_id": t_meta.id,
                "pk": round(float(probs[eff_idx, thr_idx]), 2) # use affinity as pseudo-pk
            })
            assigned_effectors.add(eff_idx)
            assigned_threats.add(thr_idx)
            
    return assignments
