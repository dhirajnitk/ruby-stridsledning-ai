import math
import copy
import random
import time
import concurrent.futures
import os
import numpy as np
from scipy.optimize import linear_sum_assignment
from models import GameState, Threat, EFFECTORS

# --- RL VALUE NETWORK INTEGRATION ---
try:
    import torch
    import torch.nn as nn
    
    class ValueNetwork(nn.Module):
        def __init__(self):
            super(ValueNetwork, self).__init__()
            self.network = nn.Sequential(
                nn.Linear(9, 64),
                nn.ReLU(),
                nn.Linear(64, 32),
                nn.ReLU(),
                nn.Linear(32, 16),
                nn.ReLU(),
                nn.Linear(16, 1)
            )
        def forward(self, x):
            return self.network(x)

    RL_MODEL = None
    MODEL_PATH = "src/value_network.pth"
    if os.path.exists(MODEL_PATH):
        RL_MODEL = ValueNetwork()
        RL_MODEL.load_state_dict(torch.load(MODEL_PATH))
        RL_MODEL.eval()
        print(f"[SYSTEM] Successfully hot-loaded RL Value Network from {MODEL_PATH}")
        
    class DoctrineNetwork(nn.Module):
        def __init__(self):
            super(DoctrineNetwork, self).__init__()
            self.network = nn.Sequential(
                nn.Linear(9, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU(),
                nn.Linear(64, 14), nn.Softplus()
            )
        def forward(self, x): return self.network(x)
        
    DOCTRINE_MODEL = None
    DOC_MODEL_PATH = "src/doctrine_network.pth"
    if os.path.exists(DOC_MODEL_PATH):
        DOCTRINE_MODEL = DoctrineNetwork()
        DOCTRINE_MODEL.load_state_dict(torch.load(DOC_MODEL_PATH))
        DOCTRINE_MODEL.eval()
        print(f"[SYSTEM] Successfully hot-loaded RL Doctrine Manager from {DOC_MODEL_PATH}")
except ImportError:
    RL_MODEL = None
    DOCTRINE_MODEL = None
    print("[SYSTEM] PyTorch not installed. Falling back to classical MCTS physics engine.")

def extract_rl_features(state: GameState, threats: list[Threat]):
    """Converts the battlefield state into a flat [9] tensor for the neural network."""
    features = {}
    for b in state.bases:
        if "Capital" in b.name: features["cap_sam"] = b.inventory.get("SAM", 0)
        elif "Northern" in b.name:
            features["base_a_sam"] = b.inventory.get("SAM", 0)
            features["base_a_fighter"] = b.inventory.get("Fighter", 0)
        elif "Highridge" in b.name:
            features["base_b_sam"] = b.inventory.get("SAM", 0)
            features["base_b_fighter"] = b.inventory.get("Fighter", 0)
            
    features["num_decoys"] = sum(1 for t in threats if t.estimated_type == "decoy")
    features["num_bombers"] = sum(1 for t in threats if t.estimated_type == "bomber")
    features["num_fast_movers"] = sum(1 for t in threats if t.estimated_type == "fast-mover")
    
    min_dist = float('inf')
    for t in threats:
        dist = math.hypot(418.3 - t.x, 95.0 - t.y)
        if dist < min_dist: min_dist = dist
    features["closest_threat_dist"] = round(min_dist, 2) if min_dist != float('inf') else 0.0
    
    return [
        features.get("cap_sam", 0), features.get("base_a_sam", 0), features.get("base_a_fighter", 0),
        features.get("base_b_sam", 0), features.get("base_b_fighter", 0),
        features.get("num_decoys", 0), features.get("num_bombers", 0), features.get("num_fast_movers", 0),
        features.get("closest_threat_dist", 0.0)
    ]

DEFAULT_WEIGHTS = {
    "t_int_mult": 1.5,
    "point_defense_bonus": 100.0,
    "fuel_penalty": 80.0,
    "sam_range_penalty": 60.0,
    "bomber_priority": 50.0,
    "economy_force": 50.0,
    "speed_deficit_mult": 0.05,
    "swarm_penalty_mult": 1.5,
    "cluster_base": 20.0,
    "sam_cluster_mult": 2.0,
    "capital_reserve": 1000.0,
    "self_defense": 80.0,
    "cross_fire": 2000.0,
    "tie_breaker": 0.1
}

class TacticalEngine:
    @staticmethod
    def get_optimal_assignments(state: GameState, threats: list[Threat], is_simulation: bool = False, log_queue=None, weather: str = "clear", weights: dict = None):
        """LAYER 1: The Hungarian Algorithm for Immediate Optimal Matching."""
        if weights is None: weights = DEFAULT_WEIGHTS
        
        # Pre-calculate Cluster Bonuses: Find threats flying within 50km of each other
        cluster_bonuses = {}
        for t1 in threats:
            nearby_count = sum(1 for t2 in threats if t1.id != t2.id and math.hypot(t1.x - t2.x, t1.y - t2.y) <= 50.0)
            cluster_bonuses[t1.id] = nearby_count * weights["cluster_base"]
            
        available_effectors = []
        # Flatten all available weapons across all bases into a single list
        for base in state.bases:
            for eff_name, count in base.inventory.items():
                for _ in range(count):
                    available_effectors.append({"base": base, "eff_name": eff_name})

        if not threats or not available_effectors:
            return []

        # Cost matrix: Rows = Effectors, Cols = Threats
        cost_matrix = np.zeros((len(available_effectors), len(threats)))

        for i, eff_data in enumerate(available_effectors):
            for j, threat in enumerate(threats):
                base = eff_data["base"]
                eff_name = eff_data["eff_name"]
                effector = EFFECTORS[eff_name]

                pk = effector.pk_matrix.get(threat.estimated_type, 0.5)
                dist = math.hypot(base.x - threat.x, base.y - threat.y)
                
                # T_int Kinematics: Calculate times in hours
                base_keyword = base.name.split()[0]
                if base_keyword in threat.heading or ("Capital" in threat.heading and "Capital" in base.name):
                    closing_speed = effector.speed_kmh + threat.speed_kmh
                    t_int_hours = dist / closing_speed if closing_speed > 0 else float('inf')
                else:
                    t_int_hours = dist / effector.speed_kmh if effector.speed_kmh > 0 else float('inf')
                t_int_mins = t_int_hours * 60.0
                
                # Check if the threat will hit the Capital (x:418.3, y:95.0) before we can intercept
                dist_to_capital = math.hypot(418.3 - threat.x, 95.0 - threat.y)
                time_to_capital_hours = dist_to_capital / threat.speed_kmh if threat.speed_kmh > 0 else float('inf')
                time_to_capital_mins = time_to_capital_hours * 60.0
                
                # Fast-forward MCTS logic: Simulate the engagement when the Ghost reaches the defense perimeter
                if is_simulation and "GHOST" in threat.id:
                    dist = min(dist, 50.0)
                    dist_to_capital = min(dist_to_capital, 50.0)

                if t_int_hours > time_to_capital_hours:
                    utility = -1e9 # Use massive penalty instead of -inf to prevent SciPy 'infeasible matrix' crash
                else:
                    # --- NEW: Dynamic P_k Degradation (Range Scaling) ---
                    dynamic_pk = pk
                    if eff_name == "SAM" and dist > 50.0:
                        dynamic_pk -= min(0.4, ((dist - 50.0) / 100.0) * 0.4) # Lose up to 40% P_k at max range
                    elif eff_name == "Fighter" and dist > 400.0:
                        dynamic_pk -= min(0.3, ((dist - 400.0) / 400.0) * 0.3) # Lose up to 30% P_k at extended range
                        
                    # --- NEW: Weather Modifier ---
                    if weather.lower() == "storm" and eff_name == "SAM":
                        dynamic_pk -= 0.30 # SAMs suffer a flat 30% hit chance penalty in storms
                        
                    # --- NEW: Time-to-Impact Criticality Escalation ---
                    urgency_multiplier = 1.0
                    if time_to_capital_mins < 15.0:
                        urgency_multiplier = 1.0 + ((15.0 - time_to_capital_mins) / 15.0) # Scales up to 2.0x value
                    effective_threat_value = threat.threat_value * urgency_multiplier

                    # Base Utility Function with advanced physics and urgency
                    utility = (dynamic_pk * effective_threat_value) - effector.cost_weight - (t_int_mins * weights["t_int_mult"])
                    
                    # Point Defense Doctrine: Heavily prioritize SAMs for close-range threats (< 150km)
                    if dist <= 150.0 and eff_name == "SAM":
                        utility += weights["point_defense_bonus"]
                        
                    # Fuel Penalty: Fighters lose utility if pushed beyond 800km range
                    if dist > 800.0 and eff_name == "Fighter":
                        utility -= weights["fuel_penalty"]
                        
                    # SAM Range Penalty: SAMs lose utility beyond their optimal 50km engagement range
                    if dist > 50.0 and eff_name == "SAM":
                        utility -= weights["sam_range_penalty"]
                        
                    # Target Priority Doctrine: Bombers are high-value strategic threats
                    if threat.estimated_type == "bomber":
                        utility += weights["bomber_priority"]
                        
                    # Economy of Force Doctrine: Use cheap Drones against Decoys
                    if threat.estimated_type == "decoy" and eff_name == "Drone":
                        utility += weights["economy_force"]
                        
                    # Dynamic Speed Mismatch Penalty: Penalize effectors slower than the threat
                    speed_deficit = threat.speed_kmh - effector.speed_kmh
                    if speed_deficit > 0:
                        utility -= (speed_deficit * weights["speed_deficit_mult"])
                        
                    # Swarm Doctrine: Conserve expensive effectors when facing a massive wave
                    if len(threats) >= 10 and effector.cost_weight >= 50.0:
                        utility -= (len(threats) * weights["swarm_penalty_mult"])
                        
                    # Cluster Priority Doctrine: Prioritize threats that are clumped together
                    # Leverage splash damage by heavily weighting SAMs against clusters
                    cluster_bonus = cluster_bonuses.get(threat.id, 0.0)
                    if eff_name == "SAM":
                        utility += cluster_bonus * weights["sam_cluster_mult"]
                    else:
                        utility += cluster_bonus
                        
                    # Capital Reserve Doctrine: Strictly hold Capital SAMs unless threat is within 100km
                    if "Capital" in base.name and eff_name == "SAM" and dist_to_capital > 100.0:
                        utility -= weights["capital_reserve"]
                        
                    # Self-Defense Doctrine: Bases prioritize threats heading directly towards them
                    base_keyword = base.name.split()[0] # e.g., 'Northern', 'Highridge', 'Arktholm'
                    if base_keyword in threat.heading or ("Capital" in threat.heading and "Capital" in base.name):
                        utility += weights["self_defense"]
                        
                    # Strict Base-Lock Doctrine: Prevent cross-firing onto threats targeting other specific bases
                    for other_b in state.bases:
                        if other_b.name != base.name:
                            other_keyword = other_b.name.split()[0]
                            if other_keyword in threat.heading or ("Capital" in threat.heading and "Capital" in other_b.name):
                                utility -= weights["cross_fire"]
                                break
                                
                    # Tie-Breaker Doctrine: Prefer Inland Base B over Coastal Base A for equidistant threats
                    if "Highridge" in base.name:
                        utility += weights["tie_breaker"]
                
                # Scipy linear_sum_assignment minimizes cost. We want to maximize utility,
                # so we invert the utility score.
                cost_matrix[i, j] = -utility 

        # Execute the Hungarian Algorithm
        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        assignments = []
        for r, c in zip(row_ind, col_ind):
            utility = -cost_matrix[r, c]
            base = available_effectors[r]["base"]
            eff_name = available_effectors[r]["eff_name"]
            threat = threats[c]
            effector = EFFECTORS[eff_name]
            
            dist = math.hypot(base.x - threat.x, base.y - threat.y)
            
            base_keyword = base.name.split()[0]
            if base_keyword in threat.heading or ("Capital" in threat.heading and "Capital" in base.name):
                closing_speed = effector.speed_kmh + threat.speed_kmh
                t_int_mins = (dist / closing_speed) * 60.0 if closing_speed > 0 else float('inf')
            else:
                t_int_mins = (dist / effector.speed_kmh) * 60.0 if effector.speed_kmh > 0 else float('inf')

            if is_simulation and "GHOST" in threat.id:
                dist = min(dist, 50.0)
                
            pk = effector.pk_matrix.get(threat.estimated_type, 0.5)
            
            # Recalculate dynamic_pk for accurate logging and MCTS rollout dice rolls
            dynamic_pk = pk
            if eff_name == "SAM" and dist > 50.0:
                dynamic_pk -= min(0.4, ((dist - 50.0) / 100.0) * 0.4)
            elif eff_name == "Fighter" and dist > 400.0:
                dynamic_pk -= min(0.3, ((dist - 400.0) / 400.0) * 0.3)
            
            if weather.lower() == "storm" and eff_name == "SAM":
                dynamic_pk -= 0.30
            
            if utility > 0: # TRIAGE: Only engage if the utility is mathematically profitable
                assignments.append({
                    "threat_id": threat.id,
                    "threat_type": threat.estimated_type,
                    "effector": eff_name,
                    "base": base.name,
                    "expected_utility": round(utility, 2),
                    "t_int_mins": round(t_int_mins, 1),
                    "pk": round(dynamic_pk, 2)
                })
            else:
                if not is_simulation:
                    reason = "Too slow (Hits Capital First)" if utility <= -1e8 else "Negative Utility (Unprofitable)"
                    msg = (f"[DEBUG TRIAGE REJECT] {eff_name} from {base.name} -> {threat.id} | "
                           f"P_k: {dynamic_pk:.2f} | Threat Val: {threat.threat_value} | Weapon Cost: {effector.cost_weight} | "
                           f"T_int: {t_int_mins:.1f}m | Reason: {reason} (Utility: {utility:.1f})")
            # Only push to the UI WebSocket queue, don't print to the Python console to prevent lag
                    if log_queue: log_queue.put(msg)

        return assignments

class StrategicMCTS:
    @staticmethod
    def _single_rollout(initial_state: GameState, current_assignments: list, initial_capital_sams: int, is_trace: bool, log_queue=None, weather: str = "clear", weights: dict = None):
        """Performs a single simulated future rollout."""
        def t_log(msg):
            if is_trace:
                print(msg)
                if log_queue: log_queue.put(msg)
                
        # 1. Clone state for this specific timeline
        sim_state = copy.deepcopy(initial_state)
        rollout_score = 0
        depletion_tracker = {}
        
        t_log("\n--- [MCTS TRACE] Simulating Future Timeline 1 ---")
        t_log("[MCTS TRACE] Applying current tactical plan and fast-forwarding...")
        
        # 2. Apply current tactical actions (Deduct fired weapons from inventory)
        for action in current_assignments:
            for b in sim_state.bases:
                if b.name == action["base"]:
                    b.inventory[action["effector"]] -= 1
                    break
                    
        # 3. SIMULATION (The Rollout)
        # Fast forward: A Ghost threat spawns from a random blind spot
        if sim_state.blind_spots:
            bx, by = random.choice(sim_state.blind_spots)
            
            # Randomly determine the Ghost Threat's profile
            ghost_type = random.choice(["bomber", "fast-mover"])
            if ghost_type == "bomber":
                ghost_speed = random.uniform(800.0, 1200.0)
                ghost_val = 90.0
            else:
                ghost_speed = random.uniform(2000.0, 4500.0)
                ghost_val = 100.0
                
            ghost = Threat(f"GHOST-{ghost_type.upper()}", bx, by, ghost_speed, "Capital", ghost_type, ghost_val)
            
            t_log(f"[MCTS TRACE] A Ghost {ghost_type} ({int(ghost_speed)} km/h) suddenly emerges from blind spot ({bx}, {by}).")
            
            ghosts_to_evaluate = [ghost]
            
            # 20% chance for Fast-Movers to spawn a secondary Decoy to confuse defenses
            if ghost_type == "fast-mover" and random.random() <= 0.20:
                decoy_speed = random.uniform(300.0, 600.0)
                decoy_ghost = Threat("GHOST-DECOY", bx + random.uniform(-5, 5), by + random.uniform(-5, 5), decoy_speed, "Capital", "decoy", 15.0)
                ghosts_to_evaluate.append(decoy_ghost)
                t_log(f"[MCTS TRACE] -> The fast-mover also deployed a Ghost DECOY ({int(decoy_speed)} km/h) alongside it!")
            
            # Can our *remaining* inventory handle these ghosts?
            ghost_defenses = TacticalEngine.get_optimal_assignments(sim_state, ghosts_to_evaluate, is_simulation=True, weather=weather, weights=weights)
            
            # Check if the primary high-value threat got assigned a defender
            primary_assigned = any(d["threat_id"] == ghost.id for d in ghost_defenses)
            
            if primary_assigned:
                destroyed_ghost_ids = set()
                for defense in ghost_defenses:
                    hit_chance = defense["pk"]
                    t_log(f"[MCTS TRACE] Found remaining defense for {defense['threat_id']}: {defense['effector']} from {defense['base']} (P_k: {hit_chance}). Rolling dice...")
                    
                    if random.random() > hit_chance:
                        if defense["threat_type"] != "decoy":
                            t_log(f"[MCTS TRACE] -> MISS! {defense['effector']} failed to kill {defense['threat_id']}.")
                        else:
                            t_log(f"[MCTS TRACE] -> MISS! {defense['effector']} failed to kill {defense['threat_id']}, but it was only a decoy.")
                    else:
                        t_log(f"[MCTS TRACE] -> SUCCESS! {defense['threat_id']} neutralized.")
                        destroyed_ghost_ids.add(defense["threat_id"])
                        
                        # Evaluate Splash Damage for SAMs in MCTS
                        if defense["effector"] == "SAM":
                            target_ghost = next((g for g in ghosts_to_evaluate if g.id == defense["threat_id"]), None)
                            if target_ghost:
                                for other_ghost in ghosts_to_evaluate:
                                    if other_ghost.id not in destroyed_ghost_ids:
                                        if math.hypot(other_ghost.x - target_ghost.x, other_ghost.y - target_ghost.y) <= 15.0:
                                            t_log(f"[MCTS TRACE] -> SPLASH DAMAGE! {other_ghost.id} caught in SAM blast.")
                                            destroyed_ghost_ids.add(other_ghost.id)

                # Verify that all real (non-decoy) threats were destroyed
                all_critical_hits = all(g.id in destroyed_ghost_ids for g in ghosts_to_evaluate if g.estimated_type != "decoy")

                if all_critical_hits:
                    rollout_score += 100 # Successfully defended the blind spot!
                    
                    # Capital Intact Bonus: Reward the engine if Capital SAMs were never fired
                    for b in sim_state.bases:
                        if "Capital" in b.name:
                            if b.inventory.get("SAM", 0) == initial_capital_sams and initial_capital_sams > 0:
                                t_log("[MCTS TRACE] -> BONUS: Capital SAM reserves are fully intact!")
                                rollout_score += 50 # Boost score for perfect reserve management
                            break
                else:
                    t_log("[MCTS TRACE] -> CRITICAL MISS! Primary threat hit the Capital.")
                    rollout_score -= 200 # Weapon missed. Capital hit.
            else:
                t_log("[MCTS TRACE] -> FATAL: No suitable weapons remaining for the primary threat! Capital destroyed.")
                rollout_score -= 500 # Reserves were empty! Capital destroyed.
                
                # Log which specific bases ran completely out of ammo
                for b in sim_state.bases:
                    if sum(b.inventory.values()) == 0:
                        depletion_tracker[b.name] = depletion_tracker.get(b.name, 0) + 1
                        
        return rollout_score, depletion_tracker

    @staticmethod
    def run_mcts_rollout(initial_state: GameState, current_assignments: list, iterations: int = 500, max_time_sec: float = 2.0, log_queue=None, weather: str = "clear", weights: dict = None):
        """LAYER 2: Monte Carlo Tree Search (Simulating futures)."""
        total_score = 0
        depletion_tracker = {}
        
        # Find initial Capital SAMs for the intact bonus check
        initial_capital_sams = 0
        for b in initial_state.bases:
            if "Capital" in b.name:
                initial_capital_sams = b.inventory.get("SAM", 0)
                break
                
        start_time = time.time()
        actual_iterations = 0
        
        # Run the first trace iteration locally to enable live WebSocket streaming without IPC issues
        if iterations > 0:
            score, depletions = StrategicMCTS._single_rollout(initial_state, current_assignments, initial_capital_sams, is_trace=True, log_queue=log_queue, weather=weather, weights=weights)
            total_score += score
            for b_name, count in depletions.items():
                depletion_tracker[b_name] = depletion_tracker.get(b_name, 0) + count
            actual_iterations += 1

        # Use ThreadPoolExecutor instead of ProcessPoolExecutor. Windows 'spawn' boots new Python 
        # interpreters, causing massive RAM spikes, hanging batch tests, and orphaned process leaks.
        safe_workers = min(4, os.cpu_count() or 1)
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=safe_workers)
        futures = []
        
        for i in range(1, iterations):
            futures.append(executor.submit(StrategicMCTS._single_rollout, initial_state, current_assignments, initial_capital_sams, False, None, weather, weights))
        
        try:
            remaining_time = max_time_sec - (time.time() - start_time)
            if remaining_time > 0:
                for future in concurrent.futures.as_completed(futures, timeout=remaining_time):
                    score, depletions = future.result()
                    total_score += score
                    for b_name, count in depletions.items():
                        depletion_tracker[b_name] = depletion_tracker.get(b_name, 0) + count
                    actual_iterations += 1
            else:
                msg = f"[MCTS TIMEOUT] Halting rollouts early at {actual_iterations} iterations to guarantee response time."
                print(msg)
                if log_queue: log_queue.put(msg)
        except concurrent.futures.TimeoutError:
            msg = f"[MCTS TIMEOUT] Halting rollouts early at {actual_iterations} iterations to guarantee response time."
            print(msg)
            if log_queue: log_queue.put(msg)
        
        # Non-blocking shutdown to ensure we don't exceed the 2.0 second limit waiting for orphaned processes
        try:
            executor.shutdown(wait=False, cancel_futures=True)
        except TypeError:
            # Fallback for Python 3.8 and older
            for f in futures:
                f.cancel()
            executor.shutdown(wait=False)
            
        # 4. BACKPROPAGATION
        # Return the average score of all simulated futures and the depletion stats
        if actual_iterations == 0:
            return 0, depletion_tracker
        return total_score / actual_iterations, depletion_tracker

