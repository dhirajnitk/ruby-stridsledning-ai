"""
src/ppo_chronos_gru.py
Tactical Chronos GRU — 15-D per-scenario input, 11-D effector priority output.

FIX B4: benchmark_boreal.py imported `from ppo_chronos_gru import BorealChronosGRU`
but no such file existed in src/.  The only BorealChronosGRU was in
src/training/ppo_chronos_gru.py with input_dim=550 (strategic/sequential use).

This wrapper provides the *tactical* variant (15-D → 11-D, returns (policy, value))
that benchmark_boreal.py and any other src-level scripts expect.
"""
import torch
import torch.nn as nn


class BorealChronosGRU(nn.Module):
    """Tactical Chronos GRU: 15-D theater snapshot → 11-D effector weights.

    Architecture
    ────────────
    Input : (Batch, 15)  — normalised theater feature vector
    ┌─ GRU(15, hidden, num_layers) with the 15-D vector treated as a single
    │   timestep (unsqueezed to (Batch, 1, 15)).
    ├─ actor_head  → (Batch, output_dim)  policy / effector priority weights
    └─ critic_head → (Batch, 1)           strategic value estimate

    Output: (policy, value) tuple
    """

    def __init__(self, input_dim: int = 15, output_dim: int = 11,
                 hidden_dim: int = 128, num_layers: int = 2):
        super().__init__()
        self.gru = nn.GRU(
            input_dim, hidden_dim,
            num_layers=num_layers,
            batch_first=True,
        )
        self.actor_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, output_dim),
            nn.Sigmoid(),
        )
        self.critic_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )

    def forward(self, x: torch.Tensor):
        # x: (Batch, 15)  →  unsqueeze to (Batch, 1, 15) for GRU
        if x.dim() == 2:
            x = x.unsqueeze(1)          # (Batch, 1, 15)
        _, h = self.gru(x)              # h: (num_layers, Batch, hidden)
        last_hidden = h[-1]             # (Batch, hidden)
        policy = self.actor_head(last_hidden)   # (Batch, output_dim)
        value  = self.critic_head(last_hidden)  # (Batch, 1)
        return policy, value
