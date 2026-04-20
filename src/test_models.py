import torch
import json
import numpy as np
from engine import ValueNetwork, DoctrineNetwork

def test_models():
    print("Testing Boreal Chessmaster RL Models")
    print("-" * 40)
    
    # 1. Load Params
    print("Loading params...")
    try:
        with open("models/value_network_params.json", "r") as f:
            params = json.load(f)
        mean = np.array(params["scaler_mean"])
        scale = np.array(params["scaler_scale"])
        input_dim = len(mean)
        print(f"Params loaded. Input dimension: {input_dim}")
        print(f"Features expected: {params['numeric_cols']}")
    except Exception as e:
        print(f"Failed to load params: {e}")
        return

    # 2. Load Models
    print("\nLoading models...")
    try:
        val_model = ValueNetwork(input_dim)
        val_model.load_state_dict(torch.load("models/value_network.pth", map_location='cpu'))
        val_model.eval()
        print(f"ValueNetwork loaded successfully.")
        
        doc_model = DoctrineNetwork(input_dim)
        doc_model.load_state_dict(torch.load("models/doctrine_network.pth", map_location='cpu'))
        doc_model.eval()
        print(f"DoctrineNetwork loaded successfully.")
    except Exception as e:
        print(f"Failed to load models: {e}")
        return

    # 3. Create a synthetic test scenario (15 features)
    # [num_threats, avg_dist, min_dist, total_val, fighters, sams, drones, cap_sams, weather_bin, blend, west, east, stress, dist_norm, val_norm]
    # Let's make a high threat scenario: 12 threats, close range (300km), high val
    raw_features = [
        12.0,       # num_threats
        400.0,      # avg_dist
        150.0,      # min_dist
        2500.0,     # total_val
        5.0,        # fighters
        20.0,       # sams
        10.0,       # drones
        5.0,        # cap_sams
        1.0,        # weather_bin (storm)
        0.5,        # blend
        8.0,        # west
        4.0,        # east
        35.0/13.0,  # stress (ammo / (threats+1))
        0.4,        # dist_norm
        2.5         # val_norm
    ]
    
    print("\nTest Scenario (Raw Features):")
    for name, val in zip(params["numeric_cols"], raw_features):
        print(f"  {name}: {val:.2f}")

    # Normalize
    norm_features = (np.array(raw_features) - mean) / scale
    input_tensor = torch.tensor([norm_features], dtype=torch.float32)

    # 4. Predict
    print("\nRunning inference...")
    with torch.no_grad():
        val_pred = val_model(input_tensor).item()
        doc_pred = doc_model(input_tensor)[0].numpy()

    print("\n--- RESULTS ---")
    print(f"Value Prediction (Strategic Consequence Score): {val_pred:.1f}")
    print("\nDoctrine Multipliers:")
    # Assuming standard order of weights:
    weight_keys = ["intercept_value", "leaker_penalty", "bomber_priority", "range_penalty", "capital_reserve", "economy_force", "fighter_risk", "swarm_penalty", "drone_attrition", "sam_depletion", "capital_proximity"]
    for i, mult in enumerate(doc_pred):
        key = weight_keys[i] if i < len(weight_keys) else f"Unknown_{i}"
        print(f"  {key}: {mult:.3f}x")

if __name__ == "__main__":
    test_models()
