# Dashboard Path Sync Design
**Date:** April 29, 2026
**Status:** Implemented

## Overview
The dashboard now renders live target and interceptor motion from the same backend physics model instead of independent frontend approximations. This keeps the visual track aligned with engine truth and makes the collision event visible when the interceptor actually reaches the threat.

## Design Goals
- Show the real engine-driven target path and interceptor path on the dashboard.
- Keep the visual origin consistent with the launching base position.
- Ensure the target and effector converge in the same coordinate frame.
- Preserve a clear, readable operator UI while using backend physics as the source of truth.

## Implementation Design
### 1. Shared backend physics run
When an interceptor is bound to a threat, the frontend requests a single `/api/simulate-kinetic-chase` result and uses that response to drive both:
- the interceptor missile trajectory
- the target trajectory

This avoids the earlier split where threat and interceptor were replayed from separate simulations and drifted apart visually.

### 2. Theater-space coordinate restoration
The backend returns relative missile coordinates after re-centering the simulation so the interceptor launch point is at the origin. The frontend now adds the base coordinates back before rendering, so the interceptor path starts from the correct launcher location on the dashboard.

### 3. Frame-rate alignment
Backend trajectories are produced at 100 ms physics ticks. Frontend playback advances at the dashboard render rate, so the visual replay steps through the backend samples at a slower rate to stay in sync with the physics timeline.

### 4. Collision and blast timing
A collision is now shown when the interceptor reaches the backend-reported intercept state. If the backend marks the run as intercepted, the dashboard displays the kill blast at the actual convergence point.

## User-Facing Result
- Threat tracks now follow the engine path instead of a local approximation.
- Effectors launch from their correct base position.
- Collision/blast visuals appear where the engine says the intercept occurs.
- The dashboard remains the operator view, but its motion is now physics-authored.

## Notes
- Decorative tactical preview tracks remain separate from live engine threats.
- The live simulation path is the authoritative source for collision display.
- The design is shared by dashboard and live-view pages through the same visualization engine.
