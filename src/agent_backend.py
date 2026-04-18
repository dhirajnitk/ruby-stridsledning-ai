import csv
import time
import os
import sys
import json
import math
import hashlib
import httpx
import asyncio
import queue
import hashlib
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from collections import OrderedDict
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# 1. CORE MODELS & LOGIC
from models import Effector, Base, Threat, GameState, EFFECTORS
from engine import evaluate_threats_advanced

# 2. CONSTANTS & CONFIG
CSV_FILE_PATH = "data/input/Boreal_passage_coordinates.csv"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")

# 3. APP INITIALIZATION
app = FastAPI(title="Boreal Chessmaster API", description="Tactical Air Defense Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(f"VALIDATION ERROR: {exc}")
    return JSONResponse(status_code=400, content={"detail": str(exc.errors())})

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
MAX_CACHE_SIZE = 100
EVALUATION_CACHE = OrderedDict()

# 5. PYDANTIC SCHEMAS
class IncomingThreat(BaseModel):
    id: str
    x: float
    y: float
    speed_kmh: float
    heading: str
    estimated_type: str
    threat_value: float

class TacticalRequest(BaseModel):
    state: dict
    threats: List[IncomingThreat]
    weather: str = "clear"
    doctrine_primary: str = "balanced"
    doctrine_secondary: Optional[str] = None
    doctrine_blend: float = 0.7
    use_rl: bool = True

# 6. HELPERS
def load_battlefield_state(filepath) -> GameState:
    bases = []
    try:
        with open(filepath, mode='r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['side'] == 'north' and row['subtype'] in ['air_base', 'capital']:
                    name = row['feature_name']
                    # Inject inventory based on base type/importance
                    inv = {"sam": 10, "fighter": 4, "drone": 15}
                    if "Capital" in name: inv = {"sam": 20, "fighter": 0, "drone": 0}
                    
                    bases.append(Base(name, float(row['x_km']), float(row['y_km']), inv))
    except Exception as e: print(f"Error loading state: {e}")
    
    # Fallback if CSV fails
    if not bases:
        bases = [
            Base("Northern Vanguard Base", 198.3, 335.0, {"sam": 10, "fighter": 4, "drone": 15}),
            Base("Highridge Command", 838.3, 75.0, {"sam": 10, "fighter": 4, "drone": 15}),
            Base("Capital X", 418.3, 95.0, {"sam": 20, "fighter": 0, "drone": 0})
        ]
    return GameState(bases=bases, blind_spots=[(656.7, 493.3)])

async def format_report_with_llm(raw_decision_data):
    system_prompt = "You are a military formatting assistant. Take the raw JSON data and format it into a professional SITREP. Do NOT change facts."
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "google/gemini-2.5-flash", "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": json.dumps(raw_decision_data)}]}
    async with httpx.AsyncClient() as client:
        response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=10.0)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']

# 7. ROUTES
@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect: ws_manager.disconnect(websocket)

@app.post("/evaluate_advanced")
async def evaluate_threats_endpoint(request: TacticalRequest):
    payload_dicts = [t.dict() for t in request.threats]
    payload_str = json.dumps({"threats": payload_dicts, "weather": request.weather, "doctrine": [request.doctrine_primary, request.doctrine_secondary, request.doctrine_blend]}, sort_keys=True)
    payload_hash = hashlib.md5(payload_str.encode()).hexdigest()
    
    if payload_hash in EVALUATION_CACHE: return EVALUATION_CACHE[payload_hash]
    
    doc_sec = request.doctrine_secondary
    if doc_sec == "none": doc_sec = None
    
    game_state = load_battlefield_state(CSV_FILE_PATH)
    active_threats = [Threat(t.id, t.x, t.y, t.speed_kmh, t.heading, t.estimated_type, t.threat_value) for t in request.threats]
    
    if not active_threats: 
        return {
            "tactical_assignments": [], 
            "strategic_consequence_score": 0, 
            "human_sitrep": "No active threats on radar.",
            "active_doctrine": {
                "primary": request.doctrine_primary,
                "secondary": doc_sec or "none",
                "blend_ratio": f"{int(request.doctrine_blend*100)}/{int((1-request.doctrine_blend)*100)}",
                "flags": load_battlefield_state(CSV_FILE_PATH).bases[0].inventory if False else {}, # Placeholder for idle
                "weights": {}
            }
        }
    
    log_queue = queue.Queue()
    async def queue_reader():
        while True:
            try:
                msg = await asyncio.to_thread(log_queue.get, True, 0.1)
                if msg == "DONE": break
                await ws_manager.broadcast(msg)
            except queue.Empty: pass
    
    reader_task = asyncio.create_task(queue_reader())
    try:
        raw_decision = await asyncio.to_thread(
            evaluate_threats_advanced, 
            game_state, 
            active_threats, 
            500, 
            log_queue, 
            request.weather, 
            2.0, 
            request.doctrine_primary, 
            doc_sec, 
            request.doctrine_blend,
            request.use_rl
        )
    finally:
        log_queue.put("DONE")
        await reader_task

    try:
        formatted_report = await format_report_with_llm(raw_decision)
    except Exception as e:
        print(f"[WARNING] LLM Fail: {e}")
        formatted_report = f"TACTICAL ALERT: {len(active_threats)} threats. Posture: {request.doctrine_primary.upper()}. Neural Conf: {raw_decision.get('rl_prediction', 0):.1f}%."

    raw_decision["human_sitrep"] = formatted_report
    EVALUATION_CACHE[payload_hash] = raw_decision
    return raw_decision

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)