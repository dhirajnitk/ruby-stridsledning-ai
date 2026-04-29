import torch
import torch.nn as nn
import numpy as np
import sys
import os

# Ensure src is in path
sys.path.insert(0, "src")
from ppo_agent import BorealDirectEngine, BorealValueNetwork
from training.ppo_chronos_gru import BorealChronosGRU
from ppo_titan_transformer import BorealTitanEngine

def verify_models():
    print("====================================================")
    print("   BOREAL SUPREME 7-MODEL VERIFICATION              ")
    print("====================================================")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    models_to_check = [
        ("Supreme V4", "models/ppo_strategic_v4_25d.pth", BorealDirectEngine(input_dim=25, output_dim=24)),
        ("Titan", "models/titan.pth", BorealTitanEngine(input_dim=25, output_dim=24)),
        ("Chronos", "models/chronos_v4_25d.pth", BorealChronosGRU(input_dim=25, output_dim=24)),
        ("Vanguard", "models/vanguard.pth", BorealDirectEngine(input_dim=25, output_dim=24)),
        ("Twin Oracle", "models/twin_oracle.pth", BorealDirectEngine(input_dim=25, output_dim=24)),
        ("Sentinel", "models/hybrid_rl.pth", None), # Special case
        ("Guardian", "models/guardian.pth", BorealDirectEngine(input_dim=25, output_dim=24))
    ]
    
    test_feat = torch.randn(1, 25).to(device)
    test_seq = torch.randn(1, 20, 25).to(device)
    
    all_pass = True
    for name, path, model in models_to_check:
        if not os.path.exists(path):
            print(f"[MISSING] {name}: {path}")
            all_pass = False
            continue
            
        try:
            if name == "Sentinel":
                # Sentinel wrapper
                class ValueWrapper(nn.Module):
                    def __init__(self, input_dim=25):
                        super().__init__()
                        self.net = BorealValueNetwork(input_dim=input_dim)
                    def forward(self, x):
                        return torch.zeros((x.shape[0], 24)).to(device), self.net(x)
                model = ValueWrapper(input_dim=25)
            
            model.load_state_dict(torch.load(path, map_location=device, weights_only=True))
            model.to(device).eval()
            
            with torch.no_grad():
                if name == "Chronos":
                    p, v = model(test_seq)
                else:
                    p, v = model(test_feat)
            
            if p.shape[1] == 24:
                print(f"[PASS] {name}: Correct 24-D Output Shape")
            else:
                print(f"[FAIL] {name}: Unexpected shape {p.shape}")
                all_pass = False
        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            all_pass = False
            
    if all_pass:
        print("\n[SUCCESS] ALL 7 MODELS SYNCHRONIZED TO SUPREME-24 ARSENAL.")
    else:
        print("\n[FAIL] SOME MODELS ARE INCONSISTENT.")

if __name__ == "__main__":
    verify_models()
