import numpy as np
import os
import random
import time
import json
import multiprocessing
from core.engine import evaluate_threats_advanced, extract_rl_features
from core.models import Threat, load_battlefield_state, CSV_FILE_PATH

# --- CONFIGURATION ---
TOTAL_SAMPLES = 2000 
BATCH_SIZE = 50
NUM_WORKERS = 2 
OUTPUT_DIR = "data/training/strategic_mega_corpus"
REAL_DATA_PATH = "data/raw/real_baltic_traffic.json"

# --- RADAR & ENGAGEMENT CONSTANTS (HARVESTED FROM TECHNICAL INTEL) ---
Pt = 100e3           # Transmitted power: 100 kW
G_db = 30            # Antenna gain in dB
G = 10**(G_db/10)    # Linear antenna gain
freq = 10e9          # Frequency: X-band (10 GHz)
c = 3e8              
wavelength = c / freq
P_min_detect = 1e-14 # Minimum Received Power threshold for a "Lock" (Watts)
MISSILE_SPEED = 800  # 800 m/s (approx Mach 2.3)
N_CONST = 4.0        # Proportional Navigation Constant

def get_radar_return(R, rcs):
    """Calculates received power using the standard Radar Equation (R^4 decay)."""
    if R <= 0: return 0
    return (Pt * (G**2) * (wavelength**2) * rcs) / (((4 * np.pi)**3) * (R**4))

def run_oracle_intercept(target_trajectory, rcs, dt=0.1):
    """
    BOREAL FUSED ORACLE: High-Fidelity PN Interceptor Simulator.
    Fuses Radar Lock Physics with Vectorized Guidance Laws.
    """
    missile_pos = np.array([0.0, 0.0, 0.0]) # Launch Site
    # Point missile initially towards target's starting position
    init_los = target_trajectory[0, 0:3] - missile_pos
    missile_vel = (init_los / np.linalg.norm(init_los)) * MISSILE_SPEED
    
    steps = len(target_trajectory)
    for i in range(1, steps):
        # Target State
        r_t = target_trajectory[i-1, 0:3]
        v_t = target_trajectory[i-1, 3:6]
        # Missile State
        r_m = missile_pos
        v_m = missile_vel
        
        # 1. Radar Lock Check (Factual Physics)
        R_target = np.linalg.norm(r_t)
        P_r = get_radar_return(R_target, rcs)
        
        # 2. Distance and Intercept Check
        r_tm = r_t - r_m
        dist = np.linalg.norm(r_tm)
        if dist < 20.0: # Intercept Success (20m proximity)
            return 1.0 # DESTROYED
            
        # 3. Guidance Logic (Proportional Navigation)
        if P_r > P_min_detect:
            # We have Radar Lock -> Apply PN Guidance
            v_tm = v_t - v_m # Relative velocity
            
            # Omega (LOS Rotation) = (r_tm X v_tm) / R^2
            omega = np.cross(r_tm, v_tm) / (dist**2)
            
            # a_c (Commanded Accel) = N * V_closing * (Omega X Unit_LOS)
            closing_vel = -np.dot(r_tm, v_tm) / dist
            unit_los = r_tm / dist
            a_c = N_CONST * closing_vel * np.cross(omega, unit_los)
            
            # Update missile velocity
            new_v_m = v_m + (a_c * dt)
            missile_vel = (new_v_m / np.linalg.norm(new_v_m)) * MISSILE_SPEED
        else:
            # Radar Lock Lost -> Fly blind (maintain previous velocity)
            pass
            
        # Update missile position
        missile_pos = missile_pos + missile_vel * dt
        
    return 0.0 # FAILED/EVADED

def load_real_clutter():
    if os.path.exists(REAL_DATA_PATH):
        with open(REAL_DATA_PATH, "r") as f:
            return json.load(f)
    return []

