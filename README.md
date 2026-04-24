# Boreal Chessmaster: 5Hz Ultra-Reflex Air Defense AI 🏆🛡️

The Boreal Chessmaster is an elite, hybrid-AI tactical engine designed for the **Saab Smart Stridsledning Hackathon.** It delivers sub-second strategic awareness by combining mathematical optimization, Monte Carlo Tree Search (MCTS), and a Deep Reinforcement Learning (RL) Neural Overlay.

---

## 🚀 Key Performance Specs
- **Ultra-Reflex Frequency**: 5Hz (Tactical evaluation every 200ms).
- **Tactical Accuracy**: 88.02% (Neural-optimized Pk).
- **Strategic Accuracy**: 100.0% (Zero impact mission success rate).
- **Benchmarking Suite**: Validated against 1,000 Monte Carlo "Ground Truth" scenarios on CUDA.

### **📊 Global Audit Performance (1,000 Scenarios)**
| Model Name | Tactical Logic | Hungarian? | Strategic Success | Tactical Pk |
| :--- | :--- | :---: | :---: | :---: |
| **Elite V3.5** 👑 | **Direct Action (PPO)** | **❌ NO** | **100.0%** | **88.02%** |
| **Hybrid RL V8.4** 🛡️ | **Bipartite Optimizer** | **✅ YES** | **100.0%** | **88.02%** |
| **Supreme V3.1** 👁️ | **Direct Action (PPO)** | **❌ NO** | 99.5% | 83.97% |
| **Heuristic Base** | **Triage-Aware** | **✅ YES** | **99.9%** | **74.5%** |

## 🚀 Mission-Critical Capabilities
- **Human-in-the-Loop (HITL)**: AI-driven decision support with commander-level approval queue.
- **Tactical Time-Freeze**: Automatic simulation pause during pending strategic decisions.
- **Manual Override (Direct Command)**: Total manual control over Target-Effector-Base assignments.
- **3D Kinetic Simulator**: High-fidelity 3D theater using Proportional Navigation (PN) guidance.
- **Doctrine Steering**: Real-time cost-matrix tuning (Balanced / Fortress / Aggressive).

- **Decision Throughput**: 1000x scenario hallucination boost via Neural Value Networks.
- **Adaptive Resource Management**: 90% CPU load reduction during idle states.

---

## 🕹️ Quick Start (Windows)
For the final demonstration, we recommend the automated PowerShell launcher which handles virtual environments and dependency syncing:
```powershell
# Open PowerShell in the project directory:
.\run_local_windows.ps1
```
*(Note: Ensure Python 3.10+ is installed on your system.)*

---

## 🧠 The Tripartite Intelligence Layer

### 1. Tactical Optimization (The Shooter)
Utilizes the **Hungarian Algorithm** to solve the weapon-target assignment problem in $O(N^3)$ time, ensuring mathematically perfect effector pairing for every incoming threat.

### 2. Strategic MCTS (The Thinker)
A game-theoretic layer that "hallucinates" 200+ future scenarios every cycle to ensure current tactical decisions do not compromise the long-term survival of the Capital.

### 3. Neural-RL Overlay (The Intuition)
A Deep Reinforcement Learning brain that micro-adjusts tactical weights and provides a **Normalized Strategic Confidence** metric to the Commander. This layer enables the AI to "feel" the risk of a saturation swarm before it arrives.

## 📊 FINAL PERFORMANCE BENCHMARKS (1,000 SCENARIOS)

| Model Name | Brain / Logic | Tactical Pk | Strategic Success | MC Raw Scoring | Strategic Pass | Verdict |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| **Elite V3.5** 👑 | Transf-ResNet / Direct | **98.02%** | **100.0%** | 8297/8453 | 1,000/1,000 | **PEAK.** Perfect Safety. |
| **Hybrid RL V8.4** 🛡️ | ResNet-128 / Hungar | **88.02%** | **100.0%** | 7455/8453 | 1,000/1,000 | **ROBUST.** Max Safety. |
| **Heuristic V2** 📜 | Static / Hungarian | 57.91% | **98.8%** | 4645/8453 | 988/1,000 | **LEGACY.** Rule-based. |

> [!IMPORTANT]
> The **Elite V3.5** core is the only architecture to achieve a perfect 1,000/1,000 pass rate under maximum saturation, making it the primary choice for national defense.

---

## 📡 Transparent Command & Control (C2)
Boreal Chessmaster is built on the principle of **Transparent AI**. The Stridsledare (Commander) maintains full control through:

- **The Global Strategic Log Hub**: A WebSocket-powered `Engine Trace` that provides real-time visibility into the AI's internal reasoning.
- **NEURAL/HEURISTIC Toggle**: Ability to bypass the Neural brain and rely on standard "Textbook" military logic in real-time.
- **Doctrine Blending**: A dynamic slider that allows the Commander to blend postures (e.g., Aggressive + Economy) to shape the AI's "Tactical Personality."
- **Flag Status Lights**: Instant visual proof of active strategic rules (e.g., CAPITAL RESERVE, POINT DEFENSE).

---

## 📁 Repository Structure
- `src/`: Core AI Engine, RL Neural Networks, and Backend API.
- `frontend/`: The 5Hz Ultra-Reflex Tactical Dashboard.
- `docs/`: Strategic manuals, Architecture guides, and Pitch scripts.


## 🎬 Demo Videos (Playwright Automation)

Full end-to-end demo videos are available, showcasing real user journeys in the tactical dashboard. These were generated using Playwright automation, both with mocked and live neural backend:

- **Demo video folders:**
	- Mocked backend: `scratch/demo-videos/`
	- Live backend: `scratch/live-videos/`
- **Format:** `.webm` (full-screen, ~1 min each)
- **How to view:** Open the folder and play any `.webm` file in a modern browser or video player.
- **How they were generated:**
	- Automated Playwright scripts simulate real user actions (clicks, navigation, scenario selection, etc.)
	- Both mocked and live backend flows are covered
	- See [docs/PLAYWRIGHT_DEMO_RESULTS.md](docs/PLAYWRIGHT_DEMO_RESULTS.md) for full details, results, and technical summary

---

## 📚 Engineering Documentation

| Document | Description |
|---------|-------------|
| [MODEL_ARCHITECTURE_REFERENCE.md](docs/MODEL_ARCHITECTURE_REFERENCE.md) | All 8 model architectures — input/output vectors, class names, bug report |
| [BENCHMARKING_METHODOLOGY.md](docs/BENCHMARKING_METHODOLOGY.md) | Four-tier benchmark pipeline, scoring formulas, how to run tests |
| [DATA_PIPELINE_AND_TRAINING.md](docs/DATA_PIPELINE_AND_TRAINING.md) | Scenario generation, Oracle labeling, corpus formats, real clutter fusion, missile range physics |
| [COORDINATE_SYSTEMS.md](docs/COORDINATE_SYSTEMS.md) | WGS84 / Theater-km / SVG units — conversion formulas, file mapping |
| [CORTEX_C2_REFERENCE.md](docs/CORTEX_C2_REFERENCE.md) | Frontend C2 console reference — panels, backend API, model profiles |
| [boreal_chessmaster_deep_dive.md](docs/boreal_chessmaster_deep_dive.md) | System architecture deep dive |
- `models/`: Pre-trained RL Value and Doctrine networks.
- `data/`: Map coordinates and adversarial "Red Team" scenarios.

---

## ⚖️ License
Distributed under the MIT License. See `LICENSE` for more information.
