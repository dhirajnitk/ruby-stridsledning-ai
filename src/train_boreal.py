import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import time

import sys
# --- CONFIGURATION ---
DEFAULT_DATASET = "data/training/strategic_mega_corpus/ppo_train_high_entropy_100k.npz"
DATASET_PATH = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DATASET
MODEL_SAVE_PATH = "models/boreal_direct_supreme.pth"
BATCH_SIZE = 128
EPOCHS = int(sys.argv[2]) if len(sys.argv) > 2 else 100
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def train_ppo():
    print(f"====================================================")
    print(f"   BOREAL STRATEGIC FORGE: CALIBRATION SPRINT       ")
    print(f"   DATASET: {os.path.basename(DATASET_PATH)}")
    print(f"====================================================")
    
    # 1. Load Data
    if not os.path.exists(DATASET_PATH):
        print(f"[ERROR] Dataset not found at {DATASET_PATH}")
        return
        
    data = np.load(DATASET_PATH)
    raw_features = torch.tensor(data['features'], dtype=torch.float32).to(DEVICE)
    raw_weights = data['weights']
    raw_scores = data['scores']
    
    # --- ORACLE CALIBRATION: Z-SCORE STANDARDIZATION ---
    feat_mean = raw_features.mean(dim=0, keepdim=True)
    feat_std = raw_features.std(dim=0, keepdim=True) + 1e-3
    features = torch.clamp((raw_features - feat_mean) / feat_std, -10.0, 10.0)
    
    # Save Normalization for Deployment
    np.save("models/feature_normalization.npy", np.array([feat_mean.cpu().numpy(), feat_std.cpu().numpy()]))
    
    # Normalize Targets
    weight_max = torch.tensor(np.max(raw_weights, axis=0) + 1e-6, dtype=torch.float32).to(DEVICE)
    target_weights = (torch.tensor(raw_weights, dtype=torch.float32).to(DEVICE) / weight_max)
    
    score_mean = float(np.mean(raw_scores))
    score_std = float(np.std(raw_scores)) + 1e-6
    target_scores = ((torch.tensor(raw_scores, dtype=torch.float32).to(DEVICE) - score_mean) / score_std)
    
    np.save("models/doctrine_normalization.npy", weight_max.cpu().numpy())
    np.save("models/value_normalization.npy", np.array([score_mean, score_std]))
    
    # 2. Initialize Model (Boreal DirectEngine)
    print(f"[MODEL] Initializing Boreal Strategic Direct Engine...")
    from ppo_agent import BorealDirectEngine
    model = BorealDirectEngine(input_dim=15, output_dim=11).to(DEVICE)
    
    optimizer = optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-2)
    
    # Robust Fixed LR for Hackathon Stability
    num_samples = len(features)
    optimizer = optim.AdamW(model.parameters(), lr=5e-4, weight_decay=1e-2)
    
    criterion_actor = nn.MSELoss()
    criterion_critic = nn.HuberLoss(delta=1.0) # Robust Strategic Signal

    # 3. Training Loop
    print(f"[TRAIN] Commencing Strategic Super-Convergence (Epochs: {EPOCHS})...", flush=True)
    
    for epoch in range(EPOCHS):
        model.train()
        epoch_loss = 0
        batch_count = 0
        indices = torch.randperm(num_samples)
        
        for i in range(0, num_samples, BATCH_SIZE):
            idx = indices[i:i+BATCH_SIZE]
            batch_features = features[idx]
            batch_targets = target_weights[idx]
            batch_scores = target_scores[idx]
            
            # Forward pass
            predicted_weights, predicted_values = model(batch_features)
            
            # Dual Loss: Oracle Strategic Balance
            loss_actor = criterion_actor(predicted_weights, batch_targets)
            loss_critic = criterion_critic(predicted_values.view(-1), batch_scores.view(-1))
            
            # 3. STRATEGIC RANKING LOSS (Intuition Upgrade)
            if len(batch_scores) > 1:
                v_a = predicted_values[:-1].view(-1)
                v_b = predicted_values[1:].view(-1)
                t_a = batch_scores[:-1].view(-1)
                t_b = batch_scores[1:].view(-1)
                
                # Ranking: 1 if A > B, -1 if A < B
                ranking_target = torch.sign(t_a - t_b)
                loss_ranking = nn.MarginRankingLoss(margin=0.5)(v_a, v_b, ranking_target) # Larger margin for elite separation
                
                # 4. CONTRASTIVE STRATEGIC LOSS (The 80% Frontier)
                # Force high-score scenarios apart from low-score scenarios
                # We define "Extreme Contrast" pairs
                dist = torch.abs(t_a - t_b)
                contrast_mask = dist > 1.0 # Only contrast scenarios with significantly different outcomes
                if contrast_mask.any():
                    loss_contrast = torch.mean(torch.abs(v_a[contrast_mask] - v_b[contrast_mask]))
                else:
                    loss_contrast = 0
            else:
                loss_ranking = 0
                loss_contrast = 0
                
            loss = loss_actor + 5.0 * loss_critic + 2.0 * loss_ranking + 1.0 * loss_contrast
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            
            epoch_loss += loss.item()
            batch_count += 1
            if batch_count % 10 == 0:
                print(".", end="", flush=True) # Heartbeat
            
        avg_loss = epoch_loss / (num_samples / BATCH_SIZE)
        print(f"\n[EPOCH {epoch+1}/{EPOCHS}] Loss: {avg_loss:.6f}", flush=True)

        if (epoch + 1) % 5 == 0:
            ckpt_path = f"models/ppo_checkpoint_epoch_{epoch+1}.pth"
            torch.save(model.state_dict(), ckpt_path)
            print(f"[CHECKPOINT] Strategic Oracle secured: {ckpt_path}", flush=True)

    # 4. Finalize
    print(f"\n[COMPLETE] Model Forged.", flush=True)
    os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
    torch.save(model.state_dict(), MODEL_SAVE_PATH)
    print(f"[SAVE] Final Hackathon Model secured: {MODEL_SAVE_PATH}", flush=True)

if __name__ == "__main__":
    train_ppo()
