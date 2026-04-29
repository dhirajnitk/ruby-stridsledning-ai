import torch
import torch.nn as nn
import torch.nn.functional as F

class BorealChronosGRU(nn.Module):
    """
    BOREAL CHRONOS GRU: Temporal Strategic Oracle.
    Processes sequences of theater telemetry to predict mission-risk.
    """
    def __init__(self, input_dim=25, output_dim=24, hidden_dim=2048, num_layers=4):
        super(BorealChronosGRU, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # 1. Hyper-Temporal Backbone (Bidirectional GRU)
        self.gru = nn.GRU(input_dim, hidden_dim, num_layers, batch_first=True, dropout=0.2, bidirectional=True)
        
        # 2. Deep Strategic Wisdom Path (Value)
        self.critic_head = nn.Sequential(
            nn.Linear(hidden_dim * 2, 2048), nn.LeakyReLU(0.1),
            nn.Linear(2048, 2048), nn.LeakyReLU(0.1),
            nn.Linear(2048, 1024), nn.LeakyReLU(0.1),
            nn.Linear(1024, 512), nn.LeakyReLU(0.1),
            nn.Linear(512, 1)
        )
        
        # 3. Tactical Action Path (Policy)
        self.actor_head = nn.Sequential(
            nn.Linear(hidden_dim * 2, 512), nn.LeakyReLU(0.1),
            nn.Linear(512, 512), nn.LeakyReLU(0.1),
            nn.Linear(512, output_dim), nn.Sigmoid()
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
