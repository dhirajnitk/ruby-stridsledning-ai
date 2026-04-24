# BOREAL WEAPON ASSIGNMENT DOCTRINE (V4.0)

This document codifies the tactical logic used by the Boreal AI to assign defensive weapon systems to multi-domain threats, including advanced threat classes added in April 2026.

**Last Updated:** 2026-04-24 — Added MARV, MIRV, Dogfight/RTB doctrine

---

## 1. THE TRIPLE-DOMAIN DEFENSE SUITE

The Boreal system manages three distinct defensive domains:

1. **DOMAIN ALPHA: KINETIC (SAM)**
   - **Target Match**: Manned Fighters, High-Altitude Bombers, Supersonic PGMs, MARV, MIRV warheads.
   - **Logic**: Proportional Navigation (PN) guidance to achieve physical impact.

2. **DOMAIN BETA: ELECTRONIC (EW)**
   - **Target Match**: Loitering Munitions, Drone Swarms, ISR Platforms, MARV early-phase (pre-jink).
   - **Logic**: Soft-kill disruption of navigation and command links.

3. **DOMAIN GAMMA: HIGH-ENERGY (LASER/CIWS)**
   - **Target Match**: Hypersonic terminal pulses, Cruise Missiles, Precision PGM.
   - **Logic**: Zero-latency intercept for high-speed point defense.

---

## 2. THE NEURAL DECISION PIPELINE

The **Supreme Elite**, **Chronos**, and **Titan** models decide the weapon mix using a **3-bit Doctrine Weight Vector**.

### Step 1: Feature Triage (Input)
The model ingests the **15-feature Intel Vector** (time-averaged from CHRONOS 60 corpus):

| Index | Feature | Notes |
|---|---|---|
| 0 | Avg Threat Velocity (km/h) | High values flag hypersonic/MARV |
| 1 | Avg Threat Proximity (m) | Closing rate to defended assets |
| 2–5 | Threat Density N/S/E/W | Saturation geometry |
| 6 | Airspace Saturation | Overall ingress volume |
| 7–8 | Capital X/Y Health | Asset survival index |
| 9 | SAM Inventory (total) | Magazine awareness |
| 10 | Active Combat Wings | Friendly air coverage |
| 11 | Electronic Warfare Level | EW jamming density |
| 12 | Detection Confidence | Sensor fusion score |
| 13 | Strategic Attrition | Cumulative loss metric |
| 14 | Combat Urgency | Time-to-impact pressure |

### Step 2: Weight Synthesis (Output)
The model outputs a vector of 3 weights: `[W_Balanced, W_Aggressive, W_Fortress]`.

| Scenario | Weights | Description |
|---|---|---|
| Balanced Theater | `[0.33, 0.33, 0.33]` | Default |
| Saturation Swarm | `[0.10, 0.80, 0.10]` | Spike EW to save SAM rounds |
| High-Value Maneuver | `[0.80, 0.10, 0.10]` | Prioritise SAMs for platform kill |
| MIRV Assault | `[0.90, 0.05, 0.05]` | Maximum SAMs — pre-release intercept priority |

---

## 3. ADVANCED THREAT DOCTRINE (NEW IN V4.0)

### 3.1 MARV — Maneuvering Re-entry Vehicle
- **Characteristics**: Lateral jink manoeuvre activates within 80 km of target, reducing effective Pk by 45%.
- **Engine flag**: `is_marv=True`, `marv_pk_penalty=0.55`, `marv_trigger_range_km=80`
- **Utility boost**: `_calculate_utility()` awards +600 utility when intercepting outside jink range (midcourse), where Pk is still nominal. Inside jink range, Pk × 0.55 is used to compute degraded utility (+400).
- **Doctrine**: Engage MARV before 80 km. Use high-Pk long-range interceptors (THAAD, PAC-3) not short-range IRIS-T.

### 3.2 MIRV — Multiple Independently Targetable Re-entry Vehicles
- **Characteristics**: Bus carries `mirv_count` (default 3) warheads, released at `mirv_release_range_km` (default 150 km) from target. Each warhead independently targets a different defended asset.
- **Engine flag**: `is_mirv=True`, `mirv_count=3`, `mirv_release_range_km=150`
- **Utility boost**: Pre-release interception of bus awards `800 × mirv_count` utility (killing bus destroys all warheads). Post-release: bus is inert, each warhead is a separate BALLISTIC threat.
- **Doctrine**: Commit long-range interceptors (THAAD) to MIRV bus before 150 km. Do not wait for terminal phase.

### 3.3 Dogfight / RTB — Enemy Fighter Aircraft
- **Characteristics**: When a hostile fighter is intercepted by a friendly SAM, it engages in Within Visual Range (WVR) dogfight. Outcome is stochastic: KILL (we destroy it), RTB (enemy breaks off), ENEMY_WIN (our interceptor is lost).
- **Engine flag**: `can_dogfight=True`, `dogfight_win_prob=0.30–0.50`, `can_rtb=True`
- **Utility function**: Prefers long-range effectors (Meteor NEZ range 150 km) to fire before the merge. Range bonus = `min(range_km/100, 5) × 200 × (1 - dogfight_win_prob)`.
- **Doctrine**: Use Meteor BVR first to force RTB or kill before merge. Reserve NASAMS for backup. Never commit IRIS-T to a dogfight-capable fighter unless cornered.

---

## 4. EFFECTOR PRIORITY MATRIX

| Threat Type | Primary Effector | Secondary | Notes |
|---|---|---|---|
| CRUISE MISSILE | NASAMS | PATRIOT PAC-3 | Multi-shot salvo |
| HYPERSONIC | THAAD | — | Time-critical; THAAD only |
| BALLISTIC | THAAD / PAC-3 | — | Salvo ratio 2:1 |
| LOITERING/DRONE | NIMBRIX EW | COYOTE B2 | Soft-kill first |
| MARV (midcourse) | THAAD | PAC-3 | Before jink activation |
| MARV (terminal) | PAC-3 | — | Degraded Pk; all shots |
| MIRV BUS | THAAD | — | Pre-release; single kill = all saved |
| MIRV WARHEAD | PAC-3 × 3 | NASAMS | One per warhead post-release |
| FIGHTER | Meteor | NASAMS | BVR first; avoid dogfight |
| FIGHTER (merged) | NASAMS | IRIS-T | Fallback only |

---

## 5. NEURAL DIRECT ACTION

Because we use **Neural Direct Action**, the assignment is instantaneous (**0.8 ms**). There is no "Optimisation Phase" — the weights are the result of learned **Strategic Intuition** from 200 × 10-timestep training scenarios in the CHRONOS 60 corpus.

**BOREAL AI IS THE DEFINITIVE MULTI-DOMAIN COMMANDER — NOW WITH MARV/MIRV/DOGFIGHT DOCTRINE.** 🇸🇪🛡️

