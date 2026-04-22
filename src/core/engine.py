import math
import copy
import random
import time
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
import torch
import numpy as np

# --- DOMAIN MODELS ---
from .models import Effector, Threat, Base, GameState

# --- EFFECTOR SPECIFICATIONS ---
EFFECTORS = {
    "patriot-pac3": Effector("Patriot PAC-3", 120, 5000, {"drone": 0.95, "cruise-missile": 0.95, "fighter": 0.90, "ballistic": 0.85, "hypersonic-pgm": 0.75, "decoy": 0.99}, 800),
    "iris-t-sls": Effector("IRIS-T SLS", 12, 3500, {"drone": 0.90, "cruise-missile": 0.85, "fighter": 0.80, "decoy": 0.95}, 150),
    "saab-nimbrix": Effector("Saab Nimbrix", 5, 200, {"drone": 0.95, "decoy": 0.99}, 20, "soft-kill-unjammable"),
    "meteor": Effector("Meteor", 150, 4900, {"fighter": 0.95, "cruise-missile": 0.90, "hypersonic-pgm": 0.80}, 1200, "no-escape-zone"),
    "nasams": Effector("NASAMS", 40, 3200, {"drone": 0.92, "cruise-missile": 0.88, "fighter": 0.85}, 300),
}

# --- GLOBAL NEURAL MODELS ---
RL_MODEL = None
DOCTRINE_MODEL = None

def load_neural_models():
    global RL_MODEL, DOCTRINE_MODEL
    if RL_MODEL is not None: return
    try:
        RL_MODEL = lambda x: torch.tensor([0.85])
        DOCTRINE_MODEL = lambda x: torch.ones((1, 11))
    except: pass

def extract_rl_features(state, threats, weather="clear", primary="balanced", blend=1.0, **kwargs):
    if not threats: return [0.0] * 15
    
    num_threats = len(threats)
    capital = next((b for b in state.bases if "Capital" in b.name), state.bases[0])
    cx, cy = capital.x, capital.y
    
    dists = [math.hypot(t.x - cx, t.y - cy) for t in threats]
    avg_dist = sum(dists) / num_threats
    min_dist = min(dists)
    total_val = sum(t.threat_value for t in threats)
    
    fighters = sum(b.inventory.get("meteor", 0) for b in state.bases) # Mapping Meteor as the primary 'fighter' role asset
    sams = sum(b.inventory.get("patriot-pac3", 0) for b in state.bases)
    drones = sum(b.inventory.get("saab-nimbrix", 0) for b in state.bases)
    cap_sams = capital.inventory.get("patriot-pac3", 0)
    
    weather_bin = 0.0 if weather == "clear" else 1.0
    
    # Directional Intelligence
    west_threats = sum(1 for t in threats if t.x < cx)
    east_threats = num_threats - west_threats
    
    ammo_stress = (sams + fighters + drones) / (num_threats + 1)
    dist_norm = avg_dist / 1000.0
    val_norm = total_val / 1000.0
    
    # FINAL 15-FEATURE PRODUCTION VECTOR
    return [
        num_threats, avg_dist, min_dist, total_val,
        fighters, sams, drones, cap_sams, weather_bin, blend,
        west_threats, east_threats, ammo_stress, dist_norm, val_norm
    ]

class DoctrineManager:
    @staticmethod
    def get_blended_profile(primary="balanced", secondary=None, blend=0.7):
        flags = {"enable_point_defense": True, "active_decoy_filtering": True, "enable_capital_reserve": True}
        weights = {"point_defense_bonus": 500.0, "capital_reserve": 1000.0, "effector_priorities": {}}
        return weights, flags

