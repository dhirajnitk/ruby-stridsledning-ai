import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import time
import sys

# Ensure src is in path
sys.path.insert(0, "src")
from ppo_agent import BorealDirectEngine, BorealValueNetwork
from training.ppo_chronos_gru import BorealChronosGRU
from ppo_titan_transformer import BorealTitanEngine

# --- CONFIGURATION ---
DATA_PATH = "data/training/strategic_mega_corpus/hyper_gold_1k.npz"
DEVICE = torch.device("cpu")
EPOCHS = 50
BATCH_SIZE = 32
LR = 1e-3

def train_model(name, model, features, weights, scores, save_path):
    print(f"\n[PHASE] Training {name}...")
    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-3)
    criterion_p = nn.MSELoss()
    criterion_v = nn.MSELoss()
    
    num_samples = len(features)
    indices = np.arange(num_samples)
    
    max_epochs = 5 if "Chronos" in name else EPOCHS
    for epoch in range(max_epochs):
        model.train()
        train_loss = 0
        np.random.shuffle(indices)
        
        for i in range(0, num_samples, BATCH_SIZE):
            idx = indices[i:i+BATCH_SIZE]
            b_feat = features[idx].to(DEVICE)
            b_weight = weights[idx].to(DEVICE)
            b_score = scores[idx].to(DEVICE)
            
            optimizer.zero_grad()
            
            if "Chronos" in name:
                seq = torch.stack([b_feat * (1.0 - 0.005 * (20 - s)) for s in range(20)], dim=1)
                pred_p, pred_v = model(seq)
            else:
                pred_p, pred_v = model(b_feat)
                
            loss_p = criterion_p(pred_p, b_weight)
            loss_v = criterion_v(pred_v.view(-1), b_score.view(-1))
            
            loss = loss_p + 1.0 * loss_v
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
        if (epoch + 1) % 10 == 0:
            print(f"  Epoch {epoch+1}/{EPOCHS} | Loss: {train_loss/(num_samples/BATCH_SIZE):.4f}")
            
    torch.save(model.state_dict(), save_path)
    print(f"[SUCCESS] {name} finalized.")

def run_final_7_model_cycle():
    print("====================================================")
    print("   BOREAL SUPREME 7-MODEL FINAL SYNCHRONIZATION     ")
    print("====================================================")
    
    if not os.path.exists(DATA_PATH):
        print(f"[ERROR] Data not found.")
        return

    data = np.load(DATA_PATH)
    features = torch.tensor(data['features'], dtype=torch.float32)
    weights = torch.tensor(data['weights'], dtype=torch.float32)
    scores = torch.tensor(data['scores'], dtype=torch.float32)
    
    # NORMALIZATION
    f_mean, f_std = features.mean(0), features.std(0) + 1e-6
    features = (features - f_mean) / f_std
    
    s_mean, s_std = scores.mean(), scores.std() + 1e-6
    scores_norm = (scores - s_mean) / s_std
    
    np.save("models/unified_24d_mean.npy", f_mean.numpy())
    np.save("models/unified_24d_std.npy", f_std.numpy())
    np.save("models/unified_24d_score_mean.npy", s_mean.numpy())
    np.save("models/unified_24d_score_std.npy", s_std.numpy())

    # 1-7 Models
    train_model("Supreme V4", BorealDirectEngine(25, 24), features, weights, scores_norm, "models/ppo_strategic_v4_25d.pth")
    train_model("Titan", BorealTitanEngine(25, 24), features, weights, scores_norm, "models/titan.pth")
    train_model("Chronos", BorealChronosGRU(25, 24), features, weights, scores_norm, "models/chronos_v4_25d.pth")
    train_model("Vanguard", BorealDirectEngine(25, 24), features, weights, scores_norm, "models/vanguard.pth")
    train_model("Twin Oracle", BorealDirectEngine(25, 24), features, weights, scores_norm, "models/twin_oracle.pth")
    
    class ValueWrapper(nn.Module):
        def __init__(self, input_dim=25):
            super().__init__()
            self.net = BorealValueNetwork(input_dim=input_dim)
        def forward(self, x): return torch.zeros((x.shape[0], 24)), self.net(x)
    
    train_model("Sentinel", ValueWrapper(25), features, weights, scores_norm, "models/hybrid_rl.pth")
    train_model("Guardian", BorealDirectEngine(25, 24), features, weights, scores_norm, "models/guardian.pth")

    print("\n====================================================")
    print("   MISSION COMPLETE: 7-MODEL SUITE SYNCHRONIZED     ")
    print("====================================================")

if __name__ == "__main__":
    run_final_7_model_cycle()
