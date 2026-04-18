# Boreal Chessmaster: System Architecture & Implementation Details

This document outlines the architecture and implementation of the **Boreal Chessmaster** tactical air defense AI. The system is designed to evaluate incoming threats, assign optimal interceptors using mathematical utility maximization, and simulate probabilistic futures using Monte Carlo Tree Search (MCTS) to ensure strategic reserves are maintained.

---

## 1. High-Level Design (System Architecture)

At the highest level, the system operates as a client-server architecture split into four primary domains. It emphasizes asynchronous operations, mathematical optimization, and real-time visualization.

### 1.1 Core Components
*   **Tactical Dashboard (Frontend UI)**: A Vanilla JavaScript/HTML5 Canvas application that acts as the commander's view. It visualizes threats, radar blind spots, base inventories, and streams the AI's internal thought process in real time.
*   **API Gateway (FastAPI Backend)**: A high-performance, asynchronous Python web server. It handles HTTP requests for tactical evaluation, manages WebSocket connections for real-time trace logging, caches repeat requests, and formats reports using an external LLM.
*   **Core AI Engine (Math & Simulation)**: The "brain" of the system. It uses a two-layer approach:
    *   *Layer 1 (Tactical)*: The Hungarian matching algorithm (SciPy) for immediate target allocation.
    *   *Layer 2 (Strategic)*: A highly parallelized Monte Carlo Tree Search (MCTS) that simulates hundreds of futures to validate the tactical plan against unknown "ghost" threats.
*   **Batch Testing & Headless SimSuite**: Python scripts (`src/batch_tester.py`, `src/simulation.py`) designed to rigorously stress-test the engine against hundreds of predefined scenarios (JSON files from `data/input/`) without the UI, logging operational efficiency and generating analytical charts in `data/results/`.

### 1.2 High-Level Data Flow
1.  **Detection**: The Frontend or Headless Simulator spawns threats and sends a JSON payload (`IncomingThreat`) to the `/api/evaluate-threats` endpoint.
2.  **Validation & Cache**: The Backend hashes the payload. If seen recently, it instantly returns the cached result.
3.  **Evaluation**: The Backend offloads the payload to the Core AI Engine via a background thread.
4.  **Tactical Allocation**: The Engine builds a utility cost matrix and uses the Hungarian algorithm to pair interceptors to threats.
5.  **Strategic Verification**: The Engine uses MCTS rollouts to verify if the allocation leaves the bases vulnerable to blind-spot ambushes.
6.  **LLM Formatting**: The raw JSON decision is passed to Gemini 2.5 Flash via OpenRouter for human-readable SITREP generation.
7.  **Response & Action**: The Frontend receives the decision, deducts local inventory, removes intercepted threats (drawing explosions), and plots the MCTS strategic score on a live chart.

---

## 2. Medium-Level Design (Component Mechanics)

### 2.1 The Two-Layer AI Engine (`src/engine.py`)

**Layer 1: TacticalEngine**
This layer resolves the Assignment Problem. It takes a flattened list of all available weapons across all bases and pairs them with incoming threats. It builds a 2D Cost Matrix where Rows are effectors and Columns are threats. It utilizes `scipy.optimize.linear_sum_assignment` to find the combination that maximizes overall utility.

**Layer 2: StrategicMCTS**
This layer tests the resilience of Layer 1's plan.
*   **Rollout Mechanism**: It clones the initial game state, deducts the weapons fired in Layer 1, and "fast-forwards" the timeline.
*   **Ghost Threats**: It spawns probabilistic "Ghost" threats from known radar blind spots. These ghosts randomly vary between heavy bombers and hypersonic fast-movers (which have a 20% chance to spawn an accompanying decoy).
*   **MCTS Fast-Forwarding (Simulation Override)**: Since Ghost Threats spawn at maximum radar distance (often > 400km away), evaluating point-defenses at spawn distance would unfairly penalize the AI. The rollout logic temporarily fast-forwards the perceived distance of the Ghost to `50.0km` to properly test if the Capital SAM reserves are capable of intercepting the threat once it enters the defense envelope.
*   **Scoring**: The rollout applies the TacticalEngine to the ghost threats. If intercepted, the timeline gains points (+100). If the capital's SAMs remain unfired, it gains a bonus (+50). If the capital is hit, it loses points (-200). If the capital is destroyed due to lack of ammo, it triggers a fatal penalty (-500).
*   **Parallelization**: Rollouts are distributed across all CPU cores using `concurrent.futures.ProcessPoolExecutor`.

