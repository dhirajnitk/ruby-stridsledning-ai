# Data Pipeline & Training Reference

> UNCLASSIFIED · EXERCISE · PROTOTYPE S28  
> Last updated: 2026-04-24

This document covers the complete end-to-end data lifecycle: how scenarios are generated, how the MCTS Oracle labels them, how real-world clutter is ingested, and how training corpora are built for all model tiers.

---

## 1. Overview — Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BOREAL DATA PIPELINE                             │
│                                                                     │
│  Stage 1: Scenario Authoring                                        │
│  ┌──────────────────┐   ┌──────────────────┐  ┌──────────────────┐ │
│  │ Algorithmic      │   │ Gemini/LLM       │  │ OpenSky Live     │ │
│  │ Generator        │   │ LLM SITREP       │  │ ADS-B Clutter    │ │
│  │ (primary)        │   │ (tactical text)  │  │ (noise layer)    │ │
│  └────────┬─────────┘   └──────────────────┘  └────────┬─────────┘ │
│           │                                              │           │
│  Stage 2: Oracle Labeling                               │           │
│  ┌────────▼─────────────────────────────────────────────▼────────┐  │
│  │  MCTS Oracle (50-500 iterations)  +  PN Physics Simulator     │  │
│  │  → strategic_consequence_score, tactical_assignments          │  │
│  │  → per-threat intercept probability (PN Oracle label)         │  │
│  └────────────────────────────┬───────────────────────────────────┘ │
│                               │                                     │
│  Stage 3: Feature Extraction                                        │
│  ┌────────────────────────────▼───────────────────────────────────┐ │
│  │  extract_rl_features() → 15-D theater snapshot                 │ │
│  │  (z-score normalised using policy_network_params.json)         │ │
│  └────────────────────────────┬───────────────────────────────────┘ │
│                               │                                     │
│  Stage 4: Corpus Packaging                                          │
│  ┌────────────────────────────▼───────────────────────────────────┐ │
│  │  .npz compressed arrays: features, scores, weights, labels     │ │
│  │  Stored in data/training/strategic_mega_corpus/                │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Scenario Generation — Algorithmic Pipeline

### 2.1 Theater Batch Generator (`src/generate_theater_batches.py`)

This is the primary scenario source. Generates **20 campaign batch files**, each containing **50 scenarios** = **1,000 scenarios** total.

**Key design rules:**
- Threats spawn 60–140 km from real Boreal/Sweden base positions (engagement envelope)
- Approach vector points back toward the spawning base (realistic inbound trajectory)
- Mixed threat compositions using weighted random selection:

| Threat type | Weight | Speed | Threat value |
|------------|--------|-------|-------------|
| Drone (Shahed-style) | 30% | 150 km/h | 25 |
| Loitering munition | 20% | 200 km/h | 40 |
| Cruise missile (Kalibr/Taurus) | 15% | 900 km/h | 250 |
| Fighter (4th gen fast mover) | 10% | 1 800 km/h | 350 |
| Hypersonic PGM (Kinzhal/Zircon) | 5% | 7 000 km/h | 500 |
| Ballistic (SRBM) | 5% | 3 000 km/h | 400 |
| Electronic decoy | 15% | 200 km/h | 15 |

- Scenario intensities: Light (3–8 tracks, 40%), Medium (8–18, 40%), Heavy (18–30, 20%)
- Validation: ~90% of threats confirmed within Patriot range (120 km) of at least one base

**Output files:** `data/input/simulated_campaign_batch_{1..20}.json`

### 2.2 Monte Carlo Ground Truth Generator (`src/precompute_truth.py`)

Generates **1,000 scenarios** with rigorous Monte Carlo ground truth for offline evaluation.

For each scenario:
1. Random threat count (2–15), types from `[bomber, fast-mover, drone, hypersonic, fighter, decoy]`
2. Threats spawn 300–800 km east of a randomly chosen Swedish target node
3. Calls `TacticalEngine.get_optimal_assignments()` → initial assignment plan
4. Runs **50 MCTS rollouts** via `StrategicMCTS._single_rollout()` → statistical spread
5. Computes expected kills from Pk matrix, leaked count, score mean/min/max/std

**Output files:**
- `data/ground_truth_scenarios.json` (full scenarios + ground truth)
- `data/ground_truth.csv` (tabular summary: 1,000 rows)

### 2.3 Blind Test Set Generator (`src/generate_blind_test_set.py`)

Generates **100 held-out scenarios** that were never seen during training — for unbiased model evaluation.

- 20 batches × 5 scenarios = 100 scenarios
- Harder than training: 15–60 threats per scenario (vs 3–25 in training)
- Speed range: 2,000–6,000 km/h (biased toward hypersonic)
- Three target bases: Northern Vanguard (198.3, 335.0), Highridge Command (838.3, 75.0), Capital X (418.3, 95.0)

