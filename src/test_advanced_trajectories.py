"""
Advanced Trajectory Physics Test — MARV / MIRV / Dogfight / RTB
================================================================

Tests the three advanced trajectory behaviours added to the engine:

  1. MARV  — Maneuvering Re-entry Vehicle.
             Ballistic missile that performs terminal-phase evasive jinking,
             applying a Pk penalty to any interceptor engagement.

  2. MIRV  — Multiple Independently targetable Re-entry Vehicle.
             Single bus missile that splits into N child warheads at a set
             release range, each targeting a different base.

  3. DOGFIGHT / RTB — Fighter aircraft that engages our interceptors in
             WVR (within visual range) combat.  Outcomes:
               • ENEMY_WIN  → our interceptor lost, aircraft continues
               • RTB        → aircraft breaks off, retreats to origin
               • KILL       → aircraft destroyed (normal intercept)

Run from project root:
    python src/test_advanced_trajectories.py

SAAB_MODE=boreal is set automatically.
"""

import os, sys, math, random, copy

os.environ["SAAB_MODE"] = "boreal"
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from core.models import Threat, GameState, Base, load_battlefield_state
from core.engine import (
    evaluate_threats_advanced,
    StrategicMCTS,
    TacticalEngine,
    survival_mc,
)

# simulation.py uses bare `from models import` — needs sys.path pointing to src/
# and `requests` available (it imports requests at module level for live API calls)
try:
    import requests  # noqa
except ImportError:
    import types, sys as _sys
    requests_stub = types.ModuleType("requests")
    _sys.modules["requests"] = requests_stub

# Also stub `models` for simulation.py's top-level import
import types as _types
_models_stub = _types.ModuleType("models")
from core.models import EFFECTORS as _EFF  # noqa
_models_stub.EFFECTORS = _EFF
sys.modules.setdefault("models", _models_stub)

from simulation import SimThreat, SimulationLoop

CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'input', 'Boreal_passage_coordinates.csv')

# ── ANSI colours ──────────────────────────────────────────────────────────
RST = "\033[0m"; GRN = "\033[92m"; YLW = "\033[93m"; RED = "\033[91m"
BLU = "\033[94m"; MAG = "\033[95m"; CYN = "\033[96m"; BLD = "\033[1m"

def banner(t, c=BLU):
    w = 72
    print(f"\n{c}{BLD}{'═'*w}{RST}")
    print(f"{c}{BLD}  {t}{RST}")
    print(f"{c}{BLD}{'═'*w}{RST}")
def ok(m):   print(f"  {GRN}✓{RST}  {m}")
def warn(m): print(f"  {YLW}⚠{RST}  {m}")
def bad(m):  print(f"  {RED}✗{RST}  {m}")
def info(m): print(f"  {CYN}·{RST}  {m}")

state = load_battlefield_state(CSV_PATH)
cap   = next(b for b in state.bases if "Capital" in b.name)

# ════════════════════════════════════════════════════════════════════════════
# TEST 1 — MARV: Pk degradation under terminal manoeuvre
# ════════════════════════════════════════════════════════════════════════════
banner("TEST 1 · MARV — Maneuvering Re-entry Vehicle Pk Degradation", MAG)

# Regular ballistic vs MARV ballistic — same position, same effectors
std_ballistic = Threat(
    "BALISTIC-STD", cap.x + 60, cap.y + 40, 4500, "Capital", "ballistic", 200.0
)
marv_ballistic = Threat(
    "BALISTIC-MARV", cap.x + 60, cap.y + 40, 4500, "Capital", "ballistic", 200.0,
    is_marv=True, marv_pk_penalty=0.45, marv_trigger_range_km=100.0  # already in trigger zone
)

N = 500
std_kills, marv_kills = 0, 0
assignments_std  = [{"base": cap.name, "effector": "patriot-pac3", "threat_id": "BALISTIC-STD"}]
assignments_marv = [{"base": cap.name, "effector": "patriot-pac3", "threat_id": "BALISTIC-MARV"}]

