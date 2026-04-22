import torch
import torch.nn as nn
import numpy as np
import os
from ppo_agent import BorealDirectEngine, BorealValueNetwork
from ppo_chronos_gru import BorealChronosGRU

# --- CONFIGURATION (INTELLIGENCE-INTEGRATED) ---
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
INPUT_DIM = 50 * 11
SEQ_LEN = 20

def load_data(path):
    if not os.path.exists(path):
        return None
    data = np.load(path)
    feat = data['features'].astype(np.float32)
    weights = data['weights'].astype(np.float32)
    return feat, weights

def evaluate_v3():
    print("====================================================")
    print("   BOREAL STRATEGIC AUDIT V3.5: FINAL FLEET       ")
    print("====================================================")
    
    # Initialize Models (InputDim=550)
    supreme = BorealDirectEngine(input_dim=INPUT_DIM * SEQ_LEN, output_dim=3).to(DEVICE)
    chronos = BorealChronosGRU(input_dim=INPUT_DIM, output_dim=3).to(DEVICE)
    v_net = BorealValueNetwork(input_dim=INPUT_DIM * SEQ_LEN).to(DEVICE)
    
    # Load standardized Elite weights
    supreme.load_state_dict(torch.load("models/boreal_supreme_elite_v35.pt"))
    chronos.load_state_dict(torch.load("models/boreal_chronos_v31.pt"))
    v_net.load_state_dict(torch.load("models/boreal_hybrid_elite_v35.pt"))
    
    supreme.eval()
    chronos.eval()
    v_net.eval()
    
    targets = [
        ("data/training/strategic_mega_corpus/boreal_object_gold_eval.npz", "GOLD EVAL"),
        ("data/training/strategic_mega_corpus/boreal_object_hard_eval.npz", "HARD TOTAL")
    ]
    
    for path, name in targets:
        data = load_data(path)
        if data is None: continue
        feat, weights = data
        
        # 1. Supreme Elite (Direct Action)
        x_flat = torch.tensor(feat.reshape(len(feat), -1)).to(DEVICE)
        with torch.no_grad():
            pred_p, _ = supreme(x_flat)
            mse_s = nn.MSELoss()(pred_p, torch.tensor(weights).to(DEVICE)).item()
            
        # 2. Chronos V3.1 (Temporal Mastery)
        x_seq = torch.tensor(feat.transpose(0, 2, 1, 3).reshape(len(feat), 20, 550)).to(DEVICE)
        with torch.no_grad():
            pred_p_c, _ = chronos(x_seq)
            mse_c = nn.MSELoss()(pred_p_c, torch.tensor(weights).to(DEVICE)).item()
            
        # 3. Hybrid Elite (Strategic Wisdom / Value)
        # We load actual scores for Value Network evaluation
        scores = np.load(path)['scores'].astype(np.float32).reshape(-1, 1)
        with torch.no_grad():
            pred_v = v_net(x_flat)
            mse_v = nn.MSELoss()(pred_v, torch.tensor(scores).to(DEVICE)).item()
            
        # Accuracy Proxy: 1.0 - sqrt(MSE)
        acc_s = max(0, 1.0 - np.sqrt(mse_s))
        acc_c = max(0, 1.0 - np.sqrt(mse_c))
        acc_v = max(0, 1.0 - np.sqrt(mse_v))
        
        print(f"[{name}] Supreme: {acc_s*100:.2f}% | Chronos: {acc_c*100:.2f}% | Hybrid Value: {acc_v*100:.2f}%")

    print("====================================================")
    print("[COMPLETE] STRATEGIC AUDIT V3 SECURED.")
    print("====================================================")

if __name__ == "__main__":
    evaluate_v3()
