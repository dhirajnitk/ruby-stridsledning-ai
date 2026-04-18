import math
import copy
import random
import time
import concurrent.futures
import os
import json
import numpy as np
from scipy.optimize import linear_sum_assignment
from models import GameState, Threat, EFFECTORS

def extract_rl_features(state, threats, weather="clear", doctrine="balanced", blend=0.7, for_value=True):
    """Converts battlefield state into a 10 or 15-feature tensor for RL networks."""
    # Numeric features
    num_threats = len(threats)
    avg_threat_dist = np.mean([math.hypot(t.x-418, t.y-95) for t in threats]) if threats else 1000.0
    max_threat_val = max([t.threat_value for t in threats]) if threats else 0.0
    total_sams = sum([b.inventory.get("sam", 0) for b in state.bases])
    total_fighters = sum([b.inventory.get("fighter", 0) for b in state.bases])
    
    features = [num_threats, avg_threat_dist/1000.0, max_threat_val/100.0, total_sams/20.0, total_fighters/10.0]
    
    if for_value:
        # 15-feature set for Value Network
        weather_map = {"clear": 1.0, "storm": 0.5, "fog": 0.7}
        features += [weather_map.get(weather, 1.0), blend]
        # One-hot doctrine (simplified)
        doc_map = {"balanced": [1,0,0], "aggressive": [0,1,0], "fortress": [0,0,1]}
        features += doc_map.get(doctrine, [1,0,0])
        while len(features) < 15: features.append(0.0)
    else:
        # 10-feature set for Doctrine Network
        while len(features) < 10: features.append(0.0)
        
    return np.array(features, dtype=np.float32)

# --- RL VALUE & POLICY NETWORK INTEGRATION ---
try:
    import torch
    import torch.nn as nn
    
    class ValueNetwork(nn.Module):
        def __init__(self, input_dim=15): # 9 numeric + 5 one-hot + 1 blend
            super(ValueNetwork, self).__init__()
            self.network = nn.Sequential(
                nn.Linear(input_dim, 64), nn.ReLU(),
                nn.Linear(64, 32), nn.ReLU(),
                nn.Linear(32, 16), nn.ReLU(),
                nn.Linear(16, 1)
            )
        def forward(self, x): return self.network(x)

    class DoctrineNetwork(nn.Module):
        def __init__(self, input_dim=10):
            super(DoctrineNetwork, self).__init__()
            self.network = nn.Sequential(
                nn.Linear(input_dim, 64), nn.ReLU(),
                nn.Linear(64, 64), nn.ReLU(),
                nn.Linear(64, 14), nn.Softplus()
            )
        def forward(self, x): return self.network(x)

    RL_MODEL = None
    RL_PARAMS = None
    MODEL_PATH = "models/value_network.pth"
    PARAMS_PATH = "models/value_network_params.json"
    
    if os.path.exists(MODEL_PATH) and os.path.exists(PARAMS_PATH):
        try:
            with open(PARAMS_PATH, "r") as f: RL_PARAMS = json.load(f)
            input_dim = len(RL_PARAMS["numeric_cols"]) + len(RL_PARAMS["doctrine_names"])
            RL_MODEL = ValueNetwork(input_dim)
            RL_MODEL.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cpu')))
            RL_MODEL.eval()
            print(f"[SYSTEM] Successfully hot-loaded RL Value Network from {MODEL_PATH}")
        except Exception as e: print(f"[SYSTEM] Failed to load RL Model: {e}")

    DOCTRINE_MODEL = None
    DOC_PARAMS = None
    DOC_MODEL_PATH = "models/doctrine_network.pth"
    DOC_PARAMS_PATH = "models/policy_network_params.json"
    
    if os.path.exists(DOC_MODEL_PATH) and os.path.exists(DOC_PARAMS_PATH):
        try:
            with open(DOC_PARAMS_PATH, "r") as f: DOC_PARAMS = json.load(f)
            DOCTRINE_MODEL = DoctrineNetwork(10)
            DOCTRINE_MODEL.load_state_dict(torch.load(DOC_MODEL_PATH, map_location=torch.device('cpu')))
            DOCTRINE_MODEL.eval()
            print(f"[SYSTEM] Successfully hot-loaded RL Doctrine Manager from {DOC_MODEL_PATH}")
        except Exception as e: print(f"[SYSTEM] Failed to load Doctrine Model: {e}")

