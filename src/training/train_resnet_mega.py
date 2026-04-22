import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import os
import time

# --- ARCHITECTURE (Re-defined for zero-dependency forge) ---
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
        self.output_layer = nn.Linear(128, 11)
    def forward(self, x):
        x = F.relu(self.input_layer(x))
        x = self.res1(x)
        x = self.res2(x)
        return torch.sigmoid(self.output_layer(x))

# --- CONFIGURATION ---
DATASET_PATH = "data/training/strategic_mega_corpus/ppo_train_100k.npz"
BATCH_SIZE = 1024
EPOCHS = 100
LEARNING_RATE = 1e-3
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def train_resnet():
    print(f"[LAUNCH] HARDENED RESNET FORGE | Device: {DEVICE}", flush=True)
    
    # Use absolute path to avoid CWD issues
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    abs_dataset_path = os.path.join(base_dir, DATASET_PATH)
    
    print(f"[INTEL] Dataset Target: {abs_dataset_path}", flush=True)
    if not os.path.exists(abs_dataset_path):
        print(f"[ERROR] Mega-Corpus not found at {abs_dataset_path}.", flush=True)
        return

    # 1. Load Data
    print(f"[DATA] Ingesting 100,000 Tactical Transitions...", flush=True)
    data = np.load(abs_dataset_path)
    features = torch.tensor(data['features'], dtype=torch.float32).to(DEVICE)
    raw_weights = data['weights']
    raw_scores = data['scores']
    print(f"[DATA] Ingestion Success. Scaling strategic features...", flush=True)
    
    # Normalize
    weight_max = np.max(raw_weights, axis=0) + 1e-6
    target_weights = torch.tensor(raw_weights / weight_max, dtype=torch.float32).to(DEVICE)
    
    score_mean = np.mean(raw_scores)
    score_std = np.std(raw_scores) + 1e-6
    target_scores = torch.tensor((raw_scores - score_mean) / score_std, dtype=torch.float32).to(DEVICE)
    
    # Initialize
    val_net = ValueNetwork(input_dim=15).to(DEVICE)
    doc_net = DoctrineNetwork(input_dim=15).to(DEVICE)
    
    val_optimizer = optim.Adam(val_net.parameters(), lr=LEARNING_RATE)
    doc_optimizer = optim.Adam(doc_net.parameters(), lr=LEARNING_RATE)
    criterion = nn.MSELoss()

    print(f"[TRAIN] Commencing Strategic ResNet Optimization (Epochs: {EPOCHS})...")
    num_samples = len(features)
    
    for epoch in range(EPOCHS):
        indices = torch.randperm(num_samples)
        v_epoch_loss = 0
        d_epoch_loss = 0
        
        for i in range(0, num_samples, BATCH_SIZE):
            idx = indices[i:i+BATCH_SIZE]
            batch_x = features[idx]
            batch_y_val = target_scores[idx].unsqueeze(1)
            batch_y_doc = target_weights[idx]
            
            # Value Train
            val_optimizer.zero_grad()
            v_out = val_net(batch_x)
            v_loss = criterion(v_out, batch_y_val)
            v_loss.backward()
            val_optimizer.step()
            v_epoch_loss += v_loss.item()
            
            # Doctrine Train
            doc_optimizer.zero_grad()
            d_out = doc_net(batch_x)
            d_loss = criterion(d_out, batch_y_doc)
            d_loss.backward()
            doc_optimizer.step()
            d_epoch_loss += d_loss.item()
            
        if (epoch + 1) % 10 == 0:
            print(f"[EPOCH {epoch+1}/{EPOCHS}] ResNet Loss | Val: {v_epoch_loss/(num_samples/BATCH_SIZE):.6f} | Doc: {d_epoch_loss/(num_samples/BATCH_SIZE):.6f}")

    # 4. Save
    os.makedirs("models", exist_ok=True)
    torch.save(val_net.state_dict(), "models/value_network.pth")
    torch.save(doc_net.state_dict(), "models/doctrine_network.pth")
    print(f"[SAVE] Strategic ResNet Models secured in models/")

if __name__ == "__main__":
    train_resnet()
