import os
import json
import torch
import numpy as np
from engine import evaluate_threats_advanced, extract_rl_features
from inference import BorealInference
from models import load_battlefield_state, CSV_FILE_PATH, Threat

MODELS = ["elite_v3_5", "generalist_e10", "hybrid_rl", "supreme_v2", "supreme_v3_1", "titan", "heuristic"]
BATCHES = ["data/input/simulated_campaign_batch_1.json", "data/input/simulated_campaign_batch_7.json"]

def run_tournament():
    results = {}
    
    # Load battlefield
    state = load_battlefield_state(CSV_FILE_PATH)
    # Give surplus ammo for fair comparison
    for b in state.bases:
        b.inventory = {"patriot-pac3": 100, "iris-t-sls": 200, "meteor": 40, "saab-nimbrix": 500}

    for model_name in MODELS:
        print(f"Testing Model: {model_name}...")
        results[model_name] = {}
        
        for batch_file in BATCHES:
            batch_id = batch_file.split("_")[-1].replace(".json", "")
            with open(batch_file, "r") as f:
                scenarios = json.load(f)
            
            total_survival = 0
            total_interception = 0
            threat_count = 0
            
            # Test first 5 scenarios of each batch for speed
            test_count = 5
            for i in range(test_count):
                scenario_id = list(scenarios.keys())[i]
                threat_data = scenarios[scenario_id]
                active_threats = [Threat(
                    id=t['id'],
                    x=float(t['start_x']),
                    y=float(t['start_y']),
                    speed_kmh=float(t['speed']),
                    heading=str(t['target_x']),
                    estimated_type=t['type'],
                    threat_value=float(t['threat_value'])
                ) for t in threat_data]
                
                # 1. Extract Features for the Brain
                features = extract_rl_features(state, active_threats)
                
                # 2. Get Neural Intuition (Actual Weights)
                if model_name == "heuristic":
                    weights = None
                else:
                    try:
                        infer = BorealInference(model_name)
                        weights = infer.predict(features)
                    except:
                        weights = None
                
                # FORCE SINGLE-FIRE (1.0) FOR RAW SKILL TEST
                score, details, _ = evaluate_threats_advanced(state, active_threats, mcts_iterations=100, salvo_ratio=1, doctrine_weights=weights)
                
                if score > 0: total_survival += 1
                total_interception += (len(active_threats) - details['leaked'])
                threat_count += len(active_threats)
            
            results[model_name][f"Batch_{batch_id}"] = {
                "survival": (total_survival / test_count) * 100,
                "interception": (total_interception / threat_count) * 100
            }

    print("\n" + "="*60)
    print("   GRAND MODEL TOURNAMENT RESULTS")
    print("="*60)
    header = f"{'Model':<15} | {'B1 Surv':<8} | {'B1 Int':<8} | {'B7 Surv':<8} | {'B7 Int':<8}"
    print(header)
    print("-" * len(header))
    
    for m in MODELS:
        b1 = results[m]["Batch_1"]
        b7 = results[m]["Batch_7"]
        print(f"{m:<15} | {b1['survival']:>7.0f}% | {b1['interception']:>7.1f}% | {b7['survival']:>7.0f}% | {b7['interception']:>7.1f}%")
    print("="*60)

if __name__ == "__main__":
    run_tournament()
