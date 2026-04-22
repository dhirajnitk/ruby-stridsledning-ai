import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
import os
import json
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# --- 1. MODEL ARCHITECTURE ---
class ValueNetwork(nn.Module):
    def __init__(self, input_dim=15):
        super(ValueNetwork, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 64), nn.ReLU(),
            nn.Linear(64, 32), nn.ReLU(),
            nn.Linear(32, 16), nn.ReLU(),
            nn.Linear(16, 1)
        )
    def forward(self, x):
        return self.network(x)

# --- 2. TRAINING LOGIC ---
def train_value():
    print("="*60)
    print("  BOREAL CHESSMASTER — VALUE NETWORK TRAINING")
    print("="*60)
    
    data_path = "data/rl_training_data.csv"
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found. Run rl_data_collector.py first.")
        return

    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} samples for training.")

    # 1. Feature Engineering (15 Features)
    numeric_cols = ["num_threats", "avg_dist", "min_dist", "total_val", "fighters", "sams", "drones", "cap_sams", "weather_bin", "blend_ratio"]
    doctrine_names = sorted(df["primary_doctrine"].unique())
    
    # Preprocessing
    X_num = df[numeric_cols].values
    scaler = StandardScaler()
    X_num_scaled = scaler.fit_transform(X_num)
    
    # One-hot doctrine
    X_doc = pd.get_dummies(df["primary_doctrine"])[doctrine_names].values
    X = np.hstack([X_num_scaled, X_doc])
    y = df["target_mcts_score"].values.reshape(-1, 1)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)

    # Tensors
    X_train_t = torch.tensor(X_train, dtype=torch.float32)
    y_train_t = torch.tensor(y_train, dtype=torch.float32)
    X_test_t = torch.tensor(X_test, dtype=torch.float32)
    y_test_t = torch.tensor(y_test, dtype=torch.float32)

    # Train
    model = ValueNetwork(input_dim=X.shape[1])
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    epochs = 500
    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        outputs = model(X_train_t)
        loss = criterion(outputs, y_train_t)
        loss.backward()
        optimizer.step()
        
        if (epoch + 1) % 50 == 0:
            model.eval()
            with torch.no_grad():
                test_loss = criterion(model(X_test_t), y_test_t)
            print(f"Epoch [{epoch+1}/{epochs}] | Loss: {loss.item():.4f} | Val Loss: {test_loss.item():.4f}")

    # Save
    os.makedirs("models", exist_ok=True)
    params = {
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "numeric_cols": numeric_cols,
        "doctrine_names": doctrine_names,
        "doctrine_categories": doctrine_names
    }
    with open("models/value_network_params.json", "w") as f: json.dump(params, f)
    torch.save(model.state_dict(), "models/value_network.pth")
    print(f"\n[OK] Value Network trained and saved to models/value_network.pth")

if __name__ == "__main__":
    train_value()