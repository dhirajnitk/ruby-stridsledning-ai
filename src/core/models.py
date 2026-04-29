from dataclasses import dataclass, field
from typing import List, Dict, Optional
import csv
import os

# --- 1. CORE DATA STRUCTURES ---
CSV_FILE_PATH = "data/input/Boreal_passage_coordinates.csv"

@dataclass
class Sensor:
    name: str
    type: str # radar_active, radar_passive, eo_ir, satellite_ir, satellite_sar
    detection_range_km: float
    field_of_view_deg: float = 360.0
    is_operational: bool = True
    altitude_m: float = 0.0 # Height for horizon calculation (Satellites use ~500,000m)

@dataclass
class Effector:
    name: str
    speed_kmh: float
    cost_weight: float
    range_km: float
    pk_matrix: Dict[str, float]
    special_logic: str = "" # unjammable, no-escape-zone, soft-kill, reusable
    weight_kg: float = 0.0 # Weight for radius calculation

@dataclass
class Base:
    name: str
    x: float
    y: float
    inventory: Dict[str, int]
    subtype: str = "ground_base" # ground_base, air_base, naval_base, carrier, destroyer, tower
    health: float = 100.0
    altitude_m: float = 0.0 # Height for radar horizon
    is_mobile: bool = False
    speed_kmh: float = 0.0
    heading_deg: float = 0.0
    sensors: List['Sensor'] = field(default_factory=list)

@dataclass
class Threat:
    id: str
    x: float
    y: float
    speed_kmh: float
    heading: str
    estimated_type: str
    threat_value: float
    is_marv: bool = False
    marv_pk_penalty: float = 0.55
    marv_trigger_range_km: float = 80.0
    is_mirv: bool = False
    mirv_count: int = 3
    mirv_release_range_km: float = 150.0
    mirv_warhead_value: float = 0.0
    mirv_released: bool = False
    can_dogfight: bool = False
    dogfight_win_prob: float = 0.5
    can_rtb: bool = False
    rtb_speed_kmh: float = 1200.0
    is_retreating: bool = False
    is_decoy: bool = False
    is_jamming: bool = False
    jamming_radius_km: float = 25.0
    jamming_strength: float = 0.4

@dataclass
class AirborneAsset:
    id: str
    name: str
    type: str  # awacs, fighter, tanker
    x: float
    y: float
    status: str = "operational"
    is_airborne: bool = False
    scramble_time_sec: float = 300.0 # 5 minutes for Alert-5 scramble
    fuel_max: float = 1000.0
    fuel_current: float = 1000.0
    endurance_min: float = 180.0 # 3 hours standard patrol
    burn_rates: Dict[str, float] = field(default_factory=lambda: {
        "CLIMB": 2.5, "CRUISE": 1.0, "COMBAT": 4.0, "LOITER": 0.8
    })
    hourly_op_cost: float = 50000.0
    weapon_inventory: Dict[str, int] = field(default_factory=dict)
    has_drop_tanks: bool = False
    waypoints: List[tuple] = field(default_factory=list)
    current_waypoint_idx: int = 0
    phase: str = "CRUISE"
    coverage_radius_km: float = 200.0
    parent_base: Optional[str] = None
    sensors: List['Sensor'] = field(default_factory=list)
    ready_at_time: float = 0.0
    turnaround_time_sec: float = 1800.0

    def get_combat_radius_km(self, effector_db: Dict[str, Effector]) -> float:
        if self.fuel_current <= 0: return 0.0
        total_payload_kg = 0
        for wname, count in self.weapon_inventory.items():
            eff = effector_db.get(wname.lower())
            if eff: total_payload_kg += eff.weight_kg * count
        drag_penalty = 1.0 + (total_payload_kg / 100.0) * 0.05
        cruise_rate = self.burn_rates.get("CRUISE", 1.0) * drag_penalty
        return (self.fuel_current / cruise_rate) / 2.0

@dataclass
class GameState:
    bases: List[Base]
    assets: List[AirborneAsset] = field(default_factory=list)
    blind_spots: List[tuple] = field(default_factory=list)

# --- 2. HIGH-FIDELITY SENSOR DATABASE ---
SENSORS = {
    "giraffe-4a": Sensor("Saab Giraffe 4A", "radar_active", 280.0),
    "erieye-awacs": Sensor("Erieye AEW&C", "radar_active", 450.0, altitude_m=10000.0),
    "ps-05a": Sensor("PS-05/A (Gripen)", "radar_active", 120.0),
    "an-mpq-65": Sensor("Raytheon AN/MPQ-65 (Patriot)", "radar_active", 170.0),
    "an-spy-6": Sensor("Raytheon AN/SPY-6 (V)1 Aegis", "radar_active", 370.0),
    "sbirs-ir": Sensor("SBIRS (Infrared Satellite)", "satellite_ir", 10000.0, altitude_m=35000000.0)
}