### 2.2 API Backend (`src/agent_backend.py`)
*   **Asynchronous I/O**: `evaluate_threats_advanced` is wrapped in `asyncio.to_thread()` to prevent CPU-bound math from blocking the FastAPI event loop. LLM calls utilize `httpx.AsyncClient` with a 3-attempt auto-retry.
*   **LRU Caching**: Uses Python's `collections.OrderedDict` to maintain a cache of the last 100 evaluated JSON payloads (hashed via MD5).
*   **WebSocket Streaming**: A custom `ConnectionManager` broadcasts internal MCTS `[TRACE]` and `[DEBUG]` logs from a queue directly to the connected UI clients.

### 2.3 Headless Simulator (`src/simulation.py`)
*   **Physics Loop**: Simulates movement ticking in 10-second intervals. Adds a 10% velocity drift to simulate real-world evasion/turbulence.
*   **Impact Mechanics**: Calculates `math.hypot` to check if a threat enters a 10km radius of Capital X, Coastal Base A, or Inland Base B.
*   **Base Destruction**: If a base is struck, its remaining inventory is instantly zeroed out, simulating catastrophic logistical failure.

---

## 3. Low-Level Design (Algorithms, Math, & Code Implementation)

### 3.1 Mathematical Utility Function
The core of the system relies on scoring the profitability of an intercept. Before applying Scipy's Hungarian algorithm, the engine inverts the utility score to trick the minimizer into finding the maximum utility.

**Base Equation:**
`Utility = (P_k * Threat_Value) - Effector_Cost - (T_int_mins * 1.5)`

*Where:*
*   `P_k`: Probability of Kill (0.0 to 1.0) derived from a pre-defined matrix mapping Effector type to Threat type.
*   `T_int_mins`: Time to intercept in minutes.
    *   **Kinematic Accuracy**: For engagements where the threat is heading directly towards the defending base, `T_int_mins` accurately utilizes **closing speed** (`effector_speed + threat_speed`) rather than a simple chase speed. This prevents mathematically invalid rejections when intercepting hypersonic targets with slower (but forward-facing) SAMs.

### 3.2 Implemented Military Doctrines (Utility Modifiers)
The engine mathematically enforces military logic through strict utility modifiers:

1.  **Point Defense Doctrine**:
    `if dist <= 150.0 and eff_name == "SAM": utility += 100.0`
    Forces bases to rely on SAMs for close-range "knife-fights", saving jets for deep strikes.
2.  **Fuel Penalty**:
    `if dist > 800.0 and eff_name == "Fighter": utility -= 80.0`
    Simulates bingo-fuel risk.
3.  **SAM Range Penalty**:
    `if dist > 50.0 and eff_name == "SAM": utility -= 60.0`
    Prevents wasting SAMs on out-of-envelope engagements.
4.  **Target Priority**:
    `if threat.estimated_type == "bomber": utility += 50.0`
5.  **Economy of Force**:
    `if threat.estimated_type == "decoy" and eff_name == "Drone": utility += 50.0`
    Ensures cheap drones intercept cheap decoys.
6.  **Dynamic Speed Mismatch**:
    `utility -= (speed_deficit * 0.05)`
    Penalizes effectors trying to chase targets faster than themselves.
7.  **Swarm Doctrine**:
    `if len(threats) >= 10 and effector.cost_weight >= 50.0: utility -= (len(threats) * 1.5)`
    Drastically penalizes the use of expensive effectors during massive decoy swarms.
8.  **Cluster Priority (Pre-calculated O(N) loop)**:
    `utility += (nearby_neighbors * 20.0)`
    Forces the engine to target dense formations to maximize splash damage/disruption.
9.  **Capital Reserve Doctrine**:
    `if "Capital" in base.name and eff_name == "SAM" and dist_to_capital > 100.0: utility -= 1000.0`
    Strict mathematical lock preventing the Capital from firing at distant targets.
10. **Base-Lock & Self-Defense Doctrine**:
    `utility += 80.0` (if heading directly for the base)
    `utility -= 2000.0` (if heading for another specific allied base)
    Prevents wasteful cross-firing across the map.

