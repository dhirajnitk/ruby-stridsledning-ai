import torch
import torch.nn as nn
import torch.optim as optim
import json
import numpy as np
import os
from engine import ValueNetwork, DoctrineNetwork

def train_resnet_models(epochs=500, batch_size=32):
    print("[TRAIN] Loading ResNet Oracle Dataset...")
    data_path = "data/training/resnet_oracle_data.json"
    if not os.path.exists(data_path):
        print(f"[ERROR] No data found at {data_path}")
        return

    with open(data_path, "r") as f:
        raw_data = json.load(f)

    # Prepare Data
    X_raw = np.array([s["features"] for s in raw_data])
    Y_val_raw = np.array([[s["target_value"]] for s in raw_data])
    Y_doc_raw = np.array([s["optimal_weights"] for s in raw_data])

    # Calculate Z-Score Scalers
    scaler_mean = X_raw.mean(axis=0)
    scaler_std = X_raw.std(axis=0)
    scaler_std[scaler_std == 0] = 1.0 # Protect against zero variance
    
    X_norm = (X_raw - scaler_mean) / scaler_std
    
    # 80/20 Random Split
    indices = np.arange(len(raw_data))
    np.random.shuffle(indices)
    split_at = int(0.8 * len(raw_data))
    
    train_idx, val_idx = indices[:split_at], indices[split_at:]
    
    X_train = torch.tensor(X_norm[train_idx], dtype=torch.float32)
    Y_val_train = torch.tensor(Y_val_raw[train_idx], dtype=torch.float32)
    Y_doc_train = torch.tensor(Y_doc_raw[train_idx], dtype=torch.float32)
    
    X_val = torch.tensor(X_norm[val_idx], dtype=torch.float32)
    Y_val_val = torch.tensor(Y_val_raw[val_idx], dtype=torch.float32)
    Y_doc_val = torch.tensor(Y_doc_raw[val_idx], dtype=torch.float32)

    # Initialize Models
    val_net = ValueNetwork(input_dim=X_train.shape[1])
    doc_net = DoctrineNetwork(input_dim=X_train.shape[1])

    val_optimizer = optim.Adam(val_net.parameters(), lr=0.001)
    doc_optimizer = optim.Adam(doc_net.parameters(), lr=0.001)
    criterion = nn.MSELoss()

    print(f"[TRAIN] Data Ready: {len(X_train)} training samples, {len(X_val)} validation samples.")
    for epoch in range(epochs):
        val_net.train(); doc_net.train()
        
        # Train Step
        val_optimizer.zero_grad(); doc_optimizer.zero_grad()
        v_out = val_net(X_train); d_out = doc_net(X_train)
        v_loss = criterion(v_out, Y_val_train); d_loss = criterion(d_out, Y_doc_train)
        (v_loss + d_loss).backward()
        val_optimizer.step(); doc_optimizer.step()

        if (epoch + 1) % 50 == 0:
            val_net.eval()
            with torch.no_grad():
                v_test = val_net(X_val)
                val_loss_metric = criterion(v_test, Y_val_val)
            print(f"Epoch {epoch+1}/{epochs} | Val Loss: {val_loss_metric.item():.4f} | Train Loss: {v_loss.item():.4f}")

    # Save Models
    os.makedirs("models", exist_ok=True)
    torch.save(val_net.state_dict(), "models/value_network.pth")
    torch.save(doc_net.state_dict(), "models/doctrine_network.pth")
    
    # Save Meta-Params with ACTUAL scalers
    params = {
        "numeric_cols": ["num_threats", "avg_dist", "min_dist", "total_val", "fighters", "sams", "drones", "cap_sams", "weather_bin", "blend", "west", "east", "stress", "dist_norm", "val_norm"],
        "doctrine_categories": ["balanced", "fortress", "aggressive"],
        "scaler_mean": scaler_mean.tolist(),
        "scaler_scale": scaler_std.tolist()
    }
    with open("models/value_network_params.json", "w") as f: json.dump(params, f)
    with open("models/policy_network_params.json", "w") as f: json.dump(params, f)

    print("[SUCCESS] ResNet Models trained and saved to models/")

if __name__ == "__main__":
    train_resnet_models()
