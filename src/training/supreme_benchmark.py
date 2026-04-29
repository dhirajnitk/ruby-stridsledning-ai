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

def benchmark_models():
    print("====================================================")
    print("   BOREAL SUPREME 7-MODEL BENCHMARK (UNBIASED)      ")
    print("====================================================")
    
    device = torch.device("cpu") # Use CPU for consistent latency measurement
    
    # Load Hold-out Data
    data_path = "data/evaluation/warzone_holdout_200.npz"
    if not os.path.exists(data_path):
        print("[ERROR] Hold-out data not found.")
        return
        
    data = np.load(data_path)
    features = torch.tensor(data['features'], dtype=torch.float32)
    true_weights = torch.tensor(data['weights'], dtype=torch.float32)
    true_scores = torch.tensor(data['scores'], dtype=torch.float32)
    
    # Load Normalization Scalers
    try:
        f_mean = torch.tensor(np.load("models/unified_24d_mean.npy"), dtype=torch.float32)
        f_std = torch.tensor(np.load("models/unified_24d_std.npy"), dtype=torch.float32)
        features = (features - f_mean) / f_std
    except:
        print("[WARNING] Normalization scalers missing. Results may be degraded.")

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
        ("Vanguard", "models/vanguard.pth", BorealDirectEngine(input_dim=25, output_dim=24)),
        ("Twin Oracle", "models/twin_oracle.pth", BorealDirectEngine(input_dim=25, output_dim=24)),
        ("Sentinel", "models/hybrid_rl.pth", ValueWrapper(input_dim=25)),
        ("Guardian", "models/guardian.pth", BorealDirectEngine(input_dim=25, output_dim=24))
    ]
    
    results = []
    
    for name, path, model in models_to_bench:
        if not os.path.exists(path):
            continue
            
        try:
            model.load_state_dict(torch.load(path, map_location=device, weights_only=True))
            model.to(device).eval()
            
            start_time = time.time()
            with torch.no_grad():
                if name == "Chronos":
                    # Simulate temporal seq for benchmark
                    seq = torch.stack([features * (1.0 - 0.005 * (20 - s)) for s in range(20)], dim=1)
                    pred_p, pred_v = model(seq)
                else:
                    pred_p, pred_v = model(features)
            
            elapsed = time.time() - start_time
            latency_ms = (elapsed / len(features)) * 1000
            
            # Metrics
            mse_p = nn.MSELoss()(pred_p, true_weights).item()
            mse_v = nn.MSELoss()(pred_v.view(-1), true_scores).item()
            
            # Top-1 Strategic Accuracy
            top1_true = torch.argmax(true_weights, dim=1)
            top1_pred = torch.argmax(pred_p, dim=1)
            accuracy = (top1_true == top1_pred).float().mean().item() * 100
            
            results.append({
                "Model": name,
                "Latency (ms)": f"{latency_ms:.3f}",
                "Strategy MSE": f"{mse_p:.6f}",
                "Value MSE": f"{mse_v:.2f}",
                "Top-1 Strategic Acc (%)": f"{accuracy:.1f}%"
            })
        except Exception as e:
            print(f"[ERROR] {name}: {e}")

    # Display Results in Markdown Table Format
    print("\n| Model | Latency (ms) | Strategy MSE | Value MSE | Top-1 Strat Acc |")
    print("| :--- | :--- | :--- | :--- | :--- |")
    for r in results:
        print(f"| {r['Model']} | {r['Latency (ms)']} | {r['Strategy MSE']} | {r['Value MSE']} | {r['Top-1 Strategic Acc (%)']} |")

if __name__ == "__main__":
    benchmark_models()
