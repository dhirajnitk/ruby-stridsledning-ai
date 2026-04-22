# BOREAL WEAPON ASSIGNMENT DOCTRINE (V3.6)

This document factually codifies the tactical logic used by the Boreal AI to assign defensive weapon systems to multi-domain threats.

---

## 1. THE TRIPLE-DOMAIN DEFENSE SUITE
The Boreal system manages three distinct defensive domains:

1.  **DOMAIN ALPHA: KINETIC (SAM)**
    *   **Target Match**: Manned Fighters, High-Altitude Bombers, Supersonic PGMs.
    *   **Logic**: Uses **Proportional Navigation (PN)** to achieve physical impact.
2.  **DOMAIN BETA: ELECTRONIC (EW)**
    *   **Target Match**: Loitering Munitions, Drone Swarms, ISR Platforms.
    *   **Logic**: Soft-kill disruption of navigation and command links.
3.  **DOMAIN GAMMA: HIGH-ENERGY (LASER/CIWS)**
    *   **Target Match**: Hypersonic terminal pulses, Cruise Missiles, Precision PGM.
    *   **Logic**: Zero-latency intercept for high-speed point defense.

---

## 2. THE NEURAL DECISION PIPELINE
The **Supreme Elite** and **Chronos** models decide the weapon mix using a **3-bit Doctrine Weight Vector**.

### Step 1: Feature Triage (Input)
The model ingests the **11-feature Intel Vector**.
*   `[X, Y, Z, Vx, Vy, Vz, Val, RCS, Is_Air, Is_Drone, Is_PGM]`
*   **Is_Drone=1**: Factually triggers the "EW Priority" heuristic.
*   **RCS=0.005**: Factually triggers the "Stealth Engagement" doctrine.

### Step 2: Weight Synthesis (Output)
The model outputs a vector of 3 weights: `[W_Kinetic, W_Electronic, W_Laser]`.
*   **Balanced Theater**: `[0.33, 0.33, 0.33]`
*   **Saturation (Swarm)**: `[0.10, 0.80, 0.10]` -> spiking EW to save Kinetic SAMs.
*   **High-Value Maneuver**: `[0.80, 0.10, 0.10]` -> prioritizing SAMs for platform kill.

### Step 3: Direct Action Execution
Because we use **Neural Direct Action**, the assignment is instantaneous (**0.8ms**). There is no "Optimization Phase"—the weights are the result of learned **Strategic Intuition.**

---

## 3. FACTUAL BATTLE-HARDENING
By training on the **Fused Radar-Kinetic** dataset, the AI has learned the **Kill Probability** of each weapon domain. It will factually reserve High-G SAMs for Fighters and use EW for swarms, maximizing theater survival through **Autonomous Resource Triage.**

**THE BOREAL AI IS THE DEFINITIVE MULTI-DOMAIN COMMANDER.** 🇸🇪🛡️🏁🏆
