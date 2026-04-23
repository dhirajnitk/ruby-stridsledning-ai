# Model Architecture Reference — Boreal Chessmaster Suite

> UNCLASSIFIED · EXERCISE · PROTOTYPE S28  
> Last updated: 2026-04-24

This document covers the full input/output specification for all 8 tactical models in the system, how the 15-D feature vector is constructed, how the 11-D output maps to actual weapon assignments, and the 9 bugs found and fixed across the codebase.

---

## 1. The 15-D Theater Feature Vector

All tactical models share the same fixed-width input: **one 15-element float vector per scenario** computed by `extract_rl_features()` in `src/core/engine.py`.

This is a **theater-level snapshot** — not per-base or per-threat. Every number is derived from the current battlefield state, aggregated across all threats and all bases.

| # | Feature | Formula | Scale (typical) |
|---|---------|---------|-----------------|
| 1 | `num_threats` | Track count | 1 – 50 |
| 2 | `avg_dist` | Mean threat-to-capital distance (km) | 100 – 2 000 |
| 3 | `min_dist` | Closest threat to capital right now (km) | 10 – 1 000 |
| 4 | `total_val` | Sum of all threat values | 100 – 15 000 |
| 5 | `fighters` | Meteor rounds across all bases | 0 – 40 |
| 6 | `sams` | PAC-3 rounds across all bases | 0 – 96 |
| 7 | `drones` | Nimbrix soft-kill units | 0 – 60 |
| 8 | `cap_sams` | PAC-3 at Capital base specifically | 0 – 30 |
| 9 | `weather_bin` | 0.0 = clear / 1.0 = degraded | 0, 1 |
| 10 | `blend` | Doctrine blend / swarm-danger scalar | 0 – 1 |
| 11 | `west_threats` | Tracks inbound from west | 0 – 50 |
| 12 | `east_threats` | Tracks inbound from east | 0 – 50 |
| 13 | `ammo_stress` | `(sams + fighters + drones) / (threats + 1)` | 0 – 20 |
| 14 | `dist_norm` | `avg_dist / 1000` | 0.1 – 2 |
| 15 | `val_norm` | `total_val / 1000` | 0.1 – 15 |

Before passing to any model the vector is **z-score normalised** using per-feature statistics stored in `models/policy_network_params.json`:

```
x_norm[i] = (x[i] - scaler_mean[i]) / (scaler_scale[i] + 1e-6)
```

---

## 2. The 11-D Output Vector — Effector Priority Weights

Every model outputs **11 float values in [0, 1]**, one per effector system.  
These are **not coordinates or fire orders** — they are priority weights passed to the geometry-aware greedy assignment engine.

| Index | Effector system | Role |
|-------|----------------|------|
| 0 | LV-103 / Lvkv 90 | SHORAD / Anti-drone |
| 1 | E-98 / IRIS-T SLS | Short-medium SAM |
| 2 | RBS-70 | IR MANPADS / drone |
| 3 | Lvkv 90 | Vehicle AA |
| 4 | Meteor | Long-range AAM |
| 5 | THAAD | Upper-tier BMD |
| 6 | Patriot PAC-3 | Area BMD / mid-tier |
| 7 | NASAMS | Medium SAM |
| 8 | C-RAM | Terminal defence |
| 9 | HELWS | Directed-energy |
| 10 | Aegis / reserve | Leak / spare slot |

The engine formula that uses these weights is `TacticalEngine._calculate_utility()`:

```
utility(base, threat, effector) =
    150
    + neural_priority[effector_idx] × 1 000   ← model output drives this
    + Pk(effector, threat_type) × 700
    − cost_weight × 0.8
    + urgency_bonus (if time-to-impact < 2 min)
```

The greedy solver then picks the highest-utility `(base, effector → threat)` triple that:
- is within the effector's range circle
- has non-zero ammo at that base  
- does not exceed the base assignment cap

**The model never chooses a coordinate — it shifts priority weights and the geometry engine resolves which base fires.**

---

## 3. Model-by-Model Architecture

### 3.1 Elite V3.5 — Transformer/ResNet (default inference)

