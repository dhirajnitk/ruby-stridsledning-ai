import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os
from ppo_agent import BorealDirectEngine, BorealValueNetwork
from ppo_chronos_gru import BorealChronosGRU

# --- CONFIGURATION (INTELLIGENCE-INTEGRATED) ---
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
INPUT_DIM = 50 * 11 # 50 Objects * 11 Features (Physics + Intel)
SEQ_LEN = 20
EPOCHS = 10
BATCH_SIZE = 32

def load_data(path):
    if not os.path.exists(path):
        return None
    data = np.load(path)
    # Reshape to (Samples, SeqLen, 550) for GRU or (Samples, 50, 20, 11) for ResNet
    feat = data['features'].astype(np.float32) # (N, 50, 20, 11)
    score = data['scores'].astype(np.float32).reshape(-1, 1)
    # Weights placeholder (Doctrine)
    weights = data['weights'].astype(np.float32) 
    return feat, score, weights

def train_strategic_v3():
    print("====================================================")
    print("   BOREAL STRATEGIC TRAINING V3: INTEL INTEGRATION  ")
    print("====================================================")
    
    # Load Training Data
    train_path = "data/training/strategic_mega_corpus/boreal_object_gold_train.npz"
    data = load_data(train_path)
    if data is None:
        print("[ERROR] No training data found.")
        return
    feat, score, weights = data
    
    # Initialize Models (InputDim=550)
    supreme = BorealDirectEngine(input_dim=INPUT_DIM * SEQ_LEN, output_dim=3).to(DEVICE)
    chronos = BorealChronosGRU(input_dim=INPUT_DIM, output_dim=3).to(DEVICE)
    v_net = BorealValueNetwork(input_dim=INPUT_DIM * SEQ_LEN).to(DEVICE)
    
    opt_s = optim.Adam(supreme.parameters(), lr=1e-4)
    opt_c = optim.Adam(chronos.parameters(), lr=1e-4)
    opt_v = optim.Adam(v_net.parameters(), lr=1e-4)
    criterion = nn.MSELoss()
    
    print(f"[START] Training on {len(feat)} Intel-Integrated Samples...")
    
    for epoch in range(EPOCHS):
        # Supreme Training (Spatial/Flattened)
        x_flat = torch.tensor(feat.reshape(len(feat), -1)).to(DEVICE)
        y = torch.tensor(weights).to(DEVICE)
        
        opt_s.zero_grad()
        pred_p, pred_v = supreme(x_flat)
        loss = criterion(pred_p, y)
        loss.backward()
        opt_s.step()
        
        # Chronos Training (Temporal)
        # Reshape to (Batch, 20, 550)
        x_seq = torch.tensor(feat.transpose(0, 2, 1, 3).reshape(len(feat), 20, 550)).to(DEVICE)
        
        opt_c.zero_grad()
        pred_p_c, pred_v_c = chronos(x_seq)
        loss_c = criterion(pred_p_c, y)
        loss_c.backward()
        opt_c.step()
        
        # Value Network Training
        opt_v.zero_grad()
        pred_v_net = v_net(x_flat)
        loss_v = criterion(pred_v_net, torch.tensor(score).to(DEVICE))
        loss_v.backward()
        opt_v.step()
        
        if epoch % 2 == 0:
            print(f"Epoch {epoch} | Supreme Loss: {loss.item():.4f} | Chronos Loss: {loss_c.item():.4f} | Value Loss: {loss_v.item():.4f}")

    # SAVE MODELS
    os.makedirs("models", exist_ok=True)
    torch.save(supreme.state_dict(), "models/boreal_supreme_elite_v35.pt")
    torch.save(chronos.state_dict(), "models/boreal_chronos_v31.pt")
    torch.save(v_net.state_dict(), "models/boreal_hybrid_elite_v35.pt")
    print("[COMPLETE] STRATEGIC V3.5 ELITE MODELS SECURED.")

if __name__ == "__main__":
    train_strategic_v3()
