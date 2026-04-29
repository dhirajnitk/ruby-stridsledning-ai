import os
import sys
sys.path.append("src")
from core.models import load_battlefield_state, CSV_FILE_PATH, Threat
from core.engine import evaluate_threats_advanced

def debug_repro():
    base_state = load_battlefield_state(CSV_FILE_PATH)
    threats = [
        Threat(id="T1", x=100, y=100, speed_kmh=800, estimated_type="drone", threat_value=50, heading="Base A")
    ]
    try:
        score, details, _ = evaluate_threats_advanced(base_state, threats, mcts_iterations=1, weather="clear")
        print("Success")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_repro()
