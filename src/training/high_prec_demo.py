import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os
import sys

# Ensure src is in path
sys.path.insert(0, "src")
from ppo_agent import BorealDirectEngine

def run_high_prec_demo():
    print("====================================================")
    print("   BOREAL HIGH-PRECISION STRATEGIC DEMO             ")
    print("====================================================")
    
    device = torch.device("cpu")
    data_path = "data/training/strategic_mega_corpus/high_prec_signal_1k.npz"
    data = np.load(data_path)
    features = torch.tensor(data['features'], dtype=torch.float32)
    weights = torch.tensor(data['weights'], dtype=torch.float32)
    scores = torch.tensor(data['scores'], dtype=torch.float32)
    
    # Normalize features
    f_mean, f_std = features.mean(0), features.std(0) + 1e-6
    features = (features - f_mean) / f_std
    
    # Z-score Normalization for Scores (Handling negative penalties)
    s_mean, s_std = scores.mean(), scores.std() + 1e-6
    target_scores = (scores - s_mean) / s_std
    
    model = BorealDirectEngine(input_dim=25, output_dim=24).to(device)
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    criterion_p = nn.MSELoss()
    criterion_v = nn.MSELoss()
    
    print("[PHASE] Training Deep Residual Brain (40 Epochs)...")
    for epoch in range(40):
        model.train()
        optimizer.zero_grad()
        
        pred_p, pred_v_norm = model(features)
        
        loss_p = criterion_p(pred_p, weights)
        # Target scores are already logged and normalized
        loss_v = criterion_v(pred_v_norm.view(-1), target_scores.view(-1))
        
        loss = loss_p + 1.0 * loss_v
        loss.backward()
        optimizer.step()
        
        if (epoch+1) % 10 == 0:
            # Eval on same set for demo convergence check
            model.eval()
            with torch.no_grad():
                pp, vv_norm = model(features)
                
                # Tactical Accuracy
                top1_true = torch.argmax(weights, dim=1)
                top1_pred = torch.argmax(pp, dim=1)
                tact_acc = (top1_true == top1_pred).float().mean().item() * 100
                
                # Strategic Accuracy (1 - Normalized MSE)
                strat_mse = nn.MSELoss()(vv_norm.view(-1), target_scores.view(-1)).item()
                strat_acc = max(0.0, 1.0 - strat_mse) * 100
                
                print(f"  Epoch {epoch+1} | Loss: {loss.item():.4f} | Tactical: {tact_acc:.1f}% | Strategic: {strat_acc:.1f}%")
                
    # Save the High-Precision Model
    torch.save(model.state_dict(), "models/ppo_strategic_v4_25d_highprec.pth")
    print("\n[SUCCESS] HIGH-PRECISION BRAIN FORGED.")

if __name__ == "__main__":
    run_high_prec_demo()
