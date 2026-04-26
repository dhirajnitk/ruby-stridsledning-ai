# Strategic Kinetic Synchronization Architecture (V4)

## 1. Overview: The "Single Version of Truth"
The Boreal Chessmaster ecosystem is built on a **Master-Follower** architecture. To ensure visual and logical parity across multiple browser tabs (Strategic Dashboard, Kinetic 3D, and Kinetic Chase), we use a high-frequency telemetry broadcast system.

### Core Components:
*   **Master (Dashboard)**: The authoritative physics and neural engine. It maintains the global tactical state.
*   **Followers (3D/Chase)**: Surrogate views that mirror the Master's state. They perform zero independent physics calculations.

---

## 2. Telemetry Broadcast Layer
The synchronization is powered by the **BroadcastChannel API** (`saab_kinetic_v8`).

### Master Behavior (`viz_engine.js`)
*   **Decoupled Clock**: The simulation engine (`updateSimulation`) is decoupled from `requestAnimationFrame`. It runs on a fixed `setInterval` at 60Hz. This ensures telemetry continues to stream even when the dashboard tab is in the background.
*   **The Heartbeat**: Every 16ms, the Master broadcasts a `STATE_SYNC` packet containing:
    *   Active Threat IDs and their exact 3D coordinates.
    *   Interceptor sub-salvo arrays (positions and status).
    *   Theater Mode (e.g., Sweden vs. Boreal) to trigger automatic camera/grid switching.

### Follower Behavior (`kinetic_3d.html`, `kinetic_chase.html`)
*   **Instant Pruning**: Follower views compare their local entity lists against the Master's packet every frame. If an ID is missing from the Master's broadcast, the follower **immediately** deletes the 3D mesh/2D marker. This eliminates visual artifacts and "ghost" missiles.
*   **Smooth Camera (Chase)**: The Chase view uses a **Low-Pass Filter** (interpolation) on its dynamic bounding box. This provides a cinematic, jitter-free "auto-zoom" that always keeps the engagement perfectly framed.

---

## 3. Temporal Engagement Awareness
To prevent double-firing and enable dynamic re-engagement, the system uses a dual-layer approach to track missiles already in flight.

### Layer A: The Tactical Heuristic (Fire Control)
*   **Location**: `src/core/engine.py` -> `TacticalEngine.get_optimal_assignments`
*   **Logic**: Before proposing a new intercept, the engine checks the `interceptors_assigned` field for each threat.
*   **Behavior**: If a threat already has an active assignment, the heuristic "gatekeeper" skips it. This prevents the "Infinite Fire" bug and conserves ammunition.

### Layer B: The Strategic MCTS (Confidence Prediction)
*   **Location**: `src/core/engine.py` -> `StrategicMCTS._single_rollout`
*   **Logic**: When the Neural Brain evaluates the "Safety" of a theater, it doesn't just look at what it's *about* to fire. It also accounts for what is *already* in the air.
*   **Simulation**: The MCTS pre-simulates the kill probability (~75% Pk) of all `interceptors_assigned`. This ensures the Strategic Confidence Score remains high even when the system is waiting for an in-flight interceptor to arrive.

---

## 4. Neural Feature Vector (18-D Compliance)
To maintain compatibility with the pre-trained **Elite V3.5** neural weights, the input vector remains strictly 18-dimensional.

1.  **Redundancy Compression**: We removed redundant normalized features (dist_norm/val_norm) that were simple linear scales of existing inputs.
2.  **Mapping Integrity**: We preserved the 18-D shape to prevent shape-mismatch errors in PyTorch.
3.  **Future-Proofing**: While the NN currently focuses on spatial and trajectory data, the **Tactical Engine** handles the temporal state, providing a robust hybrid brain that is both strategically "smart" and tactically "efficient."

---

## 5. Critical Coordinate Mapping
To bridge the gap between the **2D Strategic Map (km)** and the **3D Kinetic Simulator (meters/units)**, the system uses a calibrated projection:

*   **World Meters to 3D Units**: `(meters) / 1666`
*   **Serialization (Backend Link)**: `(3D_Units / 1666) * kmFactor`.
*   **Result**: The AI receives theater-relative coordinates that match the CSV ground truth.

## 6. Environmental Awareness (Weather Sync)
The system now integrates dynamic weather impacts into the tactical decision loop:
*   **UI Integration**: Dashboard weather selector syncs to `evaluate_advanced` payload.
*   **Pk Penalties**: 
    *   `STORM`: -20% Pk (Mod 0.8)
    *   `FOG`: -30% Pk (Mod 0.7)
*   **Consistency**: These penalties are applied both in the **Frontend Simulation** (hit detection) and the **Backend MCTS** (strategic scoring), ensuring the AI's projections match the live outcome.

## 7. Telemetry & Lifecycle Integrity
*   **Ghost Threat Filtering**: To prevent neural hallucination, dead threats (Impacted/Neutralized) are filtered out of the telemetry stream before being sent to the AI.
*   **MIRV Separation**: Upon warhead release, the parent bus is explicitly disposed. This prevents "Ghost Impacts" from empty buses and ensures the AI focuses solely on the lethal warhead clusters.
*   **Periodic Cleanup**: The `threats` array is purged every 30 frames to maintain high-frequency telemetry performance.

## 8. Inter-View Synchronization (Mirroring)
To ensure the **3D Intercept Simulator** (`kinetic_3d.html`) stays perfectly aligned with the **Strategic Dashboard**:
*   **BroadcastChannel**: Uses the `saab_kinetic_v8` bus.
*   **STATE_REQUEST Protocol**: On load/refresh, the 3D view broadcasts a `STATE_REQUEST`.
*   **Dashboard Responder**: The dashboard catches this request and immediately triggers a full `STATE_SYNC` and `INVENTORY_SYNC`.
*   **Parity**: This ensures that even if a user refreshes the 3D tab during a wave, the SAM counts, kills, and live missile positions are restored within milliseconds.

## 9. 3D Viewpoint Calibration
The 3D camera is now calibrated for maximum operational awareness:
*   **Boreal Theater**: Centered at `x: 800k, y: 1M, z: 1.8M`. This provides a high-vantage "God-eye" view of the entire Boreal Strait.
*   **Dynamic Zoom**: OrbitControls allow the operator to zoom into specific kinetic clusters without losing the theater context.
