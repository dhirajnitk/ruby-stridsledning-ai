import csv
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import os

# 1. Custom Dataset to load the CSV
class BorealValueDataset(Dataset):
    def __init__(self, csv_file):
        self.x_data = []
        self.y_data = []
        
        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"Could not find {csv_file}. Did you run generate_rl_data.py first?")
            
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip the header row
            for row in reader:
                # row[0] is scenario_id (ignore)
                # row[1:10] are the 9 input features
                features = [float(val) for val in row[1:10]]
                # row[10] is the target_mcts_score
                target = [float(row[10])]
                
                self.x_data.append(features)
                self.y_data.append(target)
                
        # Convert lists to PyTorch Tensors
        self.x_data = torch.tensor(self.x_data, dtype=torch.float32)
        self.y_data = torch.tensor(self.y_data, dtype=torch.float32)
        
    def __len__(self):
        return len(self.x_data)
        
    def __getitem__(self, idx):
        return self.x_data[idx], self.y_data[idx]

# 2. The Neural Network Architecture
class ValueNetwork(nn.Module):
    def __init__(self):
        super(ValueNetwork, self).__init__()
        # We have 9 input features and 1 continuous output (the score)
        self.network = nn.Sequential(
            nn.Linear(9, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1)  # Final scalar output
        )
        
    def forward(self, x):
        return self.network(x)

if __name__ == "__main__":
    # Hyperparameters
    EPOCHS = 500
    BATCH_SIZE = 16
    LEARNING_RATE = 0.001
    
    print("Loading dataset...")
    dataset = BorealValueDataset('rl_value_network_training_data.csv')
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    
    print(f"Dataset loaded with {len(dataset)} examples.")
    
    # Initialize Model, Loss Function, and Optimizer
    model = ValueNetwork()
    criterion = nn.MSELoss()  # Mean Squared Error for regression
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    print("Starting training loop...")
    for epoch in range(EPOCHS):
        total_loss = 0.0
        for batch_x, batch_y in dataloader:
            optimizer.zero_grad()           # 1. Clear old gradients
            predictions = model(batch_x)    # 2. Forward pass
            loss = criterion(predictions, batch_y) # 3. Calculate error
            loss.backward()                 # 4. Backpropagation
            optimizer.step()                # 5. Update weights
            total_loss += loss.item()
            
        if (epoch + 1) % 50 == 0:
            avg_loss = total_loss / len(dataloader)
            print(f"Epoch [{epoch+1}/{EPOCHS}] | Average MSE Loss: {avg_loss:.4f}")
            
    # Save the trained weights
    torch.save(model.state_dict(), 'value_network.pth')
    print("\n[SUCCESS] Training complete! Model saved to 'value_network.pth'")