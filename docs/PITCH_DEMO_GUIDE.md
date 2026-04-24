# Boreal Chessmaster — Pitch Demo Guide (V2.0)

**Updated:** 2026-04-24 — Reflects MARV/MIRV/Dogfight, Live View V6, new demo flows

---

## The Narrative

> *"In modern high-intensity conflict, the OODA loop is too fast for humans alone. The Boreal Chessmaster is an Ultra-Reflex AI that gives the Commander a 5Hz processing edge — analysing the battlefield 5 times every second while maintaining full doctrinal control. It now understands MARV evasive re-entry vehicles, MIRV bus separation, and fighter dogfight outcomes — threats no legacy system was built for."*

---

## Demo Flow (8 Phases)

### Phase 1 — Open the Portal (`index.html`)
1. Show the landing page. Point out the theater selector (Boreal / Sweden).
2. Say: *"Two operational theaters — the Boreal Passage in the Arctic, and Sweden's military installations. Same AI, theater-aware data."*
3. Show the backend health indicator going green.

### Phase 2 — Strategic Dashboard (`dashboard.html`)
1. Let AUTO mode run — show the neural engagement loop firing every 200ms.
2. Point to the live stat boxes: Intercepted / Leaked / Score.
3. Say: *"Even at rest, CORTEX-1 is in vigilance mode — zero idle load, full engagement power on contact."*

### Phase 3 — Standard Engagement
1. Click **LAUNCH ENGAGEMENT** — watch the SAM assignments populate the CoT log.
2. Point to the Engine Trace: `PAC-3 → T1 (CRUISE) Pk=0.95`.
3. Say: *"O(N³) utility optimiser assigns the best effector to each threat in 0.8ms."*

### Phase 4 — MARV Demo (`kinetic_3d.html`)
1. Open **3D Kinetic — Boreal**.
2. Select **⚡ MARV (Maneuvering RV)** from the weapon dropdown. Click **FIRE**.
3. Watch the missile fly straight then begin lateral jinking inside 100 km.
4. Say: *"MARV activates evasive maneuvering in the terminal phase. Our engine detects this and commits intercept shots early — before the jink degrades Pk by 45%."*

### Phase 5 — MIRV Demo (`kinetic_3d.html`)
1. Select **💥 MIRV (3-Warhead Bus)**. Click **FIRE**.
2. At 45% of flight, the bus separates into 3 independent warheads, each targeting a different base.
3. Say: *"One missile becomes three. Our MIRV doctrine commits a THAAD to the bus before separation — one kill saves three assets. Post-separation, each warhead needs its own interceptor."*

### Phase 6 — Dogfight Demo (`kinetic_3d.html`)
1. Select **✈ FIGHTER w/ Dogfight**. Click **FIRE**.
2. At 30% of travel the dogfight resolves — show KILL / RTB / ENEMY_WIN outcome in the log.
3. Say: *"Hostile fighters don't just fly in — they fight. Our engine models the merge, Meteor BVR shots reduce win probability. If the enemy wins, our interceptor is lost."*

### Phase 7 — Live Kinetic Audit V6 (`live_view.html`)
1. Click the **⟳ AUTO-WAVE** button — threats begin firing automatically every 6 seconds.
2. Point to the **KILLS/LEAKS/TOTAL scoreboard** updating live.
3. Watch the **threat telemetry strip** on the right — per-threat progress bars, MARV jink badges, MIRV separation badges.
4. Trigger a **⚠ SATURATION WAVE** — 8 threats including MARV/MIRV/Fighter flood simultaneously.
5. Say: *"This is what C2 looks like under saturation. The AI tracks every thread simultaneously, assigns effectors, and reports outcomes in human language."*

### Phase 8 — CORTEX-C2 HITL Mode (`cortex_c2.html`)
1. Switch to **HITL** mode. Show the approval queue populate.
2. Approve one assignment, reject another.
3. Say: *"The Commander is never cut out of the loop. HITL mode pauses the AI and presents each assignment for human approval. Doctrinal control at full tactical speed."*

---

## Key Statistics for Judges

| Metric | Value |
|---|---|
| Threat Processing Speed | 5 Hz (200ms cycle) |
| Assignment Latency | 0.8ms (neural direct action) |
| MARV Pk Degradation | 45% inside 80km jink range |
| MIRV Utility Multiplier | 800 × 3 = 2,400 pre-release |
| Dogfight Win Probability | 30–50% (configurable per threat) |
| Training Corpus | 200 scenarios × 10 timesteps × 15 features |
| Models Available | 11 neural architectures |
| Test Suite | 6/6 advanced trajectory tests passing |
| Theaters | Boreal Arctic + Sweden Military Installations |

---

## UI Component Map

