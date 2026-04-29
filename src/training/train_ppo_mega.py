import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os
import time
from ppo_agent import BorealDirectEngine

# --- CONFIGURATION ---
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
DATA_PATH = "data/training/strategic_mega_corpus/ppo_train_hard_25d_100k.npz"
MODEL_SAVE_PATH = "models/ppo_strategic_v4_25d.pth"
EPOCHS = 30
BATCH_SIZE = 64
LR = 1e-4

def train_ppo_mega():
    print("="*60, flush=True)
    print("   BOREAL CHESSMASTER: SUPREME MEGA-CORPUS TRAINING   ", flush=True)
    print("   Architecture: 25-D Tactical Feature Vector         ", flush=True)
    print("="*60, flush=True)

    if not os.path.exists(DATA_PATH):
        print(f"[ERROR] Data not found: {DATA_PATH}", flush=True)
        return

    # 1. LOAD DATA
    print(f"[1/4] Loading Mega-Corpus from {DATA_PATH}...", flush=True)
    data = np.load(DATA_PATH)
    X = torch.tensor(data['features'], dtype=torch.float32)
    Y_weights = torch.tensor(data['weights'], dtype=torch.float32)
    Y_score = torch.tensor(data['scores'], dtype=torch.float32).unsqueeze(1)
    
    dataset = torch.utils.data.TensorDataset(X, Y_weights, Y_score)
    loader = torch.utils.data.DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    # 2. INITIALIZE MODEL
    print(f"[2/4] Initializing BorealDirectEngine (25 -> 11)...", flush=True)
    model = BorealDirectEngine(input_dim=25, output_dim=11).to(DEVICE)
    optimizer = optim.Adam(model.parameters(), lr=LR)
    criterion_p = nn.MSELoss() # Policy Loss (Doctrine Weights)
    criterion_v = nn.MSELoss() # Value Loss (Mission Score)

    # 3. TRAINING LOOP
    print(f"[3/4] Starting Tabula Rasa Training on {len(X)} samples...", flush=True)
    start_time = time.time()
    
    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0
        
        for batch_x, batch_y_p, batch_y_v in loader:
            batch_x, batch_y_p, batch_y_v = batch_x.to(DEVICE), batch_y_p.to(DEVICE), batch_y_v.to(DEVICE)
            
            optimizer.zero_grad()
            pred_p, pred_v = model(batch_x)
            
            loss_p = criterion_p(pred_p, batch_y_p)
            loss_v = criterion_v(pred_v, batch_y_v)
            
            loss = loss_p + 0.5 * loss_v
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        avg_loss = total_loss / len(loader)
        elapsed = (time.time() - start_time) / 60
        print(f"Epoch [{epoch+1}/{EPOCHS}] | Avg Loss: {avg_loss:.6f} | Elapsed: {elapsed:.1f}m", flush=True)

    # 4. SAVE & SECURE
    print(f"[4/4] Training Complete. Securing model to {MODEL_SAVE_PATH}...")
    os.makedirs("models", exist_ok=True)
    torch.save(model.state_dict(), MODEL_SAVE_PATH)
    # Save a copy as 'doctrine_network_v4.pth' for the engine
    torch.save(model.state_dict(), "models/doctrine_network_v4.pth")
    print("="*60)
    print("   MISSION COMPLETE: SUPREME STRATEGIC BRAIN FORGED   ")
    print("="*60)

if __name__ == "__main__":
    train_ppo_mega()