| Property | Value |
|----------|-------|
| File | `models/elite_v3_5.pth` |
| Class | `TransformerResNet` (core/inference.py) |
| Training class | `EliteTransformer` (neural_trainer.py) |
| Input | `(Batch, 15)` |
| Output | `(Batch, 11)` policy only — single tensor |
| Architecture | Linear(15→128) → ReLU → `unsqueeze(1)` → MultiheadAttention(128, 4 heads) → ResBlock(128) → `squeeze(1)` → Linear(128→11) → Sigmoid |
| Parameters | ~98 K |
| Benchmark | 88.02 % tactical Pk, 100 % strategic success |

**Training label space** (neural_trainer.py): `EliteTransformer(15, out_dim=231)` — 21 bases × 11 effectors. After training, the 231-D assignment matrix collapses to the 11-D effector weight signal used for inference.

---

### 3.2 Supreme V3.1 — Chronos GRU (temporal)

| Property | Value |
|----------|-------|
| File | `models/supreme_v3_1.pth` (also `boreal_chronos_gru.pth`) |
| Inference class | `ChronosGRU` (core/inference.py) |
| Training class | `ChronosGRU` (neural_trainer.py) |
| Input | `(Batch, 1, 15)` — single time-step sequence |
| Output | `(Batch, 11)` policy only |
| Architecture | GRU(15→128, 2 layers) → `h[-1]` → Linear(128→11) → Sigmoid |
| Parameters | ~85 K |
| Notes | Handles temporal patterns; slightly weaker on pure snapshot scenarios |

**Strategic training variant** (`src/training/ppo_chronos_gru.py`) uses `input_dim=550` (50 bases × 11 effectors per time-step) and returns `(policy, value)` tuple for a 3-class strategic decision. That is a *different model* for different use.

---

### 3.3 Supreme V2 — Classical ResNet

| Property | Value |
|----------|-------|
| File | `models/supreme_v2.pth` |
| Inference class | `StandardResNet(15, 11, width=64)` (core/inference.py) |
| Input | `(Batch, 15)` |
| Output | `(Batch, 11)` |
| Architecture | Linear(15→64) → ReLU → ResBlock(64) → Linear(64→11) → Sigmoid |
| Parameters | ~12 K |
| Notes | Fastest inference; good generalisation baseline |

---

### 3.4 Titan Oracle — Deep Transformer (BorealTitanEngine)

| Property | Value |
|----------|-------|
| File | `models/titan.pth` |
| Class | `BorealTitanEngine` (ppo_titan_transformer.py) |
| Input | `(Batch, 15)` — lifted to `(Batch, 1, 512)` via projection |
| Output | `(policy (Batch, 11), value (Batch, 1))` tuple |
| Architecture | Linear(15→512) → 6 × TitanBlock (self-attn + MLP + LayerNorm) → global pool → actor_head(512→256→11 Sigmoid) + critic_head(512→1024→512→1) |
| Parameters | ~14 M |
| Notes | Deepest model; captures non-linear theater correlations |

`BorealInference` loads this with a lazy import of `BorealTitanEngine`; if unavailable, falls back to `TransformerResNet`.

---

### 3.5 Hybrid RL — Value-Driven PPO

| Property | Value |
|----------|-------|
| File | `models/hybrid_rl.pth` |
| Inference class | `StandardResNet(15, 11, width=128)` (core/inference.py) |
| Benchmark class | `BorealValueNetwork(15)` (ppo_agent.py) — critic only |
| Input | `(Batch, 15)` |
| Output | `(Batch, 11)` policy (for inference) / `(Batch, 1)` value (for benchmark) |
| Architecture (critic) | Linear(15→128) → ResBlock(128) → Linear(128→1) |
| Notes | "Hybrid" means the RL training jointly optimised a value critic and a greedy policy. Benchmark reads only the critic path. |

---

### 3.6 Generalist E10 — Lightweight MLP

| Property | Value |
|----------|-------|
| File | `models/generalist_e10.pth` |
| Inference class | `GeneralistMLP(15, 11)` (core/inference.py) |
| Training class | `GeneralistMLP(15, 231)` (neural_trainer.py) |
| Input | `(Batch, 15)` |
| Output | `(Batch, 11)` |
| Architecture | Linear(15→256) → ReLU → Linear(256→128) → ReLU → Linear(128→11) → Sigmoid |
| Parameters | ~36 K |
| Notes | Robust ensemble-style; lowest variance across scenario types |

