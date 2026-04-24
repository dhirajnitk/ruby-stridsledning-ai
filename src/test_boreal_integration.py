"""
Boreal Theater Threat Integration Test
=======================================
Validates the full tactical stack against real Boreal_passage_coordinates.csv positions:
  - Base loading and coordinate verification
  - 15-D feature vector extraction (with capital detection)
  - Range gate validation for each effector against each threat
  - Three threat scenarios: Ballistic, Swarm, Saturation+Decoys
  - 50-iteration MCTS rollouts → survival probability and COA assignment

Run from project root:
    python src/test_boreal_integration.py

SAAB_MODE=boreal is set automatically. No external dependencies beyond core/.
"""

import os, sys, math, json

os.environ["SAAB_MODE"] = "boreal"
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from core.models import Threat, GameState, load_battlefield_state, EFFECTORS as M_EFFECTORS
from core.engine import (
    extract_rl_features,
    evaluate_threats_advanced,
    TacticalEngine,
    StrategicMCTS,
    EFFECTORS as E_EFFECTORS,
    DOCTRINE_KEYS,
)

CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'input', 'Boreal_passage_coordinates.csv')

# ─────────────────────────────────────────────────────────────
# ANSI colour helpers
# ─────────────────────────────────────────────────────────────
C_RST  = "\033[0m"
C_GRN  = "\033[92m"
C_YLW  = "\033[93m"
C_RED  = "\033[91m"
C_BLU  = "\033[94m"
C_MAG  = "\033[95m"
C_CYN  = "\033[96m"
C_BLD  = "\033[1m"

def banner(text, colour=C_BLU):
    w = 72
    print(f"\n{colour}{C_BLD}{'═'*w}{C_RST}")
    print(f"{colour}{C_BLD}  {text}{C_RST}")
    print(f"{colour}{C_BLD}{'═'*w}{C_RST}")

def ok(msg):   print(f"  {C_GRN}✓{C_RST}  {msg}")
def warn(msg): print(f"  {C_YLW}⚠{C_RST}  {msg}")
def err(msg):  print(f"  {C_RED}✗{C_RST}  {msg}")
def info(msg): print(f"  {C_CYN}·{C_RST}  {msg}")

# ─────────────────────────────────────────────────────────────
# SECTION 1 — BASE LOADING VERIFICATION
# ─────────────────────────────────────────────────────────────
banner("SECTION 1 · Base Loading Verification (SAAB_MODE=boreal)")

state = load_battlefield_state(CSV_PATH)

EXPECTED_BASES = {
    "Arktholm (Capital X)": (418.3, 95.0),
    "Northern Vanguard Base": (198.3, 335.0),
    "Highridge Command": (838.3, 75.0),
    "Boreal Watch Post": (1158.3, 385.0),
    "Valbrek": (1423.3, 213.3),
    "Nordvik": (140.0, 323.3),
}

capital = next((b for b in state.bases if "Capital" in b.name), None)
if capital:
    ok(f"Capital detected: '{capital.name}' at ({capital.x}, {capital.y}) km")
else:
    err("No base with 'Capital' in name — extract_rl_features will fall back to bases[0]")

print()
print(f"  {'Base Name':<32} {'x_km':>8} {'y_km':>8}  {'Dist-to-Capital':>16}  Inventory")
print(f"  {'─'*32} {'─'*8} {'─'*8}  {'─'*16}  {'─'*30}")
BASES_PASSED = 0
for b in state.bases:
    expected = EXPECTED_BASES.get(b.name)
    dist = math.hypot(b.x - capital.x, b.y - capital.y) if capital else 0
    match = ""
    if expected:
        dx, dy = abs(b.x - expected[0]), abs(b.y - expected[1])
        if dx < 0.1 and dy < 0.1:
            match = C_GRN + "✓" + C_RST
            BASES_PASSED += 1
        else:
            match = C_RED + f"✗ expected {expected}" + C_RST
    inv_str = ", ".join(f"{k}:{v}" for k,v in list(b.inventory.items())[:3])
    print(f"  {match}{b.name:<31} {b.x:>8.1f} {b.y:>8.1f}  {dist:>14.1f}km  {inv_str}")

print()
if BASES_PASSED == len(EXPECTED_BASES):
    ok(f"All {BASES_PASSED} expected Boreal bases loaded at exact CSV coordinates")
else:
    warn(f"{BASES_PASSED}/{len(EXPECTED_BASES)} base positions match CSV — check SAAB_MODE and CSV path")

