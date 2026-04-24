from dataclasses import dataclass, field
from typing import List, Dict, Optional
import csv
import os

# --- 1. CORE DATA STRUCTURES ---
CSV_FILE_PATH = "data/input/Boreal_passage_coordinates.csv"

@dataclass
class Effector:
    name: str
    speed_kmh: float
    cost_weight: float
    range_km: float
    pk_matrix: Dict[str, float]
    special_logic: str = "" # unjammable, no-escape-zone, soft-kill, reusable

@dataclass
class Base:
    name: str
    x: float
    y: float
    inventory: Dict[str, int]

@dataclass
class Threat:
    id: str
    x: float
    y: float
    speed_kmh: float
    heading: str
    estimated_type: str
    threat_value: float

    # ── Advanced trajectory behaviours ──────────────────────────────
    # MARV: Maneuvering Re-entry Vehicle.
    #   When True the threat executes a terminal-phase evasive manoeuvre,
    #   applying a Pk penalty to any interceptor engagement.
    #   marv_pk_penalty: multiplicative modifier on Pk (e.g. 0.55 → 45% harder to hit).
    #   marv_trigger_range_km: range from target at which the manoeuvre kicks in.
    is_marv: bool = False
    marv_pk_penalty: float = 0.55          # effective Pk = base_Pk × 0.55
    marv_trigger_range_km: float = 80.0    # start manoeuvring within 80 km of target

    # MIRV: Multiple Independently targetable Re-entry Vehicles.
    #   When True the threat spawns `mirv_count` child threats at `mirv_release_range_km`.
    #   The child threats are injected into the active threat list by the engine rollout.
    is_mirv: bool = False
    mirv_count: int = 3
    mirv_release_range_km: float = 150.0   # release altitude/range from target
    mirv_warhead_value: float = 0.0        # set at runtime: parent.threat_value / mirv_count
    mirv_released: bool = False            # internal state — True after spawning

    # DOGFIGHT / RTB: applies to fighter/aircraft threats.
    #   can_dogfight: the aircraft will engage our interceptors in WVR combat when met.
    #   dogfight_win_prob: probability the enemy wins the 1v1 (0.0–1.0).
    #   can_rtb: if losing the dogfight the aircraft breaks off and returns to base.
    #   rtb_speed_kmh: retreat speed after break-off.
    can_dogfight: bool = False
    dogfight_win_prob: float = 0.5        # 50/50 by default
    can_rtb: bool = False
    rtb_speed_kmh: float = 1200.0
    is_retreating: bool = False            # internal state — True after break-off

@dataclass
class GameState:
    bases: List[Base]
    blind_spots: List[tuple] = field(default_factory=list)

# --- 2. HIGH-FIDELITY EFFECTOR DATABASE (NATO/SWEDEN + C-UAS) ---
EFFECTORS = {
    # C-UAS (Specialized Drone Defeat)
    "saab-nimbrix": Effector(
        name="Saab Nimbrix (Hard-Kill)", 
        speed_kmh=600.0, 
        cost_weight=2.0, # $20k-$40k (ultra-low cost)
        range_km=5.0, 
        pk_matrix={"drone": 0.98, "loiter": 0.95},
        special_logic="anti-drone-kinetic"
    ),
    "merops-interceptor": Effector(
        name="Merops Drone Interceptor", 
        speed_kmh=400.0, 
        cost_weight=1.5, # $15k per unit
        range_km=3.0, 
        pk_matrix={"drone": 0.95, "loiter": 0.90},
        special_logic="drone-on-drone"
    ),
    "coyote-block2": Effector(
        name="RTX Coyote Block 2+", 
        speed_kmh=800.0, 
        cost_weight=5.0, 
        range_km=15.0, 
        pk_matrix={"drone": 0.95, "loiter": 0.95, "cruise": 0.3},
        special_logic="swarm-defeat"
    ),
    "coyote-block3-nk": Effector(
        name="RTX Coyote Block 3 (Non-Kinetic)", 
        speed_kmh=600.0, 
        cost_weight=0.5, # Reusable cost amortization
        range_km=10.0, 
        pk_matrix={"drone": 0.90}, 
        special_logic="reusable-soft-kill"
    ),
    "lids-ew": Effector(
        name="LIDS EW Jammer", 
        speed_kmh=300000.0, # Light speed
        cost_weight=0.1, # Effectively zero marginal cost
        range_km=8.0, 
        pk_matrix={"drone": 0.85, "loiter": 0.70},
        special_logic="soft-kill-unjammable"
    ),

    # SHORAD (Point Defense)
    "rbs-70": Effector(
        name="RBS 70 NG", 
        speed_kmh=800.0, 
        cost_weight=15.0, 
        range_km=9.0, 
        pk_matrix={"drone": 0.95, "loiter": 0.95, "cruise": 0.6},
        special_logic="unjammable"
    ),
    "iris-t-sls": Effector(
        name="IRIS-T SLS", speed_kmh=1200.0, cost_weight=40.0, range_km=12.0, 
        pk_matrix={"drone": 0.9, "loiter": 0.9, "cruise": 0.8, "fighter": 0.8}
    ),

    # MRAD/LRAD (Heavy Defense)
    "nasams": Effector(
        name="NASAMS (AMRAAM)", speed_kmh=3000.0, cost_weight=100.0, range_km=40.0, 
        pk_matrix={"fighter": 0.9, "cruise": 0.9}
    ),
    "patriot-pac3": Effector(
        name="Patriot PAC-3 MSE", speed_kmh=4500.0, cost_weight=400.0, range_km=120.0, 
        pk_matrix={"ballistic": 0.65, "hypersonic": 0.6, "cruise": 0.95}
    ),
    "meteor": Effector(
        name="Meteor BVRAAM", speed_kmh=4500.0, cost_weight=200.0, range_km=150.0, 
        pk_matrix={"fighter": 0.98, "cruise": 0.85}, special_logic="no-escape-zone"
    )
}

def load_battlefield_state(filepath) -> GameState:
    mode = os.getenv("SAAB_MODE", "sweden")
    bases = []
    try:
        if os.path.exists(filepath):
            # BUG-FIX B-CSV-1: Use utf-8-sig to handle BOM and Swedish special characters (å, ä, ö)
            with open(filepath, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # BUG-FIX B-CSV-2: Sweden has naval_base subtype (Muskö, Karlskrona) that
                    # were excluded because only air_base/capital/major_city were accepted.
                    # Include naval_base for all modes.
                    valid_subtypes = ['air_base', 'capital', 'major_city', 'naval_base']
                    if row['subtype'] in valid_subtypes:
                        name = row['feature_name']
                        if mode == "sweden":
                            # Sweden "Salvo-Ready Fortress" Config
                            inv = {
                                "patriot-pac3": 100, 
                                "iris-t-sls": 200, 
                                "saab-nimbrix": 1000, 
                                "meteor": 40,
                                "nasams": 20
                            }
                        else:
                            inv = {"patriot-pac3": 60, "nasams": 100, "coyote-block2": 200, "merops-interceptor": 200}
                        bases.append(Base(name, float(row['x_km']), float(row['y_km']), inv))
    except: pass
    
    if not bases:
        bases = [
            Base("Stockholm Hub", 0.0, 0.0, {"patriot-pac3": 16, "saab-nimbrix": 200, "lids-ew": 2}),
            Base("Northern Vanguard", 400, 300, {"coyote-block2": 100, "merops-interceptor": 100})
        ]
    return GameState(bases=bases)