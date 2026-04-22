import json
try:
    with open('data/ground_truth_scenarios.json') as f:
        data = json.load(f)
    if isinstance(data, dict):
        scenarios = data.get('scenarios', [])
        print(f"Scenarios Found: {len(scenarios)}")
    else:
        print(f"Scenarios Found: {len(data)}")
except Exception as e:
    print(f"Error: {e}")
