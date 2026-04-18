from dataclasses import dataclass, field
from typing import List, Dict

# --- 1. CORE DATA STRUCTURES ---

@dataclass
class Effector:
    name: str
    speed_kmh: float
    cost_weight: float
    pk_matrix: Dict[str, float]

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

# Define Effectors based on Blueprint
EFFECTORS = {
    "fighter": Effector("Fighter", 2000.0, 50.0, {"fast-mover": 0.8, "bomber": 0.9, "decoy": 0.5}),
    "sam": Effector("SAM", 3000.0, 80.0, {"fast-mover": 0.7, "bomber": 0.95, "decoy": 0.9}),
    "drone": Effector("Drone", 400.0, 10.0, {"fast-mover": 0.1, "bomber": 0.4, "decoy": 0.8})
}