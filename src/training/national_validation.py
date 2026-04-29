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

def final_validation():
    print("====================================================")
    print("   BOREAL NATIONAL VALIDATION (UNBIASED SEED: 999)  ")
    print("====================================================")
    
    device = torch.device("cpu")
    
    # Load National Validation Data
    data_path = "data/evaluation/national_validation_500.npz"
    if not os.path.exists(data_path):
        print("[ERROR] National Validation data not found.")
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
        def forward(self, x):
            return torch.zeros((x.shape[0], 24)), self.net(x)

    models_to_bench = [
        ("Supreme V4", "models/ppo_strategic_v4_25d.pth", BorealDirectEngine(input_dim=25, output_dim=24)),
        ("Titan", "models/titan.pth", BorealTitanEngine(input_dim=25, output_dim=24)),
        ("Chronos", "models/chronos_v4_25d.pth", BorealChronosGRU(input_dim=25, output_dim=24)),
        ("Sentinel", "models/hybrid_rl.pth", ValueWrapper(input_dim=25))
    ]
    
    results = []
    
    for name, path, model in models_to_bench:
        if not os.path.exists(path): continue
        model.load_state_dict(torch.load(path, map_location=device, weights_only=True))
        model.to(device).eval()
        
        with torch.no_grad():
            if name == "Chronos":
                seq = torch.stack([features * (1.0 - 0.005 * (20 - s)) for s in range(20)], dim=1)
                pred_p, pred_v_norm = model(seq)
            else:
                pred_p, pred_v_norm = model(features)
                
            # Denormalize score for Strategic Accuracy calculation
            pred_v = pred_v_norm.view(-1) * s_std + s_mean
            
            # 1. Tactical Accuracy: Top-1 Effector Match
            top1_true = torch.argmax(true_weights, dim=1)
            top1_pred = torch.argmax(pred_p, dim=1)
            tactical_acc = (top1_true == top1_pred).float().mean().item() * 100
            
            # 2. Strategic Accuracy: Value Precision (1 - MAPE)
            # MAPE: Mean Absolute Percentage Error
            # Use a small epsilon to avoid div by zero
            abs_err = torch.abs(pred_v - true_scores)
            mape = (abs_err / (true_scores + 1e-6)).mean().item()
            strategic_acc = max(0.0, 1.0 - mape) * 100

            results.append({
                "Model": name,
                "Tactical Acc (%)": f"{tactical_acc:.1f}%",
                "Strategic Acc (%)": f"{strategic_acc:.1f}%"
            })

    print("\n| Model | Tactical Accuracy (Weapon) | Strategic Accuracy (Survival) |")
    print("| :--- | :--- | :--- |")
    for r in results:
        print(f"| {r['Model']} | {r['Tactical Acc (%)']} | {r['Strategic Acc (%)']} |")

if __name__ == "__main__":
    final_validation()