# ─────────────────────────────────────────────────────────────
# SECTION 2 — EFFECTOR RANGE REFERENCE TABLE
# ─────────────────────────────────────────────────────────────
banner("SECTION 2 · Engine EFFECTORS (corrected range_km values)")

print(f"  {'Effector':<22} {'range_km':>10} {'speed_kmh':>11} {'key threat types'}")
print(f"  {'─'*22} {'─'*10} {'─'*11} {'─'*30}")
for key, eff in E_EFFECTORS.items():
    types = ", ".join(eff.pk_matrix.keys())
    print(f"  {eff.name:<22} {eff.range_km:>10.0f} {eff.speed_kmh:>11.0f}   {types}")

# ─────────────────────────────────────────────────────────────
# SECTION 3 — THREAT SCENARIO DEFINITIONS
# ─────────────────────────────────────────────────────────────
# All threat positions chosen to be within PAC-3 range (120 km) of at
# least one base. Verified with the formula below. Spawn points represent
# realistic approach vectors from south of the north mainland coastline.
#
# North mainland southern coastline ~ y ≈ 380 km (from terrain polygon).
# Threats inside the theater (y < 380) represent threats already past the
# outer air-defence boundary — the hardest test for the engine.

def dist_to_nearest_base(tx, ty, bases):
    return min(math.hypot(b.x - tx, b.y - ty) for b in bases), \
           min(bases, key=lambda b: math.hypot(b.x - tx, b.y - ty))

SCENARIOS = {}

# ── Scenario A: Ballistic Strike on Arktholm ──────────────────
SCENARIOS["A_BALLISTIC"] = {
    "title": "SCENARIO A · Ballistic Strike — Arktholm",
    "description": (
        "Three ballistic missiles launched from south mainland heading for "
        "Arktholm (Capital X) at 418.3, 95 km. Spawned 90–115 km south "
        "of target — within Patriot PAC-3 (120 km) engagement envelope."
    ),
    "threats": [
        Threat("BM-01", 418.3, 195.0, 3000.0, "Arktholm (Capital X)", "ballistic", 400),
        Threat("BM-02", 350.0, 165.0, 3500.0, "Arktholm (Capital X)", "ballistic", 400),
        Threat("BM-03", 490.0, 175.0, 2800.0, "Arktholm (Capital X)", "ballistic", 350),
    ],
}

# ── Scenario B: Swarm Breakthrough + Fast Movers ──────────────
SCENARIOS["B_SWARM"] = {
    "title": "SCENARIO B · Swarm + Fast Mover Breakthrough (15 tracks)",
    "description": (
        "Mixed saturation: 8 drone loiterers targeting Northern Vanguard "
        "(198.3, 335), 3 cruise missiles and 1 hypersonic PGM targeting "
        "Arktholm, 2 fighters targeting Highridge (838.3, 75), 1 ghost "
        "cruise with uncertain classification."
    ),
    "threats": [
        # Drone swarm on Northern Vanguard — 20-35 km south of base
        Threat("D-01", 198.3, 355.0,  200.0, "Northern Vanguard Base", "drone",         25),
        Threat("D-02", 180.0, 362.0,  220.0, "Northern Vanguard Base", "drone",         25),
        Threat("D-03", 215.0, 358.0,  190.0, "Northern Vanguard Base", "drone",         20),
        Threat("D-04", 170.0, 370.0,  210.0, "Northern Vanguard Base", "drone",         20),
        Threat("D-05", 200.0, 348.0,  185.0, "Northern Vanguard Base", "drone",         20),
        Threat("D-06", 220.0, 375.0,  200.0, "Nordvik",                "drone",         15),
        Threat("D-07", 145.0, 360.0,  215.0, "Nordvik",                "drone",         15),
        Threat("D-08", 160.0, 350.0,  195.0, "Northern Vanguard Base", "drone",         15),
        # Cruise missiles on Arktholm — 75-95 km south
        Threat("C-01", 418.3, 180.0,  900.0, "Arktholm (Capital X)",   "cruise-missile", 250),
        Threat("C-02", 380.0, 170.0,  900.0, "Arktholm (Capital X)",   "cruise-missile", 200),
        Threat("C-03", 455.0, 175.0,  900.0, "Arktholm (Capital X)",   "cruise-missile", 200),
        # Fast movers on Highridge — 90-100 km south
        Threat("F-01", 838.3, 165.0, 1800.0, "Highridge Command",      "fighter",        300),
        Threat("F-02", 780.0, 155.0, 2000.0, "Highridge Command",      "fighter",        300),
        # Hypersonic PGM on Arktholm — 90 km south
        Threat("H-01", 418.3, 185.0, 6000.0, "Arktholm (Capital X)",   "hypersonic-pgm", 500),
        # Ghost cruise — ambiguous classification
        Threat("G-01", 300.0, 160.0,  850.0, "Arktholm (Capital X)",   "cruise-missile", 150),
    ],
}

