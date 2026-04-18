import math
import random
import time
import json
import requests
from models import EFFECTORS

# Boreal Passage Map Constants
CAPITAL_X = 418.3
CAPITAL_Y = 95.0
BLIND_SPOT_X = 656.7
BLIND_SPOT_Y = 493.3
BASE_A_X = 198.3
BASE_A_Y = 335.0
BASE_B_X = 838.3
BASE_B_Y = 75.0

class SimThreat:
    """Represents a dynamic threat moving across the map."""
    def __init__(self, t_id: str, x: float, y: float, speed_kmh: float, estimated_type: str, threat_value: float, target_x: float = CAPITAL_X, target_y: float = CAPITAL_Y):
        self.id = t_id
        self.x = x
        self.y = y
        self.speed_kmh = speed_kmh
        self.estimated_type = estimated_type
        self.threat_value = threat_value
        self.heading = f"Targeting x:{target_x}, y:{target_y}"
        
        # Physics: Calculate velocity vector towards the capital
        # 1 tick = 10 simulated seconds.
        dist_per_tick = (self.speed_kmh / 3600.0) * 10.0
        
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)
        
        if dist > 0:
            self.vx = (dx / dist) * dist_per_tick
            self.vy = (dy / dist) * dist_per_tick
        else:
            self.vx, self.vy = 0.0, 0.0

    def move(self):
        """Updates the position for one tick (10 seconds)."""
        # Add a slight random drift (up to 10% of forward movement) to simulate evasion/turbulence
        drift_mag = (self.speed_kmh / 3600.0) * 10.0 * 0.1
        drift_x = random.uniform(-drift_mag, drift_mag)
        drift_y = random.uniform(-drift_mag, drift_mag)
        
        self.x += self.vx + drift_x
        self.y += self.vy + drift_y
        
    def to_dict(self):
        """Serializes the threat to match the FastAPI IncomingThreat model."""
        return {
            "id": self.id,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "speed_kmh": self.speed_kmh,
            "heading": self.heading,
            "estimated_type": self.estimated_type,
            "threat_value": self.threat_value
        }