---

### 3.7 Heuristic — Triage-Aware WTA (no neural weights)

No `.pth` file. Pure algorithmic WTA:

1. `buildCandidates()` generates all valid `(threat → base, effector)` triples within range.
2. Sorted by `Pk × threatVal × pkWeight − cost × costWeight`.
3. Greedy selection respecting `maxPerBase` and ammo counts.

`MODEL_PROFILES.heuristic` applies `pkWeight=1.00`, `costWeight=0.015`, `maxPerBase=6`.

---

### 3.8 Heuristic V2 — Base Greedy

Same as Heuristic but with `pkWeight=0.95`, `costWeight=0.020`, `maxPerBase=4`. More conservative ammo usage; no neural weights.

---

### 3.9 Sinkhorn Oracle — Differentiable Hungarian Solver

| Property | Value |
|----------|-------|
| File | `models/boreal_sinkhorn_oracle.pth` (if present) |
| Class | `BorealSinkhornEngine(15, 11, 11)` (ppo_sinkhorn_agent.py) |
| Input | `(Batch, 15)` |
| Output | `(assignment_matrix (Batch, 11, 11), value (Batch, 1))` |
| Architecture | ResNet-12 backbone (Linear(15→256) + 6 × BN-ResBlocks) → assignment_head → `(Batch, 11, 11)` logits → **SinkhornLayer** (15 log-space iterations) → doubly-stochastic matrix + value_head |
| Notes | Output is a 11×11 probability matrix (weapon × target). For comparison with other models, the diagonal is extracted as a proxy 11-D weight vector. |

---

## 4. How the Model Picks Where to Fire a Missile

**Short answer:** the model does NOT pick coordinates. It shifts priority weights. The range geometry engine picks the base and threat.

**Full pipeline:**

```
Scenario  ─► extract_rl_features() ─► 15-D vector
                                          │
                           z-score normalise (policy_network_params.json)
                                          │
                              model.predict() ─► 11-D weights [0, 1]
                                          │
              map weights to effector_priorities dict (DOCTRINE_KEYS)
                                          │
         TacticalEngine.get_optimal_assignments()
              For each (base × threat × effector) in range:
                  utility = 150
                           + weights[eff] × 1000
                           + Pk(eff, type) × 700
                           − cost × 0.8
                           + urgency_bonus
              Sort by utility, greedy assign (salvo_ratio = 2)
                                          │
                          final assignment list: {base, effector, threat_id}
```

**The "21 × 11 = 231" dimension** appears in `neural_trainer.py` training labels — MCTS generates a binary 21×11 assignment matrix as the supervision signal. The model learns to compress that into 11 effector priority scalars. At inference time, the 21-base axis is handled by the range geometry, not the model.

---

## 5. Per-Unit Matching — ActorCriticDirect (Marathon Trainer)

`ppo_marathon_trainer.py` uses a fundamentally different architecture: a **bipartite cross-attention network** that operates at per-unit granularity rather than theater-level.

```
Input:
  eff  (N_eff, 8)  — one row per available effector instance
  thr  (N_thr, 6)  — one row per active threat

Effector features [8]:
  [x/1000, y/1000, range/10000, ammo/50, pk_avg, type_enc, availability, doctrine_affinity]

Threat features [6]:
  [x/1000, y/1000, speed/10000, value/500, type_enc, active_flag]

Network:
  eff_proj: Linear(8→64) + ReLU
  thr_proj: Linear(6→64) + ReLU
  affinity = eff_proj(eff) @ thr_proj(thr).T   → (N_eff, N_thr) logit matrix
  value    = value_head(mean(eff_proj))          → scalar

Output: (affinity_matrix, value)  — BCEWithLogitsLoss trains it to 1-hot assignment
```

Weights are saved to `models/ppo_direct_network.pth`.

This model is complementary to the theater-level 15-D models: it produces direct per-unit assignments rather than effector priority weights.

---

## 6. Bug Report & Fixes (2026-04-24)

### B1 — `BorealDirectEngine` missing value head (ppo_agent.py)

