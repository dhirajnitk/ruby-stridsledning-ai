import json
import os
import csv
import glob
import math
import numpy as np
from agent_backend import load_battlefield_state, CSV_FILE_PATH
from engine import evaluate_threats_advanced, DoctrineManager
from models import Threat, GameState

# Performance Config
MCTS_ITERATIONS = 500  # High fidelity for the teacher function
DATA_OUTPUT_PATH = "data/rl_training_data.csv"

def extract_features(state: GameState, threats: list[Threat], weather: str, primary="balanced", blend=1.0):
    """Extracts the canonical 18-feature observation vector matching core/engine.py.

    FIX B8: was 10D with wrong inventory keys (\"fighter\", \"sam\", \"drone\");
            now 18D using the same keys as extract_rl_features() in core/engine.py.
    """
    import math as _math
    num_threats = len(threats)
    if not num_threats:
        return [0.0] * 18
    capital = next((b for b in state.bases if "Capital" in b.name), state.bases[0])
    cx, cy = capital.x, capital.y

    dists = [_math.hypot(t.x - cx, t.y - cy) for t in threats]
    avg_dist   = sum(dists) / num_threats
    min_dist   = min(dists)
    total_val  = sum(t.threat_value for t in threats)

    # FIX B8: correct inventory keys — match core/engine.py extract_rl_features()
    fighters  = sum(b.inventory.get("meteor",        0) for b in state.bases)
    sams      = sum(b.inventory.get("patriot-pac3",  0) for b in state.bases)
    drones    = sum(b.inventory.get("saab-nimbrix",  0) for b in state.bases)
    cap_sams  = capital.inventory.get("patriot-pac3", 0)

    weather_bin = 0.0 if weather == "clear" else 1.0

    west_threats  = sum(1 for t in threats if t.x < cx)
    east_threats  = num_threats - west_threats
    ammo_stress   = (sams + fighters + drones) / (num_threats + 1)
    dist_norm     = avg_dist  / 1000.0
    val_norm      = total_val / 1000.0

    # Advanced Trajectory Awareness (V2 — MARV/MIRV/Dogfight)
    has_marv = 1.0 if any(getattr(t, "is_marv", False) for t in threats) else 0.0
    has_mirv = 1.0 if any(getattr(t, "is_mirv", False) and not getattr(t, "mirv_released", False)
                          for t in threats) else 0.0
    total_mirv_warheads = float(sum(getattr(t, "mirv_count", 0) for t in threats
                                    if getattr(t, "is_mirv", False) and not getattr(t, "mirv_released", False)))

    return [
        num_threats, avg_dist, min_dist, total_val,
        fighters, sams, drones, cap_sams, weather_bin, blend,
        west_threats, east_threats, ammo_stress, dist_norm, val_norm,
        has_marv, has_mirv, total_mirv_warheads,
    ]

def collect_training_data():
    print("="*60)
    print("  BOREAL CHESSMASTER — RL DATA HARVESTER (PHASE 1)")
    print("="*60)
    
    os.makedirs("data", exist_ok=True)
    INPUT_DIR = "data/input"
    batch_files = sorted(glob.glob(os.path.join(INPUT_DIR, "simulated_campaign_batch_*.json")))
    if not batch_files: return
    
    base_state = load_battlefield_state(CSV_FILE_PATH)
    configurations = [
        {"p": "balanced", "s": None, "b": 1.0},
        {"p": "aggressive", "s": None, "b": 1.0},
        {"p": "fortress", "s": None, "b": 1.0},
        {"p": "economy", "s": None, "b": 1.0},
        {"p": "fortress", "s": "economy", "b": 0.7},
        {"p": "aggressive", "s": "economy", "b": 0.5},
    ]

    with open(DATA_OUTPUT_PATH, mode='w', newline='') as f:
        writer = csv.writer(f)
        header = ["num_threats", "avg_dist", "min_dist", "total_val", "fighters", "sams", "drones", "cap_sams", "weather_bin", "blend_ratio", "primary_doctrine", "target_mcts_score"]
        writer.writerow(header)
        
        count = 0
        for file in batch_files:
            print(f"Processing {os.path.basename(file)}...")
            with open(file, 'r') as bf: scenarios = json.load(bf)
            for sc_id, threat_list in scenarios.items():
                active_threats = [Threat(t["id"], t["start_x"], t["start_y"], t["speed"], "Capital X", t["type"], t["threat_value"]) for t in threat_list]
                for config in configurations:
                    features = extract_features(base_state, active_threats, "clear", config["p"], config["b"])
                    # FIX B9: evaluate_threats_advanced returns (score, details, rl_val) tuple, not a dict
                    score, details, _rl_val = evaluate_threats_advanced(
                        base_state, active_threats,
                        mcts_iterations=MCTS_ITERATIONS,
                        doctrine_primary=config["p"],
                        doctrine_secondary=config["s"],
                        doctrine_blend=config["b"],
                    )
                    row = features + [config["p"], score]
                    writer.writerow(row)
                    count += 1
    print(f"\n[OK] Phase 1 Complete! Harvested {count} samples to {DATA_OUTPUT_PATH}")

if __name__ == "__main__":
    collect_training_data()
