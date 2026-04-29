import torch
import numpy as np
import os
import sys

# Add src to path
sys.path.append("src")

from ppo_agent import BorealDirectEngine

def audit_supreme_v4():
    print("=== BOREAL SUPREME V4 HYPER-SCALE AUDIT ===")
    
    # 1. Load Model
    model = BorealDirectEngine(input_dim=25, output_dim=24)
    model_path = "models/ppo_strategic_v4_25d.pth"
    if not os.path.exists(model_path):
        print("Error: Model not found.")
        return
        
    model.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
    model.eval()
    print(f"Model loaded: {model_path} (Hyper-Scaled: 4 Residual Blocks, 16 Heads)")

    # 2. Load Hold-out Test Data
    data_path = "data/training/strategic_mega_corpus/hyper_gold_1k.npz"
    if not os.path.exists(data_path):
        print("Error: Training data for normalization not found.")
        return
        
    data = np.load(data_path)
    features = torch.tensor(data['features'], dtype=torch.float32)
    weights = torch.tensor(data['weights'], dtype=torch.float32)
    scores = torch.tensor(data['scores'], dtype=torch.float32)
    
    # Use global normalization from training
    f_mean = features.mean(0)
    f_std = features.std(0) + 1e-6
    s_mean = scores.mean()
    s_std = scores.std() + 1e-6

    # Test on a small slice (last 100 samples as hold-out)
    test_feats = features[-100:]
    test_weights = weights[-100:]
    test_scores = scores[-100:]
    
    test_feats_norm = (test_feats - f_mean) / f_std
    test_scores_norm = (test_scores - s_mean) / s_std

    # 3. Run Inference
    with torch.no_grad():
        pred_p, pred_v = model(test_feats_norm)
        
    # 4. Calculate Accuracy
    correct_p = 0
    for i in range(len(test_weights)):
        target_idx = torch.argmax(test_weights[i]).item()
        pred_idx = torch.argmax(pred_p[i]).item()
        if target_idx == pred_idx:
            correct_p += 1
            
    tactical_acc = (correct_p / len(test_weights)) * 100
    
    v_target = test_scores_norm.view(-1).numpy()
    v_pred = pred_v.view(-1).numpy()
    correlation = np.corrcoef(v_target, v_pred)[0, 1]
    
    print(f"Tactical Accuracy: {tactical_acc:.2f}%")
    print(f"Strategic Forecasting Correlation: {correlation:.4f}")
    
    if tactical_acc > 95 and correlation > 0.9:
        print("RESULT: GOAT STATUS ACHIEVED 🇸🇪🛡️")
    else:
        print("RESULT: Operational but refinement may continue.")

if __name__ == "__main__":
    audit_supreme_v4()
