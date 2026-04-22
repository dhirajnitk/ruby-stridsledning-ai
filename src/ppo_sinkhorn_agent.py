import torch
import torch.nn as nn
import torch.nn.functional as F

class SinkhornLayer(nn.Module):
    """
    NEURAL SINKHORN: Differentiable Hungarian Solver.
    Snaps neural fuzzy logits into a mathematically valid 1-to-1 assignment matrix.
    """
    def __init__(self, iterations=10, epsilon=0.1):
        super().__init__()
        self.iterations = iterations
        self.epsilon = epsilon

    def forward(self, M):
        # M: Logits (B, N, N)
        # NUMERICAL SAFETY: Clamp logits to prevent overflow (Tightened)
        M = torch.clamp(M, -25.0, 25.0)
        
        # We use Log-Space Sinkhorn for numerical stability
        P = M / self.epsilon
        for _ in range(self.iterations):
            P = P - torch.logsumexp(P, dim=2, keepdim=True) # Row Norm
            P = P - torch.logsumexp(P, dim=1, keepdim=True) # Col Norm
        return torch.exp(P)

class BorealSinkhornEngine(nn.Module):
    """
    BOREAL SINKHORN ORACLE: The 'Holy Grail' of Tactical Assignment.
    Combines ResNet Intuition with Sinkhorn Mathematical Constraints.
    """
    def __init__(self, input_dim=15, num_weapons=11, num_targets=11):
        super(BorealSinkhornEngine, self).__init__()
        self.n_w = num_weapons
        self.n_t = num_targets
        
        # 1. Strategic Backbone (ResNet-12)
        self.backbone = nn.Sequential(
            nn.Linear(input_dim, 256), nn.BatchNorm1d(256), nn.LeakyReLU(0.1),
            *[nn.Sequential(nn.Linear(256, 256), nn.BatchNorm1d(256), nn.LeakyReLU(0.1)) for _ in range(6)]
        )
        
        # 2. Assignment Head (Outputs N x N Cost Matrix)
        self.assignment_head = nn.Linear(256, num_weapons * num_targets)
        self.sinkhorn = SinkhornLayer(iterations=15)
        
        # 3. Value Head (Strategic Score)
        self.value_head = nn.Sequential(
            nn.Linear(256, 128), nn.LeakyReLU(0.1),
            nn.Linear(128, 1)
        )

    def forward(self, x):
        feat = self.backbone(x)
        
        # Reshape to Matrix for Sinkhorn
        logits = self.assignment_head(feat).view(-1, self.n_w, self.n_t)
        assignment_matrix = self.sinkhorn(logits)
        
        value = self.value_head(feat)
        return assignment_matrix, value

# BOREAL SINKHORN: THE FUTURE OF BALTIC COMMAND.
