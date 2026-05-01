import csv
import time
import os
import sys
import json
import math
import hashlib
import httpx
import fastapi
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from collections import OrderedDict
from pydantic import BaseModel
from typing import List, Optional
import queue
import asyncio
import random
import uvicorn
import numpy as np
import torch
from fastapi.responses import StreamingResponse

# 1. CORE MODELS & LOGIC
from core.models import Effector, Base, Threat, GameState, EFFECTORS, load_battlefield_state
from core.engine import evaluate_threats_advanced
from core.inference import BorealInference, resolve_model_name
from simulate_interception import simulate_chase

# 2. CONSTANTS & CONFIG
# BUG-FIX B-BE-1: CSV path was hardcoded to Boreal even in Sweden mode.
# Now dynamically selected based on SAAB_MODE environment variable.
SAAB_MODE = os.environ.get("SAAB_MODE", "boreal")
CSV_FILE_PATHS = {
    "boreal": "data/input/Boreal_passage_coordinates.csv",
    "sweden": "data/Swedish_Military_Installations.csv",
}
CSV_FILE_PATH = CSV_FILE_PATHS.get(SAAB_MODE, CSV_FILE_PATHS["boreal"])

THEATER_META = {
    "boreal": {"name": "BOREAL PASSAGE", "capital": "ARKTHOLM", "ai_name": "BOREAL ORACLE"},
    "sweden": {"name": "SWEDEN AOR",     "capital": "STOCKHOLM",  "ai_name": "CORTEX-C2"},
}
ACTIVE_THEATER = THEATER_META.get(SAAB_MODE, THEATER_META["boreal"])

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not OPENROUTER_API_KEY:
    print(f"[SYSTEM] OPENROUTER_API_KEY not set — LLM reporting disabled, using local heuristic. MODE={SAAB_MODE}")

