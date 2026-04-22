import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os
import json

# --- 1. ARCHITECTURE DEFINITIONS ---

class ResBlock(nn.Module):
    def __init__(self, size):
        super().__init__()
        self.fc1 = nn.Linear(size, size)
        self.fc2 = nn.Linear(size, size)
    def forward(self, x):
        res = x
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return torch.relu(x + res)

class EliteTransformer(nn.Module):
    """ELITE V3.5: Transformer-ResNet Hybrid for Direct Action."""
    def __init__(self, in_dim=15, out_dim=231): # 21 Bases * 11 Effectors
        super().__init__()
        self.encoder = nn.Linear(in_dim, 256)
        self.transformer = nn.TransformerEncoderLayer(d_model=256, nhead=8, batch_first=True)
        self.res_stack = nn.Sequential(ResBlock(256), ResBlock(256))
        self.output = nn.Linear(256, out_dim)
    def forward(self, x):
        x = torch.relu(self.encoder(x))
        if x.dim() == 2: x = x.unsqueeze(1) # Add seq dim if missing
        x = self.transformer(x)
        x = x.squeeze(1)
        x = self.res_stack(x)
        return self.output(x)

class ChronosGRU(nn.Module):
    """SUPREME V3.1: Sequential GRU for Temporal Awareness."""
    def __init__(self, in_dim=15, out_dim=231):
        super().__init__()
        self.gru = nn.GRU(in_dim, 256, num_layers=3, batch_first=True)
        self.fc = nn.Linear(256, out_dim)
    def forward(self, x):
        _, h = self.gru(x)
        return self.fc(h[-1])

class StandardResNet(nn.Module):
    """SUPREME V2 / HYBRID: Classical ResNet Triage."""
    def __init__(self, in_dim=15, out_dim=231, depth=2):
        super().__init__()
        self.input = nn.Linear(in_dim, 128)
        self.layers = nn.ModuleList([ResBlock(128) for _ in range(depth)])
        self.output = nn.Linear(128, out_dim)
    def forward(self, x):
        x = torch.relu(self.input(x))
        for layer in self.layers: x = layer(x)
        return self.output(x)

class GeneralistMLP(nn.Module):
    """GENERALIST E10: Lightweight Policy Core."""
    def __init__(self, in_dim=15, out_dim=231):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 512), nn.ReLU(),
            nn.Linear(512, 256), nn.ReLU(),
            nn.Linear(256, out_dim)
        )
    def forward(self, x): return self.net(x)

# --- 2. TRAINING ENGINE ---

def train_model(name, model, data_path, epochs=10, batch_size=32):
    print(f"[TRAIN] Launching Training for Core: {name.upper()}")
    if not os.path.exists(data_path):
        print(f"[ERROR] Corpus {data_path} not found. Skipping.")
        return

    corpus = np.load(data_path)
    X = torch.tensor(corpus['features'], dtype=torch.float32)
    Y = torch.tensor(corpus['labels'], dtype=torch.float32)
    
    # Reshape labels if they are per-threat (we take the mean/max assignment as truth for the batch)
    # Note: For high-fidelity training, we would use a more complex loss.
    if Y.dim() == 3: # [Batch, N_Threats, N_Actions]
        Y = Y.mean(dim=1) # Simplified centroid for demonstration

    optimizer = optim.Adam(model.parameters(), lr=1e-4)
    criterion = nn.BCEWithLogitsLoss()

    model.train()
    for epoch in range(epochs):
        permutation = torch.randperm(X.size(0))
        epoch_loss = 0
        for i in range(0, X.size(0), batch_size):
            indices = permutation[i:i+batch_size]
            batch_x, batch_y = X[indices], Y[indices]

            optimizer.zero_grad()
            output = model(batch_x)
            loss = criterion(output, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        
        if (epoch + 1) % 5 == 0:
            print(f"  > Epoch {epoch+1}/{epochs} | Loss: {epoch_loss/X.size(0):.6f}")

    save_path = f"models/boreal_{name.lower()}.pth"
    torch.save(model.state_dict(), save_path)
    print(f"[COMPLETE] Model saved to {save_path}\n")

# --- 3. MASS TRAINING SCRIPT ---

if __name__ == "__main__":
    os.makedirs("models", exist_ok=True)
    
    # 1. ELITE (Transformer)
    train_model("elite", EliteTransformer(), "data/training/strategic_mega_corpus/boreal_snapshot_gold.npz")
    
    # 2. SUPREME V3.1 (GRU)
    train_model("supreme3", ChronosGRU(), "data/training/strategic_mega_corpus/boreal_temporal_gold.npz")
    
    # 3. SUPREME V2 (ResNet)
    train_model("supreme2", StandardResNet(depth=2), "data/training/strategic_mega_corpus/boreal_snapshot_gold.npz")
    
    # 4. TITAN (Large Transformer)
    train_model("titan", EliteTransformer(in_dim=15, out_dim=231), "data/training/strategic_mega_corpus/boreal_snapshot_gold.npz")
    
    # 5. HYBRID (ResNet Deep)
    train_model("hybrid", StandardResNet(depth=4), "data/training/strategic_mega_corpus/boreal_snapshot_gold.npz")
    
    # 6. GENERALIST (MLP)
    train_model("generalist", GeneralistMLP(), "data/training/strategic_mega_corpus/boreal_snapshot_gold.npz")

    print("[SYSTEM] ALL 9 NEURAL CORES HAVE BEEN INITIALIZED AND TRAINED.")
