import torch
import torch.nn as nn
import numpy as np
import time
import os
import sys

# Ensure src is in path
sys.path.insert(0, "src")
from ppo_agent import BorealDirectEngine, BorealValueNetwork
from training.ppo_chronos_gru import BorealChronosGRU
from ppo_titan_transformer import BorealTitanEngine

def final_validation_suite():
    print("====================================================")
    print("   BOREAL SUPREME 7-MODEL NATIONAL VALIDATION       ")
    print("====================================================")
    
    device = torch.device("cpu")
    data_path = "data/evaluation/high_prec_validation_500.npz"
    if not os.path.exists(data_path):
        print("[ERROR] High-precision validation data not found.")
        return
        
    data = np.load(data_path)
    features = torch.tensor(data['features'], dtype=torch.float32)
    true_weights = torch.tensor(data['weights'], dtype=torch.float32)
    true_scores = torch.tensor(data['scores'], dtype=torch.float32)
    
    # Load Scalers
    try:
        f_mean = torch.tensor(np.load("models/unified_24d_mean.npy"), dtype=torch.float32)
        f_std = torch.tensor(np.load("models/unified_24d_std.npy"), dtype=torch.float32)
        features = (features - f_mean) / f_std
        
        s_mean = torch.tensor(np.load("models/unified_24d_score_mean.npy"), dtype=torch.float32)
        s_std = torch.tensor(np.load("models/unified_24d_score_std.npy"), dtype=torch.float32)
    except:
        print("[WARNING] Normalization scalers missing.")
        s_mean, s_std = 0.0, 1.0

    class ValueWrapper(nn.Module):
        def __init__(self, input_dim=25):
            super().__init__()
            self.net = BorealValueNetwork(input_dim=input_dim)
        def forward(self, x): return torch.zeros((x.shape[0], 24)), self.net(x)

    models_to_bench = [
        ("Supreme V4", "models/ppo_strategic_v4_25d.pth", BorealDirectEngine(25, 24)),
        ("Titan", "models/titan.pth", BorealTitanEngine(25, 24)),
        ("Chronos", "models/chronos_v4_25d.pth", BorealChronosGRU(25, 24)),
        ("Vanguard", "models/vanguard.pth", BorealDirectEngine(25, 24)),
        ("Twin Oracle", "models/twin_oracle.pth", BorealDirectEngine(25, 24)),
        ("Sentinel", "models/hybrid_rl.pth", ValueWrapper(25)),
        ("Guardian", "models/guardian.pth", BorealDirectEngine(25, 24))
    ]
    
    print("| Model | Tactical Accuracy | Strategic Accuracy | Status |")
    print("| :--- | :--- | :--- | :--- |")
    
    for name, path, model in models_to_bench:
        if not os.path.exists(path):
            print(f"| {name} | -- | -- | MISSING |")
            continue
            
        try:
            model.load_state_dict(torch.load(path, map_location=device, weights_only=True))
            model.to(device).eval()
            
            with torch.no_grad():
                if name == "Chronos":
                    seq = torch.stack([features * (1.0 - 0.005 * (20 - s)) for s in range(20)], dim=1)
                    pred_p, pred_v_norm = model(seq)
                else:
                    pred_p, pred_v_norm = model(features)
                    
                # Denormalize
                pred_v = pred_v_norm.view(-1) * s_std + s_mean
                
                # Tactical Acc (Top-1)
                top1_true = torch.argmax(true_weights, dim=1)
                top1_pred = torch.argmax(pred_p, dim=1)
                tactical_acc = (top1_true == top1_pred).float().mean().item() * 100
                
                # Strategic Acc (1 - Relative Error)
                abs_err = torch.abs(pred_v - true_scores)
                mape = (abs_err / (torch.abs(true_scores) + 1e-6)).mean().item()
                strategic_acc = max(0.0, 1.0 - mape) * 100
                
                print(f"| {name} | {tactical_acc:.1f}% | {strategic_acc:.1f}% | OK |")
        except Exception as e:
            print(f"| {name} | ERR | ERR | {str(e)[:10]}... |")

if __name__ == "__main__":
    final_validation_suite()
