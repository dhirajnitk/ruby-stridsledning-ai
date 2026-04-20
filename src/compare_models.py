import time
import os
import glob
import json
import numpy as np
from engine import evaluate_threats_advanced
from agent_backend import load_battlefield_state, CSV_FILE_PATH
from models import Threat

def run_comparison():
    print("Loading base battlefield state...")
    base_state = load_battlefield_state(CSV_FILE_PATH)
    
    INPUT_DIR = "data/blind_test"
    batch_files = sorted(glob.glob(os.path.join(INPUT_DIR, "blind_campaign_batch_*.json")))
    
    if not batch_files:
        print("No batch files found in data/blind_test!")
        return
        
    MCTS_ITERS = 50
    total_scenarios = 0
    
    results = {
        "heuristic": {"scores": [], "times": [], "ignored": [], "survived": 0},
        "neural": {"scores": [], "times": [], "ignored": [], "survived": 0},
        "ppo": {"scores": [], "times": [], "ignored": [], "survived": 0}
    }
    
    print(f"Found {len(batch_files)} batch files. Running full campaign benchmark (MCTS Iters: {MCTS_ITERS})...\n")
    
    for file in batch_files:
        with open(file, 'r') as f:
            batch_data = json.load(f)
            
        for scenario_id, threats_data in batch_data.items():
            total_scenarios += 1
            
            # Map JSON threats to engine Threat objects
            active_threats = []
            for t in threats_data:
                target_x, target_y = t.get("target_x"), t.get("target_y")
                if target_x == 198.3 and target_y == 335.0:
                    heading = "Northern Vanguard Base"
                elif target_x == 838.3 and target_y == 75.0:
                    heading = "Highridge Command"
                elif target_x == 418.3 and target_y == 95.0:
                    heading = "Capital X"
                else:
                    heading = f"Targeting x:{target_x}, y:{target_y}"

                active_threats.append(Threat(
                    id=t["id"],
                    x=t["start_x"],
                    y=t["start_y"],
                    speed_kmh=t["speed"],
                    heading=heading,
                    estimated_type=t["type"],
                    threat_value=t["threat_value"]
                ))
                
            # --- TEST HEURISTIC ---
            start = time.time()
            dec_h = evaluate_threats_advanced(base_state, active_threats, mcts_iterations=MCTS_ITERS, use_rl=False, use_ppo=False)
            dur_h = time.time() - start
            score_h = dec_h["strategic_consequence_score"]
            results["heuristic"]["scores"].append(score_h)
            results["heuristic"]["times"].append(dur_h)
            results["heuristic"]["ignored"].append(dec_h["triage_ignored_threats"])
            if score_h > -100: results["heuristic"]["survived"] += 1
            
            # --- TEST NEURAL (RL Doctrine Manager) ---
            start = time.time()
            dec_n = evaluate_threats_advanced(base_state, active_threats, mcts_iterations=MCTS_ITERS, use_rl=True, use_ppo=False)
            dur_n = time.time() - start
            score_n = dec_n["strategic_consequence_score"]
            results["neural"]["scores"].append(score_n)
            results["neural"]["times"].append(dur_n)
            results["neural"]["ignored"].append(dec_n["triage_ignored_threats"])
            if score_n > -100: results["neural"]["survived"] += 1
            
            # --- TEST PPO (Untrained Direct Action) ---
            start = time.time()
            dec_p = evaluate_threats_advanced(base_state, active_threats, mcts_iterations=MCTS_ITERS, use_rl=True, use_ppo=True)
            dur_p = time.time() - start
            score_p = dec_p["strategic_consequence_score"]
            results["ppo"]["scores"].append(score_p)
            results["ppo"]["times"].append(dur_p)
            results["ppo"]["ignored"].append(dec_p["triage_ignored_threats"])
            if score_p > -100: results["ppo"]["survived"] += 1
            
        print(f"Processed file: {os.path.basename(file)} (Total Scenarios so far: {total_scenarios})")

    # Calculate metrics
    h_avg_score = np.mean(results["heuristic"]["scores"])
    n_avg_score = np.mean(results["neural"]["scores"])
    p_avg_score = np.mean(results["ppo"]["scores"])
    
    h_avg_time = np.mean(results["heuristic"]["times"]) * 1000  # ms
    n_avg_time = np.mean(results["neural"]["times"]) * 1000  # ms
    p_avg_time = np.mean(results["ppo"]["times"]) * 1000  # ms
    
    h_avg_ignored = np.mean(results["heuristic"]["ignored"])
    n_avg_ignored = np.mean(results["neural"]["ignored"])
    p_avg_ignored = np.mean(results["ppo"]["ignored"])
    
    h_survival = (results["heuristic"]["survived"] / total_scenarios) * 100
    n_survival = (results["neural"]["survived"] / total_scenarios) * 100
    p_survival = (results["ppo"]["survived"] / total_scenarios) * 100
    
    # Print Table
    print("\n" + "="*110)
    print(" BOREAL CHESSMASTER: GRAND CAMPAIGN EVALUATION ")
    print(f" Tested on {total_scenarios} distinct tactical scenarios from data/input/")
    print("="*110)
    print(f"{'Metric':<25} | {'Heuristic (Rule-Based)':<22} | {'Neural (RL)':<22} | {'PPO Direct (Untrained)':<22}")
    print("-" * 110)
    print(f"{'Capital Survival Rate':<25} | {h_survival:<21.1f}% | {n_survival:<21.1f}% | {p_survival:<21.1f}%")
    print(f"{'Average Tactical Score':<25} | {h_avg_score:<22.2f} | {n_avg_score:<22.2f} | {p_avg_score:<22.2f}")
    print(f"{'Execution Time (ms)':<25} | {h_avg_time:<22.2f} | {n_avg_time:<22.2f} | {p_avg_time:<22.2f}")
    print(f"{'Threats Ignored/Triage':<25} | {h_avg_ignored:<22.2f} | {n_avg_ignored:<22.2f} | {p_avg_ignored:<22.2f}")
    print("="*110)
    
if __name__ == "__main__":
    run_comparison()