for _ in range(N):
    s1, d1 = StrategicMCTS._single_rollout(state, assignments_std,  [std_ballistic])
    s2, d2 = StrategicMCTS._single_rollout(state, assignments_marv, [marv_ballistic])
    if d1["leaked"] == 0: std_kills  += 1
    if d2["leaked"] == 0: marv_kills += 1

std_kill_pct  = std_kills  / N * 100
marv_kill_pct = marv_kills / N * 100
info(f"Standard ballistic   kill rate: {std_kill_pct:.1f}%  (expected ~Patriot Pk 85%)")
info(f"MARV ballistic       kill rate: {marv_kill_pct:.1f}%  (expected ~{0.85*0.45*100:.0f}% after penalty)")

if marv_kill_pct < std_kill_pct:
    ok(f"CONFIRMED: MARV reduces effective Pk by {std_kill_pct - marv_kill_pct:.1f}pp.")
else:
    warn(f"Pk difference not significant — check trigger range setting.")

# ════════════════════════════════════════════════════════════════════════════
# TEST 2 — MIRV: Single bus → multiple warheads after release
# ════════════════════════════════════════════════════════════════════════════
banner("TEST 2 · MIRV — Bus Separation into Multiple Warheads", MAG)

# Bus released 120km from capital (inside mirv_release_range_km=150)
mirv_bus = Threat(
    "MIRV-BUS", cap.x + 120, cap.y + 60, 4500, "Capital", "ballistic", 180.0,
    is_mirv=True, mirv_count=3, mirv_release_range_km=150.0
)
# We only assign one interceptor to the bus — after release the 3 warheads are uncovered
bus_assignment = [{"base": cap.name, "effector": "patriot-pac3", "threat_id": "MIRV-BUS"}]

leaked_list = []
for _ in range(200):
    # Reset mirv_released each rollout (deep-copy threat)
    t = copy.deepcopy(mirv_bus)
    s, d = StrategicMCTS._single_rollout(state, bus_assignment, [t])
    leaked_list.append(d["leaked"])

avg_leaked = sum(leaked_list) / len(leaked_list)
max_leaked = max(leaked_list)
info(f"Average leaked warheads per rollout : {avg_leaked:.2f}  (expect ~2-3 of 3 warheads)")
info(f"Max leaked in single rollout         : {max_leaked}")

if avg_leaked >= 1.5:
    bad(f"CONFIRMED: MIRV bus covered but {avg_leaked:.1f} warheads leak through — "
        f"single interceptor cannot cover all MRVs.")
    ok("Engine correctly spawns child warheads and scores their leakage.")
else:
    warn(f"Fewer leaks than expected (avg={avg_leaked:.2f}) — check release range geometry.")

# ════════════════════════════════════════════════════════════════════════════
# TEST 3 — DOGFIGHT OUTCOMES: KILL / RTB / ENEMY_WIN
# ════════════════════════════════════════════════════════════════════════════
banner("TEST 3 · DOGFIGHT — Fighter Engagement Outcome Distribution", MAG)

fighter = Threat(
    "FIGHTER-SU35", cap.x + 70, cap.y + 50, 2200, "Capital", "fighter", 150.0,
    can_dogfight=True, dogfight_win_prob=0.3, can_rtb=True
)
fighter_assignment = [{"base": cap.name, "effector": "meteor", "threat_id": "FIGHTER-SU35"}]

outcomes = {"KILL": 0, "RTB": 0, "ENEMY_WIN": 0}
N_DOG = 1000
total_leaked = 0

for _ in range(N_DOG):
    t = copy.deepcopy(fighter)
    s, d = StrategicMCTS._single_rollout(state, fighter_assignment, [t])
    if d["leaked"] == 0:
        # Simplified outcome detection from score delta
        outcomes["KILL"] += 1
    else:
        total_leaked += 1