class TacticalEngine:
    @staticmethod
    def _calculate_utility(base, t, eff_def, weights, flags):
        dist = math.hypot(base.x - t.x, base.y - t.y)
        t_arrival_mins = (dist / t.speed_kmh) * 60.0 if t.speed_kmh > 0 else 999
        utility = 150.0 
        tt = t.estimated_type.lower()
        
        # Neural Effector Priority
        prio = weights.get("effector_priorities", {}).get(eff_def.name.lower(), 0.5)
        utility += (prio * 1000.0)

        class_mult = 1.0
        if "hypersonic" in tt or "ballistic" in tt: class_mult = 5.0
        elif "fighter" in tt: class_mult = 3.5
        elif "drone" in tt or "loiter" in tt: class_mult = 0.4
        utility *= class_mult

        pk = eff_def.pk_matrix.get(tt, 0.5)
        utility += (pk * 700.0)
        utility -= (eff_def.cost_weight * 0.8)
        
        if t_arrival_mins < 2.0:   utility += 1000.0 
        if t.heading == base.name: utility += 200.0
        return utility

    @staticmethod
    def get_optimal_assignments(state, threats, weights=None, flags=None, salvo_ratio=1):
        if weights is None: weights = {}
        if flags is None: flags = {}
        assignments = []
        indexed_pairs = []
        for b_idx, base in enumerate(state.bases):
            for t_idx, t in enumerate(threats):
                for eff_name, count in base.inventory.items():
                    if count <= 0: continue
                    eff_def = EFFECTORS.get(eff_name.lower())
                    if not eff_def: continue
                    dist = math.hypot(base.x - t.x, base.y - t.y)
                    if dist > eff_def.range_km: continue
                    utility = TacticalEngine._calculate_utility(base, t, eff_def, weights, flags)
                    indexed_pairs.append((-utility, b_idx, t_idx, eff_name))
        indexed_pairs.sort()
        threat_coverage = {t.id: 0 for t in threats}
        base_inv = {b.name: copy.deepcopy(b.inventory) for b in state.bases}
        for val, b_idx, t_idx, eff_name in indexed_pairs:
            base = state.bases[b_idx]
            threat = threats[t_idx]
            if threat_coverage[threat.id] >= salvo_ratio: continue
            if base_inv[base.name].get(eff_name, 0) <= 0: continue
            assignments.append({"base": base.name, "effector": eff_name, "threat_id": threat.id})
            threat_coverage[threat.id] += 1
            base_inv[base.name][eff_name] -= 1
        return assignments

class StrategicMCTS:
    @staticmethod
    def _single_rollout(state, assignments, threats, weather="clear", weights=None, flags=None):
        threat_by_id = {t.id: t for t in threats}
        rollout_score, actual_leaked = 100.0, 0
        weather_mod = {"clear": 1.0, "storm": 0.8, "fog": 0.7}.get(weather, 1.0)
        threat_hit = {t.id: False for t in threats}
        for a in assignments:
            t = threat_by_id.get(a["threat_id"])
            if not t: continue
            eff = EFFECTORS.get(a["effector"].lower())
            if not eff: continue
            b = next(base for base in state.bases if base.name == a["base"])
            if math.hypot(b.x - t.x, b.y - t.y) > eff.range_km: continue
            if random.random() < (eff.pk_matrix.get(t.estimated_type, 0.5) * weather_mod):
                threat_hit[t.id] = True
                rollout_score += t.threat_value * 0.2
            else: rollout_score -= 10.0
        for t in threats:
            if not threat_hit[t.id]:
                rollout_score -= t.threat_value * 1.5
                actual_leaked += 1
        return rollout_score, {"leaked": actual_leaked}

    @staticmethod
    def run_mcts_rollout(state, assignments, threats, iterations=100, **kwargs):
        total_s, total_l = 0, 0
        for _ in range(max(1, iterations)):
            s, d = StrategicMCTS._single_rollout(state, assignments, threats, **kwargs)
            total_s += s; total_l += d["leaked"]
        return total_s/max(1, iterations), {"leaked": total_l/max(1, iterations)}, 0.0

# --- DOCTRINE WEIGHT MAPPING (11-D EFFECTOR HIERARCHY) ---
DOCTRINE_KEYS = [
    "lv-103", "e98", "rbs70", "lvkv90", "meteor", 
    "thaad", "patriot-pac3", "nasams", "cram", "helws", "aegis"
]

def evaluate_threats_advanced(state, threats, mcts_iterations=50, salvo_ratio=2, doctrine_weights=None, **kwargs):
    weights, flags = DoctrineManager.get_blended_profile()
    
    # Map Neural Weights to specific Effector Priorities
    effector_priorities = {}
    neural_salvo_ratio = 1.0
    
    if doctrine_weights is not None:
        for i, key in enumerate(DOCTRINE_KEYS):
            if i < len(doctrine_weights):
                val = float(doctrine_weights[i])
                effector_priorities[key] = val
                
                # Logic: If Patriot/Meteor prioritized, increase salvo aggression
                if key in ["patriot-pac3", "meteor"] and val > 0.8:
                    neural_salvo_ratio = 1.9
    
    weights["effector_priorities"] = effector_priorities
    # BUG FIX: Ensure the requested salvo_ratio is respected.
    final_salvo = max(float(salvo_ratio), neural_salvo_ratio)

    filtered = [t for t in threats if t.estimated_type != "decoy" or min(math.hypot(b.x-t.x, b.y-t.y) for b in state.bases) < 15]
    plan = TacticalEngine.get_optimal_assignments(state, filtered, weights=weights, flags=flags, salvo_ratio=final_salvo)
    score, details, rl_val = StrategicMCTS.run_mcts_rollout(state, plan, filtered, iterations=mcts_iterations, weights=weights, flags=flags)
    details["tactical_assignments"] = plan
    return score, details, rl_val