class SimulationLoop:
    def __init__(self):
        self.tick_count = 0
        self.threats = []
        self.threat_counter = 1
        self.attack_plan = []
        self.total_damage = 0.0
        self.total_defense_cost = 0.0
        self.weather = random.choice(["Clear", "Clear", "Storm"]) # 33% chance of a storm
        self.destroyed_bases = set()
        self.base_effectors = {
            "Capital": 4,   # 4 SAMs
            "Base A": 14,   # 4 Fighters, 10 Drones
            "Base B": 14    # 4 Fighters, 10 Drones
        }

    def load_attack_plan(self, filepath: str):
        """Loads an LLM-generated JSON attack plan into the timeline."""
        with open(filepath, 'r') as f:
            self.attack_plan = json.load(f)
        print(f"Loaded Red Team Attack Plan with {len(self.attack_plan)} planned threats.")

    def spawn_decoy_wave(self):
        """THE ENEMY AI: Spawns 3 fast, cheap threats at the edges of the map."""
        print(f"[Tick {self.tick_count}] Spawning Decoy Wave...")
        for _ in range(3):
            y_pos = random.uniform(800.0, 1200.0)
            self.threats.append(SimThreat(
                t_id=f"T-DECOY-{self.threat_counter}",
                x=1600.0, # Eastern edge of the map
                y=y_pos,
                speed_kmh=1800.0,
                estimated_type="decoy",
                threat_value=15.0
            ))
            self.threat_counter += 1

    def spawn_blind_spot_ambush(self):
        """THE ENEMY AI: Spawns a high-value threat directly inside the radar blind spot."""
        print(f"[Tick {self.tick_count}] Spawning Blind Spot Ambush!")
        self.threats.append(SimThreat(
            t_id=f"T-BOMBER-{self.threat_counter}",
            x=BLIND_SPOT_X + random.uniform(-10, 10),
            y=BLIND_SPOT_Y + random.uniform(-10, 10),
            speed_kmh=2200.0,
            estimated_type="bomber",
            threat_value=95.0
        ))
        self.threat_counter += 1

    def tick(self):
        """Advances the simulation by one step."""
        self.tick_count += 1
        
        # Check if the LLM attack plan dictates spawning new threats on this tick
        spawned_this_tick = [t for t in self.attack_plan if t.get("spawn_tick") == self.tick_count]
        for t_data in spawned_this_tick:
            print(f"[{self.tick_count}] Spawning LLM Planned Threat: {t_data['id']}")
            self.threats.append(SimThreat(
                t_id=t_data["id"],
                x=t_data["start_x"],
                y=t_data["start_y"],
                speed_kmh=t_data["speed"],
                estimated_type=t_data["type"],
                threat_value=t_data["threat_value"],
                target_x=t_data["target_x"],
                target_y=t_data["target_y"]
            ))
            
        active_threats = []
        for t in self.threats:
            t.move()
            
            # Check for impact with bases (within a 10km radius)
            if math.hypot(t.x - CAPITAL_X, t.y - CAPITAL_Y) <= 10.0:
                self.total_damage += t.threat_value
                print(f"\n{'='*60}")
                print(f"💥💥💥 [CRITICAL IMPACT] {t.id} STRUCK THE CAPITAL! ({t.threat_value} DMG) 💥💥💥")
                if "Capital" not in self.destroyed_bases:
                    self.destroyed_bases.add("Capital")
                    print(f"🚨 CAPITAL DEFENSES DESTROYED! {self.base_effectors['Capital']} effectors lost in the blast! 🚨")
                    self.base_effectors["Capital"] = 0
                print(f"{'='*60}\n")
            elif math.hypot(t.x - BASE_A_X, t.y - BASE_A_Y) <= 10.0:
                self.total_damage += t.threat_value
                print(f"\n{'='*60}")
                print(f"💥 [IMPACT] {t.id} struck Coastal Base A! ({t.threat_value} DMG) 💥")
                if "Base A" not in self.destroyed_bases:
                    self.destroyed_bases.add("Base A")
                    print(f"🚨 BASE DESTROYED! {self.base_effectors['Base A']} effectors lost in the blast! 🚨")
                    self.base_effectors["Base A"] = 0
                print(f"{'='*60}\n")
            elif math.hypot(t.x - BASE_B_X, t.y - BASE_B_Y) <= 10.0:
                self.total_damage += t.threat_value
                print(f"\n{'='*60}")
                print(f"💥 [IMPACT] {t.id} struck Inland Base B! ({t.threat_value} DMG) 💥")
                if "Base B" not in self.destroyed_bases:
                    self.destroyed_bases.add("Base B")
                    print(f"🚨 BASE DESTROYED! {self.base_effectors['Base B']} effectors lost in the blast! 🚨")
                    self.base_effectors["Base B"] = 0
                print(f"{'='*60}\n")
            else:
                active_threats.append(t)
        self.threats = active_threats
            
    def get_active_threats_payload(self):
        return [t.to_dict() for t in self.threats]

    def visualize_blast_zone(self, center_t, splash_threats, radius=15.0):
        """Prints an ASCII grid showing the SAM blast radius and caught threats."""
        print(f"\n[TACTICAL GRID] SAM Detonation at X:{center_t.x:.1f}, Y:{center_t.y:.1f}")
        grid_w, grid_h = 30, 15
        window_size = radius * 1.5 # Show an area slightly larger than the blast radius
        
        for y in range(grid_h):
            row_str = ""
            cell_y = center_t.y + window_size - (y / (grid_h - 1)) * (2 * window_size)
            for x in range(grid_w):
                cell_x = center_t.x - window_size + (x / (grid_w - 1)) * (2 * window_size)
                dist = math.hypot(cell_x - center_t.x, cell_y - center_t.y)
                
                char = "."
                if dist <= radius:
                    char = "░"
                
                tol_x, tol_y = (2 * window_size) / grid_w, (2 * window_size) / grid_h
                if abs(cell_x - center_t.x) <= tol_x/2 and abs(cell_y - center_t.y) <= tol_y/2:
                    char = "X"
                elif any(abs(cell_x - st.x) <= tol_x/2 and abs(cell_y - st.y) <= tol_y/2 for st in splash_threats):
                    char = "S"
                row_str += char * 2 # Double width to account for terminal character aspect ratio
            print(row_str)
        print("Legend: [X] Primary Target  [S] Splash Victim  [░] 15km Blast Zone\n")