# ── Scenario C: Saturation + Decoys (sensor-degrading) ────────
SCENARIOS["C_SATURATION"] = {
    "title": "SCENARIO C · Saturation Strike + Decoy Swarm (10 tracks)",
    "description": (
        "Three simultaneous hypersonic PGMs targeting Arktholm and Highridge, "
        "two cruise missiles on Highridge, four radar decoys diluting the PAC-3 "
        "engagement queue. Represents maximum-stress scenario for MCTS scoring."
    ),
    "threats": [
        # Hypersonic PGMs — high priority
        Threat("H-01", 418.3, 195.0, 7000.0, "Arktholm (Capital X)", "hypersonic-pgm", 500),
        Threat("H-02", 390.0, 185.0, 6500.0, "Arktholm (Capital X)", "hypersonic-pgm", 500),
        Threat("H-03", 838.3, 165.0, 7000.0, "Highridge Command",    "hypersonic-pgm", 500),
        # Cruise missiles on Highridge — 90 km south
        Threat("C-01", 800.0, 160.0,  900.0, "Highridge Command",    "cruise-missile", 250),
        Threat("C-02", 870.0, 168.0,  900.0, "Highridge Command",    "cruise-missile", 250),
        # Decoys — dilute PAC-3 engagement queue
        Threat("DC-1", 418.3, 175.0,  300.0, "Arktholm (Capital X)", "decoy",           5),
        Threat("DC-2", 430.0, 180.0,  280.0, "Arktholm (Capital X)", "decoy",           5),
        Threat("DC-3", 838.3, 155.0,  310.0, "Highridge Command",    "decoy",           5),
        Threat("DC-4", 820.0, 170.0,  290.0, "Highridge Command",    "decoy",           5),
        Threat("DC-5", 400.0, 200.0,  320.0, "Arktholm (Capital X)", "decoy",           5),
    ],
}

# ─────────────────────────────────────────────────────────────
# SECTION 4 — RANGE GATE VALIDATION
# ─────────────────────────────────────────────────────────────
banner("SECTION 3 · Range Gate Validation — Which Base Can Engage Each Threat?")

for sc_key, sc in SCENARIOS.items():
    print(f"\n  {C_MAG}{sc['title']}{C_RST}")
    any_engageable = True
    for t in sc["threats"]:
        engagements = []
        for b in state.bases:
            dist = math.hypot(b.x - t.x, b.y - t.y)
            for eff_name, count in b.inventory.items():
                eff = E_EFFECTORS.get(eff_name)
                if not eff: continue
                if dist <= eff.range_km:
                    pk = eff.pk_matrix.get(t.estimated_type, 0)
                    engagements.append(f"{b.name[:16]}·{eff_name}(Pk={pk:.2f}@{dist:.0f}km)")
        col = C_GRN if engagements else C_RED
        eng_str = "; ".join(engagements[:3]) if engagements else "NO BASE IN RANGE"
        if not engagements: any_engageable = False
        print(f"  {col}{t.id:<7}{C_RST} {t.estimated_type:<15} → {eng_str}")
    if not any_engageable:
        warn("Some threats have no viable engagement — consider adjusting spawn positions")

# ─────────────────────────────────────────────────────────────
# SECTION 5 — 15-D FEATURE VECTOR EXTRACTION
# ─────────────────────────────────────────────────────────────
banner("SECTION 4 · 15-D Feature Vector Extraction")

FEATURE_NAMES = [
    "num_threats", "avg_dist_km", "min_dist_km", "total_value",
    "fighters(meteor)", "sams(pac3)", "drones(nimbrix)", "cap_sams(pac3)",
    "weather_bin", "blend",
    "west_threats", "east_threats", "ammo_stress", "dist_norm", "val_norm"
]

for sc_key, sc in SCENARIOS.items():
    threats = sc["threats"]
    vec = extract_rl_features(state, threats, weather="clear", primary="balanced", blend=0.5)
    print(f"\n  {C_MAG}{sc['title']}{C_RST}")
    print(f"  {'Feature':<22} Value")
    print(f"  {'─'*22} {'─'*10}")
    for name, val in zip(FEATURE_NAMES, vec):
        highlight = ""
        if name in ("min_dist_km",) and val < 50:     highlight = C_RED
        elif name in ("num_threats",) and val >= 10:  highlight = C_YLW
        elif name == "ammo_stress" and val > 5:        highlight = C_GRN
        print(f"  {name:<22} {highlight}{val:.3f}{C_RST}")

