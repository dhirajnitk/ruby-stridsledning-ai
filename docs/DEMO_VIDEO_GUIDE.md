# SAAB CORTEX-1 C2 — Demo Video Guide
**Version 10-scene · Recorded 26 Apr 2026 · Runtime ~2 min 10 sec**

---

## Files

| File | Description |
|------|-------------|
| `video/page@*.webm` | Recorded demo video (17.2 MB) |
| `video/demo_final.srt` | Subtitle track — 31 cards · 2:18 total |
| `video/record_demo.js` | Playwright recorder script — re-run to re-record |

Convert to MP4:
```
ffmpeg -i video/page@*.webm -c:v libx264 -crf 18 video/cortex_demo.mp4
```

Burn subtitles:
```
ffmpeg -i video/cortex_demo.mp4 -vf subtitles=video/demo_final.srt video/cortex_demo_subs.mp4
```

---

## Scene Map

| # | Scene | Page | Duration | Key actions |
|---|-------|------|----------|-------------|
| 1 | CORTEX Command Portal | `index.html` | ~8s | Hover all module cards |
| 2 | Boreal Strategic Command | `dashboard.html?mode=boreal` | ~22s | Model select (ELITE V3.5), doctrine cycle (Fortress→Aggressive→Balanced), MARV Bézier animation, Live MC Audit, ENGAGE buttons |
| 3 | Sweden Strategic Command | `dashboard.html?mode=sweden` | ~7s | Map pan, MARV-α/β/γ tracks, zoom |
| 4 | Boreal Tactical — Phase A | `tactical_legacy.html?mode=boreal` | ~13s | 4 bombers spawned, AUTO AI engage, kill counter |
| 4 | Boreal Tactical — Phase B | same | ~11s | HITL enabled, CHRONOSTASIS freeze, COMMENCE ENGAGEMENT |
| 4 | Boreal Tactical — Phase C | same | ~5s | Aggressive doctrine, 8 ghost threats (btn-blind), saturation AI |
| 5 | Sweden AOR Tactical | `tactical_legacy.html?mode=sweden` | ~6s | Theater title, 3 threats, AI auto-engage |
| 6 | Kinetic 3D | `kinetic_3d.html` | ~18s | MARV fire (sinusoidal jink), 2nd fire, saturation wave |
| 7 | Kinetic Chase | `kinetic_chase.html?base=10&threat=marv&dir=north&autorun=1` | ~13s | Pro-Nav S-curves, HUD spotlight, canvas zoom 1.35× |
| 8 | Swarm Physics | `swarm_physics.html` | ~12s | Auto-launch 3×MARV, PAC-3 oblique intercept, canvas zoom 1.4× |
| 9 | Live View | `live_view.html` | ~5s | Telemetry log stream pan |
| 10 | Strategic 3D | `strategic_3d.html` | ~6s | CesiumJS globe, Baltic Sea orbit drag |
| — | Return to Portal | `index.html` | ~3s | Closing frame |

---

## How to Re-record

1. Ensure backend is running:
   ```powershell
   Get-Process python* | Stop-Process -Force
   Start-Process -WindowStyle Hidden `
     -FilePath "C:\Users\dhiraj.kumar\Downloads\Saab\.venv_saab\Scripts\python.exe" `
     -ArgumentList "src/agent_backend.py" `
     -WorkingDirectory "C:\Users\dhiraj.kumar\Downloads\Saab\ruby-stridsledning-ai"
   # Wait 3s, then verify:
   Invoke-WebRequest http://localhost:8000/state -TimeoutSec 5
   ```

2. Run the recorder:
   ```powershell
   cd "C:\Users\dhiraj.kumar\Downloads\Saab\ruby-stridsledning-ai"
   node video/record_demo.js
   ```
   Runtime: ~2 min 10 sec. A new `.webm` file appears in `video/`.

3. The old `.webm` is NOT auto-deleted — rename or delete manually before re-recording if you want a clean slate.

---

## Physics & AI Parameters

### Sinusoidal MARV Jink (simulate_interception.py)
| Threat | jink_magnitude | period | trigger_range | max_g |
|--------|---------------|--------|---------------|-------|
| MARV | 750 m/s | 3.8s | 120 km | 42G |
| MIRV | 520 m/s | 2.2s | 150 km | 38G |
| BALLISTIC | 0 | — | — | 35G |

### Kinetic 3D (kinetic_3d.html)
- Three.js r128 · MIRV child `jinkDecay = 1 - ct × 1.3` (jink persists to 77% of flight)
- `INTERCEPT_FRAC = 0.72` · PAC-3 control point 55% above midpoint

### Dashboard (viz_engine.js)
- MARV Bézier: 14% perpendicular control-point offset
- PAC-3 arc: `_qbez()` quadratic with control point 55% above midpoint
- Terminal jink: sinusoidal growing in last 40%, amplitude 11px
- `PAUSE = 2.2s` post-intercept · `INTERCEPT_FRAC = 0.72`

### Kinetic Chase (kinetic_chase.html)
- Minimum X-span: 20% of Y-span enforced (prevents flat/vertical tracks)
- MIRV dropdown option added · `isMarv = threatType === 'marv' || threatType === 'mirv'`
- Pro-Nav guidance constant N = 4.0

---

## Tactical Display (tactical_legacy.html) Selector Reference

| Element | Selector | Values |
|---------|----------|--------|
| Model selector | `#sel-model` | `elite` `supreme3` `supreme2` `titan` `hybrid` `genE10` |
| Doctrine selector | `#primary-doctrine` | `balanced` `aggressive` `fortress` `economy` `ambush` `saturation` |
| Spawn threat | `#btn-threat` | click — spawns 1 bomber |
| Spawn 8 ghosts | `#btn-blind` | click — saturation ambush formation |
| Execute AI | `#btn-ai` | click — POSTs to /evaluate_advanced |
| HITL mode | `#manual-override` | checkbox — triggers CHRONOSTASIS on AI run |
| Commence | `#btn-commence` | inside `#freeze-overlay` — authorises and unfreezes |
| Kill counter | `#sa-kills` | display element |
| Mode badge | `#sa-mode-badge` | AUTONOMOUS / HITL |
