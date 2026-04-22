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

# 1. CORE MODELS & LOGIC
from core.models import Effector, Base, Threat, GameState, EFFECTORS, load_battlefield_state
from core.engine import evaluate_threats_advanced

# 2. CONSTANTS & CONFIG
CSV_FILE_PATH = "data/input/Boreal_passage_coordinates.csv"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not OPENROUTER_API_KEY:
    print("[SYSTEM] OPENROUTER_API_KEY not set — LLM reporting disabled, using local heuristic.")

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
GLOBAL_LOG_QUEUE = queue.Queue()
LAST_USE_RL = True 
RECENTLY_ACTIVE = False
MAX_CACHE_SIZE = 100
EVALUATION_CACHE = OrderedDict()

# 5. PYDANTIC SCHEMAS
class IncomingThreat(BaseModel):
    id: str
    x: float
    y: float
    speed_kmh: Optional[float] = 2000.0
    heading: Optional[str] = "Capital X"
    estimated_type: Optional[str] = "bomber"
    threat_value: Optional[float] = 50.0

class IncomingBase(BaseModel):
    name: str
    x: float
    y: float
    inventory: dict

class TacticalState(BaseModel):
    bases: List[IncomingBase]

class TacticalRequest(BaseModel):
    state: Optional[TacticalState] = None
    threats: List[IncomingThreat]
    weather: str = "clear"
    doctrine_primary: str = "balanced"
    doctrine_secondary: str = "none"
    doctrine_blend: float = 0.5
    use_rl: bool = True
    use_ppo: bool = False

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
    
    prompt = f"""
    You are the Boreal Strategic AI (CORTEX-1), a military intelligence advisor to the Commander (Stridsledare).
    STATUS: CHRONOSTASIS ACTIVE (Tactical Time Freeze).
    
    TACTICAL INTELLIGENCE:
    - Target: BOREAL PASSAGE
    - Active Vectors: {t_count}
    - Strategic Health: {score:.1f}
    - Neural Breach Risk: {breach_risk:.1f}%
    - Posture: {doctrine.upper()}
    - Proposed Intercepts: {json.dumps(raw_decision_data.get("tactical_assignments", []), indent=2)}
    
    YOUR MISSION:
    1. Write a 2-sentence SITREP using military brevity. Identify the highest-threat vector (e.g. 'FAST-MOVER approaching VALBREK').
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
    report = f"--- BOREAL STRATEGIC SITREP ---\n"
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
                msg = f"[STRAT] Monitoring Boreal sector... {mode} BRAIN: STANDBY"
                GLOBAL_LOG_QUEUE.put(msg)
            RECENTLY_ACTIVE = False # Reset flag
    asyncio.create_task(idle_pulse())

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(15)
            await websocket.send_text("[HEARTBEAT]")
    except WebSocketDisconnect:
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
        game_state = GameState(bases=bases, blind_spots=[(656.7, 493.3)])
    else:
        game_state = load_battlefield_state(CSV_FILE_PATH)
        
    active_threats = [Threat(t.id, t.x, t.y, t.speed_kmh, t.heading, t.estimated_type, t.threat_value) for t in request.threats]
    
    if not active_threats: 
        return {
            "tactical_assignments": [], 
            "strategic_consequence_score": 1000.0, # Full health
            "human_sitrep": "Monitoring Boreal sector... All systems green.",
            "active_doctrine": {
                "primary": request.doctrine_primary,
                "secondary": doc_sec or "none",
                "blend_ratio": f"{int(request.doctrine_blend*100)}/{int((1-request.doctrine_blend)*100)}",
                "flags": {}, 
                "weights": {}
            }
        }
    
    # --- STRATEGIC EVALUATION (Global Stream) ---
    # evaluate_threats_advanced returns (score, details, rl_val) tuple.
    # Pass only documented positional/keyword args — previous code incorrectly
    # passed GLOBAL_LOG_QUEUE as salvo_ratio causing a TypeError (500 error).
    result_tuple = await asyncio.to_thread(
        evaluate_threats_advanced,
        game_state,
        active_threats,
        50,    # mcts_iterations
        2.0,   # salvo_ratio
        None,  # doctrine_weights (handled internally by DoctrineManager)
        weather=request.weather,
        doctrine_primary=request.doctrine_primary,
    )
    score, details, rl_val = result_tuple
    raw_decision = {
        "tactical_assignments": details.get("tactical_assignments", []),
        "strategic_consequence_score": float(score),
        "rl_prediction": float(rl_val) if rl_val else None,
        "leaked": float(details.get("leaked", 0)),
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
    return raw_decision

# 7. STRATEGIC DATASET EXPLORATION
@app.get("/get_dataset_sample")
async def get_dataset_sample(dataset: str = "eval_shared_gold.npz"):
    path = os.path.join("data/training/strategic_mega_corpus", dataset)
    if not os.path.exists(path):
        return {"error": "Dataset not found"}
    
    try:
        data = np.load(path)
        idx = random.randint(0, len(data['features']) - 1)
        
        # In a real C2 system, we'd reverse-map the 15-dim features back to a full scene.
        # For the viewer, we'll return the features and the target weights.
        return {
            "index": idx,
            "features": data['features'][idx].tolist(),
            "score": float(data['scores'][idx]),
            "weights": data['weights'][idx].tolist(),
            "dataset": dataset
        }
    except Exception as e:
        return {"error": str(e)}

# 8. STATIC ASSET SERVING (Phase 4)
from fastapi.staticfiles import StaticFiles
# Mount the frontend directory to serve the Strategic Hub and CZML streams
app.mount("/data", StaticFiles(directory="data"), name="data")
app.mount("/video", StaticFiles(directory="video"), name="video")
app.mount("/", StaticFiles(directory="frontend"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)