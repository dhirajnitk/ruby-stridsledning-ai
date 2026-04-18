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
    """Extracts a 10-feature observation vector from the current battlefield state."""
    num_threats = len(threats)
    capital = next((b for b in state.bases if "Capital" in b.name), None)
    cx, cy = (capital.x, capital.y) if capital else (418.3, 95.0)
    
    distances = [math.hypot(t.x - cx, t.y - cy) for t in threats] if threats else [1000.0]
    avg_dist = sum(distances) / len(distances)
    min_dist = min(distances)
    total_val = sum(t.threat_value for t in threats)
    
    fighters = sum(b.inventory.get("fighter", 0) for b in state.bases)
    sams = sum(b.inventory.get("sam", 0) for b in state.bases)
    drones = sum(b.inventory.get("drone", 0) for b in state.bases)
    cap_sams = capital.inventory.get("sam", 0) if capital else 0
    weather_bin = 0.0 if weather == "clear" else 1.0
    
    return [num_threats, avg_dist, min_dist, total_val, fighters, sams, drones, cap_sams, weather_bin, blend]

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
                    res = evaluate_threats_advanced(base_state, active_threats, mcts_iterations=MCTS_ITERATIONS, doctrine_primary=config["p"], doctrine_secondary=config["s"], doctrine_blend=config["b"])
                    row = features + [config["p"], res["strategic_consequence_score"]]
                    writer.writerow(row)
                    count += 1
    print(f"\n[OK] Phase 1 Complete! Harvested {count} samples to {DATA_OUTPUT_PATH}")

if __name__ == "__main__":
    collect_training_data()
