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

def load_blind_validation_set():
    """Load the 100 blind test scenarios for validation (they are NEVER used in training)."""
    INPUT_DIR = "data/blind_test"
    batch_files = sorted(glob.glob(os.path.join(INPUT_DIR, "blind_campaign_batch_*.json")))
    dataset = []
    state = load_battlefield_state(CSV_FILE_PATH)
    
    print(f"[INIT] Loading {len(batch_files)} batches for BLIND VALIDATION...", flush=True)
    for file in batch_files:
        with open(file, 'r') as f:
            batch_data = json.load(f)
        for scenario_id, threats_data in batch_data.items():
            ts = []
            for t in threats_data:
                target_x, target_y = t.get("target_x"), t.get("target_y")
                heading = "Capital X"
                if target_x == 198.3: heading = "Northern Vanguard Base"
                elif target_x == 838.3: heading = "Highridge Command"
                ts.append(Threat(t["id"], t["start_x"], t["start_y"], t["speed"], heading, t["type"], t["threat_value"]))
            
            # Pre-compute target matrix for faster validation
            truth_plan = TacticalEngine.get_optimal_assignments(state, ts)
            eff, thr, eff_m, thr_m = extract_direct_features(state, ts)
            if eff is None: continue
            target = torch.zeros((eff.size(0), thr.size(0)))
            thr_id_to_idx = {t.id: k for k, t in enumerate(thr_m)}
            assigned = set()
            for a in truth_plan:
                t_idx = thr_id_to_idx.get(a["threat_id"])
                if t_idx is not None:
                    for e_idx, m in enumerate(eff_m):
                        if e_idx not in assigned and m["base"] == a["base"] and m["type"].lower() == a["effector"].lower():
                            target[e_idx, t_idx] = 1.0
                            assigned.add(e_idx)
                            break
            dataset.append((eff, thr, target))
    return dataset

def generate_random_training_example(state):
    """Generate a 100% unique training example on the fly."""
    num_threats = random.randint(10, 80)
    ts = [Threat(f"T-{random.randint(0,9999)}", random.uniform(500, 2500), random.uniform(100, 1500), random.uniform(2000, 6000), random.choice(["Capital X", "Northern Vanguard Base", "Highridge Command"]), random.choice(["bomber", "fighter", "drone"]), random.uniform(50, 200)) for _ in range(num_threats)]
    
    truth_plan = TacticalEngine.get_optimal_assignments(state, ts)
    eff, thr, eff_m, thr_m = extract_direct_features(state, ts)
    if eff is None: return None, None, None
    
    target = torch.zeros((eff.size(0), thr.size(0)))
    thr_id_to_idx = {t.id: k for k, t in enumerate(thr_m)}
    assigned = set()
    for a in truth_plan:
        t_idx = thr_id_to_idx.get(a["threat_id"])
        if t_idx is not None:
            for e_idx, m in enumerate(eff_m):
                if e_idx not in assigned and m["base"] == a["base"] and m["type"].lower() == a["effector"].lower():
                    target[e_idx, t_idx] = 1.0
                    assigned.add(e_idx)
                    break
    return eff, thr, target

def train_ppo_infinite():
    print("[INFINITE] Starting Stochastic PPO Training (Infinite Data Stream)...", flush=True)
    state = load_battlefield_state(CSV_FILE_PATH)
    val_set = load_blind_validation_set()
    
    model = ActorCriticDirect()
    if os.path.exists("models/ppo_direct_network.pth"):
        model.load_state_dict(torch.load("models/ppo_direct_network.pth"))
        print("[INFINITE] Bootstrapping from existing weights.", flush=True)
        
    optimizer = optim.Adam(model.parameters(), lr=1e-4) # Slower LR for refinement
    
    EPOCHS = 5000
    best_val_loss = float('inf')
    
    print(f"[INFINITE] Training on {EPOCHS} UNIQUE scenarios. Validating on 100 FIXED BLIND scenarios.", flush=True)
    
    for epoch in range(EPOCHS):
        model.train()
        
        # 1. Generate a BRAND NEW scenario for every step
        eff, thr, target = generate_random_training_example(state)
        if eff is None: continue
        
        optimizer.zero_grad()
        affinity, _ = model(eff, thr)
        
        # Priority Weighting
        weights = torch.ones_like(target)
        is_capital = (thr[:, 4] > 1.5) & (thr[:, 4] < 2.5)
        weights[:, is_capital] *= 15.0 # Increased weighting to 15x for survival mandate
        
        raw_loss = nn.BCEWithLogitsLoss(reduction='none')(affinity, target)
        weighted_loss = (raw_loss * weights).mean()
        weighted_loss.backward()
        optimizer.step()
        
        if (epoch + 1) % 100 == 0:
            model.eval()
            total_val_loss = 0
            with torch.no_grad():
                for v_eff, v_thr, v_target in val_set:
                    v_affinity, _ = model(v_eff, v_thr)
                    v_weights = torch.ones_like(v_target)
                    is_cap = (v_thr[:, 4] > 1.5) & (v_thr[:, 4] < 2.5)
                    v_weights[:, is_cap] *= 15.0
                    total_val_loss += (nn.BCEWithLogitsLoss(reduction='none')(v_affinity, v_target) * v_weights).mean().item()
            
            avg_val_loss = total_val_loss / len(val_set)
            print(f"Step {epoch+1}/{EPOCHS} | Latest Step Loss: {weighted_loss.item():.6f} | Blind Val Loss: {avg_val_loss:.6f}", flush=True)
            
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                torch.save(model.state_dict(), "models/ppo_direct_network.pth")
                print(f"  --> [NEW GEN] Best Blind Accuracy found. Weights updated.", flush=True)

    print(f"[SUCCESS] Infinite Data Sprint Complete.")

if __name__ == "__main__":
    train_ppo_infinite()
