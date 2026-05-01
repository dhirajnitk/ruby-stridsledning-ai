# BOREAL INTERCEPT VERIFICATION GUIDE
# Manual test procedure to verify all intercept fixes are working correctly

## Prerequisites
- Backend running on http://127.0.0.1:8000
- Browser open (Chrome/Edge recommended for best visualization)

## Test 1: Dashboard Mid-Theater Intercepts
**Goal**: Verify interceptors fire mid-flight (~50% of path) and chase is visually clear

1. Open: http://127.0.0.1:8000/dashboard.html?mode=boreal
2. Click "AUTO" mode
3. Select weapon: CRUISE
4. Click "Initialize Intercept"
5. **OBSERVE**:
   - Threat (red circle, r=8) spawns from east edge (right side of map)
   - Interceptor (cyan circle, r=8) launches from base when threat is ~50% across map
   - Cyan circle CHASES red circle horizontally (2D lateral pursuit)
   - Interceptor and threat circles CONVERGE mid-map (not near base edge)
   - On collision: Cyan blast effect appears
   - Threat disappears AFTER blast (not before)
   
   ✅ PASS if: Cyan circle is visible throughout chase, collision happens mid-map
   ❌ FAIL if: Dots disappear before collision, interceptor fires late (near base)

6. Repeat with BALLISTIC missile:
   - Threat at high altitude (150km) but interceptor at low altitude (5km)
   - **OBSERVE**: Interceptor still chases laterally (ignores altitude difference)
   - Kill check uses 2D x,z distance (not full 3D distance)
   
   ✅ PASS if: Interceptor doesn't climb vertically, collision happens on 2D map

## Test 2: Kinetic 3D View Camera Framing
**Goal**: Verify camera shows threats (east), bases (scattered), targets (all positions)

1. Open: http://127.0.0.1:8000/kinetic_3d.html?theater=boreal
2. Select weapon: CRUISE, outcome: INTERCEPT
3. Click "▶ FIRE DEMO"
4. **OBSERVE**:
   - Camera view shows full theater
   - Can see: threat spawning east (~X=1.5M), bases west/center, target nodes
   - No entities are cut off or outside viewport
   - Camera is positioned high and south for good overview
   
   ✅ PASS if: All entities visible in frame throughout demo
   ❌ FAIL if: Threats spawn off-screen, bases not visible, need to orbit to see action

5. Repeat with MARV and MIRV to test with high-altitude ballistic threats

## Test 3: Saturation Wave (Multiple Simultaneous Intercepts)
**Goal**: Verify multiple interceptors can engage simultaneously without premature disposal

1. Open: http://127.0.0.1:8000/live_view.html?mode=boreal
2. Select weapon: CRUISE
3. Click "⚡ SATURATION WAVE"
4. **OBSERVE**:
   - 5-6 threats spawn from east
   - Multiple cyan interceptors launch from different bases
   - Each cyan circle chases its assigned red threat
   - Multiple cyan blasts occur across the map (not all in same spot)
   - Threats don't disappear before their interceptor reaches them
   
   ✅ PASS if: Multiple clear intercepts visible, dots don't vanish prematurely
   ❌ FAIL if: Threats disappear mid-flight without blast, interceptors fire too late

## Test 4: Interceptor Visibility (Circle2D Element)
**Goal**: Verify interceptor has large visible marker (not just 3px path glyph)

1. Open: http://127.0.0.1:8000/dashboard.html?mode=boreal
2. Zoom browser to 150% (Ctrl+=)
3. Launch CRUISE intercept
4. **OBSERVE**:
   - Interceptor has TWO visual elements:
     a) Large cyan circle (r=8 SVG units) with glow filter
     b) Small 3px path marker (legacy, subtle)
   - The large circle is PRIMARY visual indicator
   - Circle is clearly visible even at 100% zoom
   
   ✅ PASS if: Cyan circle r=8 is prominent and tracks interceptor position
   ❌ FAIL if: Only seeing tiny 3px marker, no large circle visible

## Test 5: Pro-Nav 2D Guidance (No Vertical Climb)
**Goal**: Verify interceptor chases threat's X,Z position (not full 3D including altitude)

1. Open: http://127.0.0.1:8000/dashboard.html?mode=boreal
2. Launch BALLISTIC missile (high altitude: 150km)
3. **OBSERVE** in browser dev console (F12):
   - Log output shows threat altitude ~150000 (150km)
   - Log shows interceptor altitude stays ~5000-10000 (5-10km)
   - Interceptor Y velocity is near zero (not climbing rapidly)
   - Collision still occurs because kill check uses 2D distance
   
   ✅ PASS if: Interceptor stays at low altitude, collision uses 2D x,z only
   ❌ FAIL if: Interceptor climbs toward threat altitude, chase is 3D not 2D

## Expected Results Summary
All tests should PASS with the following observable behaviors:
- Interceptors launch ~50% into threat's flight path (mid-theater)
- Cyan circles (r=8) are clearly visible throughout chase
- Collision happens mid-map with cyan blast effect
- Threats don't disappear before interceptor reaches them
- Kinetic 3D view frames all entities (no off-screen spawns)
- Pro-Nav guidance is 2D lateral (interceptor doesn't climb for high-altitude threats)

## Debugging Failed Tests
If any test fails, check:
1. **viz_engine.js line 1412**: Pro-Nav `flatTarget` should use interceptor's Y altitude
2. **viz_engine.js line 84-100**: Effector ranges scaled (PAC3=550km, THAAD=750km)
3. **viz_engine.js line 1370-1377**: Interceptor `circle2D` element created with r=8
4. **viz_engine.js line 1477**: Kill threshold = 25000 (not 12000)
5. **viz_engine.js line 1702**: Threat path-end disposal blocked when interceptors active
6. **kinetic_3d.html line 321-324**: Boreal camera at (800k, 1200k, 2600k)

## Automated Test Execution
Run Playwright automated tests to capture video evidence:
```powershell
# Optimized demo (focused on intercept showcase)
npx playwright test tests/test_optimized_demo.spec.js --config=scratch/playwright.optimized.config.js

# Full mega demo (comprehensive feature tour)
npx playwright test --config=scratch/playwright.mega.config.js
```

Video output:
- Optimized: `scratch/optimized-demo/<folder>/video.webm`
- Mega: `scratch/mega-demo/<folder>/video.webm`

Open HTML report to watch recorded video:
```powershell
npx playwright show-report scratch/optimized-report
```