if __name__ == "__main__":
    # --- TEST CODE ---
    sim = SimulationLoop()
    
    # 1. Load the LLM Red Team Plan
    sim.load_attack_plan("red_team_plan.json")
    
    # Fast forward the simulation timeline to Tick 40 (When the ambush triggers)
    for _ in range(40): 
        sim.tick()
    
    payload = sim.get_active_threats_payload()
    
    print(f"\n--- CURRENT WORLD STATE (TICK {sim.tick_count}) ---")
    print(json.dumps(payload, indent=2))
    
    print(f"\n--- WEATHER CONDITIONS: {sim.weather.upper()} ---")
    
    print("\n--- SENDING TO BOREAL CHESSMASTER API ---")
    try:
        # POST the data to your FastAPI backend, including the weather query parameter
        api_url = f"http://localhost:8000/api/evaluate-threats?weather={sim.weather.lower()}"
        response = requests.post(
            api_url,
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print("\nAPI Response (Tactical Plan & LLM SITREP):")
            print(json.dumps(data, indent=2))
            
            # Remove intercepted threats from the map and calculate interceptor costs
            if "tactical_assignments" in data:
                assigned_ids = [a["threat_id"] for a in data["tactical_assignments"]]
                splash_destroyed_ids = []
                
                for assignment in data["tactical_assignments"]:
                    if assignment["effector"] == "SAM":
                        target_threat = next((t for t in sim.threats if t.id == assignment["threat_id"]), None)
                        if target_threat:
                            victims = []
                            for other_t in sim.threats:
                                if other_t.id not in assigned_ids and other_t.id not in splash_destroyed_ids:
                                    if math.hypot(other_t.x - target_threat.x, other_t.y - target_threat.y) <= 15.0:
                                        print(f"💥 [SPLASH DAMAGE] {other_t.id} caught in SAM blast targeting {assignment['threat_id']}!")
                                        splash_destroyed_ids.append(other_t.id)
                                        victims.append(other_t)
                            
                            if victims:
                                sim.visualize_blast_zone(target_threat, victims)
                
                all_destroyed_ids = set(assigned_ids + splash_destroyed_ids)
                sim.threats = [t for t in sim.threats if t.id not in all_destroyed_ids]
                
                for assignment in data["tactical_assignments"]:
                    eff_name = assignment["effector"]
                    base_name = assignment["base"]
                    
                    # Deduct fired weapons from the local pool
                    if "Capital" in base_name:
                        sim.base_effectors["Capital"] = max(0, sim.base_effectors["Capital"] - 1)
                    elif "Northern" in base_name:
                        sim.base_effectors["Base A"] = max(0, sim.base_effectors["Base A"] - 1)
                    elif "Highridge" in base_name:
                        sim.base_effectors["Base B"] = max(0, sim.base_effectors["Base B"] - 1)
                        
                    if eff_name in EFFECTORS:
                        sim.total_defense_cost += EFFECTORS[eff_name].cost_weight
        else:
            print(f"API Error {response.status_code}: {response.text}")
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Failed to connect to API. Please make sure agent_backend.py is running in another terminal.")

    print("\n--- CONTINUING SIMULATION TO RESOLUTION ---")
    max_spawn_tick = max([t.get("spawn_tick", 0) for t in sim.attack_plan]) if sim.attack_plan else 0
    while sim.threats or sim.tick_count <= max_spawn_tick:
        sim.tick()
        
    print("\n" + "="*50)
    print("====== GAME OVER ======")
    print("="*50)
    print(f"Total Damage Dealt by Red Team : {sim.total_damage}")
    print(f"Total Interceptor Cost         : {sim.total_defense_cost}")
    print(f"Operational Efficiency Score   : -{sim.total_damage + sim.total_defense_cost}")
    print("="*50)