def generate_fused_scenario(real_clutter_pool):
    # OPERATIONAL THREAT PROFILES: Fighters, Cruise Missiles, Loitering Munitions
    mode = os.getenv("CONFLICT_MODE", "standard")
    threats = []
    
    # 1. PROFILE: FIGHTER AIRCRAFT (4th Gen & Stealth)
    num_air = random.randint(5, 10)
    for i in range(num_air):
        is_stealth = random.random() < 0.3
        threats.append(Threat(
            id=f"FIGHTER-{i}", x=random.uniform(50000, 80000), y=random.uniform(5000, 15000),
            speed_kmh=random.randint(1200, 2500), heading="Sustained",
            estimated_type="stealth-fighter" if is_stealth else "4th-gen-fighter", 
            threat_value=400 
        ))
        
    # 2. PROFILE: LOITERING MUNITIONS (Swarms)
    num_loiter = random.randint(20, 50)
    for i in range(num_loiter):
        threats.append(Threat(
            id=f"LOITER-{i}", x=random.uniform(20000, 40000), y=random.uniform(50, 500),
            speed_kmh=random.randint(150, 250), heading="Saturation",
            estimated_type="loitering-munition", threat_value=50 
        ))
        
    # 3. PROFILE: CRUISE MISSILES (Subsonic Precision)
    num_cruise = random.randint(10, 20)
    for i in range(num_cruise):
        threats.append(Threat(
            id=f"CRUISE-{i}", x=random.uniform(40000, 100000), y=random.uniform(100, 1000),
            speed_kmh=900, heading="Precision Strike",
            estimated_type="cruise-missile", threat_value=250
        ))
        
    # 4. PROFILE: HYPERSONIC / PGM
    num_pgm = random.randint(5, 10)
    for i in range(num_pgm):
        threats.append(Threat(
            id=f"HYPER-{i}", x=random.uniform(80000, 150000), y=random.uniform(30000, 80000),
            speed_kmh=random.randint(5000, 15000), heading="Terminal Impact",
            estimated_type="hypersonic-pgm", threat_value=500
        ))

    # Global Clutter Fusion (OpenSky)
    if real_clutter_pool:
        num_clutter = random.randint(5, 15)
        clutter_samples = random.sample(real_clutter_pool, min(len(real_clutter_pool), num_clutter))
        for i, c in enumerate(clutter_samples):
            rel_x = (c['lon'] - 18.07) * 111.0 + 80000 # Offset to theater edge
            rel_y = (c['lat'] - 59.33) * 111.0 + 10000
            threats.append(Threat(
                id=f"CIV-{i}", x=rel_x, y=rel_y,
                speed_kmh=c.get('speed', 800), heading="Civ Traffic",
                estimated_type="civilian", threat_value=0
            ))
    return threats

    if real_clutter_pool:
        num_clutter = random.randint(10, 20) if era != "standard" else random.randint(3, 8)
        clutter_samples = random.sample(real_clutter_pool, min(len(real_clutter_pool), num_clutter))
        for i, c in enumerate(clutter_samples):
            rel_x = (c['lon'] - 18.07) * 111.0 + 800
            rel_y = (c['lat'] - 59.33) * 111.0 + 400
            threats.append(Threat(
                id=f"CIV-{i}", x=rel_x, y=rel_y,
                speed_kmh=c.get('speed', 800), heading="Civ Traffic",
                estimated_type="civilian", threat_value=0
            ))
    return threats

def worker_task(batch_id, batch_size, base_state, real_clutter_pool):
    samples = []
    for _ in range(batch_size):
        threats = generate_fused_scenario(real_clutter_pool)
        weather = random.choice(["clear", "fog", "storm"])
        primary = random.choice(["balanced", "fortress", "aggressive"])
        blend = random.uniform(0.1, 0.9)
        
        score, details, _ = evaluate_threats_advanced(
            base_state, threats, mcts_iterations=100, # Distilled Fidelity for Sprint
            weather=weather, doctrine_primary=primary, doctrine_blend=blend, use_rl=False
        )
        features = extract_rl_features(base_state, threats, weather, primary, blend, for_value=True)
        # Mock weights for synthetic generation
        mock_weights = [0.33] * 11
        samples.append({
            "features": features,
            "score": score,
            "weights": mock_weights
        })
    return samples