# ─────────────────────────────────────────────────────────────
# SECTION 6 — TACTICAL ENGINE + 50-ITERATION MCTS
# ─────────────────────────────────────────────────────────────
banner("SECTION 5 · Tactical Engine — WTA Assignments + 50-iteration MCTS")

results = {}
for sc_key, sc in SCENARIOS.items():
    threats = sc["threats"]

    score, details, rl_val = evaluate_threats_advanced(
        state, threats,
        mcts_iterations=50,
        salvo_ratio=2,
        weather="clear",
    )

    assignments = details.get("tactical_assignments", [])
    leaked       = round(details.get("leaked", 0), 2)
    covered_ids  = {a["threat_id"] for a in assignments}
    uncovered    = [t for t in threats if t.id not in covered_ids and t.estimated_type != "decoy"]

    results[sc_key] = {
        "score": score,
        "assignments": assignments,
        "leaked": leaked,
        "uncovered": uncovered,
        "threats": threats,
    }

    total_non_decoy = sum(1 for t in threats if t.estimated_type != "decoy")
    coverage_pct = (len(assignments) / max(total_non_decoy, 1)) * 100

    print(f"\n  {C_MAG}{sc['title']}{C_RST}")
    print(f"  MCTS Score     : {C_BLD}{score:+.1f}{C_RST}")
    print(f"  Assignments    : {len(assignments)} (coverage: {coverage_pct:.0f}% of non-decoys)")
    print(f"  Avg Leaked     : {leaked:.2f} threats/rollout")
    print(f"  Uncovered      : {len(uncovered)} threats {[t.id for t in uncovered]}")

    if assignments:
        print(f"\n  {'ThreatID':<8} {'Effector':<20} {'Base':<28} {'Pk':>6}")
        print(f"  {'─'*8} {'─'*20} {'─'*28} {'─'*6}")
        for a in assignments:
            t  = next((x for x in threats if x.id == a["threat_id"]), None)
            b  = next((x for x in state.bases if x.name == a["base"]), None)
            eff = E_EFFECTORS.get(a["effector"])
            pk  = eff.pk_matrix.get(t.estimated_type, 0) if eff and t else 0
            dist = math.hypot(b.x - t.x, b.y - t.y) if b and t else 0
            col = C_GRN if pk >= 0.80 else (C_YLW if pk >= 0.50 else C_RED)
            print(f"  {a['threat_id']:<8} {a['effector']:<20} {a['base']:<28} {col}{pk:.2f}{C_RST}  ({dist:.0f} km)")

# ─────────────────────────────────────────────────────────────
# SECTION 7 — MCTS SURVIVAL PROBABILITY (Monte Carlo)
# ─────────────────────────────────────────────────────────────
banner("SECTION 6 · Strategic Survival Probability — 200-iteration Monte Carlo")

import random

def survival_mc(state, threats, n_sims=200, salvo_ratio=2, weather="clear"):
    """Run N MCTS rollouts, return survival_rate (score>0) and interception_rate."""
    from core.engine import DoctrineManager
    weights, flags = DoctrineManager.get_blended_profile()
    plan = TacticalEngine.get_optimal_assignments(state, threats, weights=weights, flags=flags, salvo_ratio=salvo_ratio)

    scores = []
    for _ in range(n_sims):
        s, d = StrategicMCTS._single_rollout(state, plan, threats, weather=weather)
        scores.append(s)

    survival = sum(1 for s in scores if s > 0) / n_sims * 100
    intercept_est = sum(1 for s in scores if s > 150) / n_sims * 100
    return {
        "survival_rate_pct": round(survival, 1),
        "intercept_rate_pct": round(intercept_est, 1),
        "mean_score": round(sum(scores) / n_sims, 1),
        "min_score":  round(min(scores), 1),
        "max_score":  round(max(scores), 1),
        "plan_size":  len(plan),
    }

print()
print(f"  {'Scenario':<32} {'Surv%':>6} {'Int%':>6} {'MeanScore':>10} {'MinScore':>10} {'Assignments':>12}")
print(f"  {'─'*32} {'─'*6} {'─'*6} {'─'*10} {'─'*10} {'─'*12}")

