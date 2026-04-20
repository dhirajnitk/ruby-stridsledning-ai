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

# --- RL VALUE & POLICY NETWORK INTEGRATION ---
try:
    import torch
    import torch.nn as nn
    
    import torch.nn.functional as F

    class ResBlock(nn.Module):
        def __init__(self, size):
            super().__init__()
            self.fc1 = nn.Linear(size, size)
            self.fc2 = nn.Linear(size, size)
        def forward(self, x):
            residual = x
            x = F.relu(self.fc1(x))
            x = self.fc2(x)
            return F.relu(x + residual)

    class ValueNetwork(nn.Module):
        def __init__(self, input_dim=15):
            super(ValueNetwork, self).__init__()
            self.input_layer = nn.Linear(input_dim, 128)
            self.res1 = ResBlock(128)
            self.res2 = ResBlock(128)
            self.value_head = nn.Linear(128, 1)
        def forward(self, x):
            x = F.relu(self.input_layer(x))
            x = self.res1(x)
            x = self.res2(x)
            return self.value_head(x)

    class DoctrineNetwork(nn.Module):
        def __init__(self, input_dim=10):
            super(DoctrineNetwork, self).__init__()
            self.input_layer = nn.Linear(input_dim, 128)
            self.res1 = ResBlock(128)
            self.res2 = ResBlock(128)
            self.output_layer = nn.Linear(128, 11)
        def forward(self, x):
            x = F.relu(self.input_layer(x))
            x = self.res1(x)
            x = self.res2(x)
            return F.softplus(self.output_layer(x))

    RL_MODEL = None
    RL_PARAMS = None
    DOCTRINE_MODEL = None
    PPO_MODEL = None

    # 1. Load Value Network
    RL_MODEL_PATH = "models/value_network.pth"
    RL_PARAMS_PATH = "models/value_network_params.json"
    if os.path.exists(RL_MODEL_PATH) and os.path.exists(RL_PARAMS_PATH):
        with open(RL_PARAMS_PATH, "r") as f: RL_PARAMS = json.load(f)
        saved_state = torch.load(RL_MODEL_PATH, map_location=torch.device('cpu'))
        input_dim = saved_state['input_layer.weight'].shape[1]
        RL_MODEL = ValueNetwork(input_dim)
        RL_MODEL.load_state_dict(saved_state)
        RL_MODEL.eval()
        print(f"[SYSTEM] Successfully hot-loaded RL Value Network (input_dim={input_dim}) from {RL_MODEL_PATH}")

    # 2. Load Doctrine Network
    DOC_MODEL_PATH = "models/doctrine_network.pth"
    DOC_PARAMS_PATH = "models/policy_network_params.json"
    if os.path.exists(DOC_MODEL_PATH) and os.path.exists(DOC_PARAMS_PATH):
        with open(DOC_PARAMS_PATH, "r") as f: DOC_PARAMS = json.load(f)
        saved_state = torch.load(DOC_MODEL_PATH, map_location=torch.device('cpu'))
        input_dim = saved_state['input_layer.weight'].shape[1]
        DOCTRINE_MODEL = DoctrineNetwork(input_dim)
        DOCTRINE_MODEL.load_state_dict(saved_state)
        DOCTRINE_MODEL.eval()
        print(f"[SYSTEM] Successfully hot-loaded RL Doctrine Manager (input_dim={input_dim}) from {DOC_MODEL_PATH}")

    # 3. Load PPO Direct Action Agent (Prioritize 98k Veteran)
    from ppo_agent import ActorCriticDirect, get_ppo_assignments
    PPO_MODEL = ActorCriticDirect()
    PPO_VETERAN_PATH = "models/ppo_checkpoint_step_98000.pth"
    PPO_BASELINE_PATH = "models/ppo_direct_network.pth"
    
    if os.path.exists(PPO_VETERAN_PATH):
        PPO_MODEL.load_state_dict(torch.load(PPO_VETERAN_PATH, map_location='cpu'))
        PPO_MODEL.eval()
        print(f"[SYSTEM] Successfully hot-loaded VETERAN PPO Agent (98k iterations) from {PPO_VETERAN_PATH}")
    elif os.path.exists(PPO_BASELINE_PATH):
        PPO_MODEL.load_state_dict(torch.load(PPO_BASELINE_PATH, map_location='cpu'))
        PPO_MODEL.eval()
        print(f"[SYSTEM] Successfully hot-loaded PPO Baseline Agent from {PPO_BASELINE_PATH}")
    
