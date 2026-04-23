# Coordinate Systems Reference

> UNCLASSIFIED · EXERCISE · PROTOTYPE S28  
> Last updated: 2026-04-24

The Boreal Chessmaster system uses **three distinct coordinate systems** depending on context. Mixing them is a known source of bugs. This document defines each system, where it is used, and how to convert between them.

---

## System 1 — Geographic (WGS84) — lat/lon

**Unit:** decimal degrees  
**Origin:** Earth centre (WGS84 ellipsoid)  
**Stockholm reference:** 59.3293°N, 18.0686°E

### Where it is used

- `data/Swedish_Military_Installations.csv` — `latitude`, `longitude` columns
- `src/fetch_real_clutter.py` — OpenSky API returns `lat`, `lon`
- `src/training/mega_data_factory.py` — civilian clutter conversion from real traffic

### Example values

| Site | Latitude | Longitude |
|------|----------|-----------|
| Stockholm (STO) | 59.3293°N | 18.0686°E |
| Luleå Air Base (F21) | 65.5436°N | 22.1211°E |
| Gotland (GOT) | 57.6591°N | 18.3458°E |
| Gothenburg (GBG) | 57.7089°N | 11.9746°E |

### Conversion to System 2 (Theater-km)

The CSV file pre-computes this conversion. For custom conversion:

```python
x_km = (lon - 18.0686) * 111.0 * math.cos(math.radians(59.3293))
y_km = (lat - 59.3293) * 111.0
```

Note: 1 degree latitude ≈ 111 km. Longitude degrees are shorter by `cos(lat)` ≈ 0.573 at Stockholm's latitude, giving ~63.5 km per degree longitude.

---

## System 2 — Theater-km (Cartesian, km from Stockholm)

**Unit:** kilometres  
**Origin:** Stockholm (STO) = (0, 0)  
**Axes:** x = east (+) / west (-), y = north (+) / south (-)

This is the **canonical simulation coordinate system** used by all active Python backend code.

### Where it is used

- `data/Swedish_Military_Installations.csv` — `x_km`, `y_km` columns
- `data/input/Boreal_passage_coordinates.csv` — `x_km`, `y_km` columns
- `src/core/engine.py` — `extract_rl_features()`, threat distance calculations
- `src/core/models.py` — `EFFECTORS` range_km values, Base coordinates
- `src/generate_theater_batches.py` — threat spawn positions (60–140 km from bases)
- `src/precompute_truth.py` — scenario generation (300–800 km east of target)
- `src/training/train_models.py` — synthetic scenario generation

### Key positions (System 2)

| Site | x_km | y_km | Notes |
|------|------|------|-------|
| Stockholm (origin) | 0 | 0 | Reference point |
| Gotland (GOT) | +16 | −186 | Island, southeast |
| Muskö Naval (MUS) | +4 | −46 | Underground mountain base |
| Uppsala (F16) | −27 | +63 | North of Stockholm |
| F17 Ronneby | −172 | −340 | Southern fighter wing |
| F21 Luleå | +185 | +691 | Northernmost wing |
| Gothenburg (GBG) | −364 | −180 | Western port |
| Baltic Passage Alpha | +400 | +200 | Key threat ingress vector |
| Baltic Passage Beta | +400 | −200 | Southern ingress vector |

### Effector ranges (System 2 km)

All ranges in `src/core/models.py::EFFECTORS`:

| Effector | range_km | Engagement envelope |
|---------|---------|-------------------|
| Saab Nimbrix | 5 | Point defence bubble |
| Merops drone interceptor | 3 | Very close-in |
| LIDS EW jammer | 8 | Local jamming dome |
| RBS-70 | 9 | SHORAD belt |
| IRIS-T SLS | 12 | Short-range layer |
| Coyote Block 2 | 15 | C-UAS extended range |
| NASAMS (AMRAAM) | 40 | Medium-range area |
| Patriot PAC-3 MSE | 120 | Theatre BMD layer |
| Meteor BVRAAM | 150 | Long-range fighter kill |

### Threat spawn geometry

`src/generate_theater_batches.py` spawns threats at a random bearing, 60–140 km from a randomly chosen target base:

```python
bearing = random.uniform(0, 2 * math.pi)
dist    = random.uniform(60, 140)           # km
sx = base_x + dist * math.cos(bearing)      # Theater-km
sy = base_y + dist * math.sin(bearing)
```

---

## System 3 — SVG / Legacy Units (screen pixels, ~1 unit = 1.666 km)

**Unit:** SVG canvas pixels / legacy map units  
**Scale:** 1 unit ≈ 1.666 km (derived from original map design: Stockholm placed at ~(418, 95) to give reasonable screen coverage)  
**Origin:** Varies per SVG map — the front-end SVG uses (418.3, 95.0) as an approximate Stockholm position

### Where it is used

- `src/core/engine.py` — `EFFECTORS` range values in this file are in SVG units (not km!)
- Legacy batch JSON files — older scenario files have `start_x`, `start_y`, `target_x`, `target_y` in SVG units
- `data/boreal_ground_truth_scenarios.json` — some entries have very large coordinates (artefact of unit confusion)
- Frontend tactical SVG maps (`frontend/tactical_legacy.html`)

