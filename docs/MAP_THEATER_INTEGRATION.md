# Dual-Theater Integration — Complete Audit & Fix Log

**Date:** 2026-04-24  
**Scope:** Both CSV theaters (Sweden + Boreal), all frontend dashboards, backend API

---

## Theater Reference

| Field | Sweden AOR | Boreal Passage |
|---|---|---|
| CSV | `data/Swedish_Military_Installations.csv` | `data/input/Boreal_passage_coordinates.csv` |
| Bases | 11 (air_base, capital, major_city, **naval_base**) | 12 (air_base, capital, major_city) |
| Map SVG | `frontend/sweden-military-map.svg` | `frontend/the-boreal-passage-map.svg` |
| Coord origin | Stockholm (0, 0 km) | SVG origin (0, 0 units) |
| Coord unit | km offset from Stockholm | SVG units (1 unit = 1.667 km) |
| Y-axis | North-positive → SVG requires negation | South-positive (SVG-compatible) |
| SVG origin (OX, OY) | 545, 530 | 0, 0 |
| SVG scale | 0.48 px/km | 1.0 px/unit |
| Backend mode env | `SAAB_MODE=sweden` | `SAAB_MODE=boreal` |
| AI system name | CORTEX-C2 | BOREAL ORACLE |
| Capital | STOCKHOLM | ARKTHOLM |

### Sweden: 11 Installations

| ID | Name | Type | x_km | y_km |
|---|---|---|---|---|
| F21 | Luleå Air Base (F 21) | air_base | 185.0 | 691.0 |
| F16 | Uppsala Air Base (F 16) | air_base | -27.0 | 63.0 |
| VID | Vidsel Air Base | air_base | 95.0 | 728.0 |
| STO | Stockholm (Capital) | capital | 0.0 | 0.0 |
| MUS | Muskö Naval Base | **naval_base** | 4.0 | -46.0 |
| F7 | Såtenäs Air Base (F 7) | air_base | -313.0 | -99.0 |
| F17 | Ronneby Air Base (F 17) | air_base | -172.0 | -340.0 |
| MAL | Malmen Air Base | air_base | -150.0 | -104.0 |
| KRL | Karlskrona Naval Base | **naval_base** | -153.0 | -352.0 |
| GOT | Gotland (Visby Base) | major_city | 16.0 | -186.0 |
| GBG | Gothenburg | major_city | -364.0 | -180.0 |

### Boreal: 12 Installations

| Name | Side | Type | x_km | y_km |
|---|---|---|---|---|
| Northern Vanguard Base | north | air_base | 198.3 | 335.0 |
| Highridge Command | north | air_base | 838.3 | 75.0 |
| Boreal Watch Post | north | air_base | 1158.3 | 385.0 |
| Arktholm (Capital X) | north | capital | 418.3 | 95.0 |
| Valbrek | north | major_city | 1423.3 | 213.3 |
| Nordvik | north | major_city | 140.0 | 323.3 |
| Firewatch Station | south | air_base | 1398.3 | 1071.7 |
| Southern Redoubt | south | air_base | 321.7 | 1238.3 |
| Spear Point Base | south | air_base | 918.3 | 835.0 |
| Meridia (Capital Y) | south | capital | 1225.0 | 1208.3 |
| Callhaven | south | major_city | 96.7 | 1150.0 |
| Solano | south | major_city | 576.7 | 1236.7 |

---

## Bugs Found & Fixed

### Backend

| ID | File | Bug | Fix |
|---|---|---|---|
| B-BE-1 | `agent_backend.py` | CSV path hardcoded to Boreal regardless of `SAAB_MODE` | Dynamic `CSV_FILE_PATHS` dict keyed by `SAAB_MODE` |
| B-BE-2 | `agent_backend.py` | No `/state` or `/theater` endpoint for frontend verification | Added both endpoints with full base list and theater metadata |
| B-BE-3 | `core/models.py` | `naval_base` subtype excluded from filter → Sweden loaded 9/11 bases (missing Muskö + Karlskrona) | Added `'naval_base'` to `valid_subtypes` filter list |
| B-BE-4 | `core/models.py` | File opened with default encoding → Swedish å/ä/ö displayed as garbled characters | Changed `open(..., mode='r')` → `open(..., encoding='utf-8-sig')` to handle BOM and Swedish characters |

### Frontend / UI