### 3.3 MCTS Parallelization & Timeout Mechanics
The MCTS layer is strictly bound to a `2.0` second response time to ensure tactical viability.

```python
start_time = time.time()
executor = concurrent.futures.ProcessPoolExecutor()
futures = [executor.submit(...) for _ in range(1, iterations)]

try:
    remaining_time = max_time_sec - (time.time() - start_time)
    for future in concurrent.futures.as_completed(futures, timeout=remaining_time):
        score, depletions = future.result()
        total_score += score
        actual_iterations += 1
except concurrent.futures.TimeoutError:
    # Halts early, divides only by actual_iterations to preserve math integrity
```

### 3.4 Data Structuring & Batch Testing (`src/batch_tester.py`)
*   **Scenario Format**: Scenarios are JSON arrays strictly defining unit states at specific spawn ticks.
*   **Batch Execution**: The script loops over all JSON files, mapping payload coordinates (e.g., `198.3, 335.0`) to explicit strings (`"Northern Vanguard Base"`) so the engine's Self-Defense Doctrine parses correctly.
*   **Performance Metrics**: Evaluates *Capital Survival Rate*, *Average Tactical Score*, and *Total Interceptors Used*. 
*   **Visualization**: Utilizes `numpy.polyfit(x, y, 1)` to generate a 1st-degree polynomial trend line over a `matplotlib` bar chart, allowing engineers to visualize engine degradation or improvement over increasingly difficult scenarios. Outputs results to CSV via the native `csv` module.

### 3.5 Frontend Rendering (`frontend/index.html`)
*   **Canvas Triage Visualization**: 
    ```javascript
    ctx.fillStyle = t.threat_value < triageThreshold ? "#585b70" : "#eba0ac"; 
    ```
    Dynamically grays out non-priority targets, immediately stripping them from the payload sent to the API.
*   **WebSocket Console Parsing**: 
    Creates dynamic DOM `<span>` elements using inline CSS hex codes (`#fab387`, `#f38ba8`, etc.) to color-code backend logs based on keywords like `[MCTS TRACE]`, `[DEBUG TRIAGE REJECT]`, `FATAL`, and `SUCCESS`.
*   **Chart.js Integration**: Pushes the scalar `strategic_consequence_score` returned by the FastAPI server directly into a local instance of Chart.js, rendering an animated line graph of MCTS confidence over time.

    The dashboard uses a discrete `spawnThreat()` function triggered by user clicks to generate individual enemies. Once spawned, a `requestAnimationFrame` loop continuously calculates vector math (`vx`, `vy`) to move threats across the canvas. If the "Auto-Poll AI" toggle is active, a background interval automatically pushes the radar payload to the backend every 3 seconds, simulating continuous radar sweeps. For fully automated, continuous enemy wave generation, the headless `src/batch_tester.py` is utilized instead.

### 3.6 Hackathon Pitch Guide Integration
To seamlessly bridge the complex backend logic with the Hackathon's strict judging criteria, the `frontend/index.html` UI features a built-in **Pitch Guide**. This interactive modal explicitly maps the application's technical capabilities directly to the requested presentation points:
*   **User Goals**: Highlights the Triage Slider filtering out noise.
*   **Unavoidable Activities**: Points to the Live Engine Trace to show the optimization math running in real-time.
*   **Sub-optimalities**: Triggers a Blind Spot Ambush to visually prove the MCTS successfully reserves Capital SAMs against unpredictable threats instead of panic-firing.
*   **Groundbreaking Solution**: Details the tripartite architecture (Optimization, MCTS, LLM).

