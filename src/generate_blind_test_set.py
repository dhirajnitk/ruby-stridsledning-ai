import json
import os
import random
from models import Threat

def generate_blind_test_set():
    """Generate 100 fresh scenarios for unbiased evaluation of all models."""
    OUTPUT_DIR = "data/blind_test"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Target bases from the standard scenario
    TARGETS = [
        {"name": "Northern Vanguard Base", "x": 198.3, "y": 335.0},
        {"name": "Highridge Command", "x": 838.3, "y": 75.0},
        {"name": "Capital X", "x": 418.3, "y": 95.0}
    ]
    
    for b in range(1, 21): # 20 batches of 5 scenarios
        batch_data = {}
        for s in range(5):
            scenario_id = f"blind_scenario_{b}_{s}"
            num_threats = random.randint(15, 60) # Slightly harder than training
            threats = []
            for t_idx in range(num_threats):
                target = random.choice(TARGETS)
                threats.append({
                    "id": f"T-B{b}-S{s}-{t_idx}",
                    "start_x": random.uniform(500, 2500),
                    "start_y": random.uniform(100, 1500),
                    "speed": random.uniform(2000, 6000),
                    "target_x": target["x"],
                    "target_y": target["y"],
                    "type": random.choice(["bomber", "fighter", "drone", "fast-mover", "hypersonic"]),
                    "threat_value": random.uniform(50, 300)
                })
            batch_data[scenario_id] = threats
            
        with open(os.path.join(OUTPUT_DIR, f"blind_campaign_batch_{b}.json"), "w") as f:
            json.dump(batch_data, f, indent=2)
            
    print(f"[SUCCESS] 100 Fresh 'Blind Test' scenarios generated in {OUTPUT_DIR}")

if __name__ == "__main__":
    generate_blind_test_set()