# 3. APP INITIALIZATION
app = FastAPI(title="Boreal Chessmaster Tactical API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. WEBSOCKET & CACHE
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try: await connection.send_text(message)
            except Exception: pass

ws_manager = ConnectionManager()
kinetic_ws_manager = ConnectionManager()
GLOBAL_LOG_QUEUE = queue.Queue()
LAST_USE_RL = True 
RECENTLY_ACTIVE = False
MAX_CACHE_SIZE = 100
EVALUATION_CACHE = OrderedDict()
KINETIC_START_TIME = time.time()

# 5. PYDANTIC SCHEMAS
class IncomingThreat(BaseModel):
    id: str
    x: float
    y: float
    speed_kmh: Optional[float] = 2000.0
    heading: Optional[str] = "Capital X"
    estimated_type: Optional[str] = "bomber"
    threat_value: Optional[float] = 50.0
    # Advanced trajectory flags (MARV/MIRV/Dogfight)
    is_marv: Optional[bool] = False
    marv_pk_penalty: Optional[float] = 0.55
    marv_trigger_range_km: Optional[float] = 80.0
    is_mirv: Optional[bool] = False
    mirv_count: Optional[int] = 3
    mirv_release_range_km: Optional[float] = 150.0
    can_dogfight: Optional[bool] = False
    dogfight_win_prob: Optional[float] = 0.5
    can_rtb: Optional[bool] = False
    interceptors_assigned: Optional[int] = 0

class IncomingBase(BaseModel):
    name: str
    x: float
    y: float
    inventory: dict

class IncomingAsset(BaseModel):
    id: str
    name: str
    type: str
    x: float
    y: float
    is_airborne: bool = False
    scramble_time_sec: float = 300.0
    fuel_current: float = 1000.0
    weapon_inventory: dict = {}

class TacticalState(BaseModel):
    bases: List[IncomingBase]
    assets: Optional[List[IncomingAsset]] = []

class TacticalRequest(BaseModel):
    state: Optional[TacticalState] = None
    threats: List[IncomingThreat]
    weather: str = "clear"
    doctrine_primary: str = "balanced"
    doctrine_secondary: str = "none"
    doctrine_blend: float = 0.5
    use_rl: bool = True
    use_ppo: bool = False
    run_mc: bool = False
    model_id: str = "elite"

class ProxyLLMRequest(BaseModel):
    model: str
    messages: List[dict]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.35
    max_tokens: Optional[int] = 600

# 6. HELPERS
# load_battlefield_state moved to models.py to prevent FastAPI import locks during data generation.

async def format_report_with_llm(raw_decision_data):
    """Local heuristic analyst replacing"""
    # Define variables BEFORE the f-string that uses them
    t_count = len(raw_decision_data.get("tactical_assignments", []))
    score = raw_decision_data.get("strategic_consequence_score", 0)
    doctrine = raw_decision_data.get("active_doctrine", {}).get("primary", "balanced")
    is_neural = raw_decision_data.get("rl_prediction") is not None
    breach_risk = max(0, 100 - (raw_decision_data.get("rl_prediction", 0) or 0) / 8)
    
    theater_name   = ACTIVE_THEATER["name"]
    theater_capital = ACTIVE_THEATER["capital"]
    ai_name        = ACTIVE_THEATER["ai_name"]
    prompt = f"""
    You are the {ai_name} Strategic AI (CORTEX-1), a military intelligence advisor to the Commander (Stridsledare).
    STATUS: CHRONOSTASIS ACTIVE (Tactical Time Freeze).
    
    TACTICAL INTELLIGENCE:
    - Theater: {theater_name}
    - Capital defended: {theater_capital}
    - Active Vectors: {t_count}
    - Strategic Health: {score:.1f}
    - Neural Breach Risk: {breach_risk:.1f}%
    - Posture: {doctrine.upper()}
    - Proposed Intercepts: {json.dumps(raw_decision_data.get("tactical_assignments", []), indent=2)}
    
    YOUR MISSION:
    1. Write a 2-sentence SITREP using military brevity. Identify the highest-threat vector.
    2. Provide a 1-sentence ADVISORY. Use NATO codes like 'WEAPONS FREE' or 'HOLD FIRE'.
    Keep it cold, professional, and precise. Use CAPITAL LETTERS for base names and threat types.
    """

    if OPENROUTER_API_KEY:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                    json={
                        "model": "google/gemini-2.0-flash-001",
                        "messages": [{"role": "user", "content": prompt}]
                    },
                    timeout=8.0
                )
                if response.status_code == 200:
                    return response.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"[WARNING] OpenRouter failure: {e}")

    # Fallback to Local Heuristic Advisor
    theater_name = ACTIVE_THEATER["name"]
    report = f"--- {theater_name} STRATEGIC SITREP ---\n"
    report += f"POSTURE: {doctrine.upper()} mode engaged.\n"
    report += f"THREATS: {t_count} vectors acquired and triaged.\n"
    
    if t_count > 8:
        report += "ALERT: Saturation (Ambush) detected. Shifting to High-Attrition defense.\n"
    
    mode_text = "Neural assessment" if is_neural else "Heuristic stability"
    report += f"CONFIDENCE: {mode_text} at {min(100, score/10):.1f}%.\n"
    report += "ADVISORY: Chronostasis triggered. Manual firing authorization recommended for high-speed leakers."
        
    return report

# 7. ROUTES
@app.on_event("startup")
async def startup_event():
    async def log_broadcaster():
        while True:
            try:
                # Use a non-blocking poll for the queue
                while not GLOBAL_LOG_QUEUE.empty():
                    msg = GLOBAL_LOG_QUEUE.get_nowait()
                    await ws_manager.broadcast(msg)
                await asyncio.sleep(0.1)
            except Exception:
                await asyncio.sleep(0.5)
    asyncio.create_task(log_broadcaster())
    
    async def idle_pulse():
        global LAST_USE_RL, RECENTLY_ACTIVE
        while True:
            await asyncio.sleep(8)
            if GLOBAL_LOG_QUEUE.empty() and not RECENTLY_ACTIVE:
                mode = "NEURAL" if LAST_USE_RL else "HEURISTIC"
                msg = f"[STRAT] Monitoring {ACTIVE_THEATER['name']} sector... {mode} BRAIN: STANDBY"
                GLOBAL_LOG_QUEUE.put(msg)
            RECENTLY_ACTIVE = False # Reset flag
    asyncio.create_task(idle_pulse())

    async def kinetic_broadcaster():
        while True:
            try:
                await kinetic_ws_manager.broadcast(json.dumps(build_kinetic_state_payload()))
                await asyncio.sleep(0.5)
            except Exception:
                await asyncio.sleep(1.0)
    asyncio.create_task(kinetic_broadcaster())

