import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import csv
import os

# 1. The Policy Network Architecture
class PolicyNetwork(nn.Module):
    def __init__(self):
        super(PolicyNetwork, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(9, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            # Outputs 3 probabilities for our 3 core tactical approaches
            # Index 0: Standard Doctrine
            # Index 1: Economy of Force (Save Ammo)
            # Index 2: Capital Defense (Maximum Aggression)
            nn.Linear(32, 3), 
            nn.Softmax(dim=-1) # Converts outputs into percentages (e.g., [0.10, 0.85, 0.05])
        )
        
    def forward(self, x):
        return self.network(x)

class BorealPolicyDataset(Dataset):
    def __init__(self, csv_file):
        self.x_data = []
        self.y_data = []
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                features = [float(val) for val in row[1:10]]
                score = float(row[10])
                
                self.x_data.append(features)
                
                # For training purposes, we artificially categorize the "best" policy
                # based on the MCTS score and threat density.
                num_threats = features[5] + features[6] + features[7]
                if score < 0 and num_threats > 10:
                    self.y_data.append(1) # Class 1: Needs Economy of Force
                elif features[8] < 150.0:
                    self.y_data.append(2) # Class 2: Threat too close, needs Capital Defense
                else:
                    self.y_data.append(0) # Class 0: Standard Doctrine works
                    
        self.x_data = torch.tensor(self.x_data, dtype=torch.float32)
        self.y_data = torch.tensor(self.y_data, dtype=torch.long)
        
    def __len__(self): return len(self.x_data)
    def __getitem__(self, idx): return self.x_data[idx], self.y_data[idx]

if __name__ == "__main__":
    EPOCHS = 300
    dataset = BorealPolicyDataset('rl_value_network_training_data.csv')
    dataloader = DataLoader(dataset, batch_size=16, shuffle=True)
    
    model = PolicyNetwork()
    criterion = nn.CrossEntropyLoss() # Used for classification/probability mapping
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    print("Training Policy Network to guide MCTS search tree...")
    for epoch in range(EPOCHS):
        total_loss = 0.0
        for batch_x, batch_y in dataloader:
            optimizer.zero_grad()
            predictions = model(batch_x)
            loss = criterion(predictions, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
        if (epoch + 1) % 50 == 0:
            print(f"Epoch [{epoch+1}/{EPOCHS}] | Average Cross-Entropy Loss: {total_loss/len(dataloader):.4f}")
            
    torch.save(model.state_dict(), 'policy_network.pth')
    print("\n[SUCCESS] Model saved to 'policy_network.pth'")
