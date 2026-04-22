"""
Model Championship V2: Calculating Expected Kill Probability (EKP).
This measures the 'Intelligence' of the model by checking the quality of weapon-target pairings.
"""
import sys, os, json, csv
sys.path.insert(0, os.path.dirname(__file__))
from models import Threat, GameState, load_battlefield_state, EFFECTORS
from engine import evaluate_threats_advanced

CSV_INPUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'input', 'Boreal_passage_coordinates.csv')
SCENARIOS_JSON = os.path.join(os.path.dirname(__file__), '..', 'data', 'ground_truth_scenarios.json')

def get_pk(effector_type, threat_type):
    eff = EFFECTORS.get(effector_type.lower())
    if not eff: return 0.5
    return eff.pk_matrix.get(threat_type, 0.5)

def run_championship():
    state = load_battlefield_state(CSV_INPUT)
    with open(SCENARIOS_JSON) as f:
        all_scenarios = json.load(f)
    
    test_ids = list(all_scenarios.keys())[:100] 
    
    models = [
        {"name": "Classical Heuristic", "use_rl": False, "use_ppo": False},
        {"name": "MCTS-Optimized",      "use_rl": False, "use_ppo": False, "iters": 100},
    ]
    
    final_stats = []

    for mdef in models:
        print(f"Auditing Model: {mdef['name']}...")
        total_threats = 0
        total_epk = 0
        total_score = 0
        
        for sid in test_ids:
            sc = all_scenarios[sid]
            threat_objs = [
                Threat(t["id"], t["x"], t["y"], t["speed"], t["target_name"], t["type"], t["value"])
                for t in sc["threats"]
            ]
            
            res = evaluate_threats_advanced(
                state, threat_objs, 
                mcts_iterations=mdef.get("iters", 20),
                use_rl=mdef["use_rl"], 
                use_ppo=mdef["use_ppo"]
            )
            
            total_threats += len(threat_objs)
            # Calculate EPk for this scenario's assignments
            for a in res["tactical_assignments"]:
                t_obj = next((t for t in threat_objs if t.id == a["threat_id"]), None)
                if t_obj:
                    epk = get_pk(a["effector"], t_obj.estimated_type)
                    total_epk += epk
            
            total_score += res["strategic_consequence_score"]

        avg_epk = (total_epk / total_threats) * 100
        final_stats.append({
            "Model": mdef["name"],
            "Avg Score": round(total_score / len(test_ids), 2),
            "Expected Accuracy (EPk)": round(avg_epk, 2)
        })

    print("\nCHAMPIONSHIP RESULTS (ACCURACY AUDIT):")
    for s in final_stats:
        print(f"| {s['Model']:<20} | Score: {s['Avg Score']:<8} | Expected Acc: {s['Expected Accuracy (EPk)']}% |")

if __name__ == "__main__":
    run_championship()