### Example values (System 3)

| Site | SVG x | SVG y | System 2 equivalent |
|------|-------|-------|-------------------|
| Capital X (Stockholm proxy) | 418.3 | 95.0 | (0, 0) km |
| Northern Vanguard Base | 198.3 | 335.0 | (−367, +400) km approx |
| Highridge Command | 838.3 | 75.0 | (+700, −33) km approx |

### Effector ranges in core/engine.py (km — corrected 2026-04-24)

The `range_km` field in `src/core/engine.py`'s EFFECTORS is **in kilometres** and is compared directly against km-coordinate distances. A previous misleading comment claimed "SVG units; 1 unit ≈ 1.666 km" — this was incorrect.

**Bug fixed 2026-04-24:** All 9 effector `range_km` values in `engine.py` were 3–40× too large. Corrected values now match `cortex_c2.html::EFFECTORS_DEF` (meters ÷ 1000) and `models.py`:

| Effector | Old (wrong) km | Corrected km | Source of truth |
|---------|---------------|-------------|----------------|
| Patriot PAC-3 | 300 | **120** | cortex_c2.html: 120,000m |
| IRIS-T SLS | 120 | **12** | models.py: 12 km |
| Saab Nimbrix | 50 | **5** | models.py: 5 km |
| Meteor BVRAAM | 400 | **150** | models.py: 150 km |
| NASAMS | 250 | **40** | cortex_c2.html: 40,000m |
| Coyote Block 2 | 80 | **15** | models.py: 15 km |
| Merops interceptor | 30 | **3** | models.py: 3 km |
| **THAAD** | **500** | **200** | cortex_c2.html: 200,000m |
| LIDS EW | 60 | **8** | models.py: 8 km |

Note: The `7200` number in the THAAD Effector constructor is `speed_kmh` (interceptor speed ≈ Mach 6), **not** the range. The `range_km` field is at position 4 of the constructor — it was 500, now corrected to 200.

---

## 4. The Coordinate System Confusion Bug (Known Issue)

`data/boreal_ground_truth_scenarios.json` contains threat coordinates that look like:
```json
"x": -332235.2316764972,
"y": 190978.25139559328
```

These are in **metres** (from an absolute geographic origin), not km. The generating script multiplied degree-offsets by 111,000 instead of 111. These scenarios still work correctly for the MCTS Oracle (which uses the x,y values only for relative distance calculations), but they cannot be plotted on the System 2 theater map without conversion:

```python
# Convert boreal_ground_truth coordinates to System 2 (km)
x_km = threat['x'] / 1000.0
y_km = threat['y'] / 1000.0
```

All **current** scenario generators (`generate_theater_batches.py`, `precompute_truth.py`) correctly use **System 2 (km)**.

---

## 5. Conversion Reference Table

| From | To | Formula |
|------|----|---------|
| WGS84 (lat/lon) → Theater-km | `x_km = (lon − 18.0686) × 63.5; y_km = (lat − 59.3293) × 111.0` | ×111 for lat, ×cos(59.33°)×111 for lon |
| Theater-km → SVG units | `svg_x = x_km × 0.6 + 418.3; svg_y = −y_km × 0.6 + 95.0` | Approx only — depends on SVG viewport |
| SVG units → Theater-km | `x_km = (svg_x − 418.3) / 0.6; y_km = −(svg_y − 95.0) / 0.6` | Inverse of above |
| Metres → Theater-km | `x_km = x_m / 1000.0` | Simple scale |

---

## 6. Which System Each File Uses

| File / Script | Coordinate system |
|---------------|------------------|
| `data/Swedish_Military_Installations.csv` | Both: lat/lon + System 2 (x_km, y_km) |
| `data/input/Boreal_passage_coordinates.csv` | System 2 (x_km, y_km) |
| `data/boreal_ground_truth_scenarios.json` | metres (legacy bug — see §4) |
| `data/ground_truth_scenarios.json` | System 2 (km) |
| `data/input/simulated_campaign_batch_*.json` | System 2 (km) |
| `data/blind_test/blind_campaign_batch_*.json` | System 3 / SVG units |
| `src/core/models.py` EFFECTORS ranges | **System 2 (km)** |
| `src/core/engine.py` EFFECTORS ranges | **System 2 (km)** ← fixed 2026-04-24 |
| `src/core/engine.py` extract_rl_features | System 2 (km) distances |
| `src/training/mega_data_factory.py` | metres (m), internal use only |
| `frontend/cortex_c2.html` bases | System 3 (SVG units) for rendering |
| `frontend/cortex_c2.html` EFFECTORS_DEF ranges | **metres** (e.g. THAAD: 200,000m) |
| `frontend/kinetic_3d.html` bases | System 3 (SVG units) × SC → metres in 3D scene |
| `frontend/strategic_3d.html` entities | WGS84 (lat/lon via CesiumJS CZML) |

---

## 7. Frontend Viewer Coordinate Systems

### 7.1 CORTEX-C2 Dashboard (`frontend/cortex_c2.html`)

