import time
import json
import os
import random
import numpy as np
from fetch_real_clutter import fetch_baltic_clutter
from engine import evaluate_threats_advanced, extract_rl_features
from agent_backend import load_battlefield_state, CSV_FILE_PATH
from models import Threat

# --- CONFIGURATION ---
HARVEST_INTERVAL_SEC = 300 # Every 5 minutes
SAMPLES_PER_HARVEST = 50
OUTPUT_DIR = "data/training/live_harvester"

def live_harvester_loop():
    print(f"[LAUNCH] LIVE COMBAT HARVESTER | Interval: {HARVEST_INTERVAL_SEC}s")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    base_state = load_battlefield_state(CSV_FILE_PATH)
    
    total_samples = 0
    
    while True:
        print(f"\n[INTEL] Harvesting Live Baltic Sky...")
        real_traffic = fetch_baltic_clutter()
        
        if not real_traffic:
            print("[WARN] No live traffic acquired. Retrying in next cycle.")
            time.sleep(HARVEST_INTERVAL_SEC)
            continue
            
        print(f"[INTEL] Acquired {len(real_traffic)} live flight signatures.")
        
        harvest_features = []
        harvest_scores = []
        harvest_weights = []
        
        for i in range(SAMPLES_PER_HARVEST):
            # 1. Inject Hostiles into the LIVE scene
            n_hostile = random.randint(20, 100)
            threats = []
            
            # Real-World Clutter
            for c in real_traffic:
                # Relative KM mapping (Stockholm Anchor)
                rel_x = (c['lon'] - 18.07) * 111.0 + 800
                rel_y = (59.33 - c['lat']) * 111.0 + 650
                threats.append(Threat(
                    id=f"REAL-{c['callsign']}", x=rel_x, y=rel_y,
                    speed_kmh=c['velocity'] or 900, heading=str(c['heading'] or 0),
                    estimated_type="clutter", threat_value=0.0
                ))
            
            # Synthetic Hostiles
            for h in range(n_hostile):
                threats.append(Threat(
                    id=f"HOSTILE-{h}", x=random.uniform(1400, 1600), y=random.uniform(0, 1300),
                    speed_kmh=random.choice([2000, 4500]), heading="Capital X",
                    estimated_type="fast-mover", threat_value=random.uniform(100, 200)
                ))
                
            # 2. Oracle Labeling (MCTS)
            weather = random.choice(["clear", "fog", "storm"])
            primary = random.choice(["balanced", "aggressive", "fortress"])
            blend = random.uniform(0.1, 0.9)
            
            result = evaluate_threats_advanced(
                base_state, threats, 
                mcts_iterations=300, 
                weather=weather,
                doctrine_primary=primary,
                doctrine_blend=blend,
                use_rl=False
            )
            
            # 3. Extract Features
            features = extract_rl_features(base_state, threats, weather, primary, blend, for_value=True)
            harvest_features.append(features)
            harvest_scores.append(result["strategic_consequence_score"])
            harvest_weights.append(list(result["active_doctrine"]["blended_weights"].values()))
            
            if (i+1) % 10 == 0:
                print(f"[HARVEST] Processed {i+1}/{SAMPLES_PER_HARVEST} live-fused samples...")

        # Binary Export for this Harvest Cycle
        timestamp = int(time.time())
        output_path = os.path.join(OUTPUT_DIR, f"live_harvest_{timestamp}.npz")
        np.savez_compressed(
            output_path,
            features=np.array(harvest_features, dtype=np.float32),
            scores=np.array(harvest_scores, dtype=np.float32),
            weights=np.array(harvest_weights, dtype=np.float32)
        )
        
        total_samples += SAMPLES_PER_HARVEST
        print(f"[COMPLETE] Cycle Finished. Saved to {output_path} | Total Live Samples: {total_samples}")
        print(f"[SLEEP] Waiting for next tactical window...")
        time.sleep(HARVEST_INTERVAL_SEC)

if __name__ == "__main__":
    live_harvester_loop()