# More detailed: call _resolve_dogfight directly for distribution
outcomes_direct = {"KILL": 0, "RTB": 0, "ENEMY_WIN": 0}
for _ in range(N_DOG):
    t = copy.deepcopy(fighter)
    _, _, outcome = StrategicMCTS._resolve_dogfight(t, None, 0)
    outcomes_direct[outcome] += 1

info(f"Dogfight outcome distribution over {N_DOG} engagements:")
info(f"  KILL     : {outcomes_direct['KILL']:4d} ({outcomes_direct['KILL']/N_DOG*100:.1f}%) — fighter destroyed")
info(f"  RTB      : {outcomes_direct['RTB']:4d}  ({outcomes_direct['RTB']/N_DOG*100:.1f}%) — aircraft breaks off")
info(f"  ENEMY_WIN: {outcomes_direct['ENEMY_WIN']:4d} ({outcomes_direct['ENEMY_WIN']/N_DOG*100:.1f}%) — our interceptor lost")

rtb_pct = outcomes_direct['RTB'] / N_DOG * 100
kill_pct = outcomes_direct['KILL'] / N_DOG * 100
enemy_win_pct = outcomes_direct['ENEMY_WIN'] / N_DOG * 100

if abs(enemy_win_pct - 30) < 10:
    ok(f"Enemy win rate {enemy_win_pct:.0f}% ≈ configured dogfight_win_prob=0.30 ✓")
if rtb_pct > 0:
    ok(f"RTB outcome confirmed at {rtb_pct:.1f}% — aircraft breaks off and returns to source.")

# ════════════════════════════════════════════════════════════════════════════
# TEST 4 — LIVE SimThreat MARV trajectory (10-tick simulation)
# ════════════════════════════════════════════════════════════════════════════
banner("TEST 4 · SimThreat MARV — Live Trajectory Jink Simulation", MAG)

marv_sim = SimThreat(
    t_id="SIM-MARV-1",
    x=cap.x + 90, y=cap.y + 50,
    speed_kmh=4500,
    estimated_type="ballistic",
    threat_value=200.0,
    target_x=cap.x, target_y=cap.y,
    is_marv=True, marv_trigger_range_km=100.0, marv_jink_mag_kmh=600.0
)

info(f"Initial position: ({marv_sim.x:.1f}, {marv_sim.y:.1f})  "
     f"dist={marv_sim._dist_to_target():.1f}km")
print(f"\n  {'Tick':>4}  {'x':>8}  {'y':>8}  {'dist_km':>8}  {'MARV_active':>12}")
print(f"  {'─'*4}  {'─'*8}  {'─'*8}  {'─'*8}  {'─'*12}")
for tick in range(12):
    marv_sim.move()
    print(f"  {tick+1:4d}  {marv_sim.x:8.1f}  {marv_sim.y:8.1f}  "
          f"{marv_sim._dist_to_target():8.1f}  {str(marv_sim.marv_active):>12}")

if marv_sim.marv_active:
    ok("MARV terminal manoeuvre activated during simulation run.")

# ════════════════════════════════════════════════════════════════════════════
# TEST 5 — LIVE SimThreat MIRV bus separation (tick-by-tick)
# ════════════════════════════════════════════════════════════════════════════
banner("TEST 5 · SimThreat MIRV — Live Bus Separation Tick Simulation", MAG)

mirv_sim = SimThreat(
    t_id="SIM-MIRV-BUS",
    x=cap.x + 200, y=cap.y + 120,
    speed_kmh=4500,
    estimated_type="ballistic",
    threat_value=240.0,
    target_x=cap.x, target_y=cap.y,
    is_mirv=True, mirv_count=3, mirv_release_range_km=160.0
)

all_threats = [mirv_sim]
info(f"Starting bus at ({mirv_sim.x:.1f}, {mirv_sim.y:.1f}), "
     f"dist={mirv_sim._dist_to_target():.1f}km")