def generate_tactical_labels(base_state, threats, weather, primary, blend, max_threats=100):
    """Calculates the Gold Standard assignments using the Oracle Engine."""
    _, details, _ = evaluate_threats_advanced(
        base_state, threats, mcts_iterations=10, 
        weather=weather, doctrine_primary=primary, doctrine_blend=blend, use_rl=False
    )
    assignments = details["tactical_assignments"]
    
    # Pad to [MAX_THREATS, N_Bases * N_Effectors]
    labels = np.zeros((max_threats, 21 * 11))
    
    base_map = {b.name: i for i, b in enumerate(base_state.bases)}
    eff_list = ["lv-103", "e98", "rbs70", "lvkv90", "meteor", "thaad", "pac3", "nasams", "cram", "helws", "aegis"]
    eff_map = {name: i for i, name in enumerate(eff_list)}
    
    for a in assignments:
        t_idx = next((i for i, t in enumerate(threats) if t.id == a["threat_id"]), None)
        if t_idx is not None and t_idx < max_threats:
            b_idx = base_map.get(a["base_name"], 0)
            e_idx = eff_map.get(a["effector"].lower(), 0)
            labels[t_idx, (b_idx * 11) + e_idx] = 1.0
            
    return labels

def generate_temporal_sequence(base_state, real_clutter_pool, seq_len=10):
    threats = generate_fused_scenario(real_clutter_pool)
    weather = random.choice(["clear", "fog", "storm"])
    primary = random.choice(["balanced", "fortress", "aggressive"])
    blend = random.uniform(0.1, 0.9)
    
    sequence = []
    for step in range(seq_len):
        for t in threats:
            t.x -= (t.speed_kmh / 3600.0) * 1.0
            t.y += (random.uniform(-10, 10))
            
        features = extract_rl_features(base_state, threats, weather, primary, blend, for_value=True)
        sequence.append(features)
        
    # Get Oracle Signal and Tactical Labels
    labels = generate_tactical_labels(base_state, threats, weather, primary, blend)
    score, _, _ = evaluate_threats_advanced(base_state, threats, mcts_iterations=100, weather=weather, doctrine_primary=primary, doctrine_blend=blend, use_rl=False)
    
    return {
        "features": np.array(sequence, dtype=np.float32),
        "labels": labels, # NEW: Tactical Truth
        "score": score,
        "weights": [0.33] * 11
    }

def generate_object_tracks(base_state, real_clutter_pool, max_threats=50, seq_len=20):
    # THE 75% FRONTIER: Radar-Guided Kinetic Synthesis
    threats = generate_fused_scenario(real_clutter_pool)
    
    history = []
    labels = []
    
    for t_obj in threats:
        # Assign RCS based on Grounded OSINT (Stealth vs 4th Gen)
        t_obj.rcs = 5.0 if t_obj.estimated_type != "stealth" else 0.005
        t_obj.z = random.uniform(-5000, 5000)
        t_obj.vz = random.uniform(-50, 50)
        
        target_traj = np.zeros((seq_len, 6))
        for step in range(seq_len):
            # Simulate Maneuver DNA (Evasive Dive at Step 10)
            if step == 10 and random.random() < 0.4:
                t_obj.speed_kmh += 1000 # Burn
                t_obj.z += 200 # Hard Bank
                
            t_obj.x -= (t_obj.speed_kmh / 3600.0) * 1000 # Scalar scale for map
            t_obj.y += random.uniform(-10, 10)
            t_obj.z += t_obj.vz
            
            target_traj[step] = [t_obj.x, t_obj.y, t_obj.z, -(t_obj.speed_kmh/3.6), 0, t_obj.vz]
            
        # Oracle Labeling (Using the PN Interceptor)
        is_intercepted = run_oracle_intercept(target_traj, t_obj.rcs)
        labels.append(is_intercepted)
        history.append(target_traj) # (Seq, 6)
        
    # Reformat to (Threats, Seq, Features)
    # Features: [X, Y, Z, Vx, Vy, Vz, Val, RCS, Is_Air, Is_Drone, Is_PGM]
    final_tensor = np.zeros((max_threats, seq_len, 11))
    for i in range(min(len(history), max_threats)):
        final_tensor[i, :, 0:6] = history[i]
        final_tensor[i, :, 6] = threats[i].threat_value
        final_tensor[i, :, 7] = threats[i].rcs
        
        # Explicit Classification Intelligence (One-Hot)
        t_type = threats[i].estimated_type
        if "air" in t_type or "gen" in t_type or "stealth" in t_type:
            final_tensor[i, :, 8] = 1 # AIRCRAFT
        elif "drone" in t_type:
            final_tensor[i, :, 9] = 1 # DRONE
        elif "pgm" in t_type or "hypersonic" in t_type:
            final_tensor[i, :, 10] = 1 # PGM
        
    return {
        "features": final_tensor,
        "score": np.mean(labels) if labels else 0.0, 
        "weights": [0.4, 0.3, 0.3]
    }

