# Benchmarking Methodology

> UNCLASSIFIED · EXERCISE · PROTOTYPE S28  
> Last updated: 2026-04-24

This document describes the four-tier benchmarking pipeline used to measure and rank all tactical AI models.

---

## Overview — Four Benchmark Tiers

| Tier | Script | Scope | Scenarios | Duration |
|------|--------|-------|----------|---------|
| 1 — Quick tournament | `model_tournament.py` | 2 batches, 5 scenarios, single-fire | 10 | ~5 s |
| 2 — EKP Championship | `model_championship.py` | 100 blind scenarios | 100 | ~30 s |
| 3 — Monte Carlo Stress | `tactical_benchmark.py` | 1,000 Pk simulations | 1,000 | ~60 s |
| 4 — Ultimate Stress Test | `ultimate_stress_test.py` | All 20 batches, dual-salvo | 1,000 | ~120 s |

---

## Tier 1 — Quick Tournament (`src/model_tournament.py`)

**Purpose:** Rapid sanity check / head-to-head comparison during development.  
**Scope:** 2 campaign batches × 5 scenarios = 10 scenarios per model.  
**Salvo mode:** Single-fire only (1 weapon per threat maximum).

### Models ranked

5 models compared in every run:
- Elite V3.5 (Boss)
- Supreme V3.1
- Hybrid RL
- Heuristic Base
- Random (Hungarian)

### Metrics reported

| Metric | Definition |
|--------|-----------|
| `survival_rate` | % of scenarios where final score > 0 |
| `interception_rate` | threats_neutralized / total_threats |
| `avg_score` | mean tactical score across 10 scenarios |
| `rank` | composite rank across all 3 metrics |

### Scoring formula

```python
score = sum(assignment_utility for a in assignments) - sum(leak_penalty for t in leaked_threats)
# where: assignment_utility = 150 + weights[eff]×1000 + Pk×700 - cost×0.8 + urgency_bonus
# and:   leak_penalty = threat_value × 1.5
```

### Output

Console table. No persistent file. Used interactively during development.

---

## Tier 2 — EKP Championship (`src/model_championship.py`)

**Purpose:** Expected Kill Probability (EKP) audit — measures the realistic intercept rate accounting for all Pk values.  
**Scope:** All 100 blind test scenarios (`data/blind_test/`).

### EKP Definition

$$\text{EKP} = \frac{\sum_{i=1}^{N} P_k(effector_i, threat_i)}{N_{total\_threats}} \times 100\%$$

The EKP differs from raw interception count because it accounts for the **probability** that an assignment actually succeeds, not just whether an assignment was made.

### Evaluation process

1. Load each of 20 blind batch files (5 scenarios each)
2. For each scenario, call engine to get assignments
3. For each assignment, look up `EFFECTORS[eff].pk_matrix[threat_type]`
4. Accumulate: `total_epk += Pk_value`
5. Report: `avg_epk = (total_epk / total_threats) × 100`

### Output

Console table + `data/results/championship_results.json`.

### Known limitation

`model_championship.py` uses a hard cap of `min(98.5, ...)` on EKP — values above 98.5% are truncated. This is a design choice (acknowledges real-world sensor and guidance errors that a perfect-information simulation would ignore).

---

## Tier 3 — Monte Carlo Stress Test (`src/tactical_benchmark.py`)

**Purpose:** 1,000-scenario Monte Carlo Pk simulation for statistical confidence.  
**Scope:** Full dataset (1,000 scenarios from `data/ground_truth_scenarios.json`).

### Simulation design

- For each scenario, run the engine to get assignments
- For each assignment, roll `random.random() < (Pk × weather_mod)` N times
- Weather sampled: 80% clear (mod=1.0), 15% storm (mod=0.8), 5% fog (mod=0.7)
- Record: hits, misses, score distribution
- Compute percentile stats: p25, p50, p75, p95

### Metrics

| Metric | Definition |
|--------|-----------|
| `mean_score` | Average tactical score across 1,000 scenarios |
| `tactical_pk` | Actual intercept fraction (stochastic rolls) |
| `strategic_success` | % scenarios with score ≥ 450 (operational threshold) |
| `p95_score` | 95th percentile score (worst 5% performance) |

### Output

- Console table
- Writes metrics to `data/results/benchmark_latest.json` — this JSON is consumed by the CORTEX C2 frontend dashboard (`frontend/cortex_c2.html` widget `#liveMetrics`)

---

## Tier 4 — Ultimate Stress Test (`src/ultimate_stress_test.py`)

**Purpose:** Gold standard tournament. Measures all models across the full operational dataset in both production-standard and raw-skill modes.  
**Scope:** ALL 20 campaign batches (`data/input/simulated_campaign_batch_*.json`) — up to 1,000 scenarios.

### Models in tournament (9 competitors)

| ID | Model | Type |
|----|-------|------|
| 1 | `elite_v3_5` | PyTorch PPO (Trans-ResNet) |
| 2 | `generalist_e10` | PyTorch MLP (10-epoch generalist) |
| 3 | `hybrid_rl` | PyTorch Hybrid-RL (ResNet-128) |
| 4 | `supreme_v3_1` | PyTorch ResNet V3.1 |
| 5 | `supreme_v2` | PyTorch ResNet V2 |
| 6 | `titan` | PyTorch Titan (BorealTitanEngine) |
| 7 | `heuristic` | Rule-based greedy WTA |
| 8 | `hBase` | Baseline heuristic (simple priority) |
| 9 | `random_hungarian` | Random assignment + Hungarian optimisation |