### 3.7 Real-Time WebSocket Streaming ("Live Engine Trace")
The system features a fully functional "Live Engine Trace" panel that streams the AI's internal thought process to the commander in real-time, bridging the gap between backend math and frontend UI:
*   **Backend Thread-Safe Queue**: During heavy calculations in `evaluate_threats_advanced`, the engine pushes internal debug strings (like MCTS future rollouts or Hungarian triage logic) into a Python `queue.Queue()`.
*   **Non-Blocking Broadcast**: An asynchronous background task (`queue_reader` in `src/agent_backend.py`) continuously polls this queue and broadcasts the strings via FastAPI WebSockets (`ws://.../ws/logs`). This ensures the UI gets a live feed *before* the final HTTP JSON response is even calculated, without blocking the event loop.
*   **Frontend Color-Coding**: The dashboard (`frontend/index.html`) receives these strings and dynamically styles them for rapid military readability:
    *   **Orange (`#fab387`)** for `[MCTS TRACE]`: The AI simulating future timelines and hallucinating blind-spot ghosts.
    *   **Grey (`#6c7086`)** for `[DEBUG TRIAGE REJECT]`: The Hungarian Algorithm explaining exactly why it mathematically ignored a target (e.g., "Too slow" or "Unprofitable").
    *   **Red (`#f38ba8`)** for `FATAL` / `CRITICAL`: Simulated future timelines where the Capital was destroyed.
    *   **Green (`#a6e3a1`)** for `SUCCESS` / `BONUS`: Successful intercepts and intact reserve rewards.

---

## 4. Future Architecture: Reinforcement Learning (RL) Integration

To transition the Boreal Chessmaster from a classical algorithmic system to a self-learning, adaptive AI, the architecture is designed to support the integration of Deep Reinforcement Learning (RL). This addresses the computational limits of MCTS rollouts and the static nature of the Genetic Algorithm.

### 4.1 Supercharging MCTS (The "AlphaZero" Approach)
Currently, the Monte Carlo Tree Search (`StrategicMCTS`) is computationally bounded by running hundreds of full 15-minute physics rollouts to evaluate Capital survival. By mimicking AlphaZero, we replace these manual rollouts with highly optimized neural networks:

*   **The Value Network (Replacing `_single_rollout`):**
    *   **Architecture:** A Deep Neural Network (Feed-Forward MLP) trained via Supervised Learning on thousands of MCTS data points.
    *   **Implementation:** Instead of fast-forwarding the physics engine to see if the Capital survives, the MCTS extracts a 9-feature tensor of the board (inventories, threat proximities, unit counts) and passes it to the Value Network. The network instantly returns a scalar prediction of victory.
    *   **Impact:** Drops rollout evaluation time from milliseconds to microseconds, completely bypassing the heavy `concurrent.futures` ProcessPool.

*   **The Policy Network (Guiding the Search Tree):**
    *   **Architecture:** A Deep Neural Network utilizing a `Softmax` output layer to map a `GameState` to a probability distribution over tactical approaches.
    *   **Implementation:** Currently, MCTS explores futures somewhat blindly. The Policy Network looks at the radar and outputs percentages (e.g., `Standard: 10%`, `Economy: 85%`, `Aggressive: 5%`). The MCTS uses these probabilities to prioritize expanding only the most viable tactical branches, aggressively pruning mathematically foolish sub-trees.

### 4.2 Dynamic Doctrine Management (Replacing the Genetic Algorithm)
The current `src/genetic_optimizer.py` operates entirely offline to generate a single, static `optimized_weights.json` file. If the battlefield drastically changes (e.g., from a slow trickle of bombers to a massive hypersonic swarm), the static AI cannot adapt. We replace this with a live RL Actor network that acts as a real-time "Doctrine Manager".

*   **The RL Loop inside `evaluate_threats_advanced`:**
    1.  **State (Observation Space):** On every API request, the engine feeds a vectorized summary of the battlefield to the RL agent. *Example Vector:* `[num_active_decoys, num_active_bombers, avg_distance_to_capital, capital_sam_inventory, ...]`.
    2.  **Action (Continuous Action Space):** The agent utilizes a `Softplus` activation layer to output exactly 14 strictly positive continuous multipliers—one for each of the core military doctrines. 
    3.  **Dynamic Application:** *Scenario:* If the network spots 20 Decoys on radar, it outputs a multiplier of `3.0` for the `economy_force` doctrine and `2.5` for the `swarm_penalty_mult`. The engine applies these directly to the Hungarian Algorithm's cost matrix, instantly shifting the AI's personality to conserve advanced jets and spam cheap drones.
    4.  **Reward Function:** The agent receives the `strategic_consequence_score` from the MCTS as its reward signal.
*   **Impact:** This transitions the Boreal Chessmaster from a rigid, rules-based engine into a fluid, living AI that constantly adapts its personality to perfectly counter whatever strategy the Red Team employs.