except ImportError:
    print("[SYSTEM] PyTorch not installed. Falling back to classical MCTS engine.")
except Exception as e:
    print(f"[SYSTEM] Neural model loading failed: {e}")

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
    
    # 1. Spatial Awareness: Sector Distribution (West, Center, East)
    west_threats = sum(1 for t in threats if t.x < 500)
    east_threats = sum(1 for t in threats if t.x > 1000)
    
    total_sams = sum(b.inventory.get("sam", 0) for b in state.bases)
    total_val = sum(t.threat_value for t in threats)
    
    # 2. Logistics Stress Ratios
    ammo_stress = total_sams / (num_threats + 1)
    
    numeric_features = [
        num_threats, avg_dist, min_dist, total_val, 
        fighters, sams, drones, cap_sams, weather_bin, blend,
        west_threats, east_threats, ammo_stress,
        (avg_dist / 1000.0), (total_val / 1000.0)
    ]
    
    # 3. Final Vector Construction
    if for_value and RL_MODEL and RL_PARAMS:
        mean = np.array(RL_PARAMS["scaler_mean"])
        scale = np.array(RL_PARAMS["scaler_scale"])
        # Truncate features to match the scaler dimensions (model was trained on first N features)
        truncated = np.array(numeric_features[:len(mean)])
        return (truncated - mean) / scale
            
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
            "flags": dict(DEFAULT_FLAGS)
        },
        "aggressive": {
            "weights": {"t_int_mult": 2.5, "point_defense_bonus": 50.0, "fuel_penalty": 0.0, "sam_range_penalty": 20.0, "bomber_priority": 100.0, "economy_force": 10.0, "speed_deficit_mult": 0.1, "swarm_penalty_mult": 0.5, "cluster_base": 50.0, "sam_cluster_mult": 1.0, "capital_reserve": 10.0},
            "flags": {**DEFAULT_FLAGS, "enable_fuel_penalty": False, "enable_economy_force": False, "enable_swarm_doctrine": False, "enable_capital_reserve": False, "enable_base_lock": False}
        },
        "fortress": {
            "weights": {"t_int_mult": 1.0, "point_defense_bonus": 250.0, "fuel_penalty": 100.0, "sam_range_penalty": 100.0, "bomber_priority": 50.0, "economy_force": 200.0, "speed_deficit_mult": 0.02, "swarm_penalty_mult": 3.0, "cluster_base": 10.0, "sam_cluster_mult": 4.0, "capital_reserve": 2500.0},
            "flags": dict(DEFAULT_FLAGS)
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
        # Always return fresh copies so callers can mutate weights (e.g. apply
        # RL-network multipliers) without corrupting the PROFILES registry.
        if not secondary or secondary == "none":
            return dict(p_data["weights"]), dict(p_data["flags"])
        s_data = DoctrineManager.PROFILES.get(secondary, DoctrineManager.PROFILES["balanced"])
        b_weights = {k: (p_data["weights"][k] * blend) + (s_data["weights"][k] * (1-blend)) for k in p_data["weights"]}
        # Threshold-based flag blend: primary wins when it's the dominant profile,
        # otherwise secondary. Respects explicit enable/disable intent on both sides.
        b_flags = {k: (p_data["flags"][k] if blend >= 0.5 else s_data["flags"][k]) for k in p_data["flags"]}
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
            for effector_raw, count in b.inventory.items():
                # Normalize to lowercase so EFFECTORS lookups and string
                # comparisons work regardless of how the caller cased the keys.
                effector = effector_raw.lower() if isinstance(effector_raw, str) else effector_raw
                if effector not in EFFECTORS:
                    continue
                if count > 0:
                    for _ in range(count):
                        row = []
                        for t in threats:
                            dist = math.hypot(b.x - t.x, b.y - t.y)
                            closing_speed = t.speed_kmh
                            if t.heading == b.name: closing_speed += EFFECTORS[effector].speed_kmh
                            t_int = dist / closing_speed if closing_speed > 0 else 999
                            
                            # --- CALCULATE THREAT URGENCY ---
                            t_arrival_mins = (dist / t.speed_kmh) * 60.0 if t.speed_kmh > 0 else 999
                            
                            # Survival Mandate: If it's heading for a base, it's a priority.
                            is_point_blank = (t_arrival_mins < 5.0) 
                            is_approaching = (t.heading == b.name)
                            
                            utility = 150.0 # Increased baseline
                            
                            if flags.get("enable_point_defense", True):
                                if (dist < 50 and not is_simulation) or (is_simulation and dist < 100): utility += weights["point_defense_bonus"]
                            if flags.get("enable_fuel_penalty", True) and dist > 800: utility -= weights["fuel_penalty"]
                            if flags.get("enable_sam_range_limit", True) and effector == "sam" and dist > 400: utility -= weights["sam_range_penalty"]
                            if flags.get("enable_bomber_priority", True) and t.estimated_type == "bomber": utility += weights["bomber_priority"]
                            if flags.get("enable_economy_force", True) and effector != "drone" and t.threat_value < 30: utility -= weights["economy_force"]
                            # Scale swarm penalty by effector cost so expensive assets
                            # (SAMs) are preserved during saturation events and cheaper
                            # assets (drones) are preferred for screening.
                            if flags.get("enable_swarm_doctrine", True) and len(threats) > 10 and not is_point_blank:
                                eff_cost = EFFECTORS[effector].cost_weight
                                utility -= (len(threats) * weights["swarm_penalty_mult"] * eff_cost * 0.02)
                            
                            # DOCTRINE BALANCE: We only apply heavy penalties if the threat isn't a direct danger.
                            if not is_point_blank and not is_approaching:
                                if flags.get("enable_capital_reserve", True) and "Capital" in b.name and dist > 150: 
                                    utility -= weights["capital_reserve"]
                                if flags.get("enable_base_lock", True) and t.heading != b.name and dist > 500: 
                                    utility -= 500
                            else:
                                # Self-Defense Boost: If a base is defending itself, range penalties are halved
                                if is_approaching: utility += 200.0
                            
                            # Ensure we never choose 'nothing' over a viable intercept
                            utility = max(10.0, utility)
                            
                            row.append(-utility)
                        cost_matrix.append(row)
                        possible_pairs.append({"base": b.name, "effector": effector})

        if not cost_matrix: return []
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        assignments = []
        for r, c in zip(row_ind, col_ind):
            if cost_matrix[r][c] < 0:
                assignments.append({**possible_pairs[r], "base_name": possible_pairs[r]["base"], "threat_id": threats[c].id})
        return assignments

class StrategicMCTS:
    @staticmethod
    def _single_rollout(state, current_assignments, threats, initial_cap_sams, is_trace=False, log_queue=None, weather="clear", weights=None, flags=None):
        """Stochastic rollout of the current plan against the active threat set.

        Scores each planned engagement by the effector's Pk against the threat's
        estimated type, penalizes threats the plan chose to leak, and rewards
        preservation of capital SAM reserves. A residual ghost-threat stress test
        checks whether the plan still leaves enough capacity to react to a surprise."""
        sim_state = copy.deepcopy(state)
        threat_by_id = {t.id: t for t in threats}
        assigned_ids = set(a["threat_id"] for a in current_assignments)

        # Deplete inventory for each assignment fired (tolerate mixed-case keys).
        for a in current_assignments:
            for b in sim_state.bases:
                if b.name == a["base"]:
                    key = a["effector"]
                    if key in b.inventory:
                        b.inventory[key] = max(0, b.inventory[key] - 1)
                    elif key.lower() in b.inventory:
                        b.inventory[key.lower()] = max(0, b.inventory[key.lower()] - 1)

        rollout_score = 100.0
        weather_mod = {"clear": 1.0, "storm": 0.8, "fog": 0.7}.get(weather, 1.0)

        # 1. Score the planned engagements stochastically.
        for a in current_assignments:
            t = threat_by_id.get(a["threat_id"])
            if t is None:
                continue
            eff_key = a["effector"].lower() if isinstance(a["effector"], str) else a["effector"]
            eff = EFFECTORS.get(eff_key)
            if eff is None:
                continue
            pk = eff.pk_matrix.get(t.estimated_type, 0.5) * weather_mod
            if random.random() < pk:
                rollout_score += t.threat_value * 0.5
            else:
                rollout_score -= t.threat_value * 0.25
            rollout_score -= eff.cost_weight * 0.05  # ammunition cost
            rollout_score -= eff.cost_weight * 0.05

        # 2. Penalty for threats left un-engaged (they leak through).
        for t in threats:
            if t.id not in assigned_ids:
                rollout_score -= t.threat_value * 0.7
                if t.estimated_type in ("bomber", "fast-mover", "hypersonic"):
                    rollout_score -= 15.0

        # 3. Reward for keeping capital SAM reserves intact.
        cap = next((b for b in sim_state.bases if "Capital" in b.name), None)
        if cap and initial_cap_sams > 0:
            cap_sams_remaining = cap.inventory.get("sam", 0) + cap.inventory.get("SAM", 0)
            if cap_sams_remaining >= initial_cap_sams:
                rollout_score += 250.0
            reserve_ratio = cap_sams_remaining / initial_cap_sams
            if flags is None or flags.get("enable_capital_reserve", True):
                reserve_bonus = (weights.get("capital_reserve", 1000.0) * 0.01) if weights else 10.0
                rollout_score += reserve_bonus * reserve_ratio

        # 4. Surprise-threat stress test.
        ghost = Threat("GHOST", 650, 500, 1200, "Capital X", "bomber", 90)
        plan = TacticalEngine.get_optimal_assignments(sim_state, [ghost], is_simulation=True, weights=weights, flags=flags)
        if plan:
            rollout_score += 20.0
        else:
            rollout_score -= 80.0

        return rollout_score, {"leaked": len(threats) - len(assigned_ids)}

    @staticmethod
    def run_mcts_rollout(state, assignments, threats, iterations=100, max_time_sec=2.0, log_queue=None, weather="clear", weights=None, flags=None, use_rl=True, doctrine_primary="balanced", doctrine_blend=0.7):
        initial_cap_sams = next((b.inventory.get("sam", 0) for b in state.bases if "Capital" in b.name), 0)
        rl_val = None
        global LAST_HEURISTIC_LOG_TIME
        if 'LAST_HEURISTIC_LOG_TIME' not in globals(): LAST_HEURISTIC_LOG_TIME = 0
        
        if use_rl and RL_MODEL:
            try:
                feat = extract_rl_features(state, threats, weather, doctrine_primary, doctrine_blend, for_value=True)
                with torch.no_grad():
                    rl_val = float(RL_MODEL(torch.tensor(feat, dtype=torch.float32).unsqueeze(0)).item())
                if log_queue:
                    conf = min(100, max(0, rl_val / 8))
                    log_queue.put(f"[STRAT] Running Neural-MCTS... RL Confidence: {conf:.1f}%")
            except Exception as e:
                if log_queue: log_queue.put(f"[INTEL] Neural Heuristic analyzing sector...")
        elif log_queue:
            now = time.time()
            if now - LAST_HEURISTIC_LOG_TIME > 1.0:
                log_queue.put(f"[STRAT] Triage Active: Tracking {len(threats)} vectors. Doctrine: {doctrine_primary.upper()}.")
                LAST_HEURISTIC_LOG_TIME = now
        total = 0
        for _ in range(max(1, iterations)):
            s, _ = StrategicMCTS._single_rollout(state, assignments, threats, initial_cap_sams, weather=weather, weights=weights, flags=flags)
            total += s
        
        avg_rollout = total / max(1, iterations)
        
        # BLENDED EVALUATION: Combine stochastic rollouts with Neural Strategic Intuition
        if rl_val is not None:
            # The RL model provides the 'Strategic Anchor' while rollouts provide the 'Tactical Variance'
            final = (avg_rollout * 0.4) + (rl_val * 0.6)
        else:
            final = avg_rollout
            
        return final, {}, rl_val

def evaluate_threats_advanced(state, threats, mcts_iterations=50, log_queue=None, weather="clear", max_time_sec=2.0, doctrine_primary="balanced", doctrine_secondary=None, doctrine_blend=0.7, use_rl=True, use_ppo=False):
    weights, flags = DoctrineManager.get_blended_profile(doctrine_primary, doctrine_secondary, doctrine_blend)
    
    if use_rl:
        doc_feat = extract_rl_features(state, threats, weather, doctrine_primary, doctrine_blend, for_value=False)
        if DOCTRINE_MODEL and threats:
            with torch.no_grad():
                mults = DOCTRINE_MODEL(torch.tensor([doc_feat], dtype=torch.float32))[0].numpy()
                for i, k in enumerate(weights.keys()): weights[k] *= max(0.1, float(mults[i]))
    
    # --- STRATEGIC TRIAGE FILTER ---
    total_ammo = sum(sum(b.inventory.values()) for b in state.bases)
    if len(threats) > total_ammo:
        filtered_threats = sorted(threats, key=lambda t: t.threat_value + (200 if t.heading == "Capital X" else 0), reverse=True)
        filtered_threats = filtered_threats[:total_ammo + 5]
    else:
        filtered_threats = threats

    ignored_count = len(threats) - len(filtered_threats)

    if log_queue:
        log_queue.put(f"[STRAT] Triage Active: Tracking {len(threats)} vectors. Doctrine: {doctrine_primary.upper()}.")
        if ignored_count > 0:
            log_queue.put(f"[STRAT] TRIAGE: {ignored_count} low-priority threats deprioritized due to ammo constraints.")

    if use_ppo and PPO_MODEL:
        if log_queue: log_queue.put("[INTEL] Using Advanced PPO Agent for Direct Action Matrix.")
        plan = get_ppo_assignments(PPO_MODEL, state, filtered_threats)
    else:
        plan = TacticalEngine.get_optimal_assignments(state, filtered_threats, weights=weights, flags=flags)
    
    # --- LOG EACH ASSIGNMENT ---
    if log_queue and plan:
        log_queue.put(f"[COMMAND] Optimal plan: {len(plan)} intercepts assigned.")
        for a in plan:
            log_queue.put(f"[COMMAND] ASSIGN {a['base']} -> {a['threat_id']} via {a['effector'].upper()} (Pk: {a.get('pk', 'N/A')})")

    score, depletions, rl_val = StrategicMCTS.run_mcts_rollout(
        state, plan, filtered_threats, 
        iterations=mcts_iterations, 
        weights=weights, 
        flags=flags, 
        log_queue=log_queue, 
        use_rl=use_rl,
        doctrine_primary=doctrine_primary,
        doctrine_blend=doctrine_blend
    )

    # --- PENALIZE ABANDONED THREATS ---
    # Threats that were triaged/ignored are guaranteed leakers that will hit their targets.
    # We must severely penalize the final score so the AI accurately reports the disaster.
    if ignored_count > 0:
        score -= (ignored_count * 200.0)

    # --- LOG MCTS RESULT ---
    if log_queue:
        mode = "Neural-MCTS" if rl_val is not None else "Heuristic-MCTS"
        log_queue.put(f"[NEURAL] {mode} Score: {score:.1f} | Threats: {len(filtered_threats)} | Intercepts: {len(plan)}")
    
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