for sc_key, sc in SCENARIOS.items():
    mc = survival_mc(state, sc["threats"], n_sims=200, salvo_ratio=2)
    surv_col = C_GRN if mc["survival_rate_pct"] >= 80 else (C_YLW if mc["survival_rate_pct"] >= 50 else C_RED)
    name = sc["title"].replace("SCENARIO ", "").split("·")[0].strip()
    print(
        f"  {sc['title'].split('·')[1].strip()[:32]:<32} "
        f"{surv_col}{mc['survival_rate_pct']:>5.1f}%{C_RST} "
        f"{mc['intercept_rate_pct']:>5.1f}% "
        f"{mc['mean_score']:>10.1f} "
        f"{mc['min_score']:>10.1f} "
        f"{mc['plan_size']:>12}"
    )

# ─────────────────────────────────────────────────────────────
# SECTION 8 — WEATHER SENSITIVITY TEST
# ─────────────────────────────────────────────────────────────
banner("SECTION 7 · Weather Sensitivity — Scenario B (Swarm) across 3 conditions")

SC_B = SCENARIOS["B_SWARM"]["threats"]
print()
print(f"  {'Weather':<10} {'Surv%':>6} {'Int%':>6} {'MeanScore':>10}")
print(f"  {'─'*10} {'─'*6} {'─'*6} {'─'*10}")
for weather in ("clear", "storm", "fog"):
    mc = survival_mc(state, SC_B, n_sims=200, salvo_ratio=2, weather=weather)
    print(f"  {weather:<10} {mc['survival_rate_pct']:>5.1f}%  {mc['intercept_rate_pct']:>5.1f}%  {mc['mean_score']:>9.1f}")

# ─────────────────────────────────────────────────────────────
# SECTION 9 — SALVO MODE COMPARISON
# ─────────────────────────────────────────────────────────────
banner("SECTION 8 · Salvo Mode Comparison — Scenario C (Saturation)")

SC_C = SCENARIOS["C_SATURATION"]["threats"]
print()
print(f"  {'Salvo Ratio':<14} {'Surv%':>6} {'Int%':>6} {'MeanScore':>10} {'Assignments':>12}")
print(f"  {'─'*14} {'─'*6} {'─'*6} {'─'*10} {'─'*12}")
for salvo in (1, 2, 3):
    mc = survival_mc(state, SC_C, n_sims=200, salvo_ratio=salvo)
    print(f"  SALVO×{salvo:<8} {mc['survival_rate_pct']:>5.1f}%  {mc['intercept_rate_pct']:>5.1f}%  {mc['mean_score']:>9.1f}  {mc['plan_size']:>11}")

# ─────────────────────────────────────────────────────────────
# SECTION 10 — JSON OUTPUT (machine-readable)
# ─────────────────────────────────────────────────────────────
banner("SECTION 9 · JSON Report Output")

report = {}
for sc_key, sc in SCENARIOS.items():
    r = results[sc_key]
    mc = survival_mc(state, sc["threats"], n_sims=200, salvo_ratio=2)
    report[sc_key] = {
        "title": sc["title"],
        "num_threats": len(sc["threats"]),
        "mcts_score_50iter": round(r["score"], 2),
        "avg_leaked": r["leaked"],
        "assignments": len(r["assignments"]),
        "uncovered_count": len(r["uncovered"]),
        "mc_200iter": mc,
        "coa": [
            {"threat_id": a["threat_id"], "base": a["base"], "effector": a["effector"]}
            for a in r["assignments"]
        ],
    }

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'results')
os.makedirs(OUT_DIR, exist_ok=True)
out_path = os.path.join(OUT_DIR, 'boreal_integration_test.json')
with open(out_path, 'w') as f:
    json.dump(report, f, indent=2)
print(f"\n  Report written to: {out_path}")

# ─────────────────────────────────────────────────────────────
# FINAL PASS / FAIL SUMMARY
# ─────────────────────────────────────────────────────────────
banner("FINAL SUMMARY", colour=C_GRN)

checks = {
    "Boreal bases loaded at correct CSV coordinates": BASES_PASSED == len(EXPECTED_BASES),
    "Capital 'Arktholm (Capital X)' detected":        capital is not None,
    "Scenario A has engine assignments":               len(results["A_BALLISTIC"]["assignments"]) > 0,
    "Scenario B has engine assignments":               len(results["B_SWARM"]["assignments"]) > 0,
    "Scenario C has engine assignments":               len(results["C_SATURATION"]["assignments"]) > 0,
    "JSON report written to data/results/":            os.path.exists(out_path),
}

all_pass = True
for desc, passed in checks.items():
    if passed:
        ok(desc)
    else:
        err(desc)
        all_pass = False

print()
if all_pass:
    print(f"  {C_GRN}{C_BLD}ALL CHECKS PASSED — Boreal theater integration verified.{C_RST}")
else:
    print(f"  {C_RED}{C_BLD}SOME CHECKS FAILED — review output above.{C_RST}")
print()
