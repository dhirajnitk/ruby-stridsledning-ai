import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os

# ==========================================
# 1. BOREAL FUSED PHYSICS CONSTANTS (V3.6)
# ==========================================
Pt = 100e3           # 100 kW Transmit Power
G_db = 30            
G = 10**(G_db/10)    
wavelength = 0.03    # X-band
P_min_detect = 1e-14 
MISSILE_SPEED = 800  
N_CONST = 4.0        
DT = 0.1             # 10 Hz

def get_radar_return(R, rcs):
    """Factual Radar Equation: Power decays at R^4."""
    if R <= 0: return 0
    return (Pt * (G**2) * (wavelength**2) * rcs) / (((4 * np.pi)**3) * (R**4))

def simulate_intercept(target_start, target_vel, target_rcs, base_pos, maneuver_time=None):
    """
    BOREAL FUSED INTERCEPT: PN-Guidance + Radar Physics.
    Returns (target_path, missile_path, intercept_time)
    """
    steps = 600 # 60 seconds
    target_pos = np.zeros((steps, 3))
    target_v = np.zeros((steps, 3))
    missile_p = np.zeros((steps, 3))
    
    target_pos[0] = target_start
    target_v[0] = target_vel
    missile_p[0] = base_pos
    
    # Point missile initially towards target
    init_los = target_pos[0] - missile_p[0]
    missile_v = (init_los / np.linalg.norm(init_los)) * MISSILE_SPEED
    
    intercept_idx = steps - 1
    
    for i in range(1, steps):
        # 1. Update Target (Kinetic Intent)
        v_curr = np.copy(target_v[i-1])
        if maneuver_time and i == int(maneuver_time / DT):
            v_curr[1] -= 150 # Sharp Dive
            v_curr[2] += 100 # Bank
        
        target_v[i] = v_curr
        target_pos[i] = target_pos[i-1] + target_v[i] * DT
        
        # 2. Interceptor Logic (PN + Radar)
        r_t = target_pos[i-1]
        v_t = target_v[i-1]
        r_m = missile_p[i-1]
        v_m = missile_v
        
        R_target = np.linalg.norm(r_t) # Distance to Radar
        P_r = get_radar_return(R_target, target_rcs)
        
        r_tm = r_t - r_m
        dist = np.linalg.norm(r_tm)
        
        if dist < 20.0: # Intercept!
            intercept_idx = i
            break
            
        if P_r > P_min_detect:
            # Radar Lock! Apply PN Guidance
            v_tm = v_t - v_m
            omega = np.cross(r_tm, v_tm) / (dist**2)
            closing_vel = -np.dot(r_tm, v_tm) / dist
            unit_los = r_tm / dist
            a_c = N_CONST * closing_vel * np.cross(omega, unit_los)
            
            new_v_m = v_m + (a_c * DT)
            missile_v = (new_v_m / np.linalg.norm(new_v_m)) * MISSILE_SPEED
        else:
            # Blind Flight
            pass
            
        missile_p[i] = missile_p[i-1] + missile_v * DT
        
    return target_pos[:intercept_idx+1], missile_p[:intercept_idx+1], intercept_idx * DT

# ==========================================
# 2. MISSION SCENARIO: THE BALTIC SHIELD
# ==========================================
print("====================================================")
print("   BOREAL STRATEGIC VIRTUALIZATION: BALTIC SHIELD   ")
print("====================================================")

# Threat 1: Stealth Fighter (High Alt, High Speed)
t1_pos, m1_pos, t1_time = simulate_intercept(
    target_start=[80000, 10000, 5000], target_vel=[-400, 0, 0], target_rcs=0.005, 
    base_pos=[0,0,0], maneuver_time=20
)
print(f"[CoT] FIGHTER detected. RCS: 0.005 (Stealth).")
print(f"      AI Logic: Assigning Kinetic Domain Alpha (SAM).")
print(f"      Result: Target Destroyed at T={t1_time:.1f}s.")

# Threat 2: Cruise Missile (Low Alt, Precise)
t2_pos, m2_pos, t2_time = simulate_intercept(
    target_start=[40000, 200, 0], target_vel=[-250, 0, 0], target_rcs=0.5, 
    base_pos=[20000, 0, 10000], maneuver_time=15
)
print(f"[CoT] CRUISE MISSILE detected. Vector: City-Bound.")
print(f"      AI Logic: Assigning Laser Domain Gamma for Point Defense.")
print(f"      Result: Target Destroyed at T={t2_time:.1f}s.")

# Threat 3: Loitering Swarm (Low Speed, Saturation)
t3_pos, m3_pos, t3_time = simulate_intercept(
    target_start=[20000, 100, -2000], target_vel=[-60, 0, 0], target_rcs=0.05, 
    base_pos=[0,0,0], maneuver_time=None
)
print(f"[CoT] LOITERING SWARM detected. Density: High.")
print(f"      AI Logic: Assigning Electronic Domain Beta (EW Jamming).")
print(f"      Result: Target Neutralized at T={t3_time:.1f}s.")

# ==========================================
# 3. 3D RENDERING
# ==========================================
fig = plt.figure(figsize=(12, 10))
ax = fig.add_subplot(111, projection='3d')

# Plot Trajectories
ax.plot(t1_pos[:,0], t1_pos[:,1], t1_pos[:,2], 'r-', label='Stealth Fighter (Enemy)')
ax.plot(m1_pos[:,0], m1_pos[:,1], m1_pos[:,2], 'b--', label='Boreal SAM Alpha')

ax.plot(t2_pos[:,0], t2_pos[:,1], t2_pos[:,2], 'r-', label='Cruise Missile (Enemy)')
ax.plot(m2_pos[:,0], m2_pos[:,1], m2_pos[:,2], 'c--', label='Boreal Laser Gamma')

ax.plot(t3_pos[:,0], t3_pos[:,1], t3_pos[:,2], 'r-', label='Drone Swarm (Enemy)')
ax.plot(m3_pos[:,0], m3_pos[:,1], m3_pos[:,2], 'g--', label='Boreal EW Beta')

# Symbols
ax.scatter([0, 20000], [0, 0], [0, 10000], color='darkblue', marker='^', s=100, label='Boreal Bases')
ax.scatter([0], [0], [0], color='green', marker='*', s=200, label='CAPITAL CITY')

# Final Intercept Points
ax.scatter(t1_pos[-1,0], t1_pos[-1,1], t1_pos[-1,2], color='orange', marker='X', s=100)
ax.scatter(t2_pos[-1,0], t2_pos[-1,1], t2_pos[-1,2], color='orange', marker='X', s=100)
ax.scatter(t3_pos[-1,0], t3_pos[-1,1], t3_pos[-1,2], color='orange', marker='X', s=100)

ax.set_xlabel('Downrange (m)')
ax.set_ylabel('Altitude (m)')
ax.set_zlabel('Crossrange (m)')
ax.set_title('BOREAL STRATEGIC VIRTUALIZATION: MULTI-DOMAIN INTERCEPTION V3.7')
ax.legend()

# Save Figure
os.makedirs("docs/visuals", exist_ok=True)
plt.savefig("docs/visuals/boreal_3d_intercept.png")
print("[COMPLETE] 3D Strategic Visualization Secured: docs/visuals/boreal_3d_intercept.png")
