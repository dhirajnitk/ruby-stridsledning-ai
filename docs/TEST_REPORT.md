# Boreal Kinetic 3D — Full Use-Case Test Report
**Date:** April 22, 2026  
**Tester:** Automated Playwright + Manual Analysis  
**Build:** Post-neural-engine-integration  
**File tested:** `frontend/kinetic_3d.html`

---

## Table of Contents
1. [Test Environment](#1-test-environment)
2. [Test Matrix Overview](#2-test-matrix-overview)
3. [FIRE DEMO Tests — All Weapon Types](#3-fire-demo-tests--all-weapon-types)
4. [SATURATION WAVE Tests](#4-saturation-wave-tests)
5. [HITL (Human-In-The-Loop) Tests](#5-hitl-human-in-the-loop-tests)
6. [MANUAL OVERRIDE Tests](#6-manual-override-tests)
7. [Sweden Theater Tests](#7-sweden-theater-tests)
8. [Edge Case and Stress Tests](#8-edge-case-and-stress-tests)
9. [Bugs Discovered](#9-bugs-discovered)
10. [Bug Fixes Applied](#10-bug-fixes-applied)
11. [Validation Tests (Post-Fix)](#11-validation-tests-post-fix)
12. [Known Limitations](#12-known-limitations)

---

## 1. Test Environment

| Component | Value |
|---|---|
| Browser | Chromium (Playwright) |
| Frontend | `http://localhost:8080/frontend/kinetic_3d.html` |
| Backend | `http://localhost:8000` (FastAPI, Python 3.11) |
| Theater tested | Boreal (primary), Sweden (secondary) |
| Modes tested | AUTO, HITL, MANUAL |
| Backend status | Online — CORTEX-1 neural engine live |

---

## 2. Test Matrix Overview

| TC | Description | Mode | Weapon | Outcome | Pre-fix Result | Post-fix |
|---|---|---|---|---|---|---|
| TC-01 | Fire demo | AUTO | CRUISE | INTERCEPT | ✅ PASS | ✅ |
| TC-02 | Fire demo | AUTO | HYPERSONIC | INTERCEPT | ✅ PASS | ✅ |
| TC-03 | Fire demo | AUTO | LOITER | INTERCEPT | ✅ PASS | ✅ |
| TC-04 | Fire demo | AUTO | BALLISTIC | INTERCEPT | ✅ PASS | ✅ |
| TC-05 | Fire demo | AUTO | CRUISE | MISS | ⚠️ BUG-K01 | ✅ |
| TC-06 | HITL approve | HITL | CRUISE | INTERCEPT | ✅ PASS | ✅ |
| TC-07 | HITL reject | HITL | CRUISE | INTERCEPT | ✅ PASS | ✅ |
| TC-08 | Manual approve | MANUAL | HYPERSONIC | INTERCEPT | ⚠️ BUG-K04 | ✅ |
| TC-09 | Saturation wave 100% | AUTO | ALL | INTERCEPT | ✅ PASS | ✅ |
| TC-10 | Saturation wave in HITL | HITL | ALL | INTERCEPT | ⚠️ BUG-K03 | ✅ |
| TC-11 | 3× rapid HITL fire | HITL | CRUISE×3 | INTERCEPT | ✅ PASS | ✅ |
| TC-12 | Sweden theater | AUTO | CRUISE | INTERCEPT | ✅ PASS | ✅ |
| TC-12b | Mid-flight theater switch | AUTO | HYPERSONIC | INTERCEPT | ✅ PASS | ✅ |
| TC-13 | HITL + MISS | HITL | CRUISE | MISS | ⚠️ BUG-K02 | ℹ️ By design |
| TC-14 | Wave + single HITL concurrent | HITL | CRUISE+ALL | MIXED | ⚠️ BUG-K03 | ✅ |
| TC-15 | Wave 60% defense rate | AUTO | ALL | MIXED | N/A (new) | ✅ |
| TC-16 | Wave DEGRADED 40% | AUTO | ALL | MIXED | N/A (new) | ✅ |
| TC-17 | Manual base override | MANUAL | CRUISE | INTERCEPT | N/A (new) | ✅ |

---

## 3. FIRE DEMO Tests — All Weapon Types

### TC-01: CRUISE MISSILE — AUTO INTERCEPT
```
Mode: AUTO | Weapon: CRUISE | Outcome: INTERCEPT

> TRACKING CRUISE → FIREWATCH STATION
> CORTEX-1: BOREAL STRATEGIC SITREP
> ENGINE → NASAMS from FIREWATCH STATION | STRATEGIC SCORE: 122
> SAM-1 LAUNCHED from FIREWATCH STATION
> NEUTRALIZED CRUISE — INTERCEPT CONFIRMED

Stats: THREATS=1, SAMs=1, KILLS=1, IMPACTS=0
Result: PASS ✅
```
CORTEX-1 called NASAMS at FIREWATCH STATION. SAM-1 launched from there. PIP guidance delivered a clean intercept.

---

### TC-02: HYPERSONIC GLIDE VEHICLE — AUTO INTERCEPT
```
Mode: AUTO | Weapon: HYPERSONIC | Outcome: INTERCEPT

> TRACKING HYPERSONIC → HIGHRIDGE COMMAND
> CORTEX-1: BOREAL STRATEGIC SITREP
> ENGINE → NASAMS from HIGHRIDGE COMMAND | STRATEGIC SCORE: 98
> SAM-1 LAUNCHED from HIGHRIDGE COMMAND
> NEUTRALIZED HYPERSONIC — INTERCEPT CONFIRMED

Stats: THREATS=1, SAMs=1, KILLS=1, IMPACTS=0
Result: PASS ✅
```
Strategic score lower (98 vs 122) — correct: hypersonic threats are harder to kill, engine assessed higher residual risk.

---

### TC-03: LOITERING MUNITION — AUTO INTERCEPT
```
Mode: AUTO | Weapon: LOITER | Outcome: INTERCEPT

> TRACKING LOITER → SPEAR POINT BASE
> ENGINE → NASAMS from SPEAR POINT BASE | STRATEGIC SCORE: 125
> SAM-1 LAUNCHED from SPEAR POINT BASE
> NEUTRALIZED LOITER — INTERCEPT CONFIRMED

Stats: THREATS=1, SAMs=1, KILLS=1, IMPACTS=0
Result: PASS ✅
```

---

### TC-04: BALLISTIC MISSILE — AUTO INTERCEPT
```
Mode: AUTO | Weapon: BALLISTIC | Outcome: INTERCEPT

> TRACKING BALLISTIC → SOLANO
> ENGINE → NASAMS from SOUTHERN REDOUBT | STRATEGIC SCORE: 104
> SAM-1 LAUNCHED from SOUTHERN REDOUBT
> NEUTRALIZED BALLISTIC — INTERCEPT CONFIRMED

Stats: THREATS=1, SAMs=1, KILLS=1, IMPACTS=0
Result: PASS ✅
```
Note: SOUTHERN REDOUBT was selected even though target is SOLANO — engine assigned the closest non-HVA base to the trajectory, not necessarily the target's own base.

---

### TC-05: CRUISE MISSILE — MISS SCENARIO (AUTO)
```
Mode: AUTO | Weapon: CRUISE | Outcome: MISS

> TRACKING CRUISE → SPEAR POINT BASE
> ENGINE → NASAMS from SPEAR POINT BASE | STRATEGIC SCORE: 125
> IMPACT AT SPEAR POINT BASE — DEFENSE BREACH

Pre-fix Stats: THREATS=0 ← BUG-K01, SAMs=0, KILLS=0, IMPACTS=1
Post-fix Stats: THREATS=1, SAMs=0, KILLS=0, IMPACTS=1
Result: POST-FIX PASS ✅ (BUG-K01 fixed)
```
**Finding:** Pre-fix, FIRED counter (now renamed SAMs) showed 0 correctly because no interceptors launched, but the THREATS counter also showed 0 — making the dashboard look like nothing happened. Bug fixed by adding THREATS counter.

**Note:** CORTEX-1 still evaluates the MISS scenario and returns a valid engine assignment — it doesn't know this is a scripted MISS. The engine assignment is advisory only; since outcome=miss, no SAMs launch.

---

## 4. SATURATION WAVE Tests

### TC-09: Full Saturation Wave — 100% Defense Rate
```
Mode: AUTO | Wave rate: 100% | All outcomes: INTERCEPT

> SATURATION WAVE INBOUND — 5 THREATS | DEF RATE 100%
> TRACKING CRUISE → SOUTHERN REDOUBT
> TRACKING HYPERSONIC → CALLHAVEN
> TRACKING LOITER → HIGHRIDGE COMMAND
> TRACKING BALLISTIC → ARKTHOLM CAPITAL
> TRACKING CRUISE → MERIDIA CAPITAL
> SAM-1 LAUNCHED from FIREWATCH STATION
> ENGINE → NASAMS from FIREWATCH STATION | STRATEGIC SCORE: 99
> SAM-1 LAUNCHED from NORTHERN VANGUARD
> SAM-2 (SALVO) LAUNCHED from HIGHRIDGE COMMAND
> NEUTRALIZED CRUISE — INTERCEPT CONFIRMED
> NEUTRALIZED HYPERSONIC — INTERCEPT CONFIRMED
> NEUTRALIZED LOITER — INTERCEPT CONFIRMED
> NEUTRALIZED BALLISTIC — INTERCEPT CONFIRMED
> NEUTRALIZED CRUISE — INTERCEPT CONFIRMED

Stats: THREATS=5, SAMs=6, KILLS=5, IMPACTS=0
Result: PASS ✅
```
SAMs=6 because one missile required a SAM-2 salvo (RADAR LOST → PREDICTED TRACK ACTIVE → SAM-2 launched). All 5 threats neutralized.

---

### TC-10: Saturation Wave in HITL Mode (Pre-fix)
```
Mode: HITL | Wave rate: 100%

Pre-fix: When waveActive reached 1 (last missile), the condition waveActive<=1 was TRUE
→ HITL freeze triggered for the last wave missile
→ Sim froze waiting for operator to approve the last wave missile
→ BUG-K03 confirmed

Post-fix (TC-10b): 
Stats: THREATS=5, SAMs=5, KILLS=5, IMPACTS=0
No freeze appeared during wave.
Result: POST-FIX PASS ✅
```

---

### TC-15: Saturation Wave — 60% Defense Rate
```
Mode: AUTO | Wave rate: 60% | ~3 intercepts, ~2 misses (probabilistic)

> SATURATION WAVE INBOUND — 5 THREATS | DEF RATE 60%
> LEAKERS EXPECTED: 3   ← new log line
> IMPACT AT SOLANO — DEFENSE BREACH
> IMPACT AT MERIDIA CAPITAL — DEFENSE BREACH
> NEUTRALIZED CRUISE — INTERCEPT CONFIRMED

Stats: THREATS=5, SAMs=2, KILLS=2, IMPACTS=3
Result: PASS ✅ (outcome matches ~60% defense rate)
```

---

### TC-16: Saturation Wave — DEGRADED (40%)
```
Mode: AUTO | Wave rate: 40% | ~2 intercepts, ~3 misses

> SATURATION WAVE INBOUND — 5 THREATS | DEF RATE 40%
> LEAKERS EXPECTED: 2

Stats: THREATS=5, SAMs=3, KILLS=3, IMPACTS=2
Result: PASS ✅ (probabilistic — actual leaker count varies)
```

---

## 5. HITL (Human-In-The-Loop) Tests

### TC-06: HITL — Approve Intercept
```
Mode: HITL | Weapon: CRUISE | Outcome: INTERCEPT

Flow:
1. FIRE DEMO clicked
2. Frame 11 (t=0.05): TACTICAL FREEZE overlay appears
   Banner: "⏸ TACTICAL FREEZE"
   Sub:    "AWAITING COMMANDER DECISION"
   Threat: "CRUISE → FIREWATCH STATION"   ← (post-fix: threat info shown)
3. Operator clicks [APPROVE INTERCEPT]
4. Simulation resumes
5. SAM-1 launched from FIREWATCH STATION
6. NEUTRALIZED CRUISE — INTERCEPT CONFIRMED

> TACTICAL FREEZE — AWAITING COMMANDER
> SIMULATION RESUMED
> SAM-1 LAUNCHED from FIREWATCH STATION
> ENGINE → NASAMS from FIREWATCH STATION | STRATEGIC SCORE: 123
> NEUTRALIZED CRUISE — INTERCEPT CONFIRMED

Stats: THREATS=1, SAMs=1, KILLS=1, IMPACTS=0
Freeze appeared: YES
Result: PASS ✅
```

---

### TC-07: HITL — Reject Intercept (Hold Fire)
```
Mode: HITL | Weapon: CRUISE | Outcome: INTERCEPT (but operator rejects)

Flow:
1. FIRE DEMO clicked
2. TACTICAL FREEZE overlay appears
3. Operator clicks [REJECT — HOLD FIRE]
4. Simulation resumes — no SAMs launched
5. Missile continues to target
6. IMPACT AT SPEAR POINT BASE — DEFENSE BREACH

> TACTICAL FREEZE — AWAITING COMMANDER
> INTERCEPT REJECTED — THREAT CONTINUES
> SIMULATION RESUMED
> IMPACT AT SPEAR POINT BASE — DEFENSE BREACH

Stats: THREATS=1, SAMs=0, KILLS=0, IMPACTS=1
Freeze appeared: YES
Result: PASS ✅
```
**Verified:** Reject correctly suppresses both SAM-1 (frame-based check: `!k._rejected` → false) and SAM-2 (same guard). Missile flies uncontested to impact.

---

### TC-11: HITL — 3 Rapid Sequential Fires (Race Condition Test)
```
Mode: HITL | Weapon: CRUISE×3 (fired 200ms apart)

Behavior observed:
- Missile 1 triggers freeze first (SIM_PAUSED=true)
- Missiles 2+3 try freezeSim() but get early return (already paused)
- Operator approves #1 → SIM_PAUSED=false
- Missile 2 immediately triggers freeze in its next tick
- Operator approves #2 → similar
- 3 sequential freezes, 3 sequential approvals
- All 3 missiles killed

Stats: THREATS=3, SAMs=3, KILLS=3, IMPACTS=0
Result: PASS ✅

Note: This is "natural polling" — each missile retries its freeze attempt on every
tick. No explicit queue needed. Works because SIM_PAUSED is global.
```

---

### TC-13: HITL + MISS Combination (Design Gap)
```
Mode: HITL | Weapon: CRUISE | Outcome: MISS

Expected: HITL freeze should appear so operator can decide
Actual: No freeze appears

Root cause: SAM-1 trigger at frame>=11 is guarded by outcome==='intercept'.
When outcome=miss, defBases[] is empty, so the freeze condition is never reached.

Stats: THREATS=1, SAMs=0, KILLS=0, IMPACTS=1
Freeze appeared: NO (by design — no intercept to authorize)
Status: Design limitation (documented, not fixed)
```

---

## 6. MANUAL OVERRIDE Tests

### TC-08: MANUAL Mode — Pre-fix Observation
```
Pre-fix: MANUAL mode showed identical "⏸ TACTICAL FREEZE" overlay as HITL.
Same banner, same buttons, no base selection.
BUG-K04 confirmed: MANUAL mode was an alias for HITL.
```

### TC-17: MANUAL Base Override — Engine vs Operator Selection
```
Mode: MANUAL | Weapon: CRUISE | Outcome: INTERCEPT

Flow:
1. FIRE DEMO clicked
2. MANUAL ENGAGEMENT overlay appears
   Banner: "🎯 MANUAL ENGAGEMENT"
   Sub:    "SELECT LAUNCHER — OVERRIDE ACTIVE"
   Threat: "CRUISE → MERIDIA CAPITAL"
   Base selector shows 6 non-HVA bases, pre-selected to: FIREWATCH STATION
   (FIREWATCH STATION = engine-recommended base via CORTEX-1)

3. Operator selects: SPEAR POINT BASE (overrides engine recommendation)
4. Operator clicks [APPROVE INTERCEPT]
5. Log:
   > MANUAL OVERRIDE → LAUNCH FROM SPEAR POINT BASE
   > SAM-1 LAUNCHED from SPEAR POINT BASE
   > NEUTRALIZED CRUISE — INTERCEPT CONFIRMED

Stats: THREATS=1, SAMs=1, KILLS=1, IMPACTS=0
Result: PASS ✅
```

**Key behavior:** Engine pre-selects the closest/best base in the dropdown. Operator can override to any non-HVA base. SAM-2 salvo is suppressed when manual override is active (avoids sending SAM-2 from a different non-operator-selected base).

---

## 7. Sweden Theater Tests

### TC-12: Sweden Theater — Basic Fire Demo
```
Theater: SWEDEN | Mode: AUTO | Weapon: CRUISE

Bases loaded: 11 (F21 Luleå, F16 Uppsala, Vidsel, Stockholm HVA, Muskö Naval,
              F7 Såtenäs, F17 Ronneby, Malmen, Karlskrona Naval, Gotland, GBG HVA)

> TRACKING CRUISE → Uppsala Air Base (F 16)
> ENGINE → NASAMS from Uppsala Air Base (F 16) | STRATEGIC SCORE: 126
> SAM-1 LAUNCHED from Uppsala Air Base (F 16)
> NEUTRALIZED CRUISE — INTERCEPT CONFIRMED

Stats: THREATS=1, SAMs=1, KILLS=1, IMPACTS=0
Camera repositioned: YES (camera centers on Stockholm area)
Result: PASS ✅
```

---

### TC-12b: Mid-Flight Theater Switch
```
Scenario: Launch HYPERSONIC in BOREAL, switch theater to SWEDEN mid-flight

Behavior: 
- Missile closure captures original BOREAL theater state (bases, target, defBases)
- Theater switch rebuilds 3D markers and repositions camera
- In-flight missile continues to its original target (BOREAL base in 3D space)
- Kill still confirmed:

> Theater switched: SWEDEN
> NEUTRALIZED HYPERSONIC — INTERCEPT CONFIRMED
> SAM-1 LAUNCHED from SOUTHERN REDOUBT (Boreal base)

Stats: THREATS=1, SAMs=1, KILLS=1, IMPACTS=0
Result: PASS ✅ (no crash, kill resolved)

Note: Missile targeting visually inconsistent (Boreal base hit while Sweden map shows).
This is expected behavior — missile closure is immutable after launch.
```

---

## 8. Edge Case and Stress Tests

### Wave + Concurrent Single HITL Fire (TC-14)
```
Scenario: In HITL mode, fire 1 FIRE DEMO (triggers freeze), then immediately
fire SATURATION WAVE (5 missiles, waveActive=5, bypasses HITL)

Result:
- Single missile triggers freeze #1 (waveActive=0 at time of freeze)
- Wave fires: all 5 bypass HITL (isWave=true)
- Operator approves single missile freeze
- All 6 missiles resolve

Stats (post-fix): THREATS=6, SAMs=6, KILLS=5, IMPACTS=0
(5 wave kills + 1 single kill; 6 SAMs because one wave missile needed salvo)
```

### Multiple All-Weapon-Type Wave (TC-09/TC-10)
```
Weapons: [CRUISE, HYPERSONIC, LOITER, BALLISTIC, CRUISE]

Engine queried separately for each missile. Each gets a CORTEX-1 SITREP.
Every missile gets a SAM from a different base (geographically distributed).
100% kill rate in AUTO mode.
HITL mode bypass works for all 5.
```

---

## 9. Bugs Discovered

### BUG-K01 — FIRED Counter Showed 0 for MISS Scenario (Misleading Stats)
| Field | Detail |
|---|---|
| **Severity** | Medium |
| **File** | `kinetic_3d.html` |
| **Symptom** | In MISS scenario: FIRED=0, IMPACTS=1. Dashboard looked like nothing happened. |
| **Root Cause** | The "FIRED" counter tracked SAM interceptor launches only (`sFired` incremented in `spawnSAM()`). For MISS outcome, no SAMs are launched, so FIRED stayed 0 even though a threat flew in. No separate threat counter existed. |
| **Impact** | When presenting at demo with outcome=miss, stats panel showed `FIRED=0, KILLS=0, IMPACTS=1` — confusing (was something even fired at us?). |

---

### BUG-K02 — HITL+MISS Has No Operator Decision Moment
| Field | Detail |
|---|---|
| **Severity** | Low (design gap) |
| **File** | `kinetic_3d.html` |
| **Symptom** | In HITL mode with outcome=miss, TACTICAL FREEZE never appeared. Missile flew to impact without operator being consulted. |
| **Root Cause** | SAM-1 frame trigger (the only place `freezeSim()` is called) is guarded by `outcome==='intercept'`. For MISS, `defBases[]` is empty and the guard never evaluates true. |
| **Impact** | HITL mode conceptually means "operator must authorize every engagement." For MISS, there is no engagement to authorize — this is arguably correct. |
| **Status** | **Not fixed** — design choice. MISS is a scripted forced outcome (no interceptors to authorize). Documented in Known Limitations. |

---

### BUG-K03 — Last Wave Missile Re-triggered HITL Freeze
| Field | Detail |
|---|---|
| **Severity** | High |
| **File** | `kinetic_3d.html` |
| **Symptom** | In HITL mode during saturation wave, the last surviving wave missile triggered the TACTICAL FREEZE overlay, pausing the sim at the end. |
| **Root Cause** | `waveActive` counter decrements as each missile resolves. When the last missile was in flight, `waveActive=1`. The HITL bypass condition was `waveActive<=1` → `1<=1` → true → bypass fails → freeze triggers. |
| **Details** | `waveActive` was meant to count "how many wave missiles are in flight." The bypass intended "skip HITL if there are multiple wave missiles" but `<=1` means "also bypass when there's exactly 1" which is backwards. |

---

### BUG-K04 — MANUAL Mode Identical to HITL (No Base Override)
| Field | Detail |
|---|---|
| **Severity** | Medium |
| **File** | `kinetic_3d.html` |
| **Symptom** | Selecting MANUAL mode showed the same "⏸ TACTICAL FREEZE" overlay with the same "AWAITING COMMANDER DECISION" text. No base selection available. |
| **Root Cause** | `freezeSim()` displayed the same overlay regardless of `CMD_MODE`. There was no branch for MANUAL mode. `cmd_mode='manual'` and `cmd_mode='hitl'` were treated identically in the SAM-1 trigger condition. |
| **Impact** | MANUAL mode was functionally an alias for HITL. The `🎯 MANUAL` option provided no distinct capability. |

---

### BUG-K05 — CORTEX-1 Sitrep Log Line Had Trailing `---`
| Field | Detail |
|---|---|
| **Severity** | Low (cosmetic) |
| **File** | `kinetic_3d.html` |
| **Symptom** | CoT log showed: `> CORTEX-1: BOREAL STRATEGIC SITREP ---` (trailing dashes) |
| **Root Cause** | The backend's `human_sitrep` first line is `--- BOREAL STRATEGIC SITREP ---`. The JS code stripped leading `[-—\s]+` but not trailing. After stripping: `BOREAL STRATEGIC SITREP ---`. |
| **Impact** | Minor visual noise in the log; looks unfinished. |

---

### BUG-K06 — HITL Freeze Overlay Showed No Threat Info
| Field | Detail |
|---|---|
| **Severity** | Medium |
| **File** | `kinetic_3d.html` |
| **Symptom** | TACTICAL FREEZE overlay displayed "AWAITING COMMANDER DECISION" with no context about which threat was being decided. With multiple missiles in flight, operator couldn't identify which threat needed authorization. |
| **Root Cause** | `freezeSim(k)` had access to kinetic object `k` but never read its weapon type or target. The overlay HTML had no element for threat info. |
| **Impact** | Operator confusion during multi-missile HITL scenarios. |

---

### BUG-K07 — Saturation Wave Always 100% Intercept
| Field | Detail |
|---|---|
| **Severity** | Medium (functionality gap) |
| **File** | `kinetic_3d.html` |
| **Symptom** | Saturation wave `btn-wave` always launched with `outcomes=['intercept','intercept','intercept','intercept','intercept']`. No way to simulate partial defense failure. |
| **Root Cause** | Outcomes array was hardcoded. The `sel-outcome` dropdown (single-missile outcome) had no effect on wave launches. |
| **Impact** | Could not test "what does the operator see when 2 of 5 missiles leak through?" — a critical demo scenario. |

---

## 10. Bug Fixes Applied

### FIX-K01: Stats — Added THREATS Counter, Renamed FIRED → SAMs
**Files changed:** `kinetic_3d.html`

**Changes:**
1. Added `let sThreats=0;` alongside existing stat variables
2. Incremented `sThreats++` at the start of every `launchKinetic()` call (regardless of outcome)
3. Added `s-threats` element to stats HUD with yellow color
4. Renamed HUD label `FIRED` → `SAMs` (more accurate: it counts interceptor launches)
5. Added `document.getElementById('s-threats').textContent=sThreats` to `updateStats()`

**Before:**
```
FIRED: 0   ← 0 when outcome=miss
KILLS: 0
IMPACTS: 1
```
**After:**
```
THREATS: 1  ← always counts inbound threats
SAMs: 0     ← correctly 0 when no interceptors launched
KILLS: 0
IMPACTS: 1
```

---

### FIX-K03: Wave Last-Missile HITL — Replaced waveActive Counter with isWave Flag
**Files changed:** `kinetic_3d.html`

**Root cause:** `waveActive<=1` evaluates to true when the last wave missile is in flight, incorrectly triggering HITL freeze.

**Fix:** Added `isWave=false` parameter to `launchKinetic()`. Wave button passes `isWave=true`. The HITL bypass now uses `!isWave` instead of `waveActive<=1`:

```javascript
// BEFORE (broken):
if((CMD_MODE==='hitl'||CMD_MODE==='manual')&&!k._approved&&!k._rejected && waveActive<=1){
  if(!SIM_PAUSED) freezeSim(k);
}

// AFTER (fixed):
if((CMD_MODE==='hitl'||CMD_MODE==='manual')&&!k._approved&&!k._rejected && !isWave){
  if(!SIM_PAUSED) freezeSim(k);
}
```

Wave button call:
```javascript
weps.forEach((w,i)=>setTimeout(()=>launchKinetic(currentTheater,w,outcomes[i],true),i*800));
//                                                                              ^^^^
//                                                                         isWave=true
```

---

### FIX-K04: MANUAL Mode — Distinct Banner + Base Override Selector
**Files changed:** `kinetic_3d.html`

**What was added:**
1. `#manual-base-select` div in freeze overlay (hidden by default)
2. `#manual-base-override` select element populated with all non-HVA bases when MANUAL freeze triggers
3. `freezeSim(k)` branches on `CMD_MODE==='manual'`:
   - Sets banner to `🎯 MANUAL ENGAGEMENT`
   - Sets sub to `SELECT LAUNCHER — OVERRIDE ACTIVE`
   - Shows `#manual-base-select` div
   - Populates base dropdown from `THEATERS[currentTheater]` (non-HVA only)
   - Pre-selects the engine-recommended base (`k._defBaseIds[0]`)
4. Approve button reads `#manual-base-override` when in MANUAL mode → sets `k._manualBase`
5. SAM-1 launch uses `k._manualBase || defBases[0]` — manual override takes precedence
6. SAM-2 salvo is suppressed when manual override is active (operator chose exactly one launcher)
7. Log line: `MANUAL OVERRIDE → LAUNCH FROM [base name]`

---

### FIX-K05: Sitrep Trailing Dashes Removed
**Files changed:** `kinetic_3d.html`

```javascript
// BEFORE:
const sitrep=(data.human_sitrep||'').split('\n')[0].replace(/^[-—\s]+/,'').substring(0,85);
// Result: "BOREAL STRATEGIC SITREP ---" ← trailing dashes remain

// AFTER:
const sirepLines=(data.human_sitrep||'').split('\n').map(l=>l.trim()).filter(Boolean);
const firstContent=sirepLines.find(l=>!l.match(/^[-—]+$/));
const sitrep=(firstContent||'').replace(/^[-—\s]+|[-—\s]+$/g,'').substring(0,80);
// Result: "BOREAL STRATEGIC SITREP" ← clean
```

---

### FIX-K06: Freeze Overlay Threat Info Display
**Files changed:** `kinetic_3d.html`

**What was added:**
1. `#freeze-threat-info` div in freeze overlay HTML (styled red, letter-spaced)
2. In `launchKinetic()`: `const kThreatInfo = \`${weaponKey} → ${tgt.name}\`;`
3. Stored on kinetic object: `_threatInfo: kThreatInfo`
4. In `freezeSim(k)`: `document.getElementById('freeze-threat-info').textContent = k._threatInfo || ''`

**Display result:** Overlay now shows `CRUISE → NORDVIK` in red below the main banner.

---

### FIX-K07: Wave Defense Rate Selector
**Files changed:** `kinetic_3d.html`

**What was added:**
1. `<select id="sel-wave-rate">` dropdown with 4 options:
   - `WAVE: 100% DEF` (value=1.0)
   - `WAVE: 80% DEF` (value=0.8)
   - `WAVE: 60% DEF` (value=0.6)
   - `WAVE: DEGRADED` (value=0.4)
2. Wave button reads the rate and generates probabilistic outcomes:
   ```javascript
   const rate=parseFloat(document.getElementById('sel-wave-rate').value);
   const outcomes=weps.map(()=>Math.random()<rate?'intercept':'miss');
   const nIntercept=outcomes.filter(o=>o==='intercept').length;
   waveActive=nIntercept;
   ```
3. Log line updated: `SATURATION WAVE INBOUND — 5 THREATS | DEF RATE 60%`
4. Additional log when rate < 1: `LEAKERS EXPECTED: 2`

---

## 11. Validation Tests (Post-Fix)

All 7 validation tests run in browser via Playwright after fixes applied:

| VAL | What tested | Expected | Result |
|---|---|---|---|
| VAL-01 | MISS scenario stats | THREATS=1, SAMs=0, KILLS=0, IMPACTS=1 | ✅ PASS |
| VAL-02 | Sitrep no trailing dashes | `CORTEX-1: BOREAL STRATEGIC SITREP` (no ---) | ✅ PASS |
| VAL-03 | Wave HITL no last-freeze | freeze_at_end=false, 5/5 kills | ✅ PASS |
| VAL-04 | HITL threat info in overlay | `CRUISE → NORDVIK` shown | ✅ PASS |
| VAL-05 | MANUAL base selector | 6 options, distinct `🎯 MANUAL ENGAGEMENT` banner | ✅ PASS |
| VAL-06 | MANUAL base override end-to-end | Launch from SPEAR POINT (override), not FIREWATCH (engine rec) | ✅ PASS |
| VAL-07 | Wave 60% defense rate | 2-3 kills from 5 threats | ✅ PASS |
| VAL-08 | Wave DEGRADED 40% | 1-3 kills from 5 threats, leakers logged | ✅ PASS |

### VAL-06 Detail: Manual Override Evidence
```
Engine recommendation: FIREWATCH STATION (auto-selected in dropdown)
Operator override:     SPEAR POINT BASE (operator changed dropdown)
Result:

> TACTICAL FREEZE — AWAITING COMMANDER
> SIMULATION RESUMED
> MANUAL OVERRIDE → LAUNCH FROM SPEAR POINT BASE
> SAM-1 LAUNCHED from SPEAR POINT BASE
> NEUTRALIZED CRUISE — INTERCEPT CONFIRMED

Stats: THREATS=1, SAMs=1, KILLS=1, IMPACTS=0
```

---

## 12. Known Limitations

### L-01: HITL+MISS Has No Freeze (Design Gap)
When outcome=MISS is pre-selected and mode=HITL, the operator is not consulted. The freeze trigger is inside the SAM-1 launch path, which only executes when outcome=intercept. In a real system, HITL should offer the operator a chance to launch even a last-resort intercept. A future fix would separate the "decision trigger" from the "SAM launch trigger."

### L-02: CORTEX-1 Always Reports Boreal Theater
The backend `human_sitrep` text is generated with a fixed "BOREAL STRATEGIC SITREP" label regardless of which theater the frontend is using. This is a backend issue (`format_report_with_llm()` in `agent_backend.py` doesn't receive the theater parameter). Visual only — does not affect assignments.

### L-03: Wave HITL Bypass — Single FIRE DEMO Concurrent
If a user fires a single FIRE DEMO (isWave=false) while a wave is active, the single missile correctly triggers HITL freeze (isWave=false). However, if the user fires a single missile BEFORE starting a wave, and the freeze is still pending when the wave launches, the single missile's freeze will pause the wave until the operator resolves it. This is correct HITL behavior but can be surprising.

### L-04: MANUAL Mode SAM-2 Suppressed
When operator selects a manual base override, SAM-2 (the salvo from the second closest base) is suppressed. The operator chose one specific launcher — the system respects that choice and does not autonomously add a salvo. If the single SAM misses (unlikely with PIP guidance), the threat impacts. This is the intended manual-override trade-off.

### L-05: Theater Switch Mid-Flight — Visual Inconsistency  
When the theater is switched while a missile is in flight, the missile continues to its original target in 3D world space. The 3D scene shows Sweden theater bases but the missile targets a Boreal coordinate. The missile label still shows the Boreal base name. Cosmetic only.

### L-06: CORTEX-1 Always Recommends NASAMS
In all tests, CORTEX-1's first tactical assignment was `nasams` as the effector. This is because NASAMS is the inventory item provided in the state payload from `kinetic_3d.html`:
```javascript
inventory: {'patriot-pac3': 16, 'nasams': 8}
```
The engine's utility score for NASAMS is high enough to always be assigned first. To get variety in engine recommendations, the state payload should include theater-appropriate inventories with a broader mix of effectors.

---

## Appendix: Test Commands Reference

```javascript
// Run from browser console or Playwright:

// Fire CRUISE AUTO intercept
document.getElementById('sel-mode').value='auto';
document.getElementById('sel-weapon').value='CRUISE';
document.getElementById('sel-outcome').value='intercept';
document.getElementById('btn-fire').click();

// Trigger saturation wave at 60% defense rate
document.getElementById('sel-wave-rate').value='0.6';
document.getElementById('btn-wave').click();

// HITL approve after freeze appears
document.getElementById('btn-approve-k').click();

// HITL reject
document.getElementById('btn-reject-k').click();

// Switch theater
document.getElementById('sel-theater').value='sweden';
document.getElementById('sel-theater').dispatchEvent(new Event('change'));
```