| ID | File | Bug | Fix |
|---|---|---|---|
| UI-1 | `viz_engine.js` `callEngine()` | Sent SVG units to backend for Boreal instead of km (backend range gates in km) | Applied `kmFactor = UNIT_TO_KM = 1.667` to Boreal coords before sending |
| UI-2 | `viz_engine.js` `toSvgY()` | Sweden Y-axis not negated → north rendered at SVG bottom | `toSvgY` now returns `SVG_OY - v * SVG_SCALE` for Sweden |
| UI-3 | `viz_engine.js` `callEngine()` | Only `patriot-pac3` and `nasams` sent in inventory; missing `iris-t-sls`, `saab-nimbrix`, `meteor` (Sweden) and `coyote-block2`, `merops-interceptor` (Boreal) | Full theater-specific inventory payloads |
| UI-4 | `dashboard.html` | Theater label hardcoded "Baltic Theater"; page title not theater-aware | Dynamic label from URL param + backend `/theater` fetch |
| UI-5 | `tactical_legacy.html` | SVG map background hardcoded to Boreal; no Sweden base data; no mode-aware title | Dynamic JS sets correct SVG background and title per `?mode=`; added all 11 Sweden bases |
| UI-6 | `viz_engine.js` | `SVG_OX`, `SVG_OY`, `SVG_SCALE` assigned without `let/const` → implicit global variables | Declared with `let SVG_OX, SVG_OY, SVG_SCALE;` |
| UI-DASH-1 | `dashboard.html` live MC audit | Base coords sent as raw SVG units for Boreal (no km conversion); inventory only patriot+nasams | Applied `_mcKmFactor` and full `_mcInv` per theater |
| UI-TACT-1 | `tactical_legacy.html` `draw()` | Canvas drew all entities using raw `x_km * SCALE` — for Sweden this omits the 545/628 origin offset and Y-axis negation | All draw calls changed to `toCanvasX(x_km)` / `toCanvasY(y_km)` |
| UI-TACT-2 | `tactical_legacy.html` threat spawn | Threat spawned at `x_km: 1600` (Boreal far-east); off-screen for Sweden | Theater-aware spawn: Sweden `x_km ≈ 300–400` (eastern Baltic), Boreal `x_km ≈ 1600` |
| UI-TACT-3 | `tactical_legacy.html` physics | Threat heading hardcoded to `"Capital X"` (Boreal capital) | Theater-aware default heading: `"Stockholm (Capital)"` for Sweden |
| UI-IDX-1 | `index.html` | No theater selector — all module links lacked `?mode=` param, all defaulted to Boreal | Added BOREAL / SWEDEN toggle buttons that dynamically rewrite all `data-theater-href` links with correct `?mode=` param |

---

## Coordinate System Reference

### Sweden SVG Mapping
```
// Origin: Stockholm at SVG (545, 530)
SVG_x = 545 + x_km * 0.48
SVG_y = 530 - y_km * 0.48   ← negated because CSV y is north-positive
```

### Boreal SVG Mapping
```
// Origin: SVG top-left (0, 0)
SVG_x = 0 + x_unit * 1.0
SVG_y = 0 + y_unit * 1.0   ← direct (SVG-compatible, south-positive)
// Boreal CSV x_km / y_km → SVG units: divide by UNIT_TO_KM (1.667)
```

### Backend Coordinate Contract
All backend engine calls (`/evaluate_advanced`) expect **km** for both theaters.  
Boreal frontend THEATER_DATA stores SVG units → multiply by `UNIT_TO_KM = 200/120 ≈ 1.667` before sending.  
Sweden THEATER_DATA stores km offsets from Stockholm → send as-is.

---

## Test Results (2026-04-24)

```
DUAL-THEATER INTEGRATION TEST
============================================================

[A] SWEDEN CSV LOADING
  [PASS] Sweden: 11 bases loaded
  [PASS] Sweden: 2 naval bases (Musko + Karlskrona)
  [PASS] Sweden: 5 correct inventory keys
  [PASS] Sweden: Swedish chars decoded correctly (>=3 bases)
  [PASS] Sweden: all coords in valid range

[B] BOREAL CSV LOADING
  [PASS] Boreal: 12 bases loaded
  [PASS] Boreal: 4 correct inventory keys (incl. coyote+merops)
  [PASS] Boreal: all coords in valid range

[C] BACKEND HTTP ENDPOINTS
  [PASS] Port 8001 /theater: mode=boreal
  [PASS] Port 8001 /state: base_count=12
  [PASS] Port 8002 /theater: mode=sweden
  [PASS] Port 8002 /state: base_count=11

[D] SVG MAP FILES
  [PASS] frontend/the-boreal-passage-map.svg exists
  [PASS] frontend/sweden-military-map.svg exists
  [PASS] data/input/sweden-military-map.svg exists

TOTAL: 15/15 checks passed ✓
```

---

## Files Changed

| File | Change Summary |
|---|---|
| `src/core/models.py` | UTF-8-sig encoding, naval_base filter added |
| `src/agent_backend.py` | SAAB_MODE-aware CSV path, theater metadata, `/theater` + `/state` endpoints, SITREP text |
| `frontend/viz_engine.js` | `let` declarations, `toSvgY` Y-flip for Sweden, `callEngine` km conversion + full inventory |
| `frontend/dashboard.html` | Theater label, MC audit km conversion + full inventory |
| `frontend/tactical_legacy.html` | Sweden base array, `toCanvasX/Y` functions, draw code uses them, theater-aware spawn/heading |
| `frontend/index.html` | Theater selector (BOREAL/SWEDEN toggle), `data-theater-href` links |
| `data/input/sweden-military-map.svg` | Created — SVG map with all 11 Swedish installations |
| `frontend/sweden-military-map.svg` | Copied from data/input/ for frontend serving |
| `src/test_dual_theater.py` | New integration test (15 checks, all passing) |

---

## Backend Startup

```powershell
# Boreal mode (default)
cd ruby-stridsledning-ai
$env:SAAB_MODE = "boreal"
$env:PYTHONPATH = "src"
uvicorn src.agent_backend:app --host 0.0.0.0 --port 8000

# Sweden mode
$env:SAAB_MODE = "sweden"
uvicorn src.agent_backend:app --host 0.0.0.0 --port 8000
```

## Frontend Access

Open `frontend/index.html` in a browser (or serve via `python -m http.server 5500 --directory frontend`).  
Select **BOREAL** or **SWEDEN** theater in the portal → all module links automatically pass the correct `?mode=` param.
