import math
import random
import numpy as np
import matplotlib.pyplot as plt
import os

# ---------------------------------------------------------
# KINETIC INTERCEPT SIMULATOR: SAM vs MARV
# ---------------------------------------------------------
# This script simulates the actual physics chase between an 
# active homing SAM and a manoeuvring MARV target using 
# Proportional Navigation (PN) guidance.
# ---------------------------------------------------------

def simulate_chase(tx=None, ty=None, destx=None, desty=None, mx=None, my=None, is_marv=False, threat_type='marv', raw=False):
    # Time parameters
    dt = 0.1 # 100ms ticks
    max_time = 90.0 # seconds
    
    # If no coordinates provided, use default curve
    if tx is None:
        scenario = "marv_miss" if is_marv else "ballistic"
        tx, ty = -25000.0, 100000.0
        destx, desty = 15000.0, 0.0
        mx, my = 0.0, 0.0
    elif raw:
        # raw=True: caller passes physical meters directly (e.g. from km * 1000).
        # Re-centre so the interceptor base is at origin so Pro-Nav math stays well-conditioned.
        ox, oy = float(mx), float(my)
        tx = float(tx) - ox;  ty  = float(ty)  - oy
        destx = float(destx) - ox; desty = float(desty) - oy
        mx = 0.0; my = 0.0
    else:
        # Scale frontend units (0-854 X, 0-742 Y) to physical meters
        # 1 unit = 200 meters. Y is inverted (0 is top in UI, 0 is bottom in physics)
        def scale_coord(cx, cy):
            return (float(cx) - 427.0) * 200.0, (742.0 - float(cy)) * 200.0
        
        tx, ty = scale_coord(tx, ty)
        destx, desty = scale_coord(destx, desty)
        mx, my = scale_coord(mx, my)

    # Target (MARV) Initial State
    t_pos = np.array([tx, ty]) 
    t_speed = 3000.0 # m/s (Hypersonic)
    
    target_dest = np.array([destx, desty])
    dir_vec = target_dest - t_pos
    t_heading = math.atan2(dir_vec[1], dir_vec[0])
    t_vel = np.array([t_speed * math.cos(t_heading), t_speed * math.sin(t_heading)])
    
    # MARV / MIRV jink parameters
    # Sinusoidal oscillation produces smooth S-curves clearly visible on kinetic canvas.
    # Amplitude is the peak lateral speed (m/s); period is one full oscillation (seconds).
    trigger_range = 120000.0

    if threat_type == 'mirv':
        jink_magnitude = 520.0   # m/s lateral amplitude — busier warhead spread pattern
        max_g = 38.0
        trigger_range = 150000.0 # bus separates earlier → jink starts sooner
        jink_period = 2.2        # faster oscillation (multi-warhead chaos)
    elif is_marv:
        jink_magnitude = 750.0   # m/s — produces ~380m S-curve amplitude at 180km range
        max_g = 42.0             # PAC-3 MSE: 42G gives dramatic curved pursuit arc
        jink_period = 3.8        # one full S visible through most of canvas height
    else:
        jink_magnitude = 0.0     # ballistic: no jink — straight line
        max_g = 35.0
        jink_period = 3.8

    # Perpendicular to base heading (constant — jink is always lateral, not along track)
    perp_x = -math.sin(t_heading)
    perp_y =  math.cos(t_heading)
    jink_t = 0.0  # time accumulator for sinusoidal phase
    
    # Interceptor (SAM)
    m_pos = np.array([mx, my]) 
    m_speed = 1000.0 # Initial boost speed
    
    # Point interceptor roughly at the target's initial position
    m_dir_vec = t_pos - m_pos
    m_heading = math.atan2(m_dir_vec[1], m_dir_vec[0])
    
    # Introduce an initial off-boresight launch angle so the missile curves.
    # Proportional Navigation will smoothly correct this over the flight path,
    # demonstrating the kinematic chase visually.
    m_heading += math.radians(25)
    
    m_vel = np.array([m_speed * math.cos(m_heading), m_speed * math.sin(m_heading)])
    
    # Guidance Parameters
    N = 4.0 # Proportional Navigation Constant
    g_accel = 9.81
    
    # Tracking logs
    t_history = [t_pos.copy()]
    m_history = [m_pos.copy()]
    
    intercepted = False
    miss_distance = float('inf')
    
    for step in range(int(max_time / dt)):
        # 1. Target Movement Logic
        dist_to_target = np.linalg.norm(t_pos)
        
        if is_marv and dist_to_target < trigger_range:
            jink_t += dt
            # Smooth sinusoidal lateral oscillation — creates S-curves visible on canvas
            jink_component = jink_magnitude * math.sin(2 * math.pi * jink_t / jink_period)
            actual_t_vel = t_vel + np.array([perp_x * jink_component, perp_y * jink_component])
        else:
            actual_t_vel = t_vel
            
        t_pos += actual_t_vel * dt
        t_history.append(t_pos.copy())
        
        # 2. SAM Active Homing Logic (Proportional Navigation)
        r_tm = t_pos - m_pos # LOS vector
        dist_tm = np.linalg.norm(r_tm)
        
        if dist_tm < miss_distance:
            miss_distance = dist_tm
            
        if dist_tm < 600.0: # 600m proximity fuse
            intercepted = True
            break
            
        # LOS angle
        lambda_angle = math.atan2(r_tm[1], r_tm[0])
        
        # Relative velocity
        v_rel = actual_t_vel - m_vel
        v_close = -np.dot(v_rel, r_tm) / dist_tm 
        
        # LOS rate of change
        cross_prod = r_tm[0]*v_rel[1] - r_tm[1]*v_rel[0]
        lambda_dot = cross_prod / (dist_tm**2)
        
        # Pro-Nav Acceleration Command
        accel_cmd_mag = N * v_close * lambda_dot
        
        max_accel_ms2 = max_g * g_accel
        accel_cmd_mag = np.clip(accel_cmd_mag, -max_accel_ms2, max_accel_ms2)
        
        # Apply turning acceleration
        m_heading += (accel_cmd_mag / m_speed) * dt
        
        # Booster acceleration
        if m_speed < 2500.0:
            m_speed += 80.0 * dt
            
        m_vel = np.array([m_speed * math.cos(m_heading), m_speed * math.sin(m_heading)])
        m_pos += m_vel * dt
        m_history.append(m_pos.copy())
        
        # Stop if missile overshoots significantly
        if m_pos[1] > t_pos[1] and v_close < -500:
            break
            
    return np.array(t_history), np.array(m_history), intercepted, miss_distance

