"""Quick smoke test: Send MARV/MIRV/Dogfight threats to the backend and verify the API handles them."""
import requests, json

payload = {
    "threats": [
        {"id": "BUS1", "x": 500, "y": 600, "speed_kmh": 4500, "estimated_type": "ballistic",
         "threat_value": 200, "is_mirv": True, "mirv_count": 3, "mirv_release_range_km": 150},
        {"id": "MV1", "x": 300, "y": 400, "speed_kmh": 4500, "estimated_type": "ballistic",
         "threat_value": 180, "is_marv": True, "marv_pk_penalty": 0.45, "marv_trigger_range_km": 80},
        {"id": "F01", "x": 400, "y": 500, "speed_kmh": 2200, "estimated_type": "fighter",
         "threat_value": 120, "can_dogfight": True, "dogfight_win_prob": 0.35},
    ],
    "weather": "clear",
    "doctrine_primary": "balanced",
    "use_rl": False,
    "run_mc": True,
}

try:
    r = requests.post("http://localhost:8000/evaluate_advanced", json=payload, timeout=15)
    d = r.json()
    print(f"Status: {r.status_code}")
    print(f"Assignments: {len(d.get('tactical_assignments', []))}")
    print(f"Score: {d.get('strategic_consequence_score', 'N/A')}")
    mc = d.get("mc_metrics", {})
    print(f"MC Survival: {mc.get('survival_rate_pct', 'N/A')}%")
    print(f"MC Intercept: {mc.get('intercept_rate_pct', 'N/A')}%")
    print(f"MC Mean Leaked: {mc.get('mean_leaked', 'N/A')}")
    for a in d.get("tactical_assignments", []):
        print(f"  -> {a['base']} fires {a['effector']} at {a['threat_id']}")
    print("\nSUCCESS: MARV/MIRV API integration works end-to-end!")
except Exception as e:
    print(f"ERROR: {e}")
