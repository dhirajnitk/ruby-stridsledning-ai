import torch
import torch.nn as nn
import torch.nn.functional as F

class BorealChronosGRU(nn.Module):
    """
    BOREAL CHRONOS GRU: Temporal Strategic Oracle.
    Processes sequences of theater telemetry to predict mission-risk.
    """
    def __init__(self, input_dim=550, output_dim=3, hidden_dim=512, num_layers=2):
        super(BorealChronosGRU, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # 1. Temporal Backbone (Bidirectional GRU)
        self.gru = nn.GRU(input_dim, hidden_dim, num_layers, batch_first=True, dropout=0.1, bidirectional=True)
        
        # 2. Strategic Wisdom Path (Value)
        # Hidden dim is doubled for bidirectional
        self.critic_head = nn.Sequential(
            nn.Linear(hidden_dim * 2, 1024), nn.LeakyReLU(0.1),
            nn.Linear(1024, 512), nn.LeakyReLU(0.1),
            nn.Linear(512, 1)
        )
        
        # 3. Tactical Action Path (Policy)
        self.actor_head = nn.Sequential(
            nn.Linear(hidden_dim * 2, 256), nn.LeakyReLU(0.1),
            nn.Linear(256, output_dim), nn.Sigmoid()
        )

    def forward(self, x):
        # x shape: (Batch, SeqLen, InputDim)
        out, _ = self.gru(x)
        
        # We take the final hidden state output for prediction
        last_hidden = out[:, -1, :]
        
        value = self.critic_head(last_hidden)
        policy = self.actor_head(last_hidden)
        
        return policy, value

# CHRONOS: MASTERING THE FLOW OF THE BALTIC.
