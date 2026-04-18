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
MCTS_ITERATIONS = 500  # Faster but enough for learning trends
DATA_OUTPUT_PATH = "data/rl_training_data.csv"

def extract_features(state: GameState, threats: list[Threat], weather: str):
    """Extracts a 9-feature observation vector from the current battlefield state."""
    # 1. Threat count
    num_threats = len(threats)
    
    # 2. Avg/Min distance to Capital
    capital = next((b for b in state.bases if "Capital" in b.name), None)
    cx, cy = (capital.x, capital.y) if capital else (418.3, 95.0)
    
    distances = [math.hypot(t.x - cx, t.y - cy) for t in threats] if threats else [1000.0]
    avg_dist = sum(distances) / len(distances)
    min_dist = min(distances)
    
    # 3. Total threat value
    total_val = sum(t.threat_value for t in threats)
    
    # 4. Inventory aggregates
    fighters = sum(b.inventory.get("fighter", 0) for b in state.bases)
    sams = sum(b.inventory.get("sam", 0) for b in state.bases)
    drones = sum(b.inventory.get("drone", 0) for b in state.bases)
    
    # 5. Capital specific SAMs
    cap_sams = capital.inventory.get("sam", 0) if capital else 0
    
    # 6. Weather encoding
    weather_bin = 0.0 if weather == "clear" else 1.0
    
    return [
        num_threats, 
        avg_dist, 
        min_dist, 
        total_val, 
        fighters, 
        sams, 
        drones, 
        cap_sams, 
        weather_bin
    ]

def collect_training_data():
    print("="*60)
    print("  BOREAL CHESSMASTER — RL DATA HARVESTER (PHASE 1)")
    print("="*60)
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Load scenarios
    INPUT_DIR = "data/input"
    batch_files = sorted(glob.glob(os.path.join(INPUT_DIR, "simulated_campaign_batch_*.json")))
    
    if not batch_files:
        print("No scenarios found in data/input/!")
        return

    base_state = load_battlefield_state(CSV_FILE_PATH)
    
    # We will sweep every scenario with multiple doctrine configurations 
    # to show the network how different 'actions' lead to different 'rewards'
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
        header = [
            "num_threats", "avg_dist", "min_dist", "total_val", 
            "fighters", "sams", "drones", "cap_sams", "weather_bin",
            "primary_doctrine", "blend_ratio",
            "strategic_score"
        ]
        writer.writerow(header)
        
        count = 0
        for file in batch_files:
            print(f"Processing {os.path.basename(file)}...")
            with open(file, 'r') as bf:
                scenarios = json.load(bf)
                
            for sc_id, threat_list in scenarios.items():
                # Convert to Threat objects
                active_threats = []
                for t in threat_list:
                    active_threats.append(Threat(t["id"], t["start_x"], t["start_y"], t["speed"], "Arktholm", t["type"], t["threat_value"]))
                
                # Extract fixed state features
                features = extract_features(base_state, active_threats, "clear")
                
                for config in configurations:
                    # Run engine to get reward
                    res = evaluate_threats_advanced(
                        base_state, active_threats, 
                        mcts_iterations=MCTS_ITERATIONS,
                        doctrine_primary=config["p"],
                        doctrine_secondary=config["s"],
                        doctrine_blend=config["b"]
                    )
                    
                    score = res["strategic_consequence_score"]
                    
                    # Row: Features + Action Params + Reward
                    row = features + [config["p"], config["b"], score]
                    writer.writerow(row)
                    count += 1
                    
                print(f"  > Scenario {sc_id} complete ({len(configurations)} samples added)")

    print(f"\n[OK] Phase 1 Complete! Harvested {count} training samples to {DATA_OUTPUT_PATH}")

if __name__ == "__main__":
    collect_training_data()
