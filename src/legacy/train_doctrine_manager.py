import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import csv
import os

# 1. The Continuous Action RL Network (Actor)
class DoctrineNetwork(nn.Module):
    def __init__(self):
        super(DoctrineNetwork, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(9, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            # Outputs exactly 14 values (one multiplier for each of the 14 DEFAULT_WEIGHTS)
            nn.Linear(64, 14), 
            # Softplus ensures the network outputs strictly positive numbers (e.g., 0.1 to 3.0) 
            # so we don't accidentally invert a penalty into a bonus!
            nn.Softplus() 
        )
        
    def forward(self, x):
        return self.network(x)

class BorealDoctrineDataset(Dataset):
    def __init__(self, csv_file):
        self.x_data = []
        self.y_data = []
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                features = [float(val) for val in row[1:10]]
                self.x_data.append(features)
                
                # Behavioral Cloning: We artificially construct the "perfect" multipliers 
                # based on the battlefield state to kickstart the RL agent's training.
                multipliers = [1.0] * 14
                num_threats = features[5] + features[6] + features[7]
                closest_dist = features[8]
                
                if num_threats >= 10:
                    # MASSIVE SWARM DETECTED: Spike Economy of Force (idx 5) and Swarm Penalty (idx 7)
                    multipliers[5] = 3.0
                    multipliers[7] = 2.5
                
                if closest_dist < 150.0:
                    # EXISTENTIAL THREAT DETECTED: Spike Capital Reserve protection (idx 10)
                    multipliers[10] = 5.0
                    
                self.y_data.append(multipliers)
                    
        self.x_data = torch.tensor(self.x_data, dtype=torch.float32)
        self.y_data = torch.tensor(self.y_data, dtype=torch.float32)
        
    def __len__(self): return len(self.x_data)
    def __getitem__(self, idx): return self.x_data[idx], self.y_data[idx]

if __name__ == "__main__":
    EPOCHS = 300
    dataset = BorealDoctrineDataset('rl_value_network_training_data.csv')
    dataloader = DataLoader(dataset, batch_size=16, shuffle=True)
    
    model = DoctrineNetwork()
    criterion = nn.MSELoss() 
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    print("Training RL Doctrine Manager (Continuous Action Space)...")
    for epoch in range(EPOCHS):
        total_loss = 0.0
        for batch_x, batch_y in dataloader:
            optimizer.zero_grad()
            loss = criterion(model(batch_x), batch_y)
            loss.backward()
            optimizer.step()
            
    torch.save(model.state_dict(), 'doctrine_network.pth')
    print("\n[SUCCESS] RL Doctrine Agent trained and saved to 'doctrine_network.pth'")
