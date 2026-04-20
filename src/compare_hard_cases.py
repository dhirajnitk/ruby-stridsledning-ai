import time
import random
import os
import sys
sys.path.append('src')

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
        "ppo": {"scores": [], "times": [], "ignored": []}
    }
    
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
        
        # --- TEST NEURAL ---
        start = time.time()
        dec_n = evaluate_threats_advanced(base_state, threats, mcts_iterations=MCTS_ITERS, use_rl=False, use_ppo=False)
        dur_n = time.time() - start
        
        results["neural"]["scores"].append(dec_n["strategic_consequence_score"])
        results["neural"]["times"].append(dur_n)
        results["neural"]["ignored"].append(dec_n["triage_ignored_threats"])

        # --- TEST PPO (Trained) ---
        start = time.time()
        dec_p = evaluate_threats_advanced(base_state, threats, mcts_iterations=MCTS_ITERS, use_rl=False, use_ppo=True)
        dur_p = time.time() - start
        
        results["ppo"]["scores"].append(dec_p["strategic_consequence_score"])
        results["ppo"]["times"].append(dur_p)
        results["ppo"]["ignored"].append(dec_p["triage_ignored_threats"])
        
        print(f"Scenario {i+1}/{NUM_SCENARIOS} (Threats: {num_threats}) evaluated.")
            
    # Calculate metrics
    h_avg_score = np.mean(results["heuristic"]["scores"])
    n_avg_score = np.mean(results["neural"]["scores"])
    p_avg_score = np.mean(results["ppo"]["scores"])
    
    h_avg_time = np.mean(results["heuristic"]["times"]) * 1000
    n_avg_time = np.mean(results["neural"]["times"]) * 1000
    p_avg_time = np.mean(results["ppo"]["times"]) * 1000
    
    h_avg_ignored = np.mean(results["heuristic"]["ignored"])
    n_avg_ignored = np.mean(results["neural"]["ignored"])
    p_avg_ignored = np.mean(results["ppo"]["ignored"])
    
    print("\n" + "="*110)
    print(" BOREAL CHESSMASTER: OUTNUMBERED SATURATION BENCHMARK ")
    print(f" Defenders: ~{total_ammo} | Attackers: 350-500 ")
    print("="*110)
    print(f"{'Metric':<25} | {'Heuristic (Rule-Based)':<22} | {'Neural (RL)':<22} | {'PPO Direct (Augmented)':<22}")
    print("-" * 110)
    print(f"{'Average Tactical Score':<25} | {h_avg_score:<22.2f} | {n_avg_score:<22.2f} | {p_avg_score:<22.2f}")
    print(f"{'Execution Time (ms)':<25} | {h_avg_time:<22.2f} | {n_avg_time:<22.2f} | {p_avg_time:<22.2f}")
    print(f"{'Avg Threats Triaged/Ignored':<25} | {h_avg_ignored:<22.2f} | {n_avg_ignored:<22.2f} | {p_avg_ignored:<22.2f}")
    print("="*110)
    
if __name__ == "__main__":
    run_hard_case_comparison()
