import sys
import os
sys.path.append("src")
from engine import extract_rl_features
from models import GameState, Base, Threat
import math

print("[PROBE] Initializing Sensory Test...")
base = Base("Test Base", 400.0, 100.0, {"sam": 10})
state = GameState(bases=[base])
threats = [
    Threat(id="T1", x=410.0, y=110.0, speed_kmh=2000.0, heading="Capital X", estimated_type="bomber", threat_value=100.0),
    Threat(id="T2", x=500.0, y=500.0, speed_kmh=4500.0, heading="Capital X", estimated_type="fast-mover", threat_value=200.0)
]

print("[PROBE] Testing Feature Extraction...")
try:
    features = extract_rl_features(state, threats)
    print(f"[PROBE] SUCCESS! Features: {features}")
    print(f"[PROBE] Vector Length: {len(features)}")
except Exception as e:
    print(f"[PROBE] FAILURE: {e}")
