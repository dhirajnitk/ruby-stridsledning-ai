import json
import glob
import csv
import math
import time
from agent_backend import load_battlefield_state, CSV_FILE_PATH
from engine import evaluate_threats_advanced
from models import Threat

def extract_state_features(state, threats):
    """
    Converts the complex Python objects into a flat numerical vector [X]
    that a Neural Network can understand.
    """
    features = {}
    
    # 1. Base Inventories
    for b in state.bases:
        if "Capital" in b.name:
            features["cap_sam"] = b.inventory.get("SAM", 0)
        elif "Northern" in b.name:
            features["base_a_sam"] = b.inventory.get("SAM", 0)
            features["base_a_fighter"] = b.inventory.get("Fighter", 0)
        elif "Highridge" in b.name:
            features["base_b_sam"] = b.inventory.get("SAM", 0)
            features["base_b_fighter"] = b.inventory.get("Fighter", 0)
            
    # 2. Threat Composition
    features["num_decoys"] = sum(1 for t in threats if t.estimated_type == "decoy")
    features["num_bombers"] = sum(1 for t in threats if t.estimated_type == "bomber")
    features["num_fast_movers"] = sum(1 for t in threats if t.estimated_type == "fast-mover")
    
    # 3. Spatial Danger (Distance of the closest threat to the Capital)
    min_dist = float('inf')
    for t in threats:
        dist = math.hypot(418.3 - t.x, 95.0 - t.y)
        if dist < min_dist:
            min_dist = dist
    features["closest_threat_dist"] = round(min_dist, 2) if min_dist != float('inf') else 0.0
    
    # Return as an ordered list
    return [
        features.get("cap_sam", 0), features.get("base_a_sam", 0), features.get("base_a_fighter", 0),
        features.get("base_b_sam", 0), features.get("base_b_fighter", 0),
        features.get("num_decoys", 0), features.get("num_bombers", 0), features.get("num_fast_movers", 0),
        features.get("closest_threat_dist", 0.0)
    ]

if __name__ == "__main__":
    print("Initializing RL Data Generator...")
    base_state = load_battlefield_state(CSV_FILE_PATH)
    batch_files = sorted(glob.glob("simulated_campaign_batch_*.json"))
    
    dataset = []
    headers = ["scenario_id", "cap_sam", "base_a_sam", "base_a_fighter", "base_b_sam", "base_b_fighter", 
               "num_decoys", "num_bombers", "num_fast_movers", "closest_threat_dist", "target_mcts_score"]
    dataset.append(headers)
    
    print(f"Processing {len(batch_files)} batch files to generate training labels...")
    
    for file in batch_files:
        with open(file, 'r') as f:
            batch_data = json.load(f)
            
        for scenario_id, threats_data in batch_data.items():
            active_threats = []
            for t in threats_data:
                active_threats.append(Threat(
                    id=t["id"], x=t["start_x"], y=t["start_y"], speed_kmh=t["speed"],
                    heading="Capital X", estimated_type=t["type"], threat_value=t["threat_value"]
                ))
                
            features_X = extract_state_features(base_state, active_threats)
            decision = evaluate_threats_advanced(base_state, active_threats, mcts_iterations=200)
            label_Y = decision["strategic_consequence_score"]
            dataset.append([scenario_id] + features_X + [round(label_Y, 2)])
            print(f"Generated Data Point: {scenario_id} -> Features: {features_X} -> Target Score: {label_Y:.2f}")

    with open('rl_value_network_training_data.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(dataset)
    print("\n[SUCCESS] Exported training data to 'rl_value_network_training_data.csv'. Ready for PyTorch!")