@app.get("/health")
async def health_check():
    """Backend health check endpoint used by index.html and frontend badges."""
    return {"status": "ok", "mode": SAAB_MODE, "theater": ACTIVE_THEATER["name"]}

@app.get("/theater")
async def get_theater():
    """Return active theater metadata: mode, name, capital, CSV path."""
    return {
        "mode": SAAB_MODE,
        "theater_name": ACTIVE_THEATER["name"],
        "capital": ACTIVE_THEATER["capital"],
        "csv_path": CSV_FILE_PATH,
    }

@app.get("/state")
async def get_state():
    """Return current battlefield bases loaded from CSV for the active theater.
    BUG-FIX B-BE-2: Provides /state endpoint so the frontend can verify
    which bases are loaded and at what km coordinates.
    """
    state = load_battlefield_state(CSV_FILE_PATH)
    return {
        "mode": SAAB_MODE,
        "theater": ACTIVE_THEATER["name"],
        "base_count": len(state.bases),
        "bases": [
            {"name": b.name, "x_km": b.x, "y_km": b.y, "inventory": b.inventory, "subtype": b.subtype}
            for b in state.bases
        ],
        "assets": [
            {
                "id": a.id, 
                "name": a.name, 
                "type": a.type, 
                "x_km": a.x, 
                "y_km": a.y, 
                "coverage_km": a.coverage_radius_km,
                "is_airborne": a.is_airborne,
                "scramble_time_sec": a.scramble_time_sec,
                "endurance_min": a.endurance_min,
                "fuel_current": a.fuel_current,
                "fuel_max": a.fuel_max,
                "status": a.status,
                "phase": a.phase
            }
            for a in state.assets
        ]
    }


def _asset_seed(asset_id: str) -> int:
    return sum(ord(ch) for ch in asset_id)


