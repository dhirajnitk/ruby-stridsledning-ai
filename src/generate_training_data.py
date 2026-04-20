import json
import os
import random
import math
import numpy as np
from engine import evaluate_threats_advanced, extract_rl_features
from agent_backend import load_battlefield_state, CSV_FILE_PATH
from models import Threat

def generate_adversarial_scenario(num_threats=15):
    threats = []
    # Randomized Flank Bias (trains Spatial Awareness)
    bias = random.choice(["west", "east", "center", "split"])
    
    for i in range(num_threats):
        if bias == "west":
            x = random.uniform(0, 500)
        elif bias == "east":
            x = random.uniform(1000, 1500)
        elif bias == "center":
            x = random.uniform(600, 900)
        else: # split
            x = random.choice([random.uniform(0, 300), random.uniform(1200, 1500)])
            
        y = random.uniform(800, 1600)
        speed = random.choice([800, 2000, 4500])
        t_type = "bomber" if speed < 1000 else ("fast-mover" if speed < 3000 else "hypersonic")
        
        threats.append(Threat(
            id=f"T{i}",
            x=x, y=y,
            speed_kmh=speed,
            heading="Capital X",
            estimated_type=t_type,
            threat_value=random.uniform(50, 150)
        ))
    return threats

def collect_training_corpus(num_samples=500):
    print(f"[DATA] Initializing Oracle-based data collection ({num_samples} samples)...")
    base_state = load_battlefield_state(CSV_FILE_PATH)
    dataset = []
    
    for i in range(num_samples):
        # Vary threat density to train Logistics Stress
        n = random.randint(5, 30)
        threats = generate_adversarial_scenario(n)
        weather = random.choice(["clear", "fog", "storm"])
        primary = random.choice(["balanced", "fortress", "aggressive"])
        blend = random.uniform(0.1, 0.9)
        
        # Use MCTS Oracle (1000 iterations) to get ground truth
        result = evaluate_threats_advanced(
            base_state, threats, 
            mcts_iterations=1000, 
            weather=weather,
            doctrine_primary=primary,
            doctrine_blend=blend,
            use_rl=False # Don't use the old RL to train the new one
        )
        
        # Extract the features (using our new 15-dim extractor)
        features = extract_rl_features(base_state, threats, weather, primary, blend, for_value=True)
        
        sample = {
            "features": features,
            "target_value": result["strategic_consequence_score"],
            "optimal_weights": list(result["active_doctrine"]["blended_weights"].values()),
            "metadata": {
                "num_threats": n,
                "weather": weather,
                "survival": result["strategic_consequence_score"] > -100
            }
        }
        dataset.append(sample)
        
        if (i + 1) % 50 == 0:
            print(f"[DATA] Progress: {i+1}/{num_samples} samples collected.")

    output_path = "data/training/resnet_oracle_data.json"
    os.makedirs("data/training", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(dataset, f, indent=2)
    
    print(f"[SUCCESS] Dataset saved to {output_path}")

if __name__ == "__main__":
    collect_training_corpus(1000) # Increased to 1000 samples for high-fidelity training