| Control | Effect |
|---|---|
| AUTO mode | 5Hz evaluation loop |
| HITL mode | Freeze for human approval |
| MANUAL mode | Direct operator weapon assignment |
| Doctrine selector | Balanced / Aggressive / Fortress — reshapes neural weights |
| Saturation Wave | 8-threat salvo incl MARV/MIRV/Fighter |
| Auto-Wave | Random single threat every 6s — continuous demo |
| Theater toggle | Boreal ↔ Sweden |

---

## Technical Talking Points

- **Mirror Logic**: JavaScript engine is a faithful replica of Python physics — every visual event corresponds to a real calculation.
- **Utility-First Assignment**: `_calculate_utility()` knows MARV, MIRV, and Dogfight flags — not just threat type.
- **MCTS Rollouts**: 50 Monte Carlo simulations per evaluation cycle.
- **Zero-Scroll UX**: Designed for high-stress command room environments — all data visible without scrolling.
- **Human Override**: Every AI decision is overridable. The AI advises; the Commander decides.


---

## 🕹️ Step-by-Step Demo Flow

### Phase 1: The "Always-On" Vigilance
1.  **Preparation**: Ensure **"AUTO"** is CHECKED and **"NEURAL"** is CHECKED.
2.  **Visual**: Point to the **SITREP & DOCTRINE** panel showing **"SCANNING"**.
3.  **The Hook**: *"Judges, notice the 'SCANNING' status. Even with no threats, our system is in a state of 'Energy-Efficient Vigilance.' The Neural Brain is loaded and ready, but silent—conserving CPU power until the moment of engagement."*

### Phase 2: Standard Tactical Response
1.  **Action**: Click **"Spawn"** once.
2.  **Visual**: Watch the **Engine Trace** (Bottom Right) show the tactical assignments and **Neural Confidence**.
3.  **The Hook**: *"A standard threat appears. At 5Hz frequency, our $O(N^3)$ Optimization layer instantly locks a solution, while the Neural-MCTS tracks our strategic confidence in real-time."*

### Demo Scenario 3: The Chronostasis Event (Human-Machine Teaming)
**Goal**: Show how the AI respects human authority without losing tactical momentum.
1.  **Toggle**: Enable `OVERRIDE` mode.
2.  **Action**: Click **"Ambush (Blind Spot)"**.
3.  **The WOW Factor**: The simulation instantly **freezes**. Point to the red alert border and the blurred map.
4.  **Narrative**: *"The AI has identified a hypersonic threat from the blind spot. It has frozen time (Chronostasis) to present its advisory. The LLM SITREP provides natural-language guidance based on neural confidence."*
5.  **Conclusion**: Click **"COMMENCE ENGAGEMENT"**. The freeze lifts, and the SAMs launch instantly.

---

## 5. Key Statistics for Judges
*   **Survival Rate**: 100.0% (Verified against 100 adversarial scenarios).
*   **Decision Speed**: 1000x faster than traditional MCTS thanks to Neural-Hybrid optimization.
*   **Architecture**: Multi-Agent system (Hungarian Matcher + Neural-MCTS + Gemini LLM).

### Phase 4: The "Neural vs Heuristic" Proof (The Kill-Shot)
1.  **Action**: Uncheck **"NEURAL"**.
2.  **Visual**: Point to the confidence panel showing **"HEURISTIC"** and the trace saying `Basic effector allocation`.
3.  **The Hook**: *"To prove our edge, I've disabled the Neural layer. We are now running on 'Textbook Logic.' It's safe, but it lacks the strategic intuition needed for complex swarms. By toggling NEURAL back ON, we regain our 5Hz predictive advantage."*

### Phase 5: Strategic Blending (Human Control)
1.  **Action**: Change **Primary Doctrine** to `Fortress` and adjust the **Blend Slider**.
2.  **Visual**: Point to the **Flag Lights** (enable_capital_reserve, etc.) updating instantly.
3.  **The Hook**: *"The Commander remains the architect. By blending doctrines, I am not just giving a command; I am reshaping the AI's neural weights in real-time. This is Human-Machine Teaming at its peak."*

---

## 🛠️ UI Component Map
- **AUTO**: Toggles the 5Hz (200ms) evaluation loop.
- **NEURAL**: Toggles the RL Value Network (Neural vs Heuristic).
- **Ambush**: Triggers a 10-target saturation event.
- **Execute AI**: Manual strategic override (forces fresh MCTS logic).
- **Engine Trace**: The "Black Box" opened—100% transparent AI reasoning.

---

## 💡 Key Technical Talking Points
- **5Hz Ultra-Reflex**: Evaluation cycle every 200ms.
- **Adaptive Performance**: 0% idle load, 100% engagement power.
- **Tripartite Intelligence**: $O(N^3)$ Optimization + MCTS Simulations + Neural Intuition.
- **Zero-Scroll UX**: Designed for high-stress control room environments.