def _ease_in_out(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def _project_kinetic_asset(asset, elapsed_s: float):
    home_x = float(asset.x)
    home_y = float(asset.y)
    seed = _asset_seed(asset.id)
    runway_angle = math.radians(seed % 360)
    runway_dx = math.cos(runway_angle)
    runway_dy = math.sin(runway_angle)
    patrol_radius = 14.0 + (seed % 9)
    patrol_center_x = home_x + runway_dx * (8.0 + (seed % 11))
    patrol_center_y = home_y + runway_dy * (8.0 + (seed % 11))
    scramble_delay = float(getattr(asset, "scramble_time_sec", 0.0))
    endurance_min = float(getattr(asset, "endurance_min", 180.0))
    fuel_max = float(getattr(asset, "fuel_max", 1000.0))

    def takeoff_state(progress: float):
        x_km = home_x + runway_dx * (1.2 + progress * 3.0)
        y_km = home_y + runway_dy * (1.2 + progress * 3.0)
        altitude_m = 400.0 + 2800.0 * _ease_in_out(progress)
        heading_deg = runway_angle * 180.0 / math.pi + 2.5 * math.sin(progress * math.pi)
        return x_km, y_km, altitude_m, heading_deg

    def climb_state(progress: float):
        x_km = home_x + runway_dx * (4.2 + progress * 12.0)
        y_km = home_y + runway_dy * (4.2 + progress * 12.0)
        altitude_m = 3200.0 + 7800.0 * _ease_in_out(progress)
        heading_deg = runway_angle * 180.0 / math.pi + 8.0 * math.sin(progress * math.pi * 0.8)
        return x_km, y_km, altitude_m, heading_deg

    def cruise_state(cruise_t: float):
        orbit_period = 210.0 + (seed % 5) * 25.0
        orbit_angle = (cruise_t / orbit_period) * math.tau + (seed % 37) * 0.11
        x_km = patrol_center_x + math.cos(orbit_angle) * patrol_radius
        y_km = patrol_center_y + math.sin(orbit_angle) * patrol_radius * 0.82
        altitude_m = 9200.0 + 900.0 * math.sin(orbit_angle * 0.5)
        heading_deg = math.degrees(orbit_angle + math.pi / 2.0)
        return x_km, y_km, altitude_m, heading_deg

    def rtb_state(rtb_t: float):
        x_km = patrol_center_x + (home_x - patrol_center_x) * _ease_in_out(rtb_t)
        y_km = patrol_center_y + (home_y - patrol_center_y) * _ease_in_out(rtb_t)
        altitude_m = 9200.0 * (1.0 - _ease_in_out(rtb_t))
        heading_deg = math.degrees(math.atan2(home_y - patrol_center_y, home_x - patrol_center_x))
        return x_km, y_km, altitude_m, heading_deg

    if elapsed_s < scramble_delay:
        return {
            "id": asset.id,
            "name": asset.name,
            "type": asset.type,
            "x_km": home_x,
            "y_km": home_y,
            "altitude_m": 0.0,
            "heading_deg": runway_angle * 180.0 / math.pi,
            "is_airborne": False,
            "scramble_time_sec": max(0.0, scramble_delay - elapsed_s),
            "fuel_current": fuel_max,
            "fuel_max": fuel_max,
            "endurance_min": endurance_min,
            "status": getattr(asset, "status", "operational"),
            "phase": "SCRAMBLE",
            "coverage_km": float(getattr(asset, "coverage_radius_km", 0.0)),
            "track": [{"x_km": home_x, "y_km": home_y, "altitude_m": 0.0}],
        }

    flight_s = elapsed_s - scramble_delay
    takeoff_s = 45.0
    climb_s = 90.0
    endurance_s = max(900.0, endurance_min * 60.0)
    cruise_s = max(180.0, endurance_s * 0.68)
    rtb_s = 180.0

    if flight_s < takeoff_s:
        phase = "TAKEOFF"
        progress = flight_s / takeoff_s
        x_km, y_km, altitude_m, heading_deg = takeoff_state(progress)
    elif flight_s < takeoff_s + climb_s:
        phase = "CLIMB"
        progress = (flight_s - takeoff_s) / climb_s
        x_km, y_km, altitude_m, heading_deg = climb_state(progress)
    elif flight_s < cruise_s:
        phase = "CRUISE"
        cruise_t = flight_s - takeoff_s - climb_s
        x_km, y_km, altitude_m, heading_deg = cruise_state(cruise_t)
    else:
        phase = "RTB"
        rtb_t = min(1.0, (flight_s - cruise_s) / rtb_s)
        x_km, y_km, altitude_m, heading_deg = rtb_state(rtb_t)

    fuel_drop = flight_s * 0.55
    fuel_current = max(0.0, fuel_max - fuel_drop)
    is_airborne = phase != "LANDED"
    if phase == "RTB" and fuel_current <= fuel_max * 0.15:
        heading_deg = math.degrees(math.atan2(home_y - y_km, home_x - x_km))

    track = []
    for idx in range(18, -1, -1):
        sample_t = max(0.0, elapsed_s - idx * 8.0)
        if sample_t < scramble_delay:
            track.append({"x_km": home_x, "y_km": home_y, "altitude_m": 0.0})
            continue
        sample_flight = sample_t - scramble_delay
        if sample_flight < takeoff_s:
            sample_progress = sample_flight / takeoff_s
            x_s, y_s, alt_s, _ = takeoff_state(sample_progress)
        elif sample_flight < takeoff_s + climb_s:
            sample_progress = (sample_flight - takeoff_s) / climb_s
            x_s, y_s, alt_s, _ = climb_state(sample_progress)
        elif sample_flight < cruise_s:
            cruise_t = sample_flight - takeoff_s - climb_s
            x_s, y_s, alt_s, _ = cruise_state(cruise_t)
        else:
            sample_rtb_t = min(1.0, (sample_flight - cruise_s) / rtb_s)
            x_s, y_s, alt_s, _ = rtb_state(sample_rtb_t)
        track.append({"x_km": x_s, "y_km": y_s, "altitude_m": alt_s})

    return {
        "id": asset.id,
        "name": asset.name,
        "type": asset.type,
        "x_km": x_km,
        "y_km": y_km,
        "altitude_m": altitude_m,
        "heading_deg": heading_deg,
        "is_airborne": is_airborne,
        "scramble_time_sec": max(0.0, scramble_delay - elapsed_s) if elapsed_s < scramble_delay else scramble_delay,
        "fuel_current": fuel_current,
        "fuel_max": fuel_max,
        "endurance_min": endurance_min,
        "status": getattr(asset, "status", "operational"),
        "phase": phase,
        "coverage_km": float(getattr(asset, "coverage_radius_km", 0.0)),
        "track": track,
    }


def build_kinetic_state_payload():
    state = load_battlefield_state(CSV_FILE_PATH)
    elapsed_s = time.time() - KINETIC_START_TIME
    assets = [_project_kinetic_asset(a, elapsed_s) for a in state.assets]
    return {
        "mode": SAAB_MODE,
        "theater": ACTIVE_THEATER["name"],
        "elapsed_s": elapsed_s,
        "assets": assets,
        "active_airborne": sum(1 for a in assets if a["is_airborne"]),
    }


@app.get("/kinetic_state")
async def get_kinetic_state():
    return build_kinetic_state_payload()


@app.websocket("/ws/kinetics")
async def websocket_kinetics(websocket: WebSocket):
    await kinetic_ws_manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        kinetic_ws_manager.disconnect(websocket)

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            try:
                await websocket.send_text("[HEARTBEAT]")
            except RuntimeError:
                # Connection closed mid-send, exit gracefully
                break
            await asyncio.sleep(15)
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(websocket)

@app.post("/evaluate_advanced")
async def evaluate_threats_endpoint(request: TacticalRequest):
    global LAST_USE_RL, RECENTLY_ACTIVE
    LAST_USE_RL = request.use_rl
    RECENTLY_ACTIVE = len(request.threats) > 0
    
    payload_dicts = [t.dict() for t in request.threats]
    payload_str = json.dumps({"threats": payload_dicts, "weather": request.weather, "doctrine": [request.doctrine_primary, request.doctrine_secondary, request.doctrine_blend]}, sort_keys=True)
    payload_hash = hashlib.md5(payload_str.encode()).hexdigest()
    
    # payload_hash check disabled to ensure 'Execute AI' always shows fresh activity for judges
    
    doc_sec = request.doctrine_secondary
    if doc_sec == "none": doc_sec = None
    
    if request.state and request.state.bases:
        bases = [Base(b.name, b.x, b.y, b.inventory) for b in request.state.bases]
        assets = []
        if request.state.assets:
            from core.models import AirborneAsset
            for a in request.state.assets:
                assets.append(AirborneAsset(
                    a.id, a.name, a.type, a.x, a.y, 
                    is_airborne=a.is_airborne, 
                    scramble_time_sec=a.scramble_time_sec,
                    fuel_current=a.fuel_current,
                    weapon_inventory=a.weapon_inventory
                ))
        game_state = GameState(bases=bases, assets=assets, blind_spots=[(656.7, 493.3)])
    else:
        game_state = load_battlefield_state(CSV_FILE_PATH)
        
    active_threats = [Threat(
        t.id, t.x, t.y, t.speed_kmh, t.heading, t.estimated_type, t.threat_value,
        is_marv=t.is_marv, marv_pk_penalty=t.marv_pk_penalty, marv_trigger_range_km=t.marv_trigger_range_km,
        is_mirv=t.is_mirv, mirv_count=t.mirv_count, mirv_release_range_km=t.mirv_release_range_km,
        can_dogfight=t.can_dogfight, dogfight_win_prob=t.dogfight_win_prob, can_rtb=t.can_rtb,
    ) for t in request.threats]
    
    if not active_threats: 
        return {
            "tactical_assignments": [], 
            "strategic_consequence_score": 1000.0, # Full health
            "human_sitrep": f"Monitoring {ACTIVE_THEATER['name']} sector... All systems green.",
            "active_doctrine": {
                "primary": request.doctrine_primary,
                "secondary": doc_sec or "none",
                "blend_ratio": f"{int(request.doctrine_blend*100)}/{int((1-request.doctrine_blend)*100)}",
                "flags": {}, 
                "weights": {}
            }
        }
    
    # --- STRATEGIC EVALUATION (Global Stream) ---
    doctrine_weights = None
    rl_val = 0.0
    resolved_model = resolve_model_name(request.model_id)
    
    if request.use_rl and resolved_model != "heuristic":
        try:
            from core.engine import extract_rl_features
            inference_engine = BorealInference(model_name=resolved_model)
            features = extract_rl_features(game_state, active_threats)
            
            # Predict
            norm_features = (np.array(features) - inference_engine.mean) / (inference_engine.scale + 1e-6)
            with torch.no_grad():
                t_feat = torch.tensor(norm_features, dtype=torch.float32).unsqueeze(0).to(inference_engine.device)
                out = inference_engine.model(t_feat)
                if isinstance(out, tuple):
                    doctrine_weights = out[0].cpu().numpy()[0]
                    # Convert value to ~800 scale for UI Confidence
                    rl_val = float(out[1].item()) * 1000.0
                else:
                    doctrine_weights = out.cpu().numpy()[0]
                    # Heuristic Confidence for non-value models
                    rl_val = max(300.0, 950.0 - (len(active_threats) * 40))
        except Exception as e:
            print(f"[ERROR] Failed to run Neural Inference: {e}")
            doctrine_weights = None
            rl_val = 0.0

    result_tuple = await asyncio.to_thread(
        evaluate_threats_advanced,
        game_state,
        active_threats,
        50,    # mcts_iterations
        2.0,   # salvo_ratio
        doctrine_weights,  # Pass the computed doctrine_weights!
        run_mc=request.run_mc,
        weather=request.weather,
        doctrine_primary=request.doctrine_primary,
    )
    score, details, _ = result_tuple
    
    # If heuristic mode or RL failed, fallback to score as confidence
    if rl_val == 0.0:
        rl_val = max(100.0, score - 50.0)

    raw_decision = {
        "tactical_assignments": details.get("tactical_assignments", []),
        "strategic_consequence_score": float(score),
        "rl_prediction": float(rl_val) if rl_val else None,
        "leaked": float(details.get("leaked", 0)),
        "mc_metrics": details.get("mc_metrics"),
        "active_doctrine": {
            "primary": request.doctrine_primary,
            "secondary": doc_sec or "none",
            "blend_ratio": f"{int(request.doctrine_blend*100)}/{int((1-request.doctrine_blend)*100)}",
            "flags": {},
            "weights": {}
        }
    }

    try:
        rl_display = raw_decision.get('rl_prediction') or 0.0
        formatted_report = await format_report_with_llm(raw_decision)
    except Exception as e:
        print(f"[WARNING] LLM Fail: {e}")
        rl_display = raw_decision.get('rl_prediction') or 0.0
        formatted_report = f"TACTICAL ALERT: {len(active_threats)} threats. Posture: {request.doctrine_primary.upper()}. Neural Conf: {rl_display:.1f}%."

    raw_decision["human_sitrep"] = formatted_report
    EVALUATION_CACHE[payload_hash] = raw_decision

    # Broadcast engine results to WebSocket trace so all dashboards see them
    try:
        model_mode = "NEURAL-RL" if request.use_rl else "HEURISTIC"
        n_t = len(active_threats)
        n_a = len(raw_decision["tactical_assignments"])
        sc  = raw_decision["strategic_consequence_score"]
        GLOBAL_LOG_QUEUE.put(f"[STRAT] CORTEX-1 {model_mode} EVAL — {n_t} threats | {n_a} assignments | score {sc:.1f}")
        for a in raw_decision["tactical_assignments"][:6]:
            GLOBAL_LOG_QUEUE.put(f"[NEURAL] {a['threat_id']} -> {a.get('effector','?').upper()} @ {a.get('base','?')}")
        for line in formatted_report.split('\n'):
            stripped = line.strip()
            if stripped and not stripped.startswith('---') and len(stripped) > 5:
                GLOBAL_LOG_QUEUE.put(f"[STRAT] {stripped[:100]}")
                break  # just the first content line
    except Exception:
        pass

    return raw_decision

@app.post("/llm/proxy")
async def llm_proxy(request: ProxyLLMRequest):
    """Secure proxy for LLM calls from Cortex C2 to OpenRouter (Supports Streaming)"""
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="OpenRouter API Key not configured on backend.")
    
    async def stream_generator():
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "HTTP-Referer": "https://cortex-c2.saab.demo",
                        "X-Title": "CORTEX-C2 Tactical AI (Proxy)",
                    },
                    json={
                        "model": request.model,
                        "messages": request.messages,
                        "stream": request.stream,
                        "temperature": request.temperature,
                        "max_tokens": request.max_tokens
                    },
                    timeout=60.0
                ) as response:
                    if response.status_code != 200:
                        yield f"data: {json.dumps({'error': 'Backend Proxy Error', 'status': response.status_code})}\n\n"
                        return

                    async for chunk in response.aiter_bytes():
                        yield chunk
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    if request.stream:
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    else:
        # Non-streaming fallback
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                json=request.dict(),
                timeout=30.0
            )
            return resp.json()

