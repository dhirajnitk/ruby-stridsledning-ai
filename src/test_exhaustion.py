import json
from engine import evaluate_threats_advanced
from agent_backend import load_battlefield_state, CSV_FILE_PATH
from models import Threat

def test_saturation_triage():
    print("[TEST] Initializing Saturation Event (50 Threats vs 20 SAMs)...")
    state = load_battlefield_state(CSV_FILE_PATH)
    
    # 1. Deplete ammo to simulate exhaustion (20 SAMs total)
    for b in state.bases:
        b.inventory = {"sam": 5 if "Capital" in b.name else 2}
    
    # 2. Spawn 50 mixed threats
    threats = []
    for i in range(50):
        target = "Capital X" if i < 10 else "Nordvik"
        threats.append(Threat(
            id=f"T{i}", x=1200, y=500, speed_kmh=2000, 
            heading=target, estimated_type="fast-mover", 
            threat_value=100 if i < 10 else 20 # High value for Capital threats
        ))
    
    # 3. Run evaluation
    result = evaluate_threats_advanced(state, threats, mcts_iterations=100)
    
    assignments = result["tactical_assignments"]
    cap_targets = [a for a in assignments if a["threat_id"] in [f"T{j}" for j in range(10)]]
    
    print(f"[RESULT] Total Assignments: {len(assignments)}")
    print(f"[RESULT] Capital Defense Assignments: {len(cap_targets)}/10")
    print(f"[RESULT] Triage Ignored: {result['triage_ignored_threats']} threats")
    
    if len(cap_targets) == 10:
        print("[SUCCESS] Triage logic successfully prioritized the Capital during saturation!")
    else:
        print("[FAILURE] Capital was not fully prioritized.")

if __name__ == "__main__":
    test_saturation_triage()