def generate_visualization():
    import random
    random.seed(42) 
    
    # We don't strictly need to regenerate the static image for the user since 
    # the frontend UI will handle it, but we can update the backend test code just in case.
    pass
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 8))
    
    # Plot Standard
    ax1.plot(t_hist_std[:, 0]/1000, t_hist_std[:, 1]/1000, 'r-', label="Ballistic Threat")
    ax1.plot(m_hist_std[:, 0]/1000, m_hist_std[:, 1]/1000, 'b-', label="SAM Interceptor")
    ax1.scatter(t_hist_std[-1, 0]/1000, t_hist_std[-1, 1]/1000, color='red', marker='x', s=100)
    ax1.set_title(f"Standard Ballistic Intercept\nResult: {'HIT' if hit_std else 'MISS'} (Miss Dist: {miss_std:.1f}m)")
    ax1.set_xlabel("Crossrange (km)")
    ax1.set_ylabel("Altitude / Downrange (km)")
    ax1.grid(True)
    ax1.legend()
    ax1.set_xlim(-15, 15)
    ax1.set_ylim(0, 100)
    
    # Plot MARV
    ax2.plot(t_hist_marv[:, 0]/1000, t_hist_marv[:, 1]/1000, 'r-', label="MARV Threat (Jinking)")
    ax2.plot(m_hist_marv[:, 0]/1000, m_hist_marv[:, 1]/1000, 'b-', label="SAM Interceptor")
    # Mark trigger line
    ax2.axhline(y=40, color='orange', linestyle='--', alpha=0.5, label="MARV Trigger Range")
    
    ax2.scatter(t_hist_marv[-1, 0]/1000, t_hist_marv[-1, 1]/1000, color='red', marker='x', s=100)
    ax2.set_title(f"MARV Jink Intercept\nResult: {'HIT' if hit_marv else 'MISS'} (Miss Dist: {miss_marv:.1f}m)")
    ax2.set_xlabel("Crossrange (km)")
    ax2.set_ylabel("Altitude / Downrange (km)")
    ax2.grid(True)
    ax2.legend()
    ax2.set_xlim(-30, 30)
    ax2.set_ylim(0, 100)
    
    plt.tight_layout()
    output_path = "docs/visuals/marv_interception.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    print(f"Saved interception physics plot to {output_path}")

if __name__ == "__main__":
    generate_visualization()
