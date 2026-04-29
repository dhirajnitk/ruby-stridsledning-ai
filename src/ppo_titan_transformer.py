import torch
import torch.nn as nn
import torch.nn.functional as F

class TitanBlock(nn.Module):
    """
    BOREAL TITAN BLOCK: Self-Attention Transformer Encoder.
    Masters non-linear relationships between theater features.
    """
    def __init__(self, dim, heads=8, dropout=0.1):
        super().__init__()
        self.attn = nn.MultiheadAttention(dim, heads, dropout=dropout, batch_first=True)
        self.norm1 = nn.LayerNorm(dim)
        self.mlp = nn.Sequential(
            nn.Linear(dim, dim * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(dim * 4, dim),
            nn.Dropout(dropout)
        )
        self.norm2 = nn.LayerNorm(dim)

    def forward(self, x):
        # x: (Batch, Seq, Dim)
        attn_out, _ = self.attn(x, x, x)
        x = self.norm1(x + attn_out)
        mlp_out = self.mlp(x)
        x = self.norm2(x + mlp_out)
        return x

class BorealTitanEngine(nn.Module):
    """
    BOREAL TITAN TRANSFORMER: The 75% Intuition Oracle.
    """
    def __init__(self, input_dim=25, output_dim=24, latent_dim=1024):
        super(BorealTitanEngine, self).__init__()
        # 1. Feature Projection (Lifts 25 -> 1024)
        self.input_proj = nn.Linear(input_dim, latent_dim)
        
        # 2. Hyper-Transformer Core (12 Stages of Self-Attention)
        self.transformer = nn.Sequential(*[TitanBlock(latent_dim, heads=16) for _ in range(12)])
        
        # 3. Tactical Path (Policy)
        self.actor_head = nn.Sequential(
            nn.Linear(latent_dim, 1024), nn.LeakyReLU(0.1),
            nn.Linear(1024, 1024), nn.LeakyReLU(0.1),
            nn.Linear(1024, 512), nn.LeakyReLU(0.1),
            nn.Linear(512, output_dim), nn.Sigmoid()
        )
        
        # 4. Deep Strategic Path (High-Precision Value)
        self.critic_head = nn.Sequential(
            nn.Linear(latent_dim, 2048), nn.LeakyReLU(0.1),
            nn.Linear(2048, 1024), nn.LeakyReLU(0.1),
            nn.Linear(1024, 512), nn.LeakyReLU(0.1),
            nn.Linear(512, 1)
        )

    def forward(self, x):
        # x shape: (Batch, 15) -> (Batch, 1, 15)
        x = x.unsqueeze(1)
        x = self.input_proj(x)
        x = self.transformer(x)
        # Global Pooling
        x = x.squeeze(1)
        
        policy = self.actor_head(x)
        value = self.critic_head(x)
        return policy, value

# TITAN: THE ULTIMATE BALTIC STRATEGIST.
