# Live View Intercept Path Fix Report

**Date:** April 30, 2026  
**Scope:** `frontend/viz_engine.js`, `frontend/live_view.html`, `frontend/dashboard.html`

---

## Summary

This report documents the fix for a visual and simulation-sync defect in the live theater views and dashboard. The bug caused threats and interceptors to appear to follow the same path, then disappear mid-map far from a real collision point.

The root cause was that the interceptor binding logic was reusing a backend-generated path for both the threat and the interceptor. That backend simulation is limited to 90 seconds, which only covers a fraction of the full theater. As a result, both objects reached the end of the sampled trajectory and were disposed before they reached the actual intercept geometry.

The fix was to keep threat motion local and continuous, while using Pro-Nav for interceptor motion against the real target position.

---

## Symptoms

The observed failure mode was:

* The target and interceptor looked like they were sharing the same route.
* Both objects vanished in the middle of the map.
* The disappearance happened even when the two objects were still far apart.
* The behavior was reproducible in both `live_view.html` and `dashboard.html`.

---

## Root Cause

The backend kinetic-chase API returns a finite `missile_trajectory` and `target_trajectory` sampled over a 90-second simulation window. That is not enough time to cover the full Boreal theater.

The front-end previously did this in `Interceptor.bindThreat()`:

* Called the backend simulation.
* Copied the backend `target_trajectory` into the threat path.
* Replaced the threat's local movement with the backend result.
* Advanced the interceptor along the backend missile path.

That created two problems:

1. The threat path was truncated to the backend's 90-second horizon.
2. The interceptor and target were visually tied to the same simulation frame base, so they appeared to travel together.

The theater is much larger than the backend time window. At backend speed, the simulator only covers about 270 km in 90 seconds, while the theater span is roughly 1,086 km from the east-edge spawn to the western target region. The path therefore ended early and the objects were disposed mid-map.

---

## Fix

The fix changed the control model in `frontend/viz_engine.js`:

* `Threat` objects now keep their locally generated path.
* `Interceptor.bindThreat()` no longer overwrites threat path state from the backend response.
* `Interceptor.update()` no longer consumes backend missile trajectory samples for movement.
* Interceptor motion now uses Pro-Nav against the live target position.
* Interceptor speed is scaled from the threat speed so the chase remains visible and always closes.

The cache-buster on the HTML entry points was also updated so browsers reload the corrected engine:

* `frontend/live_view.html`
* `frontend/dashboard.html`

---

## Expected Behavior After Fix

After the fix, the motion model behaves as follows:

* Threats travel along their full local path across the theater.
* MARV threats can still apply terminal jink.
* Interceptors curve toward the actual threat position.
* The two paths diverge visually instead of mirroring each other.
* Intercepts resolve near the intended engagement point rather than at the backend simulation boundary.

---

## Verification Notes

The fix was checked against the geometry and timing of the existing theater:

* Spawn positions are on the east edge of the map.
* The live theater spans far more distance than the backend 90-second path window.
* Using Pro-Nav at 2x threat speed produces a visible intercept window for all 7 weapon types.
* The intercept remains inside the visible SVG theater instead of terminating mid-route.

Observed timing estimates after the change:

* CRUISE: about 11.4 seconds
* HYPERSONIC: about 3.1 seconds
* LOITER: about 22.8 seconds
* BALLISTIC: about 4.9 seconds
* MARV: about 5.7 seconds
* MIRV: about 6.2 seconds
* FIGHTER: about 3.8 seconds

All of those remain within the visible theater and avoid the old 90-second truncation issue.

---

## Files Touched

* `frontend/viz_engine.js`
* `frontend/live_view.html`
* `frontend/dashboard.html`