**Output:** `data/blind_test/blind_campaign_batch_{1..20}.json`

### 2.4 Boreal Ground Truth Scenarios (`data/boreal_ground_truth_scenarios.json`)

A curated set of Boreal-theater scenarios generated with explicit target names (Southern Redoubt, Meridia, Nordvik, Callhaven, etc.) and pre-computed MCTS scores. Used by `final_audit_boreal_gpu.py`.

**Note:** This dataset uses a legacy coordinate format where coordinates may appear very large (e.g. x=-332,235). These are in **meters** from an absolute origin — not the standard km-from-Stockholm system. See Coordinate Systems doc.

---

## 3. The Mega Data Factory (`src/training/mega_data_factory.py`)

For large-scale corpus generation (2,000–100,000 samples), used to train all production models.

### 3.1 Threat Profile Generation

Four threat categories with realistic operational profiles:

| Category | Speed | Altitude (y) | Count per scenario | Threat value |
|----------|-------|-------------|-------------------|-------------|
| Fighter aircraft (4th-gen & stealth) | 1,200–2,500 km/h | 5–15 km | 5–10 | 400 |
| Loitering munitions (swarms) | 150–250 km/h | 50–500 m | 20–50 | 50 |
| Cruise missiles (subsonic precision) | 900 km/h | 100–1,000 m | 10–20 | 250 |
| Hypersonic PGM | 5,000–15,000 km/h | 30–80 km | 5–10 | 500 |

Stealth variants: 30% of fighters have RCS = 0.005 m² (vs. 5.0 m² for 4th-gen).

### 3.2 Real-World Clutter Fusion

**Source:** OpenSky Network API (`src/fetch_real_clutter.py`)  
**Bounding box:** 54°N–64°N, 10°E–25°E (Stockholm/Baltic)  
**Integration:** 5–15 civilian tracks inserted per scenario, marked as `threat_value=0`

Purpose: trains the model to perform "Signal Triage" — ignore civilian ADS-B tracks while maintaining lock on hostiles.

Real tracks converted to theater-km:
```python
rel_x = (c['lon'] - 18.07) * 111.0 + 800  # km offset from Stockholm longitude
rel_y = (c['lat'] - 59.33) * 111.0 + 400  # km offset from Stockholm latitude
```

### 3.3 Three Data Formats

**`--format snapshot`** (default): One 15-D feature vector per scenario. Used for all strategic/policy models.

**`--format temporal`**: Sequence of 10 feature vectors, one per simulated time-step. Threats advance 1 km per step. Used for Chronos GRU training.

**`--format object-level`**: Per-threat 3D trajectory tensors (Threats × 20 time-steps × 11 features). Features: [X, Y, Z, Vx, Vy, Vz, threat_value, RCS, is_aircraft, is_drone, is_pgm]. Used for PN Oracle training.

### 3.4 Corpus Sizes

| Corpus file | Samples | Format | Use |
|-------------|---------|--------|-----|
| `eval_shared_gold.npz` | 5,000 | snapshot | Shared evaluation for all models |
| `rl_train_20k.npz` | 20,000 | snapshot | RL/heuristic training |
| `ppo_train_100k.npz` | 100,000 | snapshot | PPO mega-corpus |
| `boreal_snapshot_gold.npz` | varies | snapshot | Elite/Supreme training |
| `boreal_temporal_gold.npz` | varies | temporal | Chronos GRU training |
| `boreal_object_level_gold.npz` | varies | object-level | PN Oracle training |

**Command:**
```bash
python src/training/mega_data_factory.py --format snapshot --samples 2000
python src/forge_strategic_dataset.py --phases eval rl ppo
```

---

## 4. The Oracle Labeling System

### 4.1 MCTS Oracle (Tactical Labels)

The **Monte Carlo Tree Search Oracle** provides the ground-truth tactical assignments that all models are trained to imitate.

```
For each scenario:
  1. Run TacticalEngine.get_optimal_assignments()  → initial greedy plan
  2. Run StrategicMCTS.run_mcts_rollout(iterations=N)
     For each rollout:
       - Stochastic Pk roll per assignment (random.random() < Pk × weather_mod)
       - Accumulate score: +threat_value×0.2 per intercept, -10 per miss
       - Penalty for leaked threats: -threat_value×1.5
     Average across iterations
  3. Return: (mean_score, {leaked, tactical_assignments})
```

MCTS iteration counts by use:
- Blind test set generation: 50 iterations (speed)
- Standard training labels: 100–200 iterations (balanced)
- Ground truth precompute: 500 iterations (high fidelity, "teacher")

### 4.2 PN Oracle (Kinetic Labels for Object-Level Training)