**Coordinate system: System 3 (SVG units) for rendering; metres for range checks**

The tactical radar scope is an SVG with `viewBox="0 0 860 560"`. All base and threat positions are expressed in SVG units (same scale as the Sweden/Boreal tactical map).

```javascript
const UNIT_TO_M = 1666;  // 1 SVG unit ≈ 1666 metres

// Range check in buildCandidates():
const dx = (refX - b.x) * UNIT_TO_M;   // → metres
const dy = (refY - b.y) * UNIT_TO_M;   // → metres
const dist = Math.sqrt(dx*dx + dy*dy);  // → metres
if (dist > eff.range) return;           // eff.range also in metres ✓
```

**EFFECTORS_DEF range values are in metres:**

| Effector | range (m) | range (km) |
|---------|-----------|-----------|
| THAAD | 200,000 | 200 |
| PAC-3 | 120,000 | 120 |
| NASAMS | 40,000 | 40 |
| HELWS | 5,000 | 5 |
| C-RAM | 1,500 | 1.5 |

**Closest threat display** in `_extendMetrics()`:
```javascript
const d = Math.hypot(t.spawnX - b.x, t.spawnY - b.y) * 1.666;  // → km
m.closestKm = Math.round(minDist);  // reported in km
```

**Scenario threat positions** (spawnX, spawnY) are in SVG units, e.g., `spawnX:251, spawnY:720` for a threat approaching ARK from the south.

**Kinematic bridge call to Python backend** converts SVG → km for the threat speed/distance display:
```javascript
const distKm = Math.round(Math.hypot(spawnX - tgtBase.x, spawnY - tgtBase.y) * 1.666);
```

---

### 7.2 Kinetic 3D Viewer (`frontend/kinetic_3d.html`)

**Coordinate system: metres in THREE.js world space**

```javascript
const SC = 1666;  // 1 SVG unit → 1666 metres in 3D world
// Comment: SVG scale bar = 120 units / 200 km → 1 unit = 1.666 km = 1666 m

// Base placement in 3D:
mesh.position.set(b.x * SC, 0, b.y * SC);  // metres on XZ plane
```

All base coordinates come from the same SVG-unit system as `THEATER_BASES` and `SWEDEN_BASES`:
```javascript
{id:'F21', name:'Luleå Air Base (F 21)', x:185, y:691}
// → 3D position: (185 × 1666, 0, 691 × 1666) = (308,210m, 0, 1,151,106m)
```

**Weapon trajectory altitudes** (metres):
| Weapon | Peak altitude |
|--------|-------------|
| Loitering munition | 30,000 m (30 km) |
| Cruise missile | 60,000 m (60 km) |
| Hypersonic glide | 120,000 m (120 km) |
| Ballistic missile | 180,000 m (180 km) |

**Camera** starts at `position.set(0, 600,000, 1,200,000)` = 600 km altitude, 1,200 km back. Far clip plane: 12,000,000 m (12,000 km). This means the entire Sweden theater (~1500 km tall) fits in one view.

**Theater centers** (SVG units, used to focus the camera):
```javascript
const THEATER_CENTERS = {
  sweden: { x:   0, z:   0, ... },   // Stockholm origin
  boreal: { x: 456, z: 391, ... },   // Boreal map centre
};
```

---

### 7.3 Strategic 3D Viewer (`frontend/strategic_3d.html`)

**Coordinate system: WGS84 (real Earth latitude/longitude/altitude via CesiumJS)**

The viewer loads CZML files (e.g., `scenario_hostile.czml`, `scenario_commercial.czml`) which define entity positions in:
- **Latitude** (decimal degrees)
- **Longitude** (decimal degrees)  
- **Altitude** (metres above WGS84 ellipsoid)

Cesium converts these to its internal ECEF (Earth-Centred Earth-Fixed) coordinate system automatically.

```javascript
const viewer = new Cesium.Viewer('cesiumContainer', {
    terrain: Cesium.Terrain.fromWorldTerrain(),  // real Earth terrain
    ...
});
// Entities loaded from CZML have real-world WGS84 positions
commercialSource = await Cesium.CzmlDataSource.load('scenario_commercial.czml');
```

CZML entity positions look like:
```json
{
  "id": "HOSTILE-001",
  "position": {
    "cartographicDegrees": [18.07, 59.33, 10000]
  }
}
```

(lon=18.07, lat=59.33 = Stockholm; altitude=10,000 m above ground)

This is the **only viewer that shows real geographic positions**. The other two use synthetic SVG/meter coordinates.

---

### 7.4 Coordinate Summary Across All Three Viewers

| Viewer | Position units | Range units | Altitude units | Real-world? |
|--------|--------------|-------------|---------------|------------|
| CORTEX-C2 (`cortex_c2.html`) | SVG units | metres | N/A (2D) | No — abstract |
| Kinetic 3D (`kinetic_3d.html`) | SVG × 1666 = metres | N/A (no range check) | metres | No — abstract |
| Strategic 3D (`strategic_3d.html`) | WGS84 deg | N/A | metres AGL | **Yes** |
| Python backend (`engine.py`) | km | km | N/A (2D) | No — abstract |
