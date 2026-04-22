import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import sys
from ppo_sinkhorn_agent import BorealSinkhornEngine

# --- CONFIGURATION ---
DATASET_PATH = "data/training/strategic_mega_corpus/ppo_train_high_entropy_100k.npz"
MODEL_SAVE_PATH = "models/boreal_sinkhorn_oracle.pth"
DEVICE = torch.device("cpu") 
EPOCHS = 50 # Deep Burn for Structural Mastery

def train_sinkhorn():
    print(f"====================================================")
    print(f"   BOREAL RESEARCH: SINKHORN DEEP BURN (50 EP)      ")
    print(f"====================================================")
    
    # 1. Load Data
    data = np.load(DATASET_PATH)
    features = torch.tensor(data['features'], dtype=torch.float32).to(DEVICE)
    weights = torch.tensor(data['weights'], dtype=torch.float32).to(DEVICE)
    scores = torch.tensor(data['scores'], dtype=torch.float32).to(DEVICE)
    
    # 2. Initialize Model
    model = BorealSinkhornEngine(input_dim=15, num_weapons=11, num_targets=11).to(DEVICE)
    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-2)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=15, gamma=0.5) # LR Cooling
    criterion_assign = nn.MSELoss() 
    criterion_value = nn.MSELoss()
    
    num_samples = len(features)
    batch_size = 128
    
    print(f"[TRAIN] Commencing Deep Structural Mastery (Samples: {num_samples})...")
    
    for epoch in range(EPOCHS):
        model.train()
        indices = torch.randperm(num_samples)
        epoch_loss = 0
        
        for i in range(0, num_samples, batch_size):
            idx = indices[i:i+batch_size]
            b_feat = features[idx]
            b_weights = weights[idx]
            b_scores = scores[idx]
            
            # Diagonal Target Matrix (Weapon-Target Alignment)
            target_matrix = torch.diag_embed(b_weights) 
            
            # Forward
            pred_matrix, pred_val = model(b_feat)
            
            # Loss Components
            loss_a = criterion_assign(pred_matrix, target_matrix)
            loss_v = criterion_value(pred_val.view(-1), b_scores.view(-1))
            
            if len(b_scores) > 1:
                v_a, v_b = pred_val[:-1].view(-1), pred_val[1:].view(-1)
                t_a, t_b = b_scores[:-1].view(-1), b_scores[1:].view(-1)
                ranking_target = torch.sign(t_a - t_b)
                loss_ranking = nn.MarginRankingLoss(margin=0.5)(v_a, v_b, ranking_target)
            else:
                loss_ranking = 0
                
            loss = 20.0 * loss_a + 5.0 * loss_v + 5.0 * loss_ranking
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            
        scheduler.step()
        if (epoch + 1) % 5 == 0:
            print(f"  [EPOCH {epoch+1}/{EPOCHS}] Loss: {epoch_loss:.4f} (LR: {optimizer.param_groups[0]['lr']:.6f})")

    torch.save(model.state_dict(), MODEL_SAVE_PATH)
    print(f"[SAVE] Sinkhorn Oracle secured: {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    train_sinkhorn()
