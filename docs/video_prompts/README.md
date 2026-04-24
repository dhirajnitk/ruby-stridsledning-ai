# CORTEX-1 AI VIDEO PRODUCTION PROMPTS
**BOREAL MISSILE DEFENSE — CINEMATIC SCENARIO SERIES**  
**System:** CORTEX-1 v8.3 by SAAB | **Year:** 2026  
**Usage:** Gemini Veo 2, Grok Aurora, or any AI video generator — stitch 10-second clips per scenario

---

## Prompt Style Guidelines

**Visual Style:**
- Dark command center / HUD aesthetic
- Color palette: cyan/teal for friendly, red/orange for hostile, white for intercepts
- Orbitron or similar tactical font for HUD text
- Particle trails on all missiles and interceptors
- Three.js / Cesium inspired 3D tactical geometry
- Nordic/Scandinavian terrain: pine forests, coastlines, Baltic Sea, snow

**AI Prompt Tips:**
- Each clip is designed for ~10 seconds of video
- Use "cinematic," "dramatic," "dark military HUD aesthetic" as style anchors
- For UI clips: "photorealistic futuristic command console, dark background, cyan glow"
- For outdoor clips: "cinematic aerial military shot, Nordic terrain, realistic lighting"
- For space/orbital: "Cesium globe-style visualization, Earth from orbit, translucent sensor arcs"

**Stitching Order:** Use clips 01→08/09/10 per scenario in sequence for a narrative arc.

---

## Scenario Index

| File | Scenario | Theme | Clips | Duration |
|---|---|---|---|---|
| [SCENARIO_01](SCENARIO_01_BOREAL_OPENING_SALVO.md) | Boreal Opening Salvo | First cruise missile wave, Boreal theater | 8 | ~56s |
| [SCENARIO_02](SCENARIO_02_MIRV_BUS_INTERCEPT.md) | MIRV Bus Intercept | Pre-release THAAD kill, all warheads saved | 9 | ~63s |
| [SCENARIO_03](SCENARIO_03_MARV_TERMINAL_JINK.md) | MARV Terminal Jink | Evasive re-entry vehicle, degraded Pk | 8 | ~56s |
| [SCENARIO_04](SCENARIO_04_DOGFIGHT_MERGE.md) | Dogfight Merge | BVR Meteor vs fighters, dogfight resolution | 9 | ~63s |
| [SCENARIO_05](SCENARIO_05_SATURATION_ASSAULT.md) | Saturation Assault | 15-threat mixed wave, autonomous CORTEX-1 | 10 | ~70s |
| [SCENARIO_06](SCENARIO_06_HYPERSONIC_RAID.md) | Hypersonic Raid | THAAD-only 40-second engagement window | 8 | ~56s |
| [SCENARIO_07](SCENARIO_07_CORTEX_HITL_DECISION.md) | CORTEX HITL Decision | Human-in-the-loop operator approval flow | 9 | ~63s |
| [SCENARIO_08](SCENARIO_08_SWEDEN_GOTLAND.md) | Sweden Gotland Defense | Island choke point, 2 batteries vs 9 threats | 9 | ~63s |
| [SCENARIO_09](SCENARIO_09_STRATEGIC_3D_ORBITAL.md) | Strategic 3D Orbital | Cesium globe, CZML replay, orbital sensors | 8 | ~56s |
| [SCENARIO_10](SCENARIO_10_CAMPAIGN_FINAL_STAND.md) | Campaign Final Stand | MAX SATURATION, all types, campaign finale | 10 | ~70s |

**Total:** 88 video clips across 10 scenarios — ~616 seconds (~10 minutes) of stitchable content.

---

## Recommended Production Batches

**Batch A — Core Doctrine (for Hackathon pitch):**  
Scenarios 01, 02, 03, 05 — covers cruise/MIRV/MARV/saturation with clean narrative arc

**Batch B — Human + Fighter + Orbital:**  
Scenarios 04, 07, 09 — shows dogfight doctrine, HITL mode, strategic 3D

**Batch C — Theater + Campaign:**  
Scenarios 06, 08, 10 — hypersonic, Gotland island, final stand climax

---

## Clip Type Reference

| Clip Type | Visual Style | Audio Feel |
|---|---|---|
| Radar detection | Dark scope, sweeping pulse arcs | Tense, sparse tone |
| AI chain-of-thought | Console text scroll, cyan glow | Machine-like, precise |
| SAM launch | Dramatic exhaust, slow motion | Deep thud, whoosh |
| 3D intercept geometry | Three.js style, particle trails | Cinematic |
| Explosion/detonation | Slow-mo fireball, space or stratosphere | Shockwave rumble |
| Scoreboard update | Live stats, HUD elements | Click/score sound |
| Orbital/globe | Cesium style, Earth from space | Ambient, epic |
| Debrief/report | Clean tactical font, data panels | Confident readout |

---

## Scenario Screenshot Reference Assets

**Location:**

All scenario reference screenshots are saved in:

	docs/video_prompts/scenario_0X/

where `0X` is the scenario number (e.g., `scenario_01`, `scenario_02`, ... `scenario_10`).

Each folder contains PNG images named by clip (e.g., `clip01_portal_main.png`, `clip02_dashboard_boreal.png`).

**Usage:**

- These screenshots are direct captures from the live CORTEX-1 UI and 3D engine, matching each scenario and prompt.
- Use them as visual style references when generating video clips with Gemini, Veo, Grok, or other AI video tools.
- Each image corresponds to a specific prompt in the scenario markdown file (e.g., `SCENARIO_01_BOREAL_OPENING_SALVO.md`).
- For best results, match the visual composition, color palette, and HUD elements shown in the screenshots.

**Example Folder Structure:**

	docs/video_prompts/
		scenario_01/
			clip01_portal_main.png
			clip02_dashboard_boreal.png
			...
		scenario_02/
			clip01_kinetic3d_idle.png
			...
		...

**Total:** 44 screenshots across all 10 scenarios.

---

### How to Use with AI Video Generation

1. Open the relevant scenario markdown file for text prompts.
2. Use the corresponding screenshots in `scenario_0X/` as style/scene references for each prompt.
3. When prompting Gemini/Veo/Grok, attach the screenshot as a visual guide or reference the filename in your prompt.
4. Maintain the scenario and clip order for narrative consistency.

These assets ensure visual fidelity and tactical accuracy for all generated video clips.
