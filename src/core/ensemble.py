import torch
import torch.nn as nn
import os
import sys

# Ensure src is in path
sys.path.insert(0, "src")
from ppo_agent import BorealDirectEngine, BorealValueNetwork
from training.ppo_chronos_gru import BorealChronosGRU
from ppo_titan_transformer import BorealTitanEngine

class BorealSupremeEnsemble:
    """
    THE GOAT: BOREAL SUPREME 7-MODEL ENSEMBLE.
    Aggregates tactical and strategic signals from all experts for absolute precision.
    """
    def __init__(self, models_dir="models", device="cpu"):
        self.device = torch.device(device)
        self.models = {}
        
        # Load the 7 Strategic Experts
        model_configs = [
            ("SupremeV4", "ppo_strategic_v4_25d.pth", BorealDirectEngine(25, 24)),
            ("Titan", "titan.pth", BorealTitanEngine(25, 24)),
            ("Chronos", "chronos_v4_25d.pth", BorealChronosGRU(25, 24)),
            ("Vanguard", "vanguard.pth", BorealDirectEngine(25, 24)),
            ("TwinOracle", "twin_oracle.pth", BorealDirectEngine(25, 24)),
            ("Sentinel", "hybrid_rl.pth", None), # Special case wrapper
            ("Guardian", "guardian.pth", BorealDirectEngine(25, 24))
        ]
        
        for name, filename, model_obj in model_configs:
            path = os.path.join(models_dir, filename)
            if not os.path.exists(path):
                print(f"[WARNING] {name} missing. Ensemble performance may be degraded.")
                continue
                
            try:
                if name == "Sentinel":
                    # Sentinel is a value-only network in a wrapper
                    class ValueWrapper(nn.Module):
                        def __init__(self):
                            super().__init__()
                            self.net = BorealValueNetwork(25)
                        def forward(self, x): return torch.zeros((x.shape[0], 24)), self.net(x)
                    model_obj = ValueWrapper()
                
                model_obj.load_state_dict(torch.load(path, map_location=self.device, weights_only=True))
                model_obj.to(self.device).eval()
                self.models[name] = model_obj
            except Exception as e:
                print(f"[ERROR] Failed to load {name}: {e}")

    def predict(self, features):
        """Unified Ensemble Decision (Tactical + Strategic)."""
        if len(features.shape) == 1:
            features = features.unsqueeze(0)
            
        p_acc = []
        v_acc = []
        
        with torch.no_grad():
            for name, model in self.models.items():
                if name == "Chronos":
                    # Temporal sequence simulation
                    seq = torch.stack([features * (1.0 - 0.005 * (20 - s)) for s in range(20)], dim=1)
                    p, v = model(seq)
                else:
                    p, v = model(features)
                    
                p_acc.append(p)
                v_acc.append(v.view(-1))
                
        # --- THE GOAT FUSION ---
        # 1. Tactical: Weighted Mean of Policy
        # We give Titan and Supreme higher weights for tactical decisions
        weights = {"SupremeV4": 1.5, "Titan": 1.5, "Chronos": 0.5, "Vanguard": 1.0, 
                   "TwinOracle": 1.0, "Sentinel": 0.2, "Guardian": 1.0}
        
        total_p = torch.zeros_like(p_acc[0])
        total_w = 0.0
        for i, (name, _) in enumerate(self.models.items()):
            w = weights.get(name, 1.0)
            total_p += p_acc[i] * w
            total_w += w
            
        final_policy = total_p / total_w
        
        # 2. Strategic: Consensus Mean of Value
        final_value = torch.stack(v_acc).mean(dim=0)
        
        # 3. Confidence: Inverse Variance of Decisions
        # High variance between models means low confidence
        confidence = 1.0 / (torch.stack(p_acc).std(dim=0).mean() + 1e-6)
        
        return final_policy, final_value, confidence

if __name__ == "__main__":
    # Internal GOAT Test
    ensemble = BorealSupremeEnsemble()
    dummy_feat = torch.randn(1, 25)
    p, v, c = ensemble.predict(dummy_feat)
    print(f"[GOAT] Tactical Consensus: {torch.argmax(p, dim=1).item()}")
    print(f"[GOAT] Strategic Value: {v.item():.4f}")
    print(f"[GOAT] System Confidence: {c.item():.2f}")
