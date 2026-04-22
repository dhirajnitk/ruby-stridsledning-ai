import os
import json
import torch
import numpy as np
import glob
from engine import evaluate_threats_advanced, extract_rl_features
from inference import BorealInference
from models import load_battlefield_state, CSV_FILE_PATH, Threat

MODELS = [
    "elite_v3_5", "generalist_e10", "hybrid_rl", 
    "supreme_v3_1", "supreme_v2", "titan", 
    "heuristic", "hBase", "random_hungarian"
]

def run_ultimate_tournament():
    # Find all batches
    batch_files = sorted(glob.glob("data/input/simulated_campaign_batch_*.json"))
    print(f"Found {len(batch_files)} batches. Initializing Ultimate Tournament...")
    
    # Load battlefield
    state = load_battlefield_state(CSV_FILE_PATH)
    for b in state.bases:
        b.inventory = {"patriot-pac3": 100, "iris-t-sls": 200, "meteor": 40, "saab-nimbrix": 500}

    overall_results_salvo = {}
    overall_results_single = {}

    for model_name in MODELS:
        print(f"Benchmarking: {model_name}...")
        total_survival_salvo = 0
        total_interception_salvo = 0
        total_survival_single = 0
        total_interception_single = 0
        total_scenarios = 0
        total_threats = 0

        # Load Inference once per model
        infer = None
        if model_name not in ["random_hungarian", "heuristic", "hBase"]:
            try: infer = BorealInference(model_name)
            except: pass

        for batch_file in batch_files:
            with open(batch_file, "r") as f:
                scenarios = json.load(f)
            
            for i, scenario_id in enumerate(list(scenarios.keys())[:3]):
                threat_data = scenarios[scenario_id]
                active_threats = [Threat(
                    id=t['id'], x=float(t['start_x']), y=float(t['start_y']),
                    speed_kmh=float(t['speed']), heading=str(t['target_x']),
                    estimated_type=t['type'], threat_value=float(t['threat_value'])
                ) for t in threat_data]
                
                # --- Threat-type aware feature extraction ---
                # Compute a 'blend' signal from swarm composition so neural models
                # can distinguish a hypersonic raid from a drone swarm.
                # Without this, all swarms look identical in the 15-D aggregate vector.
                num_t = len(active_threats)
                n_hyper = sum(1 for t in active_threats if "hypersonic" in t.estimated_type or "ballistic" in t.estimated_type)
                n_drone = sum(1 for t in active_threats if "drone" in t.estimated_type or "loiter" in t.estimated_type)
                threat_blend = min(1.0, (n_hyper * 0.15 + n_drone * 0.03 + num_t * 0.01))
                
                features = extract_rl_features(state, active_threats, weather="clear", blend=threat_blend)
                
                # Get Weights
                if model_name == "random_hungarian":
                    weights = np.random.uniform(0, 1, 11)
                elif "heuristic" in model_name or "hBase" in model_name:
                    weights = None
                else:
                    weights = infer.predict(features) if infer else np.random.uniform(0.4, 0.6, 11)

                # 1. SALVO TEST (2.0)
                score_sa, details_sa, _ = evaluate_threats_advanced(state, active_threats, mcts_iterations=50, salvo_ratio=2, doctrine_weights=weights)
                if score_sa > 0: total_survival_salvo += 1
                total_interception_salvo += (len(active_threats) - details_sa['leaked'])

                # 2. SINGLE-FIRE TEST (1.0)
                score_si, details_si, _ = evaluate_threats_advanced(state, active_threats, mcts_iterations=50, salvo_ratio=1, doctrine_weights=weights)
                if score_si > 0: total_survival_single += 1
                total_interception_single += (len(active_threats) - details_si['leaked'])

                total_threats += len(active_threats)
                total_scenarios += 1
        
        overall_results_salvo[model_name] = {
            "survival": (total_survival_salvo / total_scenarios) * 100,
            "interception": (total_interception_salvo / total_threats) * 100
        }
        overall_results_single[model_name] = {
            "survival": (total_survival_single / total_scenarios) * 100,
            "interception": (total_interception_single / total_threats) * 100
        }

    # Print Salvo Table
    print("\n" + "="*80)
    print("   SALVO AUDIT (2.0) - THE PRODUCTION STANDARD")
    print("="*80)
    header = f"{'Model Architecture':<20} | {'Avg Survival':<15} | {'Avg Intercept':<15}"
    print(header)
    print("-" * len(header))
    sorted_salvo = sorted(overall_results_salvo.items(), key=lambda x: (x[1]['survival'], x[1]['interception']), reverse=True)
    for m, res in sorted_salvo:
        print(f"{m:<20} | {res['survival']:>13.1f}% | {res['interception']:>13.1f}%")

    # Print Single-Fire Table
    print("\n" + "="*80)
    print("   SINGLE-FIRE AUDIT (1.0) - RAW SKILL TEST")
    print("="*80)
    print(header)
    print("-" * len(header))
    sorted_single = sorted(overall_results_single.items(), key=lambda x: (x[1]['survival'], x[1]['interception']), reverse=True)
    for m, res in sorted_single:
        print(f"{m:<20} | {res['survival']:>13.1f}% | {res['interception']:>13.1f}%")
    print("="*80)

if __name__ == "__main__":
    run_ultimate_tournament()
