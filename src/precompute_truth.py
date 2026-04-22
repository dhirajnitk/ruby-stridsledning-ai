"""
Monte Carlo Ground Truth Generator — 1000 attack sequences.
For each scenario:
  1. Generate random threats (varied types, speeds, counts)
  2. Run through MCTS engine 50x to get statistical ground truth
  3. Store results in CSV + JSON for dashboard replay
"""
import sys, os, json, csv, random, math, copy
sys.path.insert(0, os.path.dirname(__file__))
from models import Threat, Base, GameState, load_battlefield_state, EFFECTORS
from engine import TacticalEngine, StrategicMCTS, DoctrineManager

CSV_INPUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'input', 'Boreal_passage_coordinates.csv')
OUT_CSV   = os.path.join(os.path.dirname(__file__), '..', 'data', 'ground_truth.csv')
OUT_JSON  = os.path.join(os.path.dirname(__file__), '..', 'data', 'ground_truth_scenarios.json')

# Swedish bases for threat targeting
TARGETS = [
    {"id":"F21","name":"Luleå","x":185,"y":691},
    {"id":"F16","name":"Uppsala","x":-27,"y":63},
    {"id":"VID","name":"Vidsel","x":95,"y":728},
    {"id":"STO","name":"Stockholm","x":0,"y":0},
    {"id":"MUS","name":"Muskö","x":4,"y":-46},
    {"id":"F7","name":"Såtenäs","x":-313,"y":-99},
    {"id":"F17","name":"Ronneby","x":-172,"y":-340},
    {"id":"GOT","name":"Gotland","x":16,"y":-186},
    {"id":"GBG","name":"Gothenburg","x":-364,"y":-180},
]

THREAT_TYPES = ["bomber","fast-mover","drone","hypersonic","fighter","decoy"]
DOCTRINES = ["balanced","aggressive","fortress","economy"]

def gen_scenario(idx):
    """Generate a random attack scenario."""
    n = random.randint(2, 15)
    threats = []
    for i in range(n):
        tgt = random.choice(TARGETS)
        ttype = random.choice(THREAT_TYPES)
        speed = {
            "bomber": random.uniform(600,1200),
            "fast-mover": random.uniform(1500,3000),
            "drone": random.uniform(200,500),
            "hypersonic": random.uniform(4000,6000),
            "fighter": random.uniform(1800,2500),
            "decoy": random.uniform(300,800),
        }[ttype]
        # Start 300-800km east of target
        sx = tgt["x"] + random.uniform(300, 800)
        sy = tgt["y"] + random.uniform(-100, 100)
        val = random.uniform(20, 250)
        threats.append({
            "id": f"S{idx}-T{i}",
            "x": round(sx, 1), "y": round(sy, 1),
            "speed": round(speed, 1),
            "type": ttype,
            "value": round(val, 1),
            "target_id": tgt["id"],
            "target_name": tgt["name"],
            "target_x": tgt["x"], "target_y": tgt["y"]
        })
    return threats

def mc_evaluate(state, threat_objs, n_rollouts=50):
    """Run Monte Carlo evaluation: get optimal assignments + rollout stats."""
    weights, flags = DoctrineManager.get_blended_profile("balanced")
    assignments = TacticalEngine.get_optimal_assignments(state, threat_objs, weights=weights, flags=flags)
    
    scores = []
    for _ in range(n_rollouts):
        s, _ = StrategicMCTS._single_rollout(
            state, assignments, threat_objs,
            initial_cap_sams=sum(b.inventory.get("sam",0) for b in state.bases if "Capital" in b.name),
            weather="clear", weights=weights, flags=flags
        )
        scores.append(s)
    
    # Calculate Pk-based expected intercepts
    expected_kills = 0
    for a in assignments:
        t = next((t for t in threat_objs if t.id == a["threat_id"]), None)
        eff = EFFECTORS.get(a["effector"].lower())
        if t and eff:
            pk = eff.pk_matrix.get(t.estimated_type, 0.5)
            expected_kills += pk
    
    n_assigned = len(assignments)
    n_leaked = len(threat_objs) - n_assigned
    
    return {
        "n_assigned": n_assigned,
        "n_leaked": n_leaked,
        "expected_kills": round(expected_kills, 2),
        "mc_mean_score": round(sum(scores)/len(scores), 2),
        "mc_min_score": round(min(scores), 2),
        "mc_max_score": round(max(scores), 2),
        "mc_std": round((sum((s - sum(scores)/len(scores))**2 for s in scores)/len(scores))**0.5, 2),
        "assignments": [{"base":a["base"],"effector":a["effector"],"threat_id":a["threat_id"]} for a in assignments]
    }

def run():
    state = load_battlefield_state(CSV_INPUT)
    N = 1000
    
    scenarios_json = {}
    csv_rows = []
    
    print(f"Generating {N} scenarios with Monte Carlo ground truth...")
    
    for i in range(N):
        raw = gen_scenario(i)
        threat_objs = [
            Threat(t["id"], t["x"], t["y"], t["speed"], t["target_name"], t["type"], t["value"])
            for t in raw
        ]
        
        result = mc_evaluate(state, threat_objs, n_rollouts=50)
        
        type_counts = {}
        for t in raw:
            type_counts[t["type"]] = type_counts.get(t["type"], 0) + 1
        type_summary = ",".join(f"{k}:{v}" for k,v in sorted(type_counts.items()))
        
        csv_rows.append({
            "scenario_id": i,
            "n_threats": len(raw),
            "threat_types": type_summary,
            "n_assigned": result["n_assigned"],
            "n_leaked": result["n_leaked"],
            "expected_kills": result["expected_kills"],
            "mc_mean_score": result["mc_mean_score"],
            "mc_min_score": result["mc_min_score"],
            "mc_max_score": result["mc_max_score"],
            "mc_std": result["mc_std"],
            "tactical_acc": round(result["expected_kills"]/max(1,result["n_assigned"])*100, 1),
            "strategic_acc": round((len(raw)-result["n_leaked"])/len(raw)*100, 1),
        })
        
        scenarios_json[str(i)] = {
            "threats": raw,
            "ground_truth": result
        }
        
        if (i+1) % 100 == 0:
            print(f"  {i+1}/{N} done...")
    
    # Write CSV
    with open(OUT_CSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
        w.writeheader()
        w.writerows(csv_rows)
    
    # Write JSON (scenarios + ground truth for dashboard replay)
    with open(OUT_JSON, 'w') as f:
        json.dump(scenarios_json, f)
    
    # Summary
    avg_tac = sum(r["tactical_acc"] for r in csv_rows) / N
    avg_str = sum(r["strategic_acc"] for r in csv_rows) / N
    avg_score = sum(r["mc_mean_score"] for r in csv_rows) / N
    
    print(f"\nDone! {N} scenarios generated.")
    print(f"Avg Tactical Accuracy:  {avg_tac:.1f}%")
    print(f"Avg Strategic Accuracy: {avg_str:.1f}%")
    print(f"Avg MC Score:           {avg_score:.1f}")
    print(f"CSV: {OUT_CSV}")
    print(f"JSON: {OUT_JSON}")

if __name__ == '__main__':
    run()
