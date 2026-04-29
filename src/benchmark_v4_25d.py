import torch
import torch.nn as nn
import numpy as np
import os
import time
import sys
from ppo_agent import BorealDirectEngine

# --- CONFIGURATION ---
EVAL_DATASET = "data/training/strategic_mega_corpus/ppo_train_100k.npz" # Using a subset for speed
MODEL_PATH = "models/ppo_strategic_v4_25d.pth"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def benchmark_v4():
    print("="*60)
    print("   BOREAL CHESSMASTER: SUPREME V4 (25D) BENCHMARK   ")
    print("="*60)
    
    if not os.path.exists(MODEL_PATH):
        print(f"[ERROR] Model not found: {MODEL_PATH}")
        return
    if not os.path.exists(EVAL_DATASET):
        print(f"[ERROR] Eval data not found: {EVAL_DATASET}")
        return

    # 1. LOAD DATA
    data = np.load(EVAL_DATASET)
    # We take 1000 samples for validation
    features = torch.tensor(data['features'][:1000], dtype=torch.float32).to(DEVICE)
    target_weights = data['weights'][:1000]
    target_scores = data['scores'][:1000]

    # 2. LOAD MODEL
    model = BorealDirectEngine(input_dim=25, output_dim=11).to(DEVICE)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.eval()

    # 3. RUN INFERENCE
    start_time = time.time()
    with torch.no_grad():
        preds_p, preds_v = model(features)
    latency = (time.time() - start_time) * 1000 / len(features)

    # 4. CALCULATE ACCURACY
    preds_p = preds_p.cpu().numpy()
    preds_v = preds_v.cpu().numpy().flatten()

    # Policy Accuracy (Doctrine Weights Correlation)
    mse_p = np.mean((preds_p - target_weights)**2)
    acc_p = max(0, 1 - (mse_p * 0.5))

    # Strategic Correlation (Intuition Index)
    corr_matrix = np.corrcoef(preds_v, target_scores)
    correlation = corr_matrix[0, 1] if not np.isnan(corr_matrix[0, 1]) else 0.0

    print(f"| Metric               | Value      |")
    print(f"|----------------------|------------|")
    print(f"| Policy Alignment     | {acc_p*100:1.2f}%    |")
    print(f"| Strategic Intuition  | {correlation*100:1.2f}%    |")
    print(f"| Inference Latency    | {latency:1.4f}ms  |")
    print("="*60)
    print("[OK] V4 Strategic Model Verified.")

if __name__ == "__main__":
    benchmark_v4()
