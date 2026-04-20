"""
Boreal Chessmaster — RL Model Trainer (Full 15-Feature)
Generates synthetic tactical scenarios and trains both ValueNetwork and DoctrineNetwork
with all 15 battlefield features for maximum strategic awareness.
"""
import sys, os, json, math, random
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

# --- NETWORK ARCHITECTURES (must match engine.py) ---
class ResBlock(nn.Module):
    def __init__(self, size):
        super().__init__()
        self.fc1 = nn.Linear(size, size)
        self.fc2 = nn.Linear(size, size)
    def forward(self, x):
        residual = x
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return F.relu(x + residual)

class ValueNetwork(nn.Module):
    def __init__(self, input_dim=15):
        super().__init__()
        self.input_layer = nn.Linear(input_dim, 128)
        self.res1 = ResBlock(128)
        self.res2 = ResBlock(128)
        self.value_head = nn.Linear(128, 1)
    def forward(self, x):
        x = F.relu(self.input_layer(x))
        x = self.res1(x)
        x = self.res2(x)
        return self.value_head(x)

class DoctrineNetwork(nn.Module):
    def __init__(self, input_dim=15):
        super().__init__()
        self.input_layer = nn.Linear(input_dim, 128)
        self.res1 = ResBlock(128)
        self.res2 = ResBlock(128)
        self.output_layer = nn.Linear(128, 11)  # 11 doctrine weight multipliers
    def forward(self, x):
        x = F.relu(self.input_layer(x))
        x = self.res1(x)
        x = self.res2(x)
        return F.softplus(self.output_layer(x))

# --- SYNTHETIC DATA GENERATOR ---
def generate_scenario():
    """Generate a single synthetic tactical scenario with complex non-linear relationships."""
    num_threats = random.randint(1, 40)
    avg_dist = random.uniform(100, 2000)
    min_dist = random.uniform(10, avg_dist)
    total_val = num_threats * random.uniform(50, 300)
    fighters = random.randint(0, 20)
    sams = random.randint(0, 80)
    drones = random.randint(0, 60)
    cap_sams = random.randint(0, 30)
    weather_bin = random.choice([0.0, 1.0])
    blend = random.uniform(0.0, 1.0)
    west_threats = random.randint(0, num_threats)
    east_threats = random.randint(0, num_threats - west_threats)
    ammo_stress = (sams + fighters + drones) / (num_threats + 1)
    dist_norm = avg_dist / 1000.0
    val_norm = total_val / 1000.0
    
    features = [
        num_threats, avg_dist, min_dist, total_val,
        fighters, sams, drones, cap_sams, weather_bin, blend,
        west_threats, east_threats, ammo_stress, dist_norm, val_norm
    ]
    
    # --- COMPLEX VALUE LABEL ---
    value = 500.0
    # Non-linear threat penalty (swarms scale exponentially in danger)
    value -= (num_threats**1.2) * 5
    # Distance scaling
    value += (avg_dist / 2000.0) * 300
    # Logistics synergy
    if ammo_stress > 5.0: value += 100
    if cap_sams > 15 and min_dist < 300: value += 150 # Strong capital defense
    # Existential threat
    if min_dist < 100: value -= 250
    if min_dist < 50 and cap_sams < 5: value -= 400 # Imminent collapse
    # Weather interaction
    if weather_bin > 0 and drones > sams: value -= 100 # Drones perform worse in storm
    
    value += random.gauss(0, 20) # Add noise
    value = max(0, min(1000, value))
    
    # --- COMPLEX DOCTRINE MULTIPLIERS ---
    mults = [1.0] * 11
    if num_threats >= 15:
        mults[5] = 2.5 + random.gauss(0, 0.2) # economy_force
        mults[7] = 2.0 + random.gauss(0, 0.2) # swarm_penalty
    if min_dist < 150:
        mults[10] = 5.0 + random.gauss(0, 0.3) # capital_proximity
    if east_threats > west_threats * 2:
        mults[3] = 2.0 + random.gauss(0, 0.1) # range_penalty
    if weather_bin > 0:
        mults[0] = 2.0 + random.gauss(0, 0.1) # intercept_value
        mults[8] = 0.5 + random.gauss(0, 0.1) # drone_attrition (drones weak in storm)
    if ammo_stress < 2.0:
        mults[9] = 3.0 + random.gauss(0, 0.2) # sam_depletion (conserve SAMs if low ammo)
        
    mults = [max(0.1, m) for m in mults]
    return features, value, mults