def run_mega_factory():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=2000)
    parser.add_argument("--output", type=str, default="data/training/strategic_mega_corpus/boreal_object_level_gold.npz")
    parser.add_argument("--mode", type=str, default="standard")
    parser.add_argument("--format", type=str, default="snapshot") # snapshot, temporal, object-level
    args = parser.parse_args()

    if args.mode == "hard":
        os.environ["HARD_MODE"] = "1"

    print(f"[LAUNCH] MEGA DATA FACTORY (FORMAT: {args.format})", flush=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    base_state = load_battlefield_state(CSV_FILE_PATH)
    real_clutter_pool = load_real_clutter()
    output_path = args.output
    
    start_time = time.time()
    total_collected = 0
    all_features, all_scores, all_weights, all_labels = [], [], [], []
    
    total_needed = args.samples
    
    for i in range(total_needed // BATCH_SIZE):
        for _ in range(BATCH_SIZE):
            if args.format == "object-level":
                s = generate_object_tracks(base_state, real_clutter_pool)
            elif args.format == "temporal":
                s = generate_temporal_sequence(base_state, real_clutter_pool)
            else:
                threats = generate_fused_scenario(real_clutter_pool)
                weather = random.choice(["clear", "fog", "storm"])
                primary = random.choice(["balanced", "fortress", "aggressive"])
                blend = random.uniform(0.1, 0.9)
                score, details, _ = evaluate_threats_advanced(base_state, threats, mcts_iterations=200, weather=weather, doctrine_primary=primary, doctrine_blend=blend, use_rl=False)
                # Features now include theater-aware inventory and effector ranges
                features = extract_rl_features(base_state, threats, weather, primary, blend, for_value=True)
                labels = generate_tactical_labels(base_state, threats, weather, primary, blend)
                s = {"features": features, "score": score, "weights": [0.33]*11, "labels": labels}
            
            all_features.append(s["features"])
            all_scores.append(s["score"])
            all_weights.append(s["weights"])
            if "labels" in s: all_labels.append(s["labels"])
            total_collected += 1
        
        elapsed = time.time() - start_time
        rate = total_collected / elapsed if elapsed > 0 else 0
        eta_min = ((total_needed - total_collected) / rate) / 60.0 if rate > 0 else 0
        
        if total_collected % 100 == 0:
            print(f"[DATA] {total_collected}/{total_needed} | Rate: {rate:.1f} s/sec | ETA: {eta_min:.1f}m", flush=True)
            save_dict = {
                "features": np.array(all_features, dtype=np.float32),
                "scores": np.array(all_scores, dtype=np.float32),
                "weights": np.array(all_weights, dtype=np.float32)
            }
            if all_labels: save_dict["labels"] = np.array(all_labels, dtype=np.float32)
            np.savez_compressed(output_path, **save_dict)

    print(f"[COMPLETE] Saved {total_collected} samples to {output_path}")

if __name__ == "__main__":
    run_mega_factory()
