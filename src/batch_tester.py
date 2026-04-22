import json
import os
import sys
import glob
import csv
import numpy as np
import matplotlib.pyplot as plt

# Auto-correct working directory if the user runs the script from inside 'src/'
if os.path.basename(os.getcwd()) == "src":
    os.chdir("..")
    
from src.engine import evaluate_threats_advanced, extract_rl_features
from src.models import load_battlefield_state, Threat, EFFECTORS
from src.inference import BorealInference

# --- CONFIGURATION ---
MCTS_ITERATIONS = 1000 # Ultra-High Fidelity
ACTIVE_MODEL_KEY = os.getenv("SAAB_MODEL", "elite") # Override: set SAAB_MODEL env var
THEATER_MODE = os.getenv("SAAB_MODE", "sweden")

def run_batch_tests():
    print(f"==================================================")
    print(f"   BOREAL NEURAL AUDIT :: {ACTIVE_MODEL_KEY.upper()}")
    print(f"   THEATER: {THEATER_MODE.upper()}")
    print(f"==================================================")
    
    # 1. Initialize Neural Inference Engine
    print(f"Loading neural weights for {ACTIVE_MODEL_KEY}...")
    # Map key to filename
    MODEL_MAP = {
        "elite": "elite_v3_5",
        "titan": "titan",
        "hybrid": "hybrid_rl",
        "supreme3": "supreme_v3_1",
        "supreme2": "supreme_v2",
        "genE10": "generalist_e10"
    }
    target_model = MODEL_MAP.get(ACTIVE_MODEL_KEY, "elite_v3_5")
    infer_engine = BorealInference(target_model)
    
    # 2. Environment Prep
    CSV_FILE_PATH = "data/input/Boreal_passage_coordinates.csv"
    RESULTS_DIR = "data/results"
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    print("Loading battlefield state...")
    base_state = load_battlefield_state(CSV_FILE_PATH)
    
    # 2. File Loading
    INPUT_DIR = "data/input"
    batch_files = sorted(glob.glob(os.path.join(INPUT_DIR, "simulated_campaign_batch_*.json")))
    
    if not batch_files:
        print("[ERROR] No simulated_campaign_batch_*.json files found in data/input.")
        return

    # 3. Metrics Tracking
    total_scenarios = 0
    survived_scenarios = 0
    total_threats_count = 0
    total_intercepted_count = 0
    total_tactical_score = 0.0
    scenario_ids = []
    scores = []
    bar_colors = []
    csv_data = [["Scenario ID", "Threat Count", "Intercepted", "MCTS Score", "Status"]]

    print(f"Found {len(batch_files)} batches. Evaluating...")
    print(f"{'SCENARIO':<10} | {'THREATS':<8} | {'SCORE':<10} | {'SURVIVAL'}")
    print("-" * 50)
    
    for file in batch_files:
        with open(file, 'r') as f:
            batch_data = json.load(f)
            
        for scenario_id, threats_data in batch_data.items():
            if total_scenarios >= 20: break
            total_scenarios += 1
            
            # Map JSON to Engine Threat classes
            active_threats = []
            for t in threats_data:
                active_threats.append(Threat(
                    id=t["id"],
                    x=t["start_x"],
                    y=t["start_y"],
                    speed_kmh=t["speed"],
                    heading=f"Vector_{t.get('target_x')}_{t.get('target_y')}",
                    estimated_type=t["type"],
                    threat_value=t["threat_value"]
                ))
            
            # NEURAL INFERENCE: Get optimal doctrine weights from our trained .pth
            # This is the "Brain" of the operation
            
            # --- BUG FIX: Compute threat-type distribution for richer context ---
            # The 15-D swarm vector has no target label awareness. We compensate
            # by passing weather and a blend value that reflects swarm danger.
            num_t = len(active_threats)
            n_hyper    = sum(1 for t in active_threats if "hypersonic" in t.estimated_type or "ballistic" in t.estimated_type)
            n_drone    = sum(1 for t in active_threats if "drone" in t.estimated_type or "loiter" in t.estimated_type)
            # Blend encodes threat severity: higher = more dangerous swarm
            threat_blend = min(1.0, (n_hyper * 0.15 + n_drone * 0.03 + num_t * 0.01))
            
            # Extract 15-D features with correct blend signal
            features = extract_rl_features(
                base_state, active_threats,
                weather="clear", primary="balanced", blend=threat_blend
            )
            neural_weights = infer_engine.predict(features)
            
            # --- BUG FIX: Explicitly pass salvo_ratio=2 (Salvo 2.0 doctrine) ---
            # Without this, the engine falls back to salvo_ratio=1 if neural
            # weights don't hit the 0.8 threshold, killing Elite's performance.
            score, details, rl_val = evaluate_threats_advanced(
                base_state,
                active_threats,
                mcts_iterations=MCTS_ITERATIONS,
                doctrine_weights=neural_weights,
                doctrine_primary="balanced",
                salvo_ratio=2  # SALVO 2.0 — MANDATORY FOR COMBAT OPERATIONS
            )
            
            # 3. Calculate Metrics
            leaked_count = details.get("leaked", 0)
            intercepted = len(active_threats) - leaked_count
            total_threats_count += len(active_threats)
            total_intercepted_count += intercepted
            
            is_safe = score > -100 # Strategic threshold for "SAFE" status
            status = "SAFE" if is_safe else "HIT"
            if is_safe: survived_scenarios += 1
            
            total_tactical_score += score
            scenario_ids.append(scenario_id)
            scores.append(score)
            bar_colors.append("green" if is_safe else "red")
            
            csv_data.append([scenario_id, len(active_threats), f"{intercepted:.1f}", f"{score:.2f}", status])
            
            if True:
                print(f"{scenario_id:<10} | {len(active_threats):<8} | {score:<10.2f} | {status} (Int: {intercepted:.1f}/{len(active_threats)})")
        if total_scenarios >= 20: break

    # 4. Final Reporting
    survival_rate = (survived_scenarios / total_scenarios) * 100 if total_scenarios > 0 else 0
    interception_rate = (total_intercepted_count / total_threats_count) * 100 if total_threats_count > 0 else 0
    
    print("\n" + "="*50)
    print(f"   BATCH SUMMARY :: {ACTIVE_MODEL_KEY.upper()}")
    print(f"   Survival Rate:   {survival_rate:.1f}%")
    print(f"   Interception:    {interception_rate:.1f}%")
    print(f"   Avg Score:       {total_tactical_score/total_scenarios:.2f}")
    print("="*50)
    
    # 5. Visualization & Export
    try:
        plt.figure(figsize=(15, 5))
        plt.bar(scenario_ids, scores, color=bar_colors)
        plt.title(f'Boreal Campaign Audit :: {ACTIVE_MODEL_KEY.upper()} ({THEATER_MODE.upper()})')
        plt.ylabel('Strategic Score')
        plt.xticks(rotation=90, fontsize=6)
        plt.tight_layout()
        plt.savefig(os.path.join(RESULTS_DIR, f'batch_audit_{ACTIVE_MODEL_KEY}.png'))
        print(f"Visual report saved to {RESULTS_DIR}/batch_audit_{ACTIVE_MODEL_KEY}.png")
    except:
        print("[WARN] Matplotlib plot failed. Skipping visual output.")

    csv_path = os.path.join(RESULTS_DIR, f'batch_audit_{ACTIVE_MODEL_KEY}.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)
    print(f"Detailed CSV saved to {csv_path}")

if __name__ == "__main__":
    run_batch_tests()