| | |
|-|-|
| **File** | `src/ppo_agent.py` |
| **Symptom** | `ValueError: too many values to unpack` in benchmark_boreal.py line `preds, values = model(features_norm)` |
| **Root cause** | `BorealDirectEngine.forward()` returned a single tensor; all benchmark paths expect a `(policy, value)` tuple |
| **Fix** | Added `self.value_head = nn.Linear(128, 1)` and changed return to `return policy, value` |

### B2 — `ActorCriticDirect` and `extract_direct_features` missing (ppo_agent.py)

| | |
|-|-|
| **File** | `src/ppo_agent.py` |
| **Symptom** | `ImportError: cannot import name 'ActorCriticDirect' from 'ppo_agent'` when running marathon trainer |
| **Root cause** | `ppo_marathon_trainer.py` imports both symbols but they were never defined |
| **Fix** | Added `ActorCriticDirect` (cross-attention bipartite network) and `extract_direct_features()` (per-unit feature extraction) to `ppo_agent.py` |

### B3 — `from engine import ValueNetwork` at module level (benchmark_boreal.py)

| | |
|-|-|
| **File** | `src/benchmark_boreal.py` |
| **Symptom** | `ModuleNotFoundError: No module named 'engine'` on import (crashes entire benchmark) |
| **Root cause** | `src/engine.py` does not exist; `ValueNetwork` and `DoctrineNetwork` live in `src/training/train_models.py`; `TacticalEngine` is in `src/core/engine.py` |
| **Fix** | Moved `from engine import ValueNetwork/DoctrineNetwork` inside guarded `if os.path.exists(path)` blocks with correct import path; changed `from engine import TacticalEngine` to `from core.engine import TacticalEngine` |

### B4 — `ppo_chronos_gru.py` missing from `src/` (benchmark_boreal.py)

| | |
|-|-|
| **File** | `src/benchmark_boreal.py` |
| **Symptom** | `ModuleNotFoundError: No module named 'ppo_chronos_gru'` |
| **Root cause** | The file exists only at `src/training/ppo_chronos_gru.py` with `input_dim=550` (strategic sequential model). Benchmark needs tactical variant with `input_dim=15, output_dim=11` |
| **Fix** | Created `src/ppo_chronos_gru.py` with `BorealChronosGRU(15, 11)` returning `(policy, value)`. Fixed import in benchmark to use `sys.path` pointing to `src/training/` |

### B5 — `.train()` mode used during inference (benchmark_boreal.py)

| | |
|-|-|
| **File** | `src/benchmark_boreal.py` |
| **Symptom** | Non-deterministic benchmark results; Sinkhorn BatchNorm statistics corrupted; dropout active during eval |
| **Root cause** | Three model branches called `model.train()` with comment "ENABLE BATCHNORM TRACKING" — incorrect; this should only be done during actual training |
| **Fix** | Changed all three occurrences to `model.eval()` |

### B6 — Wrong architecture for titan/hybrid/generalist in inference (core/inference.py)

| | |
|-|-|
| **File** | `src/core/inference.py` |
| **Symptom** | `RuntimeError: Error(s) in loading state_dict` — key mismatches when loading titan.pth or generalist_e10.pth |
| **Root cause** | `BorealInference.__init__` had only two branches (`supreme_v3_1` → ChronosGRU, `supreme_v2` → StandardResNet); everything else fell through to `TransformerResNet`, which has incompatible weights for Titan (512-wide transformer) and Generalist (MLP) |
| **Fix** | Added explicit branches: `titan` → lazy-import `BorealTitanEngine` with graceful fallback; `generalist` → new `GeneralistMLP(15,11)`; `hybrid` → `StandardResNet(15, 11, width=128)`. Added `try/except RuntimeError` around `load_state_dict` with a warning message instead of crash |

### B7 — `predict()` crashes on tuple-returning models (core/inference.py)

| | |
|-|-|
| **File** | `src/core/inference.py` |
| **Symptom** | `AttributeError: 'tuple' object has no attribute 'squeeze'` when loading a model that returns `(policy, value)` |
| **Root cause** | `predict()` called `.squeeze(0)` directly on `out` without checking if it was a tuple |
| **Fix** | Added `if isinstance(out, tuple): out = out[0]` before squeeze |

