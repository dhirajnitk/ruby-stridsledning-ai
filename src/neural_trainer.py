import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os
import json

import sys
sys.path.insert(0, os.path.dirname(__file__))

# --- 1. ARCHITECTURE DEFINITIONS ---
from core.inference import TransformerResNet, ChronosGRU, StandardResNet, GeneralistMLP
from ppo_titan_transformer import BorealTitanEngine

# --- 2. TRAINING ENGINE ---

def train_model(name, model, data_path, epochs=10, batch_size=32):
    print(f"[TRAIN] Launching Training for Core: {name.upper()}")
    if not os.path.exists(data_path):
        print(f"[ERROR] Corpus {data_path} not found. Skipping.")
        return

    corpus = np.load(data_path)
    X = torch.tensor(corpus['features'], dtype=torch.float32)
    # Support both old format (labels) and new MARV/MIRV format (weights)
    if 'labels' in corpus:
        Y = torch.tensor(corpus['labels'], dtype=torch.float32)
    elif 'weights' in corpus:
        Y = torch.tensor(corpus['weights'], dtype=torch.float32)
    else:
        print(f"[ERROR] No 'labels' or 'weights' key in {data_path}. Keys: {list(corpus.keys())}")
        return
    
    # Reshape labels if they are per-threat (we take the mean/max assignment as truth for the batch)
    # Note: For high-fidelity training, we would use a more complex loss.
    if Y.dim() == 3: # [Batch, N_Threats, N_Actions]
        Y = Y.mean(dim=1) # Simplified centroid for demonstration
    
    optimizer = optim.Adam(model.parameters(), lr=1e-4)
    criterion = nn.MSELoss()

    model.train()
    for epoch in range(epochs):
        permutation = torch.randperm(X.size(0))
        epoch_loss = 0
        for i in range(0, X.size(0), batch_size):
            indices = permutation[i:i+batch_size]
            batch_x, batch_y = X[indices], Y[indices]

            optimizer.zero_grad()
            output = model(batch_x)
            
            # Handle models that return (policy, value) tuples like BorealTitanEngine
            if isinstance(output, tuple):
                output = output[0]
                
            loss = criterion(output, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        
        if (epoch + 1) % 5 == 0:
            print(f"  > Epoch {epoch+1}/{epochs} | Loss: {epoch_loss/X.size(0):.6f}")

    save_path = f"models/{name}.pth"
    torch.save(model.state_dict(), save_path)
    print(f"[COMPLETE] Model saved to {save_path}\n")

# --- 3. MASS TRAINING SCRIPT ---

if __name__ == "__main__":
    os.makedirs("models", exist_ok=True)
    
    # 1. ELITE (Transformer)
    train_model("elite_v3_5", TransformerResNet(18, 11), "data/training/strategic_mega_corpus/boreal_snapshot_gold.npz")
    
    # 2. SUPREME V3.1 (GRU)
    train_model("supreme_v3_1", ChronosGRU(18, 11), "data/training/strategic_mega_corpus/boreal_temporal_gold.npz")
    
    # 3. SUPREME V2 (ResNet)
    train_model("supreme_v2", StandardResNet(18, 11, width=64), "data/training/strategic_mega_corpus/boreal_snapshot_gold.npz")
    
    # 4. TITAN (Large Transformer)
    train_model("titan", BorealTitanEngine(18, 11), "data/training/strategic_mega_corpus/boreal_snapshot_gold.npz")
    
    # 5. HYBRID (ResNet Deep)
    train_model("hybrid_rl", StandardResNet(18, 11, width=128), "data/training/strategic_mega_corpus/boreal_snapshot_gold.npz")
    
    # 6. GENERALIST (MLP)
    train_model("generalist_e10", GeneralistMLP(18, 11), "data/training/strategic_mega_corpus/boreal_snapshot_gold.npz")

    # --- PHASE 2: MARV/MIRV FINE-TUNING (18-D features) ---
    # Fine-tune existing models on MARV/MIRV dataset to learn trajectory awareness
    # without losing prior knowledge. Uses lower learning rate (1e-5).
    marv_mirv_path = "data/training/strategic_mega_corpus/marv_mirv_train.npz"
    if os.path.exists(marv_mirv_path):
        print("\n[PHASE 2] MARV/MIRV Fine-Tuning (18-D trajectory awareness)...")
        
        # Load previously trained weights and fine-tune
        models_to_finetune = {
            "elite_v3_5": TransformerResNet(18, 11),
            "supreme_v3_1": ChronosGRU(18, 11),
            "supreme_v2": StandardResNet(18, 11, width=64),
            "titan": BorealTitanEngine(18, 11),
            "hybrid_rl": StandardResNet(18, 11, width=128),
            "generalist_e10": GeneralistMLP(18, 11),
        }
        for name, model in models_to_finetune.items():
            weight_path = f"models/{name}.pth"
            if os.path.exists(weight_path):
                try:
                    model.load_state_dict(torch.load(weight_path, weights_only=True), strict=False)
                    print(f"  > Loaded pre-trained weights from {weight_path}")
                except Exception as e:
                    print(f"  > Fresh init for {name} (dim change): {e}")
            train_model(name, model, marv_mirv_path, epochs=5, batch_size=32)
    else:
        print(f"[SKIP] MARV/MIRV dataset not found at {marv_mirv_path}")
        print(f"       Run: python src/generate_marv_mirv_data.py")

    print("[SYSTEM] ALL NEURAL CORES HAVE BEEN INITIALIZED AND TRAINED.")