def evaluate_threats_advanced(state: GameState, threats: list[Threat], mcts_iterations: int = 500, log_queue=None, weather: str = "clear", weights: dict = None, max_time_sec: float = 2.0):
    """Master Function: Combines Layer 1 (Tactical) and Layer 2 (Strategic)."""
    
    # 0. Extract features for the RL Agents
    features = extract_rl_features(state, threats)
    
    # 1. RL DOCTRINE MANAGER (Dynamic Weight Tuning)
    dynamic_weights = copy.deepcopy(weights) if weights else copy.deepcopy(DEFAULT_WEIGHTS)
    
    if DOCTRINE_MODEL is not None and len(threats) > 0:
        input_tensor = torch.tensor([features], dtype=torch.float32)
        with torch.no_grad():
            # Output is a [14] tensor of continuous multipliers
            multipliers = DOCTRINE_MODEL(input_tensor)[0].numpy() 
            
        keys = list(dynamic_weights.keys())
        for idx, key in enumerate(keys):
            # Apply the RL agent's multiplier (capped at minimum 0.1 to prevent dividing by zero elsewhere)
            dynamic_weights[key] *= max(0.1, float(multipliers[idx]))
            
        if log_queue:
            # Send a cool visual message to the UI terminal
            eco_mult = multipliers[5]
            log_queue.put(f"[MCTS TRACE] RL Doctrine Manager engaged. Battlefield state analyzed.")
            if eco_mult > 1.5:
                log_queue.put(f"[MCTS TRACE] -> SWARM DETECTED: Economy of Force doctrine temporarily increased by {eco_mult:.1f}x!")
                
    # Swap in the dynamically generated weights for this specific tick
    active_weights = dynamic_weights
    
    # Layer 1: Get absolute mathematically perfect assignment for the current wave
    tactical_plan = TacticalEngine.get_optimal_assignments(state, threats, is_simulation=False, log_queue=log_queue, weather=weather, weights=active_weights)
    
    # Layer 2: Strategic Evaluation (Neural Network OR Physics Rollouts)
    if RL_MODEL is not None:
        # --- SUPERCHARGED ALPHA-ZERO PATH ---
        sim_state = copy.deepcopy(state)
        assigned_ids = set(a["threat_id"] for a in tactical_plan)
        remaining_threats = [t for t in threats if t.id not in assigned_ids]
        
        for action in tactical_plan:
            for b in sim_state.bases:
                if b.name == action["base"]:
                    b.inventory[action["effector"]] -= 1
                    break
                    
        input_tensor = torch.tensor([features], dtype=torch.float32)
        with torch.no_grad():
            future_score = RL_MODEL(input_tensor).item()
            
        depletion_tracker = {}
        msg = f"[MCTS TRACE] Neural Network predicted strategic score: {future_score:.2f} (Bypassed {mcts_iterations} physics rollouts)"
        print(msg)
        if log_queue: log_queue.put(msg)
    else:
        # --- CLASSICAL MCTS PATH ---
        future_score, depletion_tracker = StrategicMCTS.run_mcts_rollout(state, tactical_plan, iterations=mcts_iterations, max_time_sec=max_time_sec, log_queue=log_queue, weather=weather, weights=active_weights)
    
    # Final Evaluation
    is_plan_safe = future_score > -100 
    
    warning_msg = "Reserves sufficient for blind spot defense."
    if not is_plan_safe:
        warning_msg = "CRITICAL: Reserve depletion risks Capital!"
        if depletion_tracker:
            empty_bases = [name for name, count in depletion_tracker.items()]
            if empty_bases:
                ammo_warning = f" Ammo depleted at: {', '.join(empty_bases)}."
                warning_msg += ammo_warning
                msg = f"[MCTS LOG] Capital destroyed in rollouts!{ammo_warning}"
                print(msg)
                if log_queue: log_queue.put(msg)

    return {
        "tactical_assignments": tactical_plan,
        "strategic_consequence_score": round(future_score, 2),
        "strategic_warning": warning_msg,
        "triage_ignored_threats": len(threats) - len(tactical_plan)
    }