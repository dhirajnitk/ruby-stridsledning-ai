import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import sys
from ppo_chronos_gru import BorealChronosGRU

# --- CONFIGURATION ---
DATASET_PATH = "data/training/strategic_mega_corpus/chronos_60_maneuver.npz"
MODEL_SAVE_PATH = "models/boreal_chronos_gru.pth"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
EPOCHS = 100 
LR = 1e-3

def train_chronos():
    print(f"====================================================")
    print(f"   BOREAL CHRONOS: TEMPORAL STRATEGIC FORGE         ")
    print(f"====================================================")
    
    # 1. Load Data
    if not os.path.exists(DATASET_PATH):
        print(f"[ERROR] Chronos Corpus not found at {DATASET_PATH}")
        return

    data = np.load(DATASET_PATH)
    features = torch.tensor(data['features'], dtype=torch.float32).to(DEVICE)
    weights = torch.tensor(data['weights'], dtype=torch.float32).to(DEVICE)
    scores = torch.tensor(data['scores'], dtype=torch.float32).to(DEVICE)
    
    # 2. Initialize Chronos Engine
    model = BorealChronosGRU(input_dim=15, output_dim=11).to(DEVICE)
    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-2)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)
    
    criterion_p = nn.MSELoss()
    criterion_v = nn.MSELoss()
    criterion_rank = nn.MarginRankingLoss(margin=0.5) 
    
    num_samples = len(features)
    batch_size = 64
    
    print(f"[TRAIN] Commencing Temporal Immersion (Samples: {num_samples})...")
    
    for epoch in range(EPOCHS):
        model.train()
        indices = torch.randperm(num_samples)
        epoch_loss = 0
        
        for i in range(0, num_samples, batch_size):
            idx = indices[i:i+batch_size]
            b_feat = features[idx] # (Batch, 10, 15)
            b_weights = weights[idx]
            b_scores = scores[idx]
            
            # Forward
            pred_p, pred_v = model(b_feat)
            
            # 1. Tactical Loss (Targeting the Final State)
            loss_p = criterion_p(pred_p, b_weights)
            
            # 2. Strategic Loss (Value + Ranking)
            loss_v = criterion_v(pred_v.view(-1), b_scores.view(-1))
            
            if len(b_scores) > 1:
                v_a, v_b = pred_v[:-1].view(-1), pred_v[1:].view(-1)
                t_a, t_b = b_scores[:-1].view(-1), b_scores[1:].view(-1)
                ranking_target = torch.sign(t_a - t_b)
                loss_ranking = criterion_rank(v_a, v_b, ranking_target)
            else:
                loss_ranking = 0
                
            # Unified Loss
            loss = 1.0 * loss_p + 5.0 * loss_v + 10.0 * loss_ranking
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            
        scheduler.step()
        if (epoch + 1) % 10 == 0:
            print(f"  [EPOCH {epoch+1}/{EPOCHS}] Loss: {epoch_loss:.4f} (LR: {optimizer.param_groups[0]['lr']:.6f})")

    torch.save(model.state_dict(), MODEL_SAVE_PATH)
    print(f"[SAVE] Boreal Chronos Oracle secured: {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    train_chronos()