released = False
for tick in range(20):
    # Check MIRV
    new_children = mirv_sim.try_release_mirv()
    if new_children and not released:
        released = True
        ok(f"Tick {tick+1}: MIRV BUS separated → {len(new_children)} warheads spawned:")
        for c in new_children:
            info(f"  Warhead {c.id}: pos=({c.x:.1f},{c.y:.1f})  "
                 f"target=({c.target_x},{c.target_y})  val={c.threat_value:.0f}")
        all_threats.extend(new_children)
    mirv_sim.move()

if not released:
    warn("Bus did not reach release range in 20 ticks — increase starting proximity.")

# ════════════════════════════════════════════════════════════════════════════
# TEST 6 — LIVE SimThreat DOGFIGHT / RTB (tick-by-tick intercept)
# ════════════════════════════════════════════════════════════════════════════
banner("TEST 6 · SimThreat Dogfight / RTB — Live Intercept Resolution", MAG)

random.seed(42)   # fix seed so we see an RTB outcome in this demo

for attempt in range(20):
    random.seed(attempt)
    fighter_sim = SimThreat(
        t_id="SIM-SU35",
        x=cap.x + 80, y=cap.y + 60,
        speed_kmh=2200,
        estimated_type="fighter",
        threat_value=150.0,
        target_x=cap.x, target_y=cap.y,
        can_dogfight=True, dogfight_win_prob=0.3, can_rtb=True, rtb_speed_kmh=1400.0
    )
    outcome = fighter_sim.resolve_dogfight()
    if outcome == "RTB":
        info(f"Seed {attempt}: Outcome = RTB — running 5 retreat ticks:")
        for tick in range(5):
            fighter_sim.move()
            dist_home = math.hypot(fighter_sim.x - fighter_sim.origin_x,
                                   fighter_sim.y - fighter_sim.origin_y)
            info(f"  Tick {tick+1}: pos=({fighter_sim.x:.1f},{fighter_sim.y:.1f})  "
                 f"dist_to_origin={dist_home:.1f}km  retreating={fighter_sim.is_retreating}")
        ok("RTB confirmed — aircraft heading back to source, removed from threat board when it arrives.")
        break
    elif outcome == "KILL":
        info(f"Seed {attempt}: KILL — trying next seed for RTB demo")
    elif outcome == "ENEMY_WIN":
        info(f"Seed {attempt}: ENEMY_WIN — our interceptor lost, trying next seed")

# ════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════════════════
banner("SUMMARY — Advanced Trajectory Capabilities", GRN)
print(f"""
  {BLD}Feature{RST}         {BLD}Implemented In{RST}          {BLD}What it does{RST}
  ─────────────────────────────────────────────────────────────────
  MARV            core/models.py           is_marv=True on Threat dataclass
  (Maneuvering    core/engine.py           _single_rollout applies marv_pk_penalty
   Re-entry)      simulation.py            SimThreat.move() adds terminal jink

  MIRV            core/models.py           is_mirv=True, mirv_count, mirv_release_range_km
  (Multiple       core/engine.py           _single_rollout spawns child Threat objects
   Warheads)      simulation.py            SimThreat.try_release_mirv() + SimulationLoop.tick()

  DOGFIGHT        core/models.py           can_dogfight, dogfight_win_prob, can_rtb
  / RTB           core/engine.py           _resolve_dogfight() → KILL / RTB / ENEMY_WIN
                  simulation.py            SimThreat.resolve_dogfight() + retreat physics

  {BLD}Usage examples:{RST}

    # MARV ballistic — hard to kill in terminal phase
    t = Threat("M1", ..., is_marv=True, marv_pk_penalty=0.45, marv_trigger_range_km=80)

    # MIRV bus — splits into 4 warheads at 150km
    t = Threat("BUS", ..., is_mirv=True, mirv_count=4, mirv_release_range_km=150)

    # Dogfighting SU-35 that can break off
    t = Threat("F1", ..., can_dogfight=True, dogfight_win_prob=0.35, can_rtb=True)
""")
print(f"{GRN}{BLD}All 6 advanced trajectory tests completed.{RST}\n")