### B8 — `extract_features` was 10-D with wrong inventory keys (rl_data_collector.py)

| | |
|-|-|
| **File** | `src/rl_data_collector.py` |
| **Symptom** | Training data always had zeros for `fighters`, `sams`, `drones` (features 5-7); produced 10-element vectors incompatible with 15-D models |
| **Root cause** | `extract_features()` used keys `"fighter"`, `"sam"`, `"drone"` which don't exist in any base inventory; and returned only 10 features, missing `west_threats`, `east_threats`, `ammo_stress`, `dist_norm`, `val_norm` |
| **Fix** | Rewrote to match `core/engine.py::extract_rl_features()` exactly: correct keys (`meteor`, `patriot-pac3`, `saab-nimbrix`), 15 features, same formula |

### B9 — Tuple return from `evaluate_threats_advanced` treated as dict (rl_data_collector.py)

| | |
|-|-|
| **File** | `src/rl_data_collector.py` |
| **Symptom** | `TypeError: tuple indices must be integers or slices, not str` on `res["strategic_consequence_score"]` |
| **Root cause** | `evaluate_threats_advanced()` returns `(score, details, rl_val)` but code did `res["strategic_consequence_score"]` |
| **Fix** | Changed to `score, details, _rl_val = evaluate_threats_advanced(...)` and used `score` directly |

### B10 — All 9 effector `range_km` values inflated 3–40× in engine.py (core/engine.py)

| | |
|-|-|
| **File** | `src/core/engine.py` |
| **Symptom** | Tactical engine assigns weapons to threats **far outside real engagement envelopes** — e.g. IRIS-T SLS (12 km real) was engaging threats 120 km away; Saab Nimbrix (5 km) engaging at 50 km |
| **Root cause** | A misleading comment said ranges were "in SVG units" but the range check `if dist > eff_def.range_km: continue` compares km distances directly. All values were 3–40× too large. THAAD `range_km = 500` (should be 200); note that `7200` is `speed_kmh`, not range. |
| **Fix** | Corrected all 9 values to match `cortex_c2.html::EFFECTORS_DEF` (meters ÷ 1000) and `models.py`; removed misleading comment |

| Effector | Was (km) | Fixed (km) |
|---------|---------|-----------|
| Patriot PAC-3 | 300 | **120** |
| IRIS-T SLS | 120 | **12** |
| Saab Nimbrix | 50 | **5** |
| Meteor BVRAAM | 400 | **150** |
| NASAMS | 250 | **40** |
| Coyote Block 2 | 80 | **15** |
| Merops interceptor | 30 | **3** |
| **THAAD** | **500** | **200** |
| LIDS EW | 60 | **8** |

---

## 7. Files Changed (this session)

| File | Change |
|------|--------|
| `src/ppo_agent.py` | Added value_head to BorealDirectEngine; added ActorCriticDirect + extract_direct_features |
| `src/core/inference.py` | Fixed architecture mapping; added GeneralistMLP; fixed tuple handling in predict() |
| `src/rl_data_collector.py` | Rewrote extract_features to 15-D; fixed inventory keys; fixed tuple return |
| `src/benchmark_boreal.py` | Fixed broken imports; fixed .train()→.eval(); fixed import paths |
| `src/ppo_chronos_gru.py` | **Created** — tactical BorealChronosGRU(15→11) returning (policy, value) |

---

## 8. Related Documentation

| Document | Contents |
|---------|---------|
| [BENCHMARKING_METHODOLOGY.md](BENCHMARKING_METHODOLOGY.md) | Four benchmark tiers, scoring formulas, how to run all tests |
| [DATA_PIPELINE_AND_TRAINING.md](DATA_PIPELINE_AND_TRAINING.md) | Scenario generation, Oracle labeling, corpus formats, real clutter fusion |
| [COORDINATE_SYSTEMS.md](COORDINATE_SYSTEMS.md) | WGS84 / Theater-km / SVG units — conversion formulas, which file uses which system |
| [CORTEX_C2_REFERENCE.md](CORTEX_C2_REFERENCE.md) | Frontend model profiles, sensor quality Pk multipliers, backend payload formats |
