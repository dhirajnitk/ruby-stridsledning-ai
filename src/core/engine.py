import math
import copy
import random
import time
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
import numpy as np

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("[SYSTEM] PyTorch DLL not found — Neural Models disabled. Using Heuristic Triage.")

# --- DOMAIN MODELS ---
from .models import Effector, Threat, Base, GameState

# --- EFFECTOR SPECIFICATIONS ---
# range_km is in kilometres — compared directly against km-coordinate distances from load_battlefield_state().
# Authoritative values aligned with cortex_c2.html::EFFECTORS_DEF (meters ÷ 1000) and src/core/models.py.
# speed_kmh is the interceptor missile speed (not used in range gating, only in arrival-time urgency calc).
EFFECTORS = {
    "patriot-pac3":  Effector("Patriot PAC-3",  4500, 800, 120, {"drone": 0.95, "cruise-missile": 0.95, "fighter": 0.90, "ballistic": 0.85, "hypersonic-pgm": 0.75, "decoy": 0.99}),
    "iris-t-sls":    Effector("IRIS-T SLS",      3500, 150,  12, {"drone": 0.90, "cruise-missile": 0.85, "fighter": 0.80, "decoy": 0.95}),
    "saab-nimbrix":  Effector("Saab Nimbrix",     600,  20,   5, {"drone": 0.95, "decoy": 0.99}, "soft-kill-unjammable"),
    "meteor":        Effector("Meteor",           4500, 1200, 150, {"fighter": 0.95, "cruise-missile": 0.90, "hypersonic-pgm": 0.80}, "no-escape-zone"),
    "nasams":        Effector("NASAMS",           3000, 300,  40, {"drone": 0.92, "cruise-missile": 0.88, "fighter": 0.85}),
    "coyote-block2": Effector("RTX Coyote B2",    800,   5,  15, {"drone": 0.95, "cruise-missile": 0.30}),
    "merops-interceptor": Effector("Merops",       400,   2,   3, {"drone": 0.95}),
    "thaad":         Effector("THAAD",            7200, 800, 200, {"ballistic": 0.98, "hypersonic-pgm": 0.80, "cruise-missile": 0.40}),
    "lids-ew":       Effector("LIDS EW",       300000,   1,   8, {"drone": 0.85}, "soft-kill-unjammable"),
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
    """Extract the 18-D tactical feature vector for PPO / neural inference.
    
    Features 0-12: Classic production features.
    Feature 13: total_assigned (TemporalCommitment).
    Feature 14: high_threat_unassigned (ReEngagementTrigger).
    Features 15-17: Advanced trajectory awareness.

    The strategic MCTS layer uses a separate 3-D temporal context so the
    existing PPO checkpoints can stay at 18 inputs while MCTS reasons over
    the extra commitment state.
    """
    if not threats: return [0.0] * 18
    
    num_threats = len(threats)
    capital = next((b for b in state.bases if "Capital" in b.name), state.bases[0])
    cx, cy = capital.x, capital.y
    
    dists = [math.hypot(t.x - cx, t.y - cy) for t in threats]
    avg_dist = sum(dists) / num_threats
    min_dist = min(dists)
    total_val = sum(t.threat_value for t in threats)
    
    fighters = sum(b.inventory.get("meteor", 0) for b in state.bases)
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
    
    # Advanced Trajectory Awareness (MARV/MIRV)
    has_marv = 1.0 if any(getattr(t, "is_marv", False) for t in threats) else 0.0
    has_mirv = 1.0 if any(getattr(t, "is_mirv", False) and not getattr(t, "mirv_released", False)
                          for t in threats) else 0.0
    total_mirv_warheads = float(sum(getattr(t, "mirv_count", 0) for t in threats
                                    if getattr(t, "is_mirv", False) and not getattr(t, "mirv_released", False)))
    
    # FINAL 18-FEATURE PRODUCTION VECTOR (Preserving Training Distribution)
    return [
        num_threats, avg_dist, min_dist, total_val,
        fighters, sams, drones, cap_sams, weather_bin, blend,
        west_threats, east_threats, ammo_stress, dist_norm, val_norm,
        has_marv, has_mirv, total_mirv_warheads
    ]

def extract_mcts_temporal_context(threats):
    """Extract the 3 temporal inputs used only by the strategic MCTS layer.

    1. total_assigned: total interceptors already committed across threats.
    2. assigned_ratio: commitment saturation normalized by threat count.
    3. high_threat_unassigned: uncovered high-value threats that should trigger
       a follow-on shot / re-engagement bias.
    """
    num_threats = len(threats)
    total_assigned = float(sum(getattr(t, "interceptors_assigned", 0) for t in threats))
    high_threat_unassigned = float(sum(
        1 for t in threats
        if t.threat_value > 70 and getattr(t, "interceptors_assigned", 0) == 0
    ))
    assigned_ratio = total_assigned / (num_threats + 1)
    return {
        "total_assigned": total_assigned,
        "assigned_ratio": assigned_ratio,
        "high_threat_unassigned": high_threat_unassigned,
    }

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

        # ── MARV: terminal manoeuvre degrades Pk — boost intercept urgency
        #    so the engine prefers committing multiple interceptors early,
        #    before the jink phase begins (i.e. when still outside trigger range).
        if getattr(t, "is_marv", False):
            trigger_km = getattr(t, "marv_trigger_range_km", 80.0)
            if dist > trigger_km:
                # Threat still in midcourse — intercept now while Pk is nominal
                utility += 600.0
            else:
                # Already jinking — Pk is degraded; still worth trying but less confident
                pk_eff = pk * getattr(t, "marv_pk_penalty", 0.55)
                utility += (pk_eff * 400.0)

        # ── MIRV: bus spawns mirv_count independent warheads — each interceptor
        #    only covers the bus, not its children.  Reward launching BEFORE
        #    release range so one shot can kill all warheads simultaneously.
        if getattr(t, "is_mirv", False) and not getattr(t, "mirv_released", False):
            release_km = getattr(t, "mirv_release_range_km", 150.0)
            if dist > release_km:
                # Pre-release: killing bus kills all warheads — highest priority
                mirv_n = getattr(t, "mirv_count", 3)
                utility += 800.0 * mirv_n   # proportional to number of warheads saved
            else:
                # Post-release: bus is empty, treat as normal ballistic remnant
                utility += 100.0

        # ── DOGFIGHT: fighter can down our interceptor — favour longer-range
        #    shots (Meteor / PAC-3) to engage before merge.
        if getattr(t, "can_dogfight", False):
            dog_prob = getattr(t, "dogfight_win_prob", 0.5)
            # Prefer effectors that have range advantage (fire before merge)
            range_bonus = min(eff_def.range_km / 100.0, 5.0) * 200.0
            # Penalise if enemy win probability is high — deprioritise costly shots
            utility += range_bonus * (1.0 - dog_prob)

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
            
            # Account for in-flight interceptors already assigned by the frontend
            effective_coverage = threat_coverage[threat.id] + getattr(threat, "interceptors_assigned", 0)
            if effective_coverage >= salvo_ratio: continue
            if base_inv[base.name].get(eff_name, 0) <= 0: continue
            assignments.append({"base": base.name, "effector": eff_name, "threat_id": threat.id})
            threat_coverage[threat.id] += 1
            base_inv[base.name][eff_name] -= 1
        return assignments

class StrategicMCTS:
    @staticmethod
    def _resolve_dogfight(t, eff, rollout_score):
        """
        Resolve a fighter/aircraft intercept as a dogfight when can_dogfight=True.

        Outcomes (all stochastic):
          WIN  (enemy wins dogfight) → our interceptor is lost, threat survives.
                                        Score penalised by threat_value × 1.0.
          LOSE (we win dogfight)     → enemy destroyed, same as a normal kill.
          RTB  (enemy breaks off)    → enemy retreats, threat_value halved
                                        (aborted mission, still costs ammo).

        Returns (threat_neutralised:bool, score_delta:float, outcome:str)
        """
        r = random.random()
        if r < t.dogfight_win_prob:
            # Enemy wins the merge — our interceptor shot down
            return False, -(t.threat_value * 1.0), "ENEMY_WIN"
        elif t.can_rtb and r < (t.dogfight_win_prob + (1.0 - t.dogfight_win_prob) * 0.4):
            # Enemy breaks off (RTB) — partial success
            return True, t.threat_value * 0.05, "RTB"
        else:
            # We kill the fighter cleanly
            return True, t.threat_value * 0.2, "KILL"

    @staticmethod
    def _single_rollout(state, assignments, threats, weather="clear", weights=None, flags=None, mcts_temporal_context=None):
        threat_by_id = {t.id: t for t in threats}
        rollout_score, actual_leaked = 100.0, 0
        weather_mod = {"clear": 1.0, "storm": 0.8, "fog": 0.7}.get(weather, 1.0)
        threat_hit = {t.id: False for t in threats}

        temporal_context = mcts_temporal_context or {}
        total_assigned = float(temporal_context.get("total_assigned", 0.0))
        assigned_ratio = float(temporal_context.get("assigned_ratio", 0.0))
        high_threat_unassigned = float(temporal_context.get("high_threat_unassigned", 0.0))

        # Strategic pressure from commitment state: reward coverage, but penalise
        # uncovered high-value leakers and oversaturated salvos before the rollout.
        rollout_score += total_assigned * 0.5
        rollout_score -= high_threat_unassigned * 20.0
        if assigned_ratio > 1.0:
            rollout_score -= (assigned_ratio - 1.0) * 8.0

        # ── MIRV: expand parent threats into child warheads before engagement ──
        active_threats = list(threats)
        mirv_children = []
        for t in threats:
            if getattr(t, "is_mirv", False) and not getattr(t, "mirv_released", False):
                # Check if parent is within MIRV release range of any base/capital
                cap = next((b for b in state.bases if "Capital" in b.name), state.bases[0])
                dist_to_cap = math.hypot(t.x - cap.x, t.y - cap.y)
                if dist_to_cap <= getattr(t, "mirv_release_range_km", 150.0):
                    t.mirv_released = True
                    child_val = t.threat_value / max(1, t.mirv_count)
                    # Spread warheads towards random bases
                    targets = random.choices(state.bases, k=t.mirv_count)
                    for i, tgt_base in enumerate(targets):
                        spread_x = t.x + random.uniform(-30, 30)
                        spread_y = t.y + random.uniform(-30, 30)
                        child = Threat(
                            id=f"{t.id}-MRV{i}",
                            x=spread_x, y=spread_y,
                            speed_kmh=t.speed_kmh * 1.2,   # warheads slightly faster
                            heading=tgt_base.name,
                            estimated_type="ballistic",     # re-entry vehicles
                            threat_value=child_val,
                        )
                        mirv_children.append(child)
                        threat_hit[child.id] = False
                    # Parent bus is now empty — mark it hit (bus itself is not a warhead)
                    threat_hit[t.id] = True

        active_threats = active_threats + mirv_children

        # ── TEMPORAL FEEDBACK: Account for interceptors already in flight ──
        for t in active_threats:
            assigned_count = getattr(t, "interceptors_assigned", 0)
            if assigned_count > 0 and not threat_hit[t.id]:
                # Simulate in-flight interceptors using a generic high-performance Pk (e.g. 0.75)
                # This ensures the MCTS 'knows' a threat is being handled.
                for _ in range(assigned_count):
                    if random.random() < 0.75 * weather_mod:
                        threat_hit[t.id] = True
                        rollout_score += t.threat_value * 0.15 # Reduced bonus for legacy shots
                        break

        for a in assignments:
            t = threat_by_id.get(a["threat_id"])
            if not t: continue
            eff = EFFECTORS.get(a["effector"].lower())
            if not eff: continue
            b = next(base for base in state.bases if base.name == a["base"])
            if math.hypot(b.x - t.x, b.y - t.y) > eff.range_km: continue

            effective_pk = eff.pk_matrix.get(t.estimated_type, 0.5) * weather_mod

            # ── MARV: apply Pk penalty when threat is in terminal manoeuvre ──
            if getattr(t, "is_marv", False):
                cap = next((base for base in state.bases if "Capital" in base.name), state.bases[0])
                dist_to_target = math.hypot(t.x - cap.x, t.y - cap.y)
                if dist_to_target <= getattr(t, "marv_trigger_range_km", 80.0):
                    effective_pk *= getattr(t, "marv_pk_penalty", 0.55)

            # ── DOGFIGHT: fighter aircraft engage interceptors ──
            tt = t.estimated_type.lower()
            if getattr(t, "can_dogfight", False) and ("fighter" in tt or "aircraft" in tt):
                neutralised, delta, outcome = StrategicMCTS._resolve_dogfight(t, eff, rollout_score)
                rollout_score += delta
                if neutralised:
                    threat_hit[t.id] = True
                # if enemy wins (not neutralised) the threat remains — handled in leak loop below
                continue

            if random.random() < effective_pk:
                threat_hit[t.id] = True
                rollout_score += t.threat_value * 0.2
            else:
                rollout_score -= 10.0

        # ── MIRV child warheads not covered by existing assignments leak through ──
        for t in active_threats:
            if not threat_hit.get(t.id, False):
                rollout_score -= t.threat_value * 1.5
                actual_leaked += 1

        return rollout_score, {"leaked": actual_leaked}

    @staticmethod
    def run_mcts_rollout(state, assignments, threats, iterations=100, mcts_temporal_context=None, **kwargs):
        total_s, total_l = 0, 0
        for _ in range(max(1, iterations)):
            s, d = StrategicMCTS._single_rollout(
                state,
                assignments,
                threats,
                mcts_temporal_context=mcts_temporal_context,
                **kwargs,
            )
            total_s += s; total_l += d["leaked"]
        return total_s/max(1, iterations), {"leaked": total_l/max(1, iterations)}, 0.0

# --- DOCTRINE WEIGHT MAPPING (11-D EFFECTOR HIERARCHY) ---
DOCTRINE_KEYS = [
    "lv-103", "e98", "rbs70", "lvkv90", "meteor", 
    "thaad", "patriot-pac3", "nasams", "cram", "helws", "aegis"
]

def survival_mc(state, threats, n_sims=100, salvo_ratio=2, weather="clear", mcts_temporal_context=None):
    """Run N strategic rollouts, return survival_rate (score>0) and mean score."""
    weights, flags = DoctrineManager.get_blended_profile()
    plan = TacticalEngine.get_optimal_assignments(state, threats, weights=weights, flags=flags, salvo_ratio=salvo_ratio)

    scores = []
    leaked_list = []
    for _ in range(n_sims):
        s, d = StrategicMCTS._single_rollout(
            state,
            plan,
            threats,
            weather=weather,
            mcts_temporal_context=mcts_temporal_context,
        )
        scores.append(s)
        leaked_list.append(d.get("leaked", 0))

    survival = sum(1 for s in scores if s > 0) / n_sims * 100
    intercept_est = sum(1 for s in scores if s > 150) / n_sims * 100
    return {
        "survival_rate_pct": round(survival, 1),
        "intercept_rate_pct": round(intercept_est, 1),
        "mean_score": round(sum(scores) / n_sims, 1),
        "mean_leaked": round(sum(leaked_list) / n_sims, 2),
        "plan_size": len(plan),
    }

def evaluate_threats_advanced(state, threats, mcts_iterations=50, salvo_ratio=2, doctrine_weights=None, run_mc=False, **kwargs):
    # ── 4. NEURAL INFERENCE (Elite V3.5) ──
    # Dynamically adjust doctrine based on Neural Brain if requested and environment allows
    if kwargs.get("use_rl", False) and HAS_TORCH:
        try:
            from .inference import run_elite_inference
            filtered_for_nn = [t for t in threats if t.estimated_type != "decoy"]
            feats = extract_rl_features(state, filtered_for_nn)
            nn_doctrine, _ = run_elite_inference(feats)
            doctrine_weights = nn_doctrine
        except Exception as e:
            print(f"[WARNING] Neural Inference failed: {e}. Falling back to Heuristic weights.")

    weights, flags = DoctrineManager.get_blended_profile()
    mcts_temporal_context = extract_mcts_temporal_context(threats)
    
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
    
    # Force Aggressive Posture if MIRV detected in the swarm
    if any(getattr(t, "is_mirv", False) and not getattr(t, "mirv_released", False) for t in threats):
        neural_salvo_ratio = max(neural_salvo_ratio, 2.0)
    
    weights["effector_priorities"] = effector_priorities
    # BUG FIX: Ensure the requested salvo_ratio is respected.
    final_salvo = max(float(salvo_ratio), neural_salvo_ratio)

    filtered = [t for t in threats if t.estimated_type != "decoy" or min(math.hypot(b.x-t.x, b.y-t.y) for b in state.bases) < 15]
    plan = TacticalEngine.get_optimal_assignments(state, filtered, weights=weights, flags=flags, salvo_ratio=final_salvo)
    score, details, rl_val = StrategicMCTS.run_mcts_rollout(
        state,
        plan,
        filtered,
        iterations=mcts_iterations,
        mcts_temporal_context=mcts_temporal_context,
        weights=weights,
        flags=flags,
    )
    
    if run_mc:
        details["mc_metrics"] = survival_mc(
            state,
            filtered,
            n_sims=100,
            salvo_ratio=final_salvo,
            weather=kwargs.get("weather", "clear"),
            mcts_temporal_context=mcts_temporal_context,
        )
    
    details["tactical_assignments"] = plan
    details["mcts_temporal_context"] = mcts_temporal_context
    return score, details, rl_val