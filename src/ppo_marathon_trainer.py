import torch
import torch.nn as nn
import torch.optim as optim
import os
import glob
import json
import random
import time
import numpy as np
from ppo_agent import ActorCriticDirect, extract_direct_features
from agent_backend import load_battlefield_state, CSV_FILE_PATH
from engine import TacticalEngine
from models import Threat

def load_blind_validation_set():
    INPUT_DIR = "data/blind_test"
    batch_files = sorted(glob.glob(os.path.join(INPUT_DIR, "blind_campaign_batch_*.json")))
    dataset = []
    state = load_battlefield_state(CSV_FILE_PATH)
    print(f"[MARATHON] Pre-loading {len(batch_files)*5} validation scenarios...", flush=True)
    for file in batch_files:
        with open(file, 'r') as f:
            batch_data = json.load(f)
        for _, threats_data in batch_data.items():
            ts = []
            for t in threats_data:
                target_x = t.get("target_x")
                heading = "Capital X"
                if target_x == 198.3: heading = "Northern Vanguard Base"
                elif target_x == 838.3: heading = "Highridge Command"
                ts.append(Threat(t["id"], t["start_x"], t["start_y"], t["speed"], heading, t["type"], t["threat_value"]))
            
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
    num_threats = random.randint(10, 100)
    ts = [Threat(f"T-{random.randint(0,99999)}", random.uniform(500, 2500), random.uniform(100, 1500), random.uniform(2000, 7000), random.choice(["Capital X", "Northern Vanguard Base", "Highridge Command"]), random.choice(["bomber", "fighter", "drone", "hypersonic"]), random.uniform(50, 400)) for _ in range(num_threats)]
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

def run_ppo_marathon():
    MAX_DURATION_SECONDS = 3600 # 1 hour
    CHECKPOINT_INTERVAL = 1000
    START_TIME = time.time()
    
    print(f"[MARATHON] Starting 1-Hour Neural Sprint...", flush=True)
    state = load_battlefield_state(CSV_FILE_PATH)
    val_set = load_blind_validation_set()
    
    model = ActorCriticDirect()
    if os.path.exists("models/ppo_direct_network.pth"):
        model.load_state_dict(torch.load("models/ppo_direct_network.pth"))
        print("[MARATHON] Resuming from current production weights.", flush=True)
    
    optimizer = optim.Adam(model.parameters(), lr=5e-5)
    best_val_loss = float('inf')
    step = 0
    
    while True:
        elapsed = time.time() - START_TIME
        if elapsed > MAX_DURATION_SECONDS:
            print(f"[MARATHON] Time limit reached ({elapsed:.0f}s). Terminating.", flush=True)
            break
            
        model.train()
        eff, thr, target = generate_random_training_example(state)
        if eff is None: continue
        
        optimizer.zero_grad()
        affinity, _ = model(eff, thr)
        
        # Priority Weighting
        weights = torch.ones_like(target)
        is_capital = (thr[:, 4] > 1.5) & (thr[:, 4] < 2.5)
        weights[:, is_capital] *= 20.0 # Extreme priority for Marathon
        
        loss = (nn.BCEWithLogitsLoss(reduction='none')(affinity, target) * weights).mean()
        loss.backward()
        optimizer.step()
        
        step += 1
        
        if step % CHECKPOINT_INTERVAL == 0:
            model.eval()
            total_val_loss = 0
            with torch.no_grad():
                for v_eff, v_thr, v_target in val_set:
                    v_affinity, _ = model(v_eff, v_thr)
                    v_weights = torch.ones_like(v_target)
                    v_weights[:, (v_thr[:, 4] > 1.5) & (v_thr[:, 4] < 2.5)] *= 20.0
                    total_val_loss += (nn.BCEWithLogitsLoss(reduction='none')(v_affinity, v_target) * v_weights).mean().item()
            
            avg_val_loss = total_val_loss / len(val_set)
            checkpoint_path = f"models/ppo_checkpoint_step_{step}.pth"
            torch.save(model.state_dict(), checkpoint_path)
            
            remaining = (MAX_DURATION_SECONDS - elapsed) / 60
            print(f"Step {step} | Val Loss: {avg_val_loss:.6f} | Checkpoint: {checkpoint_path} | Time Remaining: {remaining:.1f} min", flush=True)
            
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                torch.save(model.state_dict(), "models/ppo_direct_network.pth")
                print(f"  --> [RECORD] Production weights updated at step {step}.", flush=True)

    print(f"[SUCCESS] Marathon Sprint Complete. Checkpoints saved in models/")

if __name__ == "__main__":
    run_ppo_marathon()