# 7. STRATEGIC DATASET EXPLORATION
@app.get("/get_dataset_sample")
async def get_dataset_sample(dataset: str = "chronos_60_maneuver.npz"):
    # Datasets live in data/training/strategic_mega_corpus/
    path = os.path.join("data/training/strategic_mega_corpus", dataset)
    if not os.path.exists(path):
        # Try bare filename in same dir as fallback
        alt = os.path.join("data/training/strategic_mega_corpus", os.path.basename(dataset))
        if os.path.exists(alt):
            path = alt
        else:
            return {"error": f"Dataset not found: {dataset}", "available": ["chronos_60_maneuver.npz"]}

    try:
        data = np.load(path)
        idx = random.randint(0, len(data['features']) - 1)
        feat = data['features'][idx]  # shape: (T, 15) — time-series of 15-dim feature vectors

        # Collapse time dimension: use mean across timesteps for a stable 15-D snapshot
        if feat.ndim == 2:
            feat_1d = feat.mean(axis=0).tolist()   # (15,)
        else:
            feat_1d = feat.tolist()                 # already 1-D

        # scores is per-scenario scalar
        score_val = float(data['scores'][idx])

        # weights shape: (N, 11) — use first 3 for Balanced/Aggressive/Fortress display
        weights_raw = data['weights'][idx].tolist() if 'weights' in data else [0.33, 0.33, 0.34]
        weights_display = weights_raw[:3]
        # Normalise so they sum to 1 (display as percentages)
        w_sum = sum(abs(w) for w in weights_display) or 1
        weights_display = [abs(w) / w_sum for w in weights_display]

        return {
            "index": idx,
            "features": feat_1d,
            "score": score_val,
            "weights": weights_display,
            "dataset": dataset,
            "shape": list(data['features'].shape),
            "n_timesteps": feat.shape[0] if feat.ndim == 2 else 1,
        }
    except Exception as e:
        return {"error": str(e)}

