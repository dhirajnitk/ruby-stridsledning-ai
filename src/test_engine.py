import json
from engine import evaluate_threats_advanced
from models import GameState, Threat, Base

def test_boreal_scenario():
    # Using the exact JSON structure you defined
    scenario_json = """
    {
      "tick": 42,
      "bases": [
        {
          "id": "Northern Vanguard Base",
          "x": 198.3,
          "y": 335.0,
          "inventory": { "fighters": 4, "sams": 10 }
        },
        {
          "id": "Highridge Command",
          "x": 838.3,
          "y": 75.0,
          "inventory": { "fighters": 6, "sams": 2 }
        }
      ],
      "detected_threats": [
        {
          "id": "T-001",
          "type": "decoy",
          "loc": { "x": 1400.0, "y": 300.0 },
          "heading_vector": { "vx": -15.0, "vy": 2.5 }
        },
        {
          "id": "T-002",
          "type": "unknown",
          "loc": { "x": 550.0, "y": 200.0 }, 
          "heading_vector": { "vx": -10.0, "vy": -2.0 },
          "note": "SPAWNED IN BLIND SPOT"
        }
      ]
    }
    """
    
    data = json.loads(scenario_json)
    
    # Map the JSON dictionary into our Data Classes
    bases = [Base(name=b["id"], x=b["x"], y=b["y"], inventory={"fighter": b["inventory"].get("fighters", 0), "sam": b["inventory"].get("sams", 0), "drone": 10}) for b in data["bases"]]
    game_state = GameState(bases=bases, blind_spots=[(656.7, 493.3)])
    
    threats = []
    for t in data["detected_threats"]:
        # Derive a rough speed from the heading vector for the engine
        speed_kmh = (abs(t["heading_vector"]["vx"]) + abs(t["heading_vector"]["vy"])) * 100 
        threats.append(Threat(id=t["id"], x=t["loc"]["x"], y=t["loc"]["y"], speed_kmh=speed_kmh, heading="Capital", estimated_type=t["type"], threat_value=15.0 if t["type"] == "decoy" else 85.0))
        
    result = evaluate_threats_advanced(game_state, threats)
    print("Test Result for Boreal Scenario:\n", json.dumps(result, indent=2))

if __name__ == "__main__":
    test_boreal_scenario()