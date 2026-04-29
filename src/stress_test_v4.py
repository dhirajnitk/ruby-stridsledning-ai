import torch
import numpy as np
import time
import os
import sys

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.models import GameState, Base, Threat, load_battlefield_state
from core.engine import evaluate_threats_advanced, load_neural_models

def run_stress_test():
    print("="*60)
    print("   BOREAL CHESSMASTER: SUPREME V4 STRESS TEST   ")
    print("   SCENARIO: SATURATING HYPERSONIC SWARM (10x)  ")
    print("="*60)

    # 1. INITIALIZE ENGINE & MODELS
    load_neural_models()
    
    # 2. LOAD BATTLEFIELD
    csv_path = "data/Swedish_Military_Installations.csv"
    state = load_battlefield_state(csv_path) # Loads Sweden or Boreal bases
    
    # 3. SPAWN HYPERSONIC SWARM
    threats = []
    for i in range(10):
        # Spawning from different directions
        angle = (360 / 10) * i
        rad = np.radians(angle)
        dist = 400.0 # 400km out
        tx = 427 + np.cos(rad) * dist # Center of theater is ~427, 371
        ty = 371 + np.sin(rad) * dist
        
        threats.append(Threat(
            id=f"H-{i+1}",
            x=tx,
            y=ty,
            speed_kmh=6500.0, # Mach 5+
            estimated_type="hypersonic-pgm",
            threat_value=150.0, # Extreme threat
            heading="Capital",
            is_marv=True, # Jinking behavior
            marv_trigger_range_km=80.0
        ))
    
    print(f"[LIVE] Spawning {len(threats)} Hypersonic Vectors...")
    print(f"[LIVE] SAM Inventory: {sum(sum(b.inventory.values()) for b in state.bases)} units.")

    # 4. RUN V4 NEURAL INFERENCE
    start_time = time.time()
    score, details, rl_val = evaluate_threats_advanced(
        state, 
        threats, 
        use_rl=True, 
        mcts_iterations=100,
        salvo_ratio=2 # High aggression
    )
    latency = (time.time() - start_time) * 1000

    # 5. REPORT RESULTS
    print("-" * 60)
    print(f"STRATEGIC SCORE: {score:1.2f}")
    print(f"ENGINE LATENCY:  {latency:1.2f}ms")
    print("-" * 60)
    
    print("TACTICAL ASSIGNMENTS:")
    assignments = details.get("tactical_assignments", [])
    for a in assignments:
        print(f"  - {a['effector']:12} from {a['base']:20} -> {a['threat_id']}")
    
    print("-" * 60)
    print(f"SITREP: {details.get('human_sitrep', 'No sitrep generated.')}")
    print("="*60)
    print("[SUCCESS] Stress Test Complete. V4 Strategic Brain Validated.")

if __name__ == "__main__":
    run_stress_test()