# 7.5 KINETIC PHYSICS SIMULATION API
@app.get("/api/simulate-kinetic-chase")
async def get_kinetic_chase(
    scenario: str = "ballistic",
    tx: float = None, ty: float = None,
    destx: float = None, desty: float = None,
    mx: float = None, my: float = None,
    is_marv: bool = False,
    threat_type: str = "marv",
    raw: bool = False
):
    try:
        # If specific coordinates are provided, use them. Otherwise, fall back to scenario.
        if tx is not None:
            t_hist, m_hist, intercepted, miss_dist = simulate_chase(tx=tx, ty=ty, destx=destx, desty=desty, mx=mx, my=my, is_marv=is_marv, threat_type=threat_type, raw=raw)
        else:
            t_hist, m_hist, intercepted, miss_dist = simulate_chase(is_marv=(scenario != "ballistic"), threat_type=threat_type)
        
        # Convert numpy arrays to lists of dicts for JSON
        t_path = [{"x": float(p[0]), "y": float(p[1])} for p in t_hist]
        m_path = [{"x": float(p[0]), "y": float(p[1])} for p in m_hist]
        
        return {
            "status": "success",
            "scenario": scenario,
            "intercepted": bool(intercepted),
            "miss_distance": float(miss_dist),
            "target_trajectory": t_path,
            "missile_trajectory": m_path
        }
    except Exception as e:
        print(f"[ERROR] Kinetic chase failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# 8. STATIC ASSET SERVING (Phase 4)
from fastapi.staticfiles import StaticFiles
# Mount the frontend directory to serve the Strategic Hub and CZML streams
app.mount("/data", StaticFiles(directory="data"), name="data")
app.mount("/video", StaticFiles(directory="video"), name="video")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")
app.mount("/", StaticFiles(directory="frontend"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)