For per-trajectory labeling, a high-fidelity **Proportional Navigation interceptor simulator** is used:

```python
def run_oracle_intercept(target_trajectory, rcs, dt=0.1):
```

**Physics implemented:**

1. **Radar equation** — determines whether guidance radar maintains lock:

$$P_r = \frac{P_t \cdot G^2 \cdot \lambda^2 \cdot \sigma}{(4\pi)^3 \cdot R^4}$$

| Parameter | Value |
|-----------|-------|
| Transmitted power $P_t$ | 100 kW |
| Antenna gain $G$ | 30 dB (linear: 1,000×) |
| Frequency | 10 GHz (X-band) |
| Wavelength $\lambda$ | 0.03 m |
| Min detection $P_{min}$ | 10⁻¹⁴ W |

2. **Lock loss:** If $P_r < P_{min}$, guidance is lost — missile flies blind at last velocity
3. **Proportional Navigation guidance** (when lock held):

$$\mathbf{a_c} = N \cdot V_c \cdot (\boldsymbol{\Omega} \times \hat{\mathbf{r}}_{LOS})$$

Where $N=4.0$ (standard NATO PN constant), $V_c$ = closing velocity, $\boldsymbol{\Omega}$ = LOS rotation rate.

4. **Intercept condition:** distance < 20 m → label = 1.0 (destroyed)
5. **Maneuver injection:** At step 10 (of 20), 40% probability of burn+bank evasion

### 4.3 Tactical Label Format

For assignment labeling, the output is a sparse binary matrix:

```
labels[threat_idx, (base_idx × 11) + effector_idx] = 1.0
```

Dimensions: `(max_threats=100, 21 bases × 11 effectors = 231)`

This is the training signal that Elite V3.5 learns to compress into its 11-D effector priority output.

---

## 5. How Missiles Lose Interception Capability with Distance

There are three separate distance-dependent degradation mechanisms in the system, operating at different layers.

### 5.1 Hard Range Gate (Tactical Engine)

The first and most important cutoff. In `TacticalEngine.get_optimal_assignments()`:

```python
if dist > eff_def.range_km: continue  # hard cutoff — this effector cannot engage this threat
```

Once a threat is outside the effector's maximum range, Pk = 0 — not degraded, simply not assigned. This is realistic: beyond maximum range a missile literally cannot reach.

| Effector | Range (km) | Threat types | Nominal Pk |
|---------|-----------|-------------|-----------|
| Saab Nimbrix (C-UAS hard-kill) | 5 | drone, loiter | 0.95–0.98 |
| Merops drone interceptor | 3 | drone, loiter | 0.90–0.95 |
| IRIS-T SLS | 12 | drone, cruise, fighter | 0.80–0.90 |
| Coyote Block 2 | 15 | drone, cruise | 0.30–0.95 |
| RBS-70 (unjammable) | 9 | drone, cruise | 0.60–0.95 |
| NASAMS (AMRAAM) | 40 | fighter, cruise | 0.90 |
| Patriot PAC-3 MSE | 120 | ballistic, hypersonic, cruise | 0.60–0.95 |
| Meteor BVRAAM | 150 | fighter, cruise | 0.85–0.98 |
| THAAD (engine.py SVG units) | 7,200 units (~12 km equiv) | ballistic, hypersonic | 0.80–0.98 |
| HELWS (directed energy) | effectively unlimited | drone | 0.95 |

### 5.2 Radar R⁴ Signal Decay (PN Oracle Layer)

At the physics simulation layer (used for object-level training labels), radar detection degrades with the **4th power of range**:

$$P_r \propto \frac{1}{R^4}$$

A target at 2× the range returns only **1/16th** the signal power. When the received power drops below $P_{min} = 10^{-14}$ W, radar lock is lost. Effects:

| Scenario | Detection |
|---------|-----------|
| Stealth fighter (RCS = 0.005 m²) at 80 km | Often below lock threshold — guidance goes blind |
| 4th-gen fighter (RCS = 5.0 m²) at 80 km | 1,000× stronger return — reliable lock |
| Drone (RCS = 0.1 m²) at 40 km | Marginal detection — weather-dependent |

This teaches the neural models that **stealth + range = evasion**, not just a Pk number.

### 5.3 Time-to-Intercept Urgency Bonus (Tactical Scoring)

In `TacticalEngine._calculate_utility()`, a threat that is **very close** (< 2 minutes to impact) receives a large priority bonus — not a Pk penalty for distance, but an urgency reward for nearby threats:

```python
t_arrival_mins = (dist / t.speed_kmh) * 60.0
if t_arrival_mins < 2.0:
    utility += 1000.0   # high urgency: prioritise now
```

This means the engine will preferentially assign weapons to the closest threats first, creating an implicit range-based prioritisation.

