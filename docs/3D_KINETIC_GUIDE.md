# Boreal Kinetic 3D: Tactical Simulation Guide

## 1. Overview
The Boreal Kinetic 3D suite (`kinetic_3d.html`) is a high-fidelity visualizer that bridges the gap between the heuristic engine and the neural truth. It uses **Three.js** to render real-time engagements across both the Sweden and Boreal theaters.

## 2. Kinematics & Physics Engine
Unlike standard animations, Boreal 3D uses the same guidance laws found in `src/mega_data_factory.py`:

### **A. Interceptor Guidance (Proportional Navigation)**
The SAM interceptors utilize **Proportional Navigation (PN)** with a constant $N=4.0$. 
*   **Vectorized LOS Rate**: The missile calculates the rotation of the Line-of-Sight vector.
*   **Commanded Acceleration**: The interceptor "pulls lead" to impact the threat at the projected future position, rather than chasing the tail.
*   **Speed**: Fixed at **800 m/s** (Mach 2.3).

### **B. Threat Profiles**
*   **Hypersonic (Yellow)**: Performs high-altitude glides followed by a terminal ballistic dive. High RCS signature.
*   **Cruise (Red)**: Maintains low-altitude terrain following.
*   **Loitering (Purple)**: Slow, erratic "Swarm" patterns.
*   **Ballistic (Orange)**: High-altitude arc with extreme terminal velocity.

## 3. UI Controls
*   **Fire Demo**: Launches a single chosen weapon vs a random base.
*   **Saturation Wave**: Simulates a "Worst Case" scenario (5+ concurrent vectors).
*   **Theater Switcher**: Adaptively updates base coordinates and map geometry (Stockholm vs Arktholm).

## 4. Visual Indicators
*   **Cyan Trail**: SAM Interceptor flight path history.
*   **Weapon Trails**: Color-coded trajectory history (40-point buffer).
*   **Particle Bursts**: 
    *   **White/Cyan**: Successful Kinetic Intercept.
    *   **Red/Orange**: Ground Impact (Defense Breach).
    *   **Expanding Ring**: Ground shockwave simulation.

---
> [!NOTE]
> All 3D coordinates are scaled at **1:1000** for visualization stability, while kinematics calculations are performed in true SI units (m/s) to maintain fidelity with the **Boreal Oracle** dataset.