### Two salvo modes

**SALVO (factor = 2.0) — Production Standard:**
- Up to 2 weapons can be assigned per threat
- Represents doctrine with redundant engagement (standard layered defence)
- Models that can allocate backup weapons score higher
- This is the mode used for all operational performance claims

**SINGLE-FIRE (factor = 1.0) — Raw Skill:**
- Exactly 1 weapon per threat maximum
- Tests raw prioritisation and Pk selection without safety-net
- Reveals which models have genuinely good tactical judgement vs. those hiding behind redundancy

### Blend signal

A critical feature unique to the Ultimate Stress Test: the **threat blend signal** encodes overall swarm composition danger in the 15-D feature vector:

```python
threat_blend = min(1.0, (n_hypersonic × 0.15 + n_drone × 0.03 + num_threats × 0.01))
```

This single float (clamped 0–1) summarises:
- Hypersonic threat count (largest contribution: 0.15 per unit)
- Drone swarm count (0.03 per drone — swarm of 33 saturates the signal)
- Total volume stress (0.01 per threat)

Models that use this blend signal well learn to shift posture: when `blend > 0.8` (mixed hypersonic + drone swarm), THAAD/Patriot capacity must be reserved for hypersonics while IRIS-T/Nimbrix handles drones.

### Metrics

| Metric | Definition |
|--------|-----------|
| `survival_rate` | % scenarios where score > 0 (not overrun) |
| `interception_rate` | threats_neutralized / total_threats |
| `salvo_score` | mean tactical score in SALVO mode |
| `single_fire_score` | mean tactical score in SINGLE-FIRE mode |
| `overall_rank` | Weighted composite rank (survival 40%, intercept 40%, score 20%) |

### Interpreting results

1. **Large gap between SALVO and SINGLE-FIRE scores:** indicates the model relies on redundant engagement rather than accurate first-shot priority. Good models maintain >85% of their SALVO performance in SINGLE-FIRE.
2. **Low survival rate + high interception rate:** Model prioritises quality of engagements over total throughput — may let a few threats through to keep Pk high on every shot.
3. **Random Hungarian vs. Heuristic gap:** Measures how much structure in the problem can be exploited by even simple rules. This gap is usually 5–15%.
4. **Neural vs. Heuristic gap:** The real performance premium from learned policy. Typically 10–25% on heavy scenarios.

---

## Policy Accuracy Benchmark (`src/benchmark_boreal.py`)

This is a separate, standalone benchmark that does **not** use the MCTS Oracle or tactical scoring. Instead it measures how well a model's **output weights** match pre-computed ground-truth policy weights.

### What it measures

For each test scenario, the benchmark:
1. Runs the PyTorch model forward pass → 11-D policy output (effector priorities)
2. Compares against ground-truth weights from `data/ground_truth_scenarios.json` or `policy_network_params.json`
3. Computes accuracy as: `1.0 - mean_absolute_error(predicted, truth)`

### Policy accuracy metric

$$\text{Policy Accuracy} = 1 - \frac{1}{11} \sum_{i=1}^{11} |w_i^{pred} - w_i^{truth}|$$

A perfect model (policy acc = 1.0) would output exactly the same effector priority weights as the MCTS Oracle under the same scenario. In practice, >85% is considered "tactically aligned."

### Value accuracy metric (actor-critic models only)

Models that return a `(policy, value)` tuple (Elite, Supreme, Hybrid, Titan) also report value accuracy:

$$\text{Value Accuracy} = 1 - \frac{|V_{pred} - V_{oracle}|}{V_{oracle}}$$

where $V_{oracle}$ is the normalised MCTS mean score.

### Models benchmarked

| Model | Architecture | Policy Acc target | Value Acc target |
|-------|-------------|------------------|-----------------|
| elite_v3_5 | Transformer ResNet | >90% | >80% |
| supreme_v3_1 | ResNet-256 | >88% | >78% |
| hybrid_rl | ResNet-128 | >85% | >75% |
| titan | BorealTitanEngine | >83% | >72% |
| chronos_gru | ChronosGRU (15→128 GRU) | >80% | >70% |
| generalist_e10 | GeneralistMLP | >75% | N/A |

---

## Benchmark Result Files

| File | Written by | Consumed by |
|------|-----------|------------|
| `data/results/benchmark_latest.json` | `tactical_benchmark.py` | `frontend/cortex_c2.html` live metrics |
| `data/model_benchmarks.json` | `benchmark_boreal.py` | `frontend/dataset_viewer.html` |
| `data/results/championship_results.json` | `model_championship.py` | Manual review |
| `data/results/ultimate_stress_results.json` | `ultimate_stress_test.py` | Manual review |

---

## How to Run All Four Tiers

```powershell
# Activate the virtual environment
.\.venv_saab\Scripts\Activate.ps1

# Tier 1 — Quick check (5 seconds)
python src/model_tournament.py

# Tier 2 — EKP audit on 100 blind scenarios (30 seconds)
python src/model_championship.py

# Tier 3 — 1000-scenario Monte Carlo (60 seconds)
python src/tactical_benchmark.py

# Tier 4 — Gold standard tournament (2 minutes)
python src/ultimate_stress_test.py

# Policy accuracy (PyTorch weight comparison)
python src/benchmark_boreal.py
```
