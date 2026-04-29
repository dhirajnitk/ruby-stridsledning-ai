import torch
import numpy as np
import os
import sys
import torch.nn as nn

# Add src to path
sys.path.append("src")

from ppo_agent import BorealDirectEngine
from ppo_titan_transformer import BorealTitanEngine
from training.ppo_chronos_gru import BorealChronosGRU

def run_final_audit():
    print("=== BOREAL GOAT TOURNAMENT: DEFINITIVE AUDIT ===")
    
    # 1. Load Blind Eval Data
    eval_path = "data/training/strategic_mega_corpus/goat_eval_blind_500.npz"
    if not os.path.exists(eval_path):
        print(f"Error: Eval data not found at {eval_path}")
        return
        
    data = np.load(eval_path)
    features = torch.tensor(data['features'], dtype=torch.float32)
    weights = torch.tensor(data['weights'], dtype=torch.float32)
    scores = torch.tensor(data['scores'], dtype=torch.float32)
    
    # Load Unified Normalization
    f_mean = np.load("models/unified_24d_mean.npy")
    f_std = np.load("models/unified_24d_std.npy")
    s_mean = np.load("models/unified_24d_score_mean.npy")
    s_std = np.load("models/unified_24d_score_std.npy")

    features_norm = (features - torch.tensor(f_mean)) / (torch.tensor(f_std) + 1e-6)
    scores_norm = (scores - torch.tensor(s_mean)) / (torch.tensor(s_std) + 1e-6)

    # 2. Model Registry (Strict Alignment)
    # Using specific architectures to avoid caching issues
    models_to_test = [
        ("Supreme V4", BorealDirectEngine(25, 24), "models/ppo_strategic_v4_25d.pth"),
        ("Titan-12",   BorealTitanEngine(25, 24, latent_dim=1024), "models/titan.pth"),
        ("Chronos-4",  BorealChronosGRU(25, 24), "models/chronos_v4_25d.pth"),
        ("Vanguard",   BorealDirectEngine(25, 24), "models/vanguard.pth"),
        ("Twin Oracle",BorealDirectEngine(25, 24), "models/twin_oracle.pth"),
        ("Sentinel",   BorealDirectEngine(25, 24), "models/sentinel.pth"),
        ("Guardian",   BorealDirectEngine(25, 24), "models/guardian.pth"),
    ]

    results = []

    for name, model, path in models_to_test:
        if not os.path.exists(path):
            print(f"Skipping {name}: checkpoint not found.")
            continue
            
        print(f"Evaluating {name}...")
        try:
            model.load_state_dict(torch.load(path, map_location="cpu", weights_only=True))
            model.eval()
        except Exception as e:
            print(f"Error loading {name}: {e}")
            continue
        
        with torch.no_grad():
            if "Chronos" in name:
                pred_p, pred_v = model(features_norm.unsqueeze(1))
                pred_p, pred_v = pred_p.squeeze(1), pred_v.squeeze(1)
            else:
                pred_p, pred_v = model(features_norm)
        
        # Tactical Accuracy
        correct_p = 0
        for i in range(len(weights)):
            target_idx = torch.argmax(weights[i]).item()
            pred_idx = torch.argmax(pred_p[i]).item()
            if target_idx == pred_idx: correct_p += 1
        tactical_acc = (correct_p / len(weights)) * 100
        
        # Strategic Correlation
        v_target = scores_norm.view(-1).numpy()
        v_pred = pred_v.view(-1).numpy()
        correlation = np.corrcoef(v_target, v_pred)[0, 1]
        
        results.append({
            "Model": name,
            "Tactical": f"{tactical_acc:.2f}%",
            "Strategic": f"{correlation:.4f}"
        })

    # 3. Output Table (No Emojis for Windows compatibility)
    print("\n| Model | Tactical Acc | Strategic Corr | Status |")
    print("| :--- | :--- | :--- | :--- |")
    for r in results:
        status = "GOAT" if float(r['Tactical'].strip('%')) > 95 or float(r['Strategic']) > 0.9 else "Operational"
        print(f"| {r['Model']} | {r['Tactical']} | {r['Strategic']} | {r['Status'] if 'Status' in r else status} |")

if __name__ == "__main__":
    run_final_audit()