def main():
    NUM_SCENARIOS = 10000
    EPOCHS = 300
    BATCH_SIZE = 128
    LR = 0.002
    INPUT_DIM = 15
    
    print(f"[TRAIN] Generating {NUM_SCENARIOS} advanced tactical scenarios...")
    data = [generate_scenario() for _ in range(NUM_SCENARIOS)]
    
    features = torch.tensor([d[0] for d in data], dtype=torch.float32)
    values = torch.tensor([[d[1]] for d in data], dtype=torch.float32)
    mults = torch.tensor([d[2] for d in data], dtype=torch.float32)
    
    feat_mean = features.mean(dim=0).tolist()
    feat_std = features.std(dim=0).tolist()
    feat_std = [max(s, 1e-6) for s in feat_std]
    features_norm = (features - torch.tensor(feat_mean)) / torch.tensor(feat_std)
    
    print(f"\n[TRAIN] Training ValueNetwork (input_dim={INPUT_DIM}, epochs={EPOCHS})...")
    value_net = ValueNetwork(INPUT_DIM)
    optimizer_v = optim.Adam(value_net.parameters(), lr=LR, weight_decay=1e-5)
    scheduler_v = optim.lr_scheduler.ReduceLROnPlateau(optimizer_v, 'min', patience=10, factor=0.5)
    criterion = nn.MSELoss()
    
    for epoch in range(EPOCHS):
        perm = torch.randperm(len(features_norm))
        total_loss = 0
        batches = 0
        for i in range(0, len(features_norm), BATCH_SIZE):
            idx = perm[i:i+BATCH_SIZE]
            pred = value_net(features_norm[idx])
            loss = criterion(pred, values[idx])
            optimizer_v.zero_grad()
            loss.backward()
            optimizer_v.step()
            total_loss += loss.item()
            batches += 1
        avg_loss = total_loss/batches
        scheduler_v.step(avg_loss)
        if (epoch + 1) % 50 == 0:
            print(f"  Epoch {epoch+1}/{EPOCHS} — Loss: {avg_loss:.4f} (LR: {optimizer_v.param_groups[0]['lr']:.6f})")
    
    print(f"\n[TRAIN] Training DoctrineNetwork (input_dim={INPUT_DIM}, epochs={EPOCHS})...")
    doc_net = DoctrineNetwork(INPUT_DIM)
    optimizer_d = optim.Adam(doc_net.parameters(), lr=LR, weight_decay=1e-5)
    scheduler_d = optim.lr_scheduler.ReduceLROnPlateau(optimizer_d, 'min', patience=10, factor=0.5)
    
    for epoch in range(EPOCHS):
        perm = torch.randperm(len(features_norm))
        total_loss = 0
        batches = 0
        for i in range(0, len(features_norm), BATCH_SIZE):
            idx = perm[i:i+BATCH_SIZE]
            pred = doc_net(features_norm[idx])
            loss = criterion(pred, mults[idx])
            optimizer_d.zero_grad()
            loss.backward()
            optimizer_d.step()
            total_loss += loss.item()
            batches += 1
        avg_loss = total_loss/batches
        scheduler_d.step(avg_loss)
        if (epoch + 1) % 50 == 0:
            print(f"  Epoch {epoch+1}/{EPOCHS} — Loss: {avg_loss:.4f} (LR: {optimizer_d.param_groups[0]['lr']:.6f})")
    
    os.makedirs("models", exist_ok=True)
    torch.save(value_net.state_dict(), "models/value_network.pth")
    torch.save(doc_net.state_dict(), "models/doctrine_network.pth")
    
    params = {
        "numeric_cols": ["num_threats", "avg_dist", "min_dist", "total_val", "fighters", "sams", "drones", "cap_sams", "weather_bin", "blend", "west", "east", "stress", "dist_norm", "val_norm"],
        "doctrine_categories": ["balanced", "fortress", "aggressive"],
        "scaler_mean": feat_mean,
        "scaler_scale": feat_std
    }
    with open("models/value_network_params.json", "w") as f: json.dump(params, f, indent=2)
    with open("models/policy_network_params.json", "w") as f: json.dump(params, f, indent=2)
    
    print("\n[SUCCESS] Advanced RL Models trained and saved.")

if __name__ == "__main__":
    main()
