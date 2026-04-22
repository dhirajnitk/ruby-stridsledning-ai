import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
import os
import json
from sklearn.preprocessing import StandardScaler

# --- 1. MODEL ARCHITECTURE ---
class PolicyNetwork(nn.Module):
    def __init__(self, input_dim=10, output_dim=14):
        super(PolicyNetwork, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 64), nn.ReLU(),
            nn.Linear(64, 64), nn.ReLU(),
            nn.Linear(64, output_dim), nn.Softplus()
        )
    def forward(self, x): return self.network(x)

# --- 2. TRAINING LOGIC ---
def train_policy():
    print("="*60)
    print("  BOREAL CHESSMASTER — POLICY NETWORK TRAINING")
    print("="*60)
    
    data_path = "data/rl_training_data.csv"
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found. Run rl_data_collector.py first.")
        return

    df = pd.read_csv(data_path)
    feature_cols = ["num_threats", "avg_dist", "min_dist", "total_val", "fighters", "sams", "drones", "cap_sams", "weather_bin", "blend_ratio"]
    X_raw = df[feature_cols].values
    
    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)
    
    # Tactical Reflex Teacher Function
    y = []
    for row in X_raw:
        mults = np.ones(14)
        num_threats, avg_dist, min_dist, total_val, fighters, sams, drones, cap_sams, weather_bin, blend = row
        if num_threats > 5:
            mults[5] = 1.5 + (num_threats * 0.05) # economy_force
            mults[6] = 1.2 # swarm_penalty
        if min_dist < 150:
            mults[1] = 2.0 # point_defense
            mults[0] = 1.3 # t_int
        if cap_sams < 3: mults[10] = 2.5 # capital_reserve
        y.append(mults)
    
    X_train = torch.tensor(X, dtype=torch.float32)
    y_train = torch.tensor(y, dtype=torch.float32)
    
    model = PolicyNetwork(input_dim=10, output_dim=14)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    for epoch in range(300):
        model.train()
        optimizer.zero_grad()
        loss = criterion(model(X_train), y_train)
        loss.backward()
        optimizer.step()
        if (epoch+1) % 50 == 0: print(f"Epoch [{epoch+1}/300] | Loss: {loss.item():.6f}")

    os.makedirs("models", exist_ok=True)
    params = {"scaler_mean": scaler.mean_.tolist(), "scaler_scale": scaler.scale_.tolist()}
    with open("models/policy_network_params.json", "w") as f: json.dump(params, f)
    torch.save(model.state_dict(), "models/policy_network.pth")
    torch.save(model.state_dict(), "models/doctrine_network.pth")
    print(f"\n[OK] Policy Network trained and saved to models/doctrine_network.pth")

if __name__ == "__main__":
    train_policy()
