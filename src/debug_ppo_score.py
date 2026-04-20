import torch
import random
from engine import evaluate_threats_advanced, TacticalEngine
from agent_backend import load_battlefield_state
from models import Threat

state = load_battlefield_state('data/input/Boreal_passage_coordinates.csv')
threats = []
for i in range(450):
    threats.append(Threat(f"T-{i}", random.uniform(500, 2500), random.uniform(100, 800), 3000, "Capital X", "bomber", 100))

print("Evaluating with Heuristic...")
dec_h = evaluate_threats_advanced(state, threats, mcts_iterations=10, use_rl=False, use_ppo=False)
print(f"Heuristic Score: {dec_h['strategic_consequence_score']}")

print("\nEvaluating with PPO...")
dec_p = evaluate_threats_advanced(state, threats, mcts_iterations=10, use_rl=False, use_ppo=True)
print(f"PPO Score: {dec_p['strategic_consequence_score']}")
print(f"PPO Assignments: {len(dec_p['tactical_assignments'])}")