### 5.4 Weather Degradation on Pk (MCTS Rollouts)

In MCTS rollout scoring, weather multipliers reduce the effective Pk of every assignment:

```python
weather_mod = {"clear": 1.0, "storm": 0.8, "fog": 0.7}.get(weather, 1.0)
random.random() < (eff.pk_matrix.get(t.estimated_type, 0.5) * weather_mod)
```

A Patriot PAC-3 with nominal Pk=0.95 against cruise missiles becomes Pk=0.665 in fog.

### 5.5 Sensor Quality Pk Multiplier (Frontend C2 Layer)

In `frontend/cortex_c2.html`, sensor quality computed from scenario state further degrades effective Pk:

$$Pk_{effective} = Pk_{nominal} \times \text{sensor multiplier}$$

| Threat type | Sensor cuing formula | Jammed scenario example |
|------------|---------------------|------------------------|
| BALLISTIC | RADAR×0.60 + ESM×0.40 | 12%×0.60 + 50%×0.40 = 27% mult |
| HYPERSONIC | RADAR×0.70 + IR/EO×0.30 | ~30% mult |
| CRUISE | RADAR×0.50 + IR/EO×0.30 + LINK16×0.20 | ~35% mult |
| LOITER/DRONE | IR/EO×0.60 + RADAR×0.30 + LINK16×0.10 | ~40% mult |
| FIGHTER | RADAR×0.50 + LINK16×0.40 + IR/EO×0.10 | ~30% mult |
| **Floor** | | **0.30 minimum** (never below 30%) |

---

## 6. Real-World OSINT Data Integration

### 6.1 OpenSky Network (Live Baltic Clutter)

**Script:** `src/fetch_real_clutter.py`  
**API:** `https://opensky-network.org/api/states/all`  
**Bounding box:** Lat 54–64°N, Lon 10–25°E (Baltic Sea / Stockholm)  
**Output:** `data/raw/real_baltic_traffic.json`

Each ADS-B record contains: callsign, country, lat, lon, altitude, velocity, heading. Classified as EASY/HARD/RARE based on callsign and speed patterns. SAR, NAVY, MIL, COAST callsigns flagged as RARE.

20% of every training scenario is populated with these civilian tracks. The model must learn to produce zero engagement assignments for `threat_value=0` civilian tracks (signal triage).

### 6.2 Historical OSINT Datasets

| Dataset | Source | Local path | Tactical use |
|---------|--------|-----------|-------------|
| Ukraine air raid sirens | Vadimkin/GitHub | `data/raw/ukraine_sirens_official.csv` | EW jitter calibration (15 m GPS deviation, 252 jamming zones) |
| Iran–Israel 2026 strikes | Daniel Rosehill/GitHub | `data/raw/iran_israel_tactical_2026.json` | Hypersonic/ballistic saturation ratios |
| Global conflict feed | NewFeeds/GitHub | `data/raw/global_attacks_master.json` | 60/40 drone-to-ballistic ratio calibration |

### 6.3 LLM Tactical Analysis (Gemini via OpenRouter)

The Gemini model (`google/gemini-2.0-flash-001`) is used in `agent_backend.py` for **tactical SITREP generation** — converting the raw engine output (score, assignments, leaked count) into human-readable military brevity text for the C2 operator. This is **post-hoc analysis**, not scenario generation.

```python
response = await client.post("https://openrouter.ai/api/v1/chat/completions",
    json={"model": "google/gemini-2.0-flash-001", "messages": [{"role": "user", "content": prompt}]})
```

The prompt includes: threat count, strategic health, breach risk, posture, and assignment list. The model returns a 2-sentence SITREP + 1-sentence advisory in NATO brevity format.

---

## 7. Training Data Summary

| Corpus | Scenarios | Features | Labels | Labeling method |
|--------|----------|---------|--------|----------------|
| Campaign batches (data/input/) | 1,000 | — | — | No labels (inference only) |
| ground_truth_scenarios.json | 1,000 | raw threats | MCTS-50 score | Monte Carlo |
| blind test set | 100 | raw threats | — | Unbiased eval only |
| rl_training_data.csv | varies | 15-D vector | MCTS score | Tabular supervised |
| eval_shared_gold.npz | 5,000 | 15-D vector | score + weights | MCTS-100 |
| rl_train_20k.npz | 20,000 | 15-D vector | score + weights | MCTS-100 |
| ppo_train_100k.npz | 100,000 | 15-D vector | score + weights | MCTS-200 |
| boreal_object_level_gold.npz | varies | 50 × 20 × 11 | PN intercept (0/1) | PN Oracle |
| boreal_temporal_gold.npz | varies | N × 10 × 15 | score + weights | MCTS-100 |
