import csv
import time
import os
import sys
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

# Auto-correct working directory if the user runs the script from inside 'src/'
if os.path.basename(os.getcwd()) == "src":
    os.chdir("..")

import json
import math
import hashlib
import httpx
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from collections import OrderedDict
import queue
from pydantic import BaseModel
from typing import List
import uvicorn

from models import Effector, Base, Threat, GameState, EFFECTORS
from engine import evaluate_threats_advanced

# Constants
CSV_FILE_PATH = "data/input/Boreal_passage_coordinates.csv"
# Best practice: Set this in your environment variables before running, or replace the string temporarily for testing.
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")

app = FastAPI(title="Boreal Chessmaster API", description="Tactical Air Defense Engine")

# Allow cross-origin requests from our local HTML file
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (POST, GET, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Global WebSocket Manager to stream logs directly to the dashboard
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
            try:
                await connection.send_text(message)
            except Exception:
                pass

ws_manager = ConnectionManager()

# Global LRU cache to store previous evaluations without overloading memory
MAX_CACHE_SIZE = 100
EVALUATION_CACHE = OrderedDict()

# Pydantic model defining the expected JSON format from your Map UI
class IncomingThreat(BaseModel):
    id: str
    x: float
    y: float
    speed_kmh: float
    heading: str
    estimated_type: str
    threat_value: float

def load_battlefield_state(filepath) -> GameState:
    """Reads the CSV and extracts locations into our GameState."""
    bases = []
    try:
        with open(filepath, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['record_type'] == 'location' and row['side'] == 'north':
                    inventory = {}
                    if row['subtype'] == 'air_base':
                        inventory = {"Fighter": 4, "Drone": 10, "SAM": 0}
                    elif row['subtype'] == 'capital':
                        inventory = {"Fighter": 0, "Drone": 0, "SAM": 4}
                        
                    if inventory:
                        bases.append(Base(
                            name=row['feature_name'],
                            x=float(row['x_km']),
                            y=float(row['y_km']),
                            inventory=inventory
                        ))
    except FileNotFoundError:
        print(f"Error: Could not find the file at {filepath}")
    
    # Define known blind spot (North Strait Island West coordinates from CSV)
    return GameState(bases=bases, blind_spots=[(656.7, 493.3)])


async def format_report_with_llm(raw_decision_data):
    """LLM LAYER: Only used for beautification, formatting, and making it human-readable."""
    
    system_prompt = "You are a military formatting assistant. Take the provided raw JSON data and format it into a professional, easy-to-read military SITREP (Situation Report) paragraph. Do NOT change any facts, numbers, or logic. Just make it read well for a human commander."
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "google/gemini-2.5-flash", 
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(raw_decision_data)}
        ]
        # We removed the strict JSON response format because we want human-readable text now
    }
    
    print("Sending raw data to Gemini for beautification...")
    
    max_retries = 3
    async with httpx.AsyncClient() as client:
        for attempt in range(1, max_retries + 1):
            try:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                return result['choices'][0]['message']['content']
            except httpx.RequestError as e:
                print(f"API Request failed on attempt {attempt}/{max_retries}: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(2)
    return None

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text() # Keeps the connection open
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

@app.post("/api/evaluate-threats")
async def evaluate_threats_endpoint(threats_payload: List[IncomingThreat], weather: str = "clear"):
    """API Endpoint: Receives threats from UI, runs Hungarian+MCTS Engine, returns SITREP."""
    
    # 0. Check Cache: Generate a deterministic hash of the incoming threats
    payload_dicts = [t.dict() for t in threats_payload]
    payload_str = json.dumps({"threats": payload_dicts, "weather": weather}, sort_keys=True)
    payload_hash = hashlib.md5(payload_str.encode()).hexdigest()
    
    if payload_hash in EVALUATION_CACHE:
        # Silently return cache to prevent spamming the console every 3 seconds during auto-polling
        return EVALUATION_CACHE[payload_hash]
        
    # 1. Load the fresh static state
    game_state = load_battlefield_state(CSV_FILE_PATH)
    
    # 2. Convert incoming API JSON payload into our internal Data Classes
    active_threats = []
    for t in threats_payload:
        active_threats.append(Threat(
            id=t.id, x=t.x, y=t.y, speed_kmh=t.speed_kmh,
            heading=t.heading, estimated_type=t.estimated_type,
            threat_value=t.threat_value
        ))
        
    if not active_threats:
        raise HTTPException(status_code=400, detail="No threats provided.")
        
    log_queue = queue.Queue()
    
    async def queue_reader():
        while True:
            try:
                # Poll the queue continuously without blocking the FastAPI event loop
                msg = await asyncio.to_thread(log_queue.get, True, 0.1)
                if msg == "DONE":
                    break
                await ws_manager.broadcast(msg)
            except queue.Empty:
                pass
                
    reader_task = asyncio.create_task(queue_reader())
        
    # 3. ADVANCED ENGINE: Calculate perfect assignment + Rollout futures
    print("Calculating optimal assignment and running MCTS simulations...")
    engine_start_time = time.time()
    try:
        raw_decision = await asyncio.to_thread(evaluate_threats_advanced, game_state, active_threats, 500, log_queue, weather)
        elapsed_time_ms = (time.time() - engine_start_time) * 1000.0
        time_msg = f"[SYSTEM] SUCCESS: Engine execution completed in {elapsed_time_ms:.2f} ms"
        print(time_msg)
        log_queue.put(time_msg)
    finally:
        log_queue.put("DONE")
        await reader_task # Ensure all final logs flush to the UI
    
    # 4. LLM LAYER: Format for the UI
    formatted_report = await format_report_with_llm(raw_decision)
    
    print("\n=== [GEMINI SITREP GENERATED] ===")
    print(formatted_report)
    print("=================================\n")
    
    # Log the SITREP to a file for testing and benchmarking
    log_file_path = "data/results/sitrep_benchmark.log"
    try:
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(f"=== SITREP [{time.ctime()}] ===\n")
            f.write(f"RAW JSON MATH:\n{json.dumps(raw_decision, indent=2)}\n\n")
            f.write(f"LLM OUTPUT:\n{formatted_report}\n")
            f.write("=" * 50 + "\n\n")
    except Exception as e:
        print(f"Error logging SITREP: {e}")

    # Append the human-readable text to the JSON response going back to the UI
    raw_decision["human_sitrep"] = formatted_report
    
    # Save to cache before returning
    EVALUATION_CACHE[payload_hash] = raw_decision
    if len(EVALUATION_CACHE) > MAX_CACHE_SIZE:
        EVALUATION_CACHE.popitem(last=False) # Remove the oldest entry
    
    return raw_decision

if __name__ == "__main__":
    # Start the server locally on port 8000
    print("Starting Boreal Chessmaster API on http://localhost:8000 ...")
    uvicorn.run(app, host="0.0.0.0", port=8000)