except ImportError:
    RL_MODEL = DOCTRINE_MODEL = None
    print("[SYSTEM] PyTorch not installed. Falling back to classical MCTS engine.")

def extract_rl_features(state: GameState, threats: list[Threat], weather: str = "clear", primary: str = "balanced", blend: float = 1.0, for_value: bool = False):
    """Converts battlefield state into a flat tensor for RL networks."""
    num_threats = len(threats)
    capital = next((b for b in state.bases if "Capital" in b.name), None)
    cx, cy = (capital.x, capital.y) if capital else (418.3, 95.0)
    
    distances = [math.hypot(t.x - cx, t.y - cy) for t in threats] if threats else [1000.0]
    avg_dist = sum(distances) / len(distances)
    min_dist = min(distances)
    total_val = sum(t.threat_value for t in threats)
    
    fighters = sum(b.inventory.get("fighter", 0) for b in state.bases)
    sams = sum(b.inventory.get("sam", 0) for b in state.bases)
    drones = sum(b.inventory.get("drone", 0) for b in state.bases)
    cap_sams = capital.inventory.get("sam", 0) if capital else 0
    weather_bin = 0.0 if weather == "clear" else 1.0
    
    numeric_features = [num_threats, avg_dist, min_dist, total_val, fighters, sams, drones, cap_sams, weather_bin, blend]
    
    if for_value and RL_MODEL and RL_PARAMS:
        mean = np.array(RL_PARAMS["scaler_mean"])
        scale = np.array(RL_PARAMS["scaler_scale"])
        scaled_numeric = (np.array(numeric_features) - mean) / scale
        one_hot = [1.0 if d == primary else 0.0 for d in RL_PARAMS["doctrine_categories"]]
        return np.hstack([scaled_numeric, one_hot])
        
    if DOC_PARAMS:
        mean = np.array(DOC_PARAMS["scaler_mean"])
        scale = np.array(DOC_PARAMS["scaler_scale"])
        return (np.array(numeric_features) - mean) / scale
        
    return numeric_features

class DoctrineManager:
    """Manages profile registry, blending, and flag short-circuiting."""
    DEFAULT_FLAGS = {
        "enable_point_defense": True, "enable_fuel_penalty": True, "enable_sam_range_limit": True,
        "enable_bomber_priority": True, "enable_economy_force": True, "enable_swarm_doctrine": True,
        "enable_capital_reserve": True, "enable_base_lock": True
    }

    PROFILES = {
        "balanced": {
            "weights": {"t_int_mult": 1.5, "point_defense_bonus": 100.0, "fuel_penalty": 80.0, "sam_range_penalty": 60.0, "bomber_priority": 50.0, "economy_force": 50.0, "speed_deficit_mult": 0.05, "swarm_penalty_mult": 1.5, "cluster_base": 20.0, "sam_cluster_mult": 2.0, "capital_reserve": 1000.0},
            "flags": DEFAULT_FLAGS
        },
        "aggressive": {
            "weights": {"t_int_mult": 2.5, "point_defense_bonus": 50.0, "fuel_penalty": 0.0, "sam_range_penalty": 20.0, "bomber_priority": 100.0, "economy_force": 10.0, "speed_deficit_mult": 0.1, "swarm_penalty_mult": 0.5, "cluster_base": 50.0, "sam_cluster_mult": 1.0, "capital_reserve": 10.0},
            "flags": {**DEFAULT_FLAGS, "enable_fuel_penalty": False, "enable_economy_force": False, "enable_swarm_doctrine": False, "enable_capital_reserve": False, "enable_base_lock": False}
        },
        "fortress": {
            "weights": {"t_int_mult": 1.0, "point_defense_bonus": 250.0, "fuel_penalty": 100.0, "sam_range_penalty": 100.0, "bomber_priority": 50.0, "economy_force": 200.0, "speed_deficit_mult": 0.02, "swarm_penalty_mult": 3.0, "cluster_base": 10.0, "sam_cluster_mult": 4.0, "capital_reserve": 2500.0},
            "flags": DEFAULT_FLAGS
        },
        "economy": {
            "weights": {"t_int_mult": 1.2, "point_defense_bonus": 50.0, "fuel_penalty": 150.0, "sam_range_penalty": 50.0, "bomber_priority": 20.0, "economy_force": 500.0, "speed_deficit_mult": 0.03, "swarm_penalty_mult": 1.0, "cluster_base": 10.0, "sam_cluster_mult": 1.5, "capital_reserve": 500.0},
            "flags": {**DEFAULT_FLAGS, "enable_point_defense": False}
        },
        "ambush": {
            "weights": {"t_int_mult": 3.0, "point_defense_bonus": 0.0, "fuel_penalty": 50.0, "sam_range_penalty": 0.0, "bomber_priority": 150.0, "economy_force": 20.0, "speed_deficit_mult": 0.2, "swarm_penalty_mult": 0.1, "cluster_base": 100.0, "sam_cluster_mult": 0.5, "capital_reserve": 100.0},
            "flags": {**DEFAULT_FLAGS, "enable_point_defense": False, "enable_sam_range_limit": False}
        },
        "saturation": {
            "weights": {"t_int_mult": 2.0, "point_defense_bonus": 150.0, "fuel_penalty": 20.0, "sam_range_penalty": 30.0, "bomber_priority": 50.0, "economy_force": 0.0, "speed_deficit_mult": 0.05, "swarm_penalty_mult": 0.1, "cluster_base": 80.0, "sam_cluster_mult": 0.5, "capital_reserve": 500.0},
            "flags": {**DEFAULT_FLAGS, "enable_economy_force": False, "enable_swarm_doctrine": False}
        },
        "scout": {
            "weights": {"t_int_mult": 4.0, "point_defense_bonus": 0.0, "fuel_penalty": 0.0, "sam_range_penalty": 0.0, "bomber_priority": 200.0, "economy_force": 10.0, "speed_deficit_mult": 0.3, "swarm_penalty_mult": 1.0, "cluster_base": 20.0, "sam_cluster_mult": 1.0, "capital_reserve": 0.0},
            "flags": {**DEFAULT_FLAGS, "enable_point_defense": False, "enable_fuel_penalty": False, "enable_capital_reserve": False}
        }
    }

    @staticmethod
    def get_blended_profile(primary, secondary=None, blend=0.7):
        p_data = DoctrineManager.PROFILES.get(primary, DoctrineManager.PROFILES["balanced"])
        if not secondary or secondary == "none": return p_data["weights"], p_data["flags"]
        s_data = DoctrineManager.PROFILES.get(secondary, DoctrineManager.PROFILES["balanced"])
        b_weights = {k: (p_data["weights"][k] * blend) + (s_data["weights"][k] * (1-blend)) for k in p_data["weights"]}
        b_flags = {k: p_data["flags"][k] or s_data["flags"][k] for k in p_data["flags"]}
        return b_weights, b_flags

class TacticalEngine:
    @staticmethod
    def get_optimal_assignments(state, threats, is_simulation=False, log_queue=None, weather="clear", weights=None, flags=None):
        if not threats: return []
        if not weights: weights, flags = DoctrineManager.get_blended_profile("balanced")
        if not flags: flags = DoctrineManager.DEFAULT_FLAGS
        
        cost_matrix = []
        possible_pairs = []
        for b in state.bases:
            for effector, count in b.inventory.items():
                if count > 0:
                    for _ in range(count):
                        row = []
                        for t in threats:
                            dist = math.hypot(b.x - t.x, b.y - t.y)
                            closing_speed = t.speed_kmh
                            if t.heading == b.name: closing_speed += EFFECTORS[effector].speed_kmh
                            t_int = dist / closing_speed if closing_speed > 0 else 999
                            utility = 100.0
                            
                            if flags.get("enable_point_defense", True):
                                if (dist < 50 and not is_simulation) or (is_simulation and dist < 100): utility += weights["point_defense_bonus"]
                            if flags.get("enable_fuel_penalty", True) and dist > 800: utility -= weights["fuel_penalty"]
                            if flags.get("enable_sam_range_limit", True) and effector == "SAM" and dist > 400: utility -= weights["sam_range_penalty"]
                            if flags.get("enable_bomber_priority", True) and t.estimated_type == "bomber": utility += weights["bomber_priority"]
                            if flags.get("enable_economy_force", True) and effector != "Drone" and t.threat_value < 30: utility -= weights["economy_force"]
                            if flags.get("enable_swarm_doctrine", True) and len(threats) > 10: utility -= (len(threats) * weights["swarm_penalty_mult"])
                            if flags.get("enable_capital_reserve", True) and "Capital" in b.name and dist > 150: utility -= weights["capital_reserve"]
                            if flags.get("enable_base_lock", True) and t.heading != b.name and dist > 500: utility -= 500
                            
                            row.append(-utility)
                        cost_matrix.append(row)
                        possible_pairs.append({"base": b.name, "effector": effector})

        if not cost_matrix: return []
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        assignments = []
        for r, c in zip(row_ind, col_ind):
            if cost_matrix[r][c] < 0:
                assignments.append({**possible_pairs[r], "threat_id": threats[c].id})
        return assignments

class StrategicMCTS:
    @staticmethod
    def _single_rollout(state, current_assignments, initial_cap_sams, is_trace=False, log_queue=None, weather="clear", weights=None, flags=None):
        sim_state = copy.deepcopy(state)
        assigned_ids = set(a["threat_id"] for a in current_assignments)
        for a in current_assignments:
            for b in sim_state.bases:
                if b.name == a["base"]: b.inventory[a["effector"]] -= 1
        
        rollout_score = 100.0
        ghost = Threat("GHOST", 650, 500, 1200, "Capital X", "bomber", 90)
        ghosts = [ghost]
        
        plan = TacticalEngine.get_optimal_assignments(sim_state, ghosts, is_simulation=True, weights=weights, flags=flags)
        if plan: rollout_score += 50
        else: rollout_score -= 500
        return rollout_score, {}

    @staticmethod
    def run_mcts_rollout(state, assignments, iterations=100, max_time_sec=2.0, log_queue=None, weather="clear", weights=None, flags=None, use_rl=True):
        initial_cap_sams = next((b.inventory.get("sam", 0) for b in state.bases if "Capital" in b.name), 0)
        rl_val = None
        if use_rl and RL_MODEL:
            try:
                feat = extract_rl_features(state, [], weather, "balanced", 1.0, for_value=True)
                with torch.no_grad(): rl_val = float(RL_MODEL(torch.tensor(feat, dtype=torch.float32).unsqueeze(0)).item())
                if log_queue: log_queue.put(f"[MCTS TRACE] Neural Prediction: {rl_val:.2f}")
            except Exception as e:
                if log_queue: log_queue.put(f"[MCTS ERROR] Neural Heuristic failed: {e}")

        total = 0
        for _ in range(max(1, iterations)):
            s, _ = StrategicMCTS._single_rollout(state, assignments, initial_cap_sams, weights=weights, flags=flags)
            total += s
        avg = total / max(1, iterations)
        final = (avg * 0.7) + (rl_val * 0.3) if rl_val is not None else avg
        return final, {}, rl_val

def evaluate_threats_advanced(state, threats, mcts_iterations=500, log_queue=None, weather="clear", max_time_sec=2.0, doctrine_primary="balanced", doctrine_secondary=None, doctrine_blend=0.7, use_rl=True):
    weights, flags = DoctrineManager.get_blended_profile(doctrine_primary, doctrine_secondary, doctrine_blend)
    
    if use_rl:
        doc_feat = extract_rl_features(state, threats, weather, doctrine_primary, doctrine_blend, for_value=False)
        if DOCTRINE_MODEL and threats:
            with torch.no_grad():
                mults = DOCTRINE_MODEL(torch.tensor([doc_feat], dtype=torch.float32))[0].numpy()
                for i, k in enumerate(weights.keys()): weights[k] *= max(0.1, float(mults[i]))
    
    # Triage filtering
    triage_threshold = 0
    filtered_threats = [t for t in threats if t.threat_value >= triage_threshold]
    ignored_count = len(threats) - len(filtered_threats)
    
    plan = TacticalEngine.get_optimal_assignments(state, filtered_threats, weights=weights, flags=flags)
    score, depletions, rl_val = StrategicMCTS.run_mcts_rollout(state, plan, iterations=mcts_iterations, weights=weights, flags=flags, log_queue=log_queue, use_rl=use_rl)
    
    return {
        "tactical_assignments": plan,
        "strategic_consequence_score": score,
        "rl_prediction": rl_val,
        "triage_ignored_threats": ignored_count,
        "active_doctrine": {
            "label": doctrine_primary,
            "primary": doctrine_primary,
            "secondary": doctrine_secondary,
            "blend_ratio": f"{int(doctrine_blend*100)}/{int((1-doctrine_blend)*100)}",
            "active_flags": flags,
            "blended_weights": weights
        }
    }