# --- 3. HIGH-FIDELITY EFFECTOR DATABASE (THE BOREAL SUPREME 24) ---
EFFECTORS = {
    "meteor": Effector("Meteor BVRAAM", 4500.0, 200.0, 150.0, {"fighter": 0.98, "cruise": 0.85, "bomber": 0.99}, weight_kg=190.0, special_logic="no-escape-zone"),
    "aim-120d": Effector("AIM-120D AMRAAM", 4000.0, 150.0, 120.0, {"fighter": 0.90, "cruise": 0.80}, weight_kg=152.0),
    "aim-9x": Effector("AIM-9X Sidewinder", 3000.0, 80.0, 20.0, {"fighter": 0.95, "drone": 0.90}, weight_kg=85.0),
    "iris-t-air": Effector("IRIS-T (Air)", 3000.0, 90.0, 25.0, {"fighter": 0.96, "drone": 0.92}, weight_kg=87.0),
    "patriot-pac3": Effector("Patriot PAC-3 MSE", 4500.0, 400.0, 60.0, {"ballistic": 0.95, "hypersonic": 0.85}, weight_kg=312.0),
    "patriot-pac2": Effector("Patriot PAC-2 GEM-T", 4000.0, 300.0, 160.0, {"fighter": 0.90, "cruise": 0.90}, weight_kg=900.0),
    "thaad": Effector("THAAD", 7200.0, 800.0, 200.0, {"ballistic": 0.98, "hypersonic": 0.80}, weight_kg=900.0),
    "samp-t": Effector("SAMP/T (Aster 30)", 4500.0, 350.0, 120.0, {"fighter": 0.92, "cruise": 0.90}, weight_kg=450.0),
    "nasams": Effector("NASAMS (AMRAAM-ER)", 3500.0, 150.0, 40.0, {"fighter": 0.85, "cruise": 0.88}, weight_kg=152.0),
    "iris-t-slm": Effector("IRIS-T SLM", 3500.0, 120.0, 40.0, {"fighter": 0.88, "cruise": 0.90}, weight_kg=87.0),
    "iris-t-sls": Effector("IRIS-T SLS (RBS-98)", 3000.0, 60.0, 12.0, {"drone": 0.95, "cruise": 0.80}, weight_kg=87.0),
    "camm": Effector("CAMM (Land Ceptor)", 3700.0, 130.0, 25.0, {"fighter": 0.90, "cruise": 0.92}, weight_kg=99.0),
    "rbs-70-ng": Effector("RBS 70 NG", 800.0, 20.0, 9.0, {"drone": 0.98, "cruise": 0.60}, weight_kg=25.0, special_logic="unjammable"),
    "stinger": Effector("FIM-92 Stinger", 700.0, 15.0, 5.0, {"drone": 0.90, "loiter": 0.85}, weight_kg=15.0),
    "sm-6": Effector("SM-6 ERAM", 4300.0, 450.0, 240.0, {"ballistic": 0.60, "fighter": 0.95, "cruise": 0.95}, weight_kg=1500.0),
    "sm-2": Effector("SM-2 Block IV", 3500.0, 250.0, 160.0, {"fighter": 0.85, "cruise": 0.85}, weight_kg=700.0),
    "sea-sparrow": Effector("RIM-162 ESSM", 4900.0, 150.0, 50.0, {"cruise": 0.92, "drone": 0.85}, weight_kg=280.0),
    "aster-15": Effector("Aster 15", 3500.0, 180.0, 30.0, {"cruise": 0.90, "drone": 0.88}, weight_kg=310.0),
    "phalanx": Effector("Phalanx CIWS", 1100.0, 5.0, 1.5, {"cruise": 0.40, "drone": 0.70}, weight_kg=6000.0, special_logic="point-defense-gun"),
    "skynex": Effector("Oerlikon Skynex (35mm)", 1000.0, 2.0, 4.0, {"drone": 0.99, "cruise": 0.30}, weight_kg=4000.0, special_logic="point-defense-gun"),
    "saab-nimbrix": Effector("Saab Nimbrix", 600.0, 20.0, 5.0, {"drone": 0.98}, weight_kg=12.0, special_logic="soft-kill-unjammable"),
    "coyote-b3": Effector("RTX Coyote Block 3", 800.0, 15.0, 15.0, {"drone": 0.96}, weight_kg=15.0),
    "helws": Effector("HELWS (Laser)", 300000.0, 0.5, 3.0, {"drone": 0.90}, weight_kg=1000.0, special_logic="soft-kill-unjammable"),
    "lids-ew": Effector("LIDS EW Jammer", 300000.0, 0.1, 8.0, {"drone": 0.85}, weight_kg=200.0, special_logic="soft-kill-unjammable")
}

def load_battlefield_state(filepath) -> GameState:
    mode = os.getenv("SAAB_MODE", "sweden")
    bases = []
    try:
        if os.path.exists(filepath):
            with open(filepath, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    valid_subtypes = ['air_base', 'capital', 'major_city', 'naval_base']
                    if row['subtype'] in valid_subtypes:
                        name = row['feature_name']
                        subtype = row['subtype']
                        # Standardized Baseline
                        inv = {"patriot-pac3": 32, "nasams": 64, "saab-nimbrix": 500}
                        base_sensors = []
                        if subtype == "air_base": base_sensors.append(SENSORS["giraffe-4a"])
                        elif subtype == "capital": base_sensors.append(SENSORS["an-mpq-65"])
                        bases.append(Base(name, float(row['x_km']), float(row['y_km']), inv, subtype=subtype, sensors=base_sensors))
    except Exception as e:
        print(f"[ERROR] CSV Load Error: {e}")
    
    # --- SUPREME 24 SETTLED INVENTORIES ---
    assets = []
    carrier_x, carrier_y = 100.0, 400.0
    csg_carrier = Base("HMS-VICTORIOUS", carrier_x, carrier_y, 
                       {
                           "meteor": 120, "iris-t-air": 60, "aim-9x": 60,
                           "sea-sparrow": 64, "aster-15": 32, "phalanx": 1000
                       }, 
                       subtype="carrier", is_mobile=True, speed_kmh=55.0)
    
    csg_destroyer = Base("DDG-102-AEGIS", carrier_x + 15.0, carrier_y - 10.0,
                         {
                             "sm-6": 96, "sm-2": 48, "sea-sparrow": 32, "phalanx": 500
                         },
                         subtype="destroyer", is_mobile=True, speed_kmh=60.0,
                         sensors=[SENSORS["an-spy-6"]])
    
    air_hub = Base("SAVENAS-AIRBASE", 150.0, 150.0,
                   {
                       "patriot-pac3": 32, "patriot-pac2": 16, "nasams": 24,
                       "iris-t-slm": 16, "skynex": 8, "saab-nimbrix": 200
                   },
                   subtype="air_base")
    
    capital_shield = Base("STOCKHOLM-HUB", 0.0, 0.0,
                          {
                              "thaad": 12, "patriot-pac3": 64, "nasams": 32,
                              "iris-t-sls": 48, "rbs-70-ng": 100, "helws": 4, "lids-ew": 2
                          },
                          subtype="capital")

    space_ops = Base("SPACE-OPS-NORDIC", 450.0, 450.0, 
                     {"stinger": 20, "skynex": 2}, 
                     subtype="hva", sensors=[SENSORS["sbirs-ir"]])
    
    frontier = Base("NORTHERN-VANGUARD", 400, 300, 
                    {
                        "samp-t": 16, "camm": 32, "coyote-b3": 100, "skynex": 4
                    }, 
                    subtype="ground_base")

    bases.extend([csg_carrier, csg_destroyer, air_hub, capital_shield, space_ops, frontier])

    if mode == "sweden":
        assets.append(AirborneAsset("S102", "GLOBALEYE-1", "awacs", 200.0, 300.0, coverage_radius_km=450.0, fuel_max=15000, sensors=[SENSORS["erieye-awacs"]]))
        assets.append(AirborneAsset("N01", "GRIPEN-SEA-1", "fighter", carrier_x, carrier_y, 
                                     weapon_inventory={"meteor": 4, "iris-t-air": 2, "aim-9x": 2}, fuel_max=3400, sensors=[SENSORS["ps-05a"]]))
        assets.append(AirborneAsset("N02", "GRIPEN-SEA-2", "fighter", carrier_x, carrier_y, 
                                     weapon_inventory={"meteor": 6, "iris-t-air": 2}, fuel_max=3400, sensors=[SENSORS["ps-05a"]]))
        assets.append(AirborneAsset("G01", "GRIPEN-E-1", "fighter", 150.0, 150.0, 
                                     weapon_inventory={"meteor": 4, "aim-120d": 2, "aim-9x": 2}, fuel_max=3400, sensors=[SENSORS["ps-05a"]]))
    else:
        assets.append(AirborneAsset("A-01", "ORACLE-EYE", "awacs", 500.0, 400.0, coverage_radius_km=350.0, fuel_max=90000))

    return GameState(bases=bases, assets=assets)