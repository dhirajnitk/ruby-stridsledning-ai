import torch
import torch.nn as nn
import torch.optim as optim
import os
import glob
import json
import random
import numpy as np
from ppo_agent import ActorCriticDirect, extract_direct_features
from agent_backend import load_battlefield_state, CSV_FILE_PATH
from engine import TacticalEngine, StrategicMCTS
from models import Threat

def train_ppo_hybrid():
    print("[HYBRID] Starting PPO Evolution: Improving on the Hungarian Baseline...", flush=True)
    state = load_battlefield_state(CSV_FILE_PATH)
    
    model = ActorCriticDirect()
    # Load our best cloned weights as the starting point
    if os.path.exists("models/ppo_direct_network.pth"):
        model.load_state_dict(torch.load("models/ppo_direct_network.pth"))
        print("[HYBRID] Expert weights loaded. Bootstrapping from Hungarian baseline.", flush=True)
    
    optimizer = optim.Adam(model.parameters(), lr=5e-4)
    
    # HYPERPARAMETERS
    EPOCHS = 1000
    ALPHA = 0.7  # Weight for Imitation (cloning)
    BETA = 0.3   # Weight for Strategic Reward (improvement)
    
    best_total_score = -float('inf')

    for epoch in range(EPOCHS):
        model.train()
        
        # 1. Generate a complex, randomized scenario
        num_threats = random.randint(20, 80)
        threats = [Threat(f"H-{j}", random.uniform(500, 2500), random.uniform(100, 1500), random.uniform(2000, 6000), random.choice(["Capital X", "Northern Vanguard Base", "Highridge Command"]), random.choice(["bomber", "fighter", "drone"]), random.uniform(50, 200)) for j in range(num_threats)]
        
        # 2. Get Teacher (Hungarian) baseline
        truth_plan = TacticalEngine.get_optimal_assignments(state, threats)
        eff, thr, eff_m, thr_m = extract_direct_features(state, threats)
        if eff is None: continue
        
        # Build Target Matrix for Imitation
        target_matrix = torch.zeros((eff.size(0), thr.size(0)))
        thr_id_to_idx = {t.id: k for k, t in enumerate(thr_m)}
        assigned = set()
        for a in truth_plan:
            t_idx = thr_id_to_idx.get(a["threat_id"])
            if t_idx is not None:
                for e_idx, m in enumerate(eff_m):
                    if e_idx not in assigned and m["base"] == a["base"] and m["type"].lower() == a["effector"].lower():
                        target_matrix[e_idx, t_idx] = 1.0
                        assigned.add(e_idx)
                        break
        
        # 3. Forward Pass
        optimizer.zero_grad()
        affinity, value_pred = model(eff, thr)
        
        # 4. IMITATION LOSS (BCE)
        weights = torch.ones_like(target_matrix)
        is_cap = (thr[:, 4] > 1.5) & (thr[:, 4] < 2.5)
        weights[:, is_cap] *= 5.0
        imitation_loss = (nn.BCEWithLogitsLoss(reduction='none')(affinity, target_matrix) * weights).mean()
        
        # 5. STRATEGIC REWARD (The Improvement)
        # We sample an action from the current policy and evaluate it via MCTS
        probs = torch.sigmoid(affinity)
        # Create a plan from the PPO's current predictions
        ppo_plan = []
        assigned_e = set()
        assigned_t = set()
        # Simple greedy decode for the "Improvement" step
        flat_indices = torch.argsort(probs.flatten(), descending=True)
        for idx in flat_indices[:num_threats]:
            e_idx = idx // probs.shape[1]
            t_idx = idx % probs.shape[1]
            if e_idx not in assigned_e and t_idx not in assigned_t and probs[e_idx, t_idx] > 0.1:
                ppo_plan.append({"base": eff_m[e_idx]["base"], "effector": eff_m[e_idx]["type"], "threat_id": thr_m[t_idx].id})
                assigned_e.add(e_idx)
                assigned_t.add(t_idx)
        
        # Evaluate PPO plan via Strategic MCTS
        ppo_score, _, _ = StrategicMCTS.run_mcts_rollout(state, ppo_plan, threats, iterations=5, use_rl=False)
        # Normalize score (e.g. 1000 is good, -5000 is bad)
        reward = torch.tensor([ppo_score / 1000.0], dtype=torch.float32)
        
        # VALUE LOSS: Critic should predict the Strategic Score
        value_loss = nn.MSELoss()(value_pred, reward)
        
        # 6. TOTAL HYBRID LOSS
        # We want to minimize Imitation Loss AND maximize the Reward (minimize -Reward)
        total_loss = (ALPHA * imitation_loss) + (BETA * value_loss)
        
        total_loss.backward()
        optimizer.step()
        
        if (epoch + 1) % 50 == 0:
            print(f"Epoch {epoch+1}/{EPOCHS} | Imitation: {imitation_loss.item():.4f} | Strat Score: {ppo_score:.1f} | ValPred: {value_pred.item():.4f}", flush=True)
            if ppo_score > best_total_score:
                best_total_score = ppo_score
                torch.save(model.state_dict(), "models/ppo_direct_network.pth")
                print(f"  --> [NEW RECORD] Strategy improved to {ppo_score:.1f}. Weights updated.", flush=True)

    print(f"[SUCCESS] Hybrid Evolution Complete. Best Strategic Performance: {best_total_score:.1f}")

if __name__ == "__main__":
    train_ppo_hybrid()
