import torch
import numpy as np
import os
from ppo_sinkhorn_agent import BorealSinkhornEngine

class BorealSinkhornInference:
    """
    BOREAL SINKHORN INFERENCE: The Future of Baltic Strategic Command.
    Delivers mathematically valid 1-to-1 assignments via Neural Sinkhorn.
    """
    def __init__(self, device="cpu"):
        self.device = torch.device(device)
        self.model = BorealSinkhornEngine(input_dim=15, num_weapons=11, num_targets=11).to(self.device)
        
        model_path = "models/boreal_sinkhorn_oracle.pth"
        if os.path.exists(model_path):
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()

    def predict(self, features_list):
        feats = torch.tensor(features_list, dtype=torch.float32).to(self.device)
        
        with torch.no_grad():
            # Sinkhorn outputs a valid (N x N) Matrix
            pred_matrix, value = self.model(feats)
            
            # For 1-to-1 Action, we take the argmax of the matrix
            # Matrix: [Weapons, Targets]
            matrix = pred_matrix[0].cpu().numpy()
            assignments = np.argmax(matrix, axis=1) # Mapping Weapon i to Target j
            
            risk_score = value.cpu().numpy().flatten()[0]
            
        return assignments, risk_score

if __name__ == "__main__":
    print("[TEST] Initializing Sinkhorn Oracle Inference...")
    engine = BorealSinkhornInference()
    dummy_feat = [np.zeros(15)]
    assignments, score = engine.predict(dummy_feat)
    print(f"  -> assignments: {assignments}")
    print(f"  -> risk_score: {score:.2f}")
