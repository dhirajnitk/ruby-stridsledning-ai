import time
import random
import os
import sys
import torch
import engine
from ppo_agent import ActorCriticDirect

from engine import evaluate_threats_advanced
from agent_backend import load_battlefield_state
from models import Threat
import numpy as np

def generate_hard_threats(num_threats=400):
    threats = []
    for i in range(num_threats):
        threats.append(Threat(
            id=f"T-{i}",
            x=random.uniform(500, 2500),
            y=random.uniform(100, 800),
            speed_kmh=random.choice([3000, 4500, 6000]),
            heading=random.choice(["Capital X", "Northern Vanguard Base", "Highridge Command", "Boreal Watch Post"]),
            estimated_type=random.choice(["bomber", "fast-mover", "ghost", "hypersonic"]),
            threat_value=random.uniform(80, 250)
        ))
    return threats

def run_hard_case_comparison():
    print("Loading base battlefield state...")
    base_state = load_battlefield_state('data/input/Boreal_passage_coordinates.csv')
    total_ammo = sum(sum(b.inventory.values()) for b in base_state.bases)
    print(f"Total Defenders (Ammo) Available: {total_ammo}")
    
    NUM_SCENARIOS = 15
    MCTS_ITERS = 50
    
    print(f"\nRunning {NUM_SCENARIOS} MASSIVE SATURATION scenarios (Threats > Ammo)...\n")
    
    results = {
        "heuristic": {"scores": [], "times": [], "ignored": []},
        "neural": {"scores": [], "times": [], "ignored": []},
        "ppo_98k": {"scores": [], "times": [], "ignored": []}
    }
    
    # Hot-load the 98k Veteran
    print("[SYSTEM] Hot-loading PPO Veteran (98,000 Iterations)...")
    veteran_model = ActorCriticDirect()
    VETERAN_PATH = "models/ppo_checkpoint_step_98000.pth"
    if os.path.exists(VETERAN_PATH):
        veteran_model.load_state_dict(torch.load(VETERAN_PATH, map_location='cpu'))
        veteran_model.eval()
        orig_ppo = engine.PPO_MODEL
        engine.PPO_MODEL = veteran_model
    else:
        print(f"WARNING: {VETERAN_PATH} not found!")
    
    for i in range(NUM_SCENARIOS):
        num_threats = random.randint(350, 500)  # Significantly more than ammo
        threats = generate_hard_threats(num_threats)
        
        # --- TEST HEURISTIC ---
        start = time.time()
        dec_h = evaluate_threats_advanced(base_state, threats, mcts_iterations=MCTS_ITERS, use_rl=False, use_ppo=False)
        dur_h = time.time() - start
        
        results["heuristic"]["scores"].append(dec_h["strategic_consequence_score"])
        results["heuristic"]["times"].append(dur_h)
        results["heuristic"]["ignored"].append(dec_h["triage_ignored_threats"])
        
        # --- TEST NEURAL (Doctrine Manager) ---
        start = time.time()
        dec_n = evaluate_threats_advanced(base_state, threats, mcts_iterations=MCTS_ITERS, use_rl=True, use_ppo=False)
        dur_n = time.time() - start
        
        results["neural"]["scores"].append(dec_n["strategic_consequence_score"])
        results["neural"]["times"].append(dur_n)
        results["neural"]["ignored"].append(dec_n["triage_ignored_threats"])

        # --- TEST PPO VETERAN (98k) ---
        start = time.time()
        # Ensure engine.PPO_MODEL is the veteran (already loaded)
        dec_p = evaluate_threats_advanced(base_state, threats, mcts_iterations=MCTS_ITERS, use_rl=True, use_ppo=True)
        dur_p = time.time() - start
        
        results["ppo_98k"]["scores"].append(dec_p["strategic_consequence_score"])
        results["ppo_98k"]["times"].append(dur_p)
        results["ppo_98k"]["ignored"].append(dec_p["triage_ignored_threats"])
        
        print(f"Scenario {i+1}/{NUM_SCENARIOS} (Threats: {num_threats}) evaluated.")
            
    # Calculate metrics
    h_avg_score = np.mean(results["heuristic"]["scores"])
    n_avg_score = np.mean(results["neural"]["scores"])
    p_avg_score = np.mean(results["ppo_98k"]["scores"])
    
    h_avg_time = np.mean(results["heuristic"]["times"]) * 1000
    n_avg_time = np.mean(results["neural"]["times"]) * 1000
    p_avg_time = np.mean(results["ppo_98k"]["times"]) * 1000
    
    h_avg_ignored = np.mean(results["heuristic"]["ignored"])
    n_avg_ignored = np.mean(results["neural"]["ignored"])
    p_avg_ignored = np.mean(results["ppo_98k"]["ignored"])
    
    h_survival = (np.array(results["heuristic"]["scores"]) > -100).mean() * 100
    n_survival = (np.array(results["neural"]["scores"]) > -100).mean() * 100
    p_survival = (np.array(results["ppo_98k"]["scores"]) > -100).mean() * 100

    print("\n" + "="*110)
    print(" BOREAL CHESSMASTER: OUTNUMBERED SATURATION BENCHMARK ")
    print(f" Defenders: ~{total_ammo} | Attackers: 350-500 ")
    print("="*110)
    print(f"{'Metric':<25} | {'Heuristic (Rule-Based)':<22} | {'Neural (RL)':<22} | {'PPO Veteran (98k)':<22}")
    print("-" * 110)
    print(f"{'Survival Rate':<25} | {h_survival:<21.1f}% | {n_survival:<21.1f}% | {p_survival:<21.1f}%")
    print(f"{'Average Tactical Score':<25} | {h_avg_score:<22.2f} | {n_avg_score:<22.2f} | {p_avg_score:<22.2f}")
    print(f"{'Execution Time (ms)':<25} | {h_avg_time:<22.2f} | {n_avg_time:<22.2f} | {p_avg_time:<22.2f}")
    print(f"{'Avg Threats Ignored':<25} | {h_avg_ignored:<22.2f} | {n_avg_ignored:<22.2f} | {p_avg_ignored:<22.2f}")
    print("="*110)
    
    # Restore original PPO model
    if 'orig_ppo' in locals():
        engine.PPO_MODEL = orig_ppo
    
if __name__ == "__main__":
    run_hard_case_comparison()
