import torch
import torch.nn as nn
import numpy as np
import time
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from core.inference import TransformerResNet, ChronosGRU, StandardResNet, GeneralistMLP
from ppo_titan_transformer import BorealTitanEngine

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
EVAL_DATASET = "data/training/strategic_mega_corpus/marv_mirv_eval.npz"

def benchmark():
    print("===============================================================")
    print("   BOREAL CHESSMASTER: MARV/MIRV 18-D MODEL BENCHMARK          ")
    print("===============================================================")
    
    if not os.path.exists(EVAL_DATASET):
        print(f"[ERROR] Evaluation dataset not found at {EVAL_DATASET}")
        return

    data = np.load(EVAL_DATASET)
    features = torch.tensor(data['features'], dtype=torch.float32).to(DEVICE)
    target_weights = data['weights'] # Shape: (N, 11)
    
    # Optional: if weights need normalization, but in generate_marv_mirv_data.py they are in [0, 1]
    targets = torch.tensor(target_weights, dtype=torch.float32).to(DEVICE)

    models_to_eval = {
        "Elite V3.5 (Transformer)": ("elite_v3_5", TransformerResNet(18, 11)),
        "Supreme V3.1 (GRU)": ("supreme_v3_1", ChronosGRU(18, 11)),
        "Supreme V2 (ResNet-64)": ("supreme_v2", StandardResNet(18, 11, width=64)),
        "Titan Oracle (Transformer)": ("titan", BorealTitanEngine(18, 11)),
        "Hybrid RL V8 (ResNet-128)": ("hybrid_rl", StandardResNet(18, 11, width=128)),
        "Generalist E10 (MLP)": ("generalist_e10", GeneralistMLP(18, 11)),
    }

    results = []

    for model_name, (filename, model) in models_to_eval.items():
        path = f"models/{filename}.pth"
        if not os.path.exists(path):
            print(f"[WARNING] {path} missing, skipping...")
            continue
        
        try:
            model.load_state_dict(torch.load(path, map_location=DEVICE, weights_only=True))
            model = model.to(DEVICE)
            model.eval()
        except Exception as e:
            print(f"[ERROR] Could not load {filename}: {e}")
            continue

        with torch.no_grad():
            # Warmup
            _ = model(features[:10])
            
            # Latency benchmark
            start_time = time.perf_counter()
            output = model(features)
            end_time = time.perf_counter()
            
            # Handle Titan returning (policy, value)
            if isinstance(output, tuple):
                output = output[0]
                
            latency_ms = ((end_time - start_time) * 1000) / features.size(0)
            
            # Accuracy metric (MSE to Percentage)
            mse = nn.MSELoss()(output, targets).item()
            # 0.0 MSE = 100%, 0.1 MSE = 90%, etc.
            accuracy = max(0.0, (1.0 - (mse * 5.0)) * 100) # Scaled so differences are visible
            
        results.append({
            "Name": model_name,
            "Accuracy": accuracy,
            "MSE": mse,
            "Latency": latency_ms
        })

    # Sort by accuracy descending
    results.sort(key=lambda x: x['Accuracy'], reverse=True)

    print(f"\nTested on {features.size(0)} hard MARV/MIRV sequences.")
    print(f"{'Model Name':<28} | {'Accuracy':<10} | {'MSE':<8} | {'Latency (ms/sample)':<20}")
    print("-" * 75)
    for r in results:
        print(f"{r['Name']:<28} | {r['Accuracy']:>5.2f}%    | {r['MSE']:.4f}   | {r['Latency']:.4f} ms")
    print("===============================================================\n")

    # Document Results
    doc_content = "# Boreal Chessmaster: MARV/MIRV 18-D Model Benchmarks\n\n"
    doc_content += "These benchmarks measure the accuracy and inference latency of the newly trained 18-D models on the dedicated MARV/MIRV evaluation dataset.\n\n"
    doc_content += f"**Dataset:** `{EVAL_DATASET}` ({features.size(0)} samples)\n"
    doc_content += f"**Device:** `{DEVICE}`\n\n"
    doc_content += "| Model Name | Accuracy (Scaled) | Mean Squared Error | Latency (ms/sample) |\n"
    doc_content += "|---|---|---|---|\n"
    for r in results:
        doc_content += f"| {r['Name']} | {r['Accuracy']:.2f}% | {r['MSE']:.4f} | {r['Latency']:.4f} ms |\n"
    
    with open("../docs/MODEL_BENCHMARKS_MARV_MIRV.md", "w") as f:
        f.write(doc_content)
    print("=> Documented results to docs/MODEL_BENCHMARKS_MARV_MIRV.md")

if __name__ == "__main__":
    benchmark()
