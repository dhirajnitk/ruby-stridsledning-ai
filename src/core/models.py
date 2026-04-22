from dataclasses import dataclass, field
from typing import List, Dict
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
            with open(filepath, mode='r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['subtype'] in ['air_base', 'capital', 'major_city']:
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