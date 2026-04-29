import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import sys

# Ensure src is in path
sys.path.insert(0, "src")
from ppo_agent import BorealDirectEngine, BorealValueNetwork
from training.ppo_chronos_gru import BorealChronosGRU
from ppo_titan_transformer import BorealTitanEngine

DATA_PATH = "data/training/strategic_mega_corpus/ppo_train_hard_24d_100k.npz"
DEVICE = torch.device("cpu")
EPOCHS = 1 # Even faster
BATCH_SIZE = 64

def train_model(name, model, features, weights, scores, save_path):
    print(f"\n[PHASE] Training {name}...")
    optimizer = optim.AdamW(model.parameters(), lr=1e-4)
    criterion_p = nn.MSELoss()
    criterion_v = nn.MSELoss()
    
    for epoch in range(EPOCHS):
        model.train()
        # Train on first 1000 samples for speed demo
        for i in range(0, 1000, BATCH_SIZE):
            idx = slice(i, i+BATCH_SIZE)
            b_feat = features[idx]
            b_weight = weights[idx]
            b_score = scores[idx]
            
            optimizer.zero_grad()
            if "Chronos" in name:
                seq = [b_feat * (1.0 - 0.005 * (20 - s)) for s in range(20)]
                x_seq = torch.stack(seq, dim=1)
                pred_p, pred_v = model(x_seq)
            else:
                pred_p, pred_v = model(b_feat)
                
            loss = criterion_p(pred_p, b_weight) + 2.0 * criterion_v(pred_v.view(-1), b_score.view(-1))
            loss.backward()
            optimizer.step()
        
        torch.save(model.state_dict(), save_path)
    print(f"[SUCCESS] {name} trained and saved.")

def train_missing():
    data = np.load(DATA_PATH)
    features = torch.tensor(data['features'][:1000], dtype=torch.float32)
    weights = torch.tensor(data['weights'][:1000], dtype=torch.float32)
    scores = torch.tensor(data['scores'][:1000], dtype=torch.float32)
    
    # 3. Chronos
    train_model("Chronos", BorealChronosGRU(input_dim=25, output_dim=24), features, weights, scores, "models/chronos_v4_25d.pth")
    # 4. Vanguard
    train_model("Vanguard", BorealDirectEngine(input_dim=25, output_dim=24), features, weights, scores, "models/vanguard.pth")
    # 5. Twin Oracle
    train_model("Twin Oracle", BorealDirectEngine(input_dim=25, output_dim=24), features, weights, scores, "models/twin_oracle.pth")
    # 6. Sentinel
    class ValueWrapper(nn.Module):
        def __init__(self, input_dim=25):
            super().__init__()
            self.net = BorealValueNetwork(input_dim=input_dim)
        def forward(self, x):
            return torch.zeros((x.shape[0], 24)), self.net(x)
    train_model("Sentinel", ValueWrapper(input_dim=25), features, weights, scores, "models/hybrid_rl.pth")
    # 7. Guardian
    train_model("Guardian", BorealDirectEngine(input_dim=25, output_dim=24), features, weights, scores, "models/guardian.pth")

if __name__ == "__main__":
    train_missing()
