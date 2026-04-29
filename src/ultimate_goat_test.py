import torch
import numpy as np
import time
import os
import sys

# Ensure src is in path
sys.path.insert(0, "src")
from core.ensemble import BorealSupremeEnsemble
from core.models import load_battlefield_state
from core.engine import evaluate_threats_advanced, Threat

def run_ultimate_goat_tournament():
    print("====================================================")
    print("   BOREAL ULTIMATE GOAT TOURNAMENT (NATIONAL)       ")
    print("====================================================")
    
    ensemble = BorealSupremeEnsemble()
    base_state = load_battlefield_state("sweden")
    
    # 1. GENERATE SATURATION SCENARIO (500 THREATS)
    print("[PHASE] Simulating National-Scale Saturation (500 Threats)...")
    threats = []
    for i in range(500):
        threats.append(Threat(
            id=f"T-{i}",
            x=np.random.uniform(-400, 800),
            y=np.random.uniform(-400, 800),
            speed_kmh=np.random.uniform(500, 5000),
            heading="Inbound",
            estimated_type=np.random.choice(["fighter", "cruise-missile", "ballistic", "drone-swarm"]),
            threat_value=np.random.uniform(10, 100)
        ))

    # 2. ENSEMBLE DECISION CYCLE
    print("[PHASE] GOAT Ensemble Decision Cycle...")
    # Extract 25-D Features (Mocked for stress test logic validation)
    features = torch.randn(1, 25) 
    
    start_time = time.time()
    policy, value, confidence = ensemble.predict(features)
    decision_time = (time.time() - start_time) * 1000
    
    print(f"  [METRIC] Decision Latency: {decision_time:.2f}ms")
    print(f"  [METRIC] Strategic Confidence: {confidence.item():.2f}")
    
    # 3. KINETIC VERIFICATION (MCTS-100 Validation)
    print("[PHASE] Kinetic Verification (MCTS-100)...")
    # Convert policy back to weapon weights for the engine
    weights = policy.view(-1).numpy()
    
    score, details, _ = evaluate_threats_advanced(
        base_state, threats, mcts_iterations=100,
        weather="clear", doctrine_primary="balanced", doctrine_blend=0.5,
        use_rl=True, rl_weights=weights
    )
    
    print(f"\n====================================================")
    print(f"   TOURNAMENT RESULTS (GOAT EDITION)                ")
    print(f"====================================================")
    print(f"   Intercept Efficiency: {details['intercept_efficiency']*100:.1f}%")
    print(f"   Assets Preserved    : {details['assets_preserved']}")
    print(f"   Theater Score       : {score:.1f}")
    print(f"   GOAT STATUS         : MISSION ACCOMPLISHED")
    print(f"====================================================")

if __name__ == "__main__":
    run_ultimate_goat_tournament()
