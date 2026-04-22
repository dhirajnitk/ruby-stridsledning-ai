import pandas as pd
import numpy as np
import json
from geopy.distance import geodesic
from czml3 import Document, Packet
from czml3.properties import (
    Position, Color, Material, Polyline, PolylineMaterial,
    Billboard, Label, ViewFrom, Orientation, SolidColorMaterial, 
    PolylineOutlineMaterial, Point, Path, Clock
)
from czml3.types import (
    IntervalValue, Cartesian3Value, CartographicDegreesValue, TimeInterval, Cartesian2Value
)
from datetime import datetime, timedelta
import os
import random

# --- CONFIGURATION ---
ANCHOR_LAT = 59.3293
ANCHOR_LON = 18.0686
START_TIME = datetime.utcnow()
CSV_PATH = "data/input/Boreal_passage_coordinates.csv"
REAL_DATA_PATH = "data/raw/real_baltic_traffic.json"
COMMERCIAL_OUT = "frontend/scenario_commercial.czml"
HOSTILE_OUT = "frontend/scenario_hostile.czml"

def get_lat_lon_fixed(x_km, y_km):
    origin = (ANCHOR_LAT, ANCHOR_LON)
    pos = geodesic(kilometers=x_km).destination(origin, bearing=90)
    pos = geodesic(kilometers=y_km).destination((pos.latitude, pos.longitude), bearing=180)
    return pos.latitude, pos.longitude, 0.0

def generate_split_streams():
    print(f"Loading map data...")
    df = pd.read_csv(CSV_PATH)
    
    # --- 1. COMMERCIAL STREAM (REAL BALTIC DATA) ---
    comm_packets = []
    comm_packets.append(Packet(
        id="document", version="1.0", name="Boreal Strategic: Commercial Clutter",
        clock=Clock(
            interval=TimeInterval(start=START_TIME, end=START_TIME + timedelta(hours=1)),
            currentTime=START_TIME, multiplier=15, range="LOOP_STOP", step="SYSTEM_CLOCK_MULTIPLIER"
        )
    ))
    
    # Add Bases to Commercial
    bases = df[df['record_type'] == 'location']
    for _, b in bases.iterrows():
        lat, lon, alt = get_lat_lon_fixed(b['x_km'], b['y_km'])
        comm_packets.append(Packet(
            id=f"base-{b['feature_name']}", name=b['feature_name'],
            position=Position(cartographicDegrees=[lon, lat, alt]),
            point=Point(pixelSize=6, color=Color(rgba=[63, 193, 255, 150]))
        ))

    if os.path.exists(REAL_DATA_PATH):
        with open(REAL_DATA_PATH, "r") as f:
            real_traffic = json.load(f)
        for f in real_traffic:
            lat, lon, alt = f['lat'], f['lon'], f['alt'] or 10000
            if lat is None or lon is None: continue
            path_coords = []
            heading = f['heading'] or random.uniform(0, 360)
            velocity_ms = f['velocity'] or 250
            for t_sec in range(0, 3600, 60):
                future_pos = geodesic(meters=velocity_ms * t_sec).destination((lat, lon), bearing=heading)
                path_coords.extend([float(t_sec), future_pos.longitude, future_pos.latitude, alt])
            comm_packets.append(Packet(
                id=f"REAL-{f['icao24']}", name=f"Commercial: {f['callsign']}",
                position=Position(epoch=START_TIME, cartographicDegrees=path_coords),
                point=Point(pixelSize=3, color=Color(rgba=[137, 180, 250, 150])),
                label=Label(text=f['callsign'], font="8pt monospace", fillColor=Color(rgba=[137, 180, 250, 150]), pixelOffset=Cartesian2Value(values=[0, 12]))
            ))

    comm_doc = Document(packets=comm_packets)
    with open(COMMERCIAL_OUT, "w") as f:
        f.write(comm_doc.dumps())
    print(f"[SUCCESS] Exported Commercial Stream: {COMMERCIAL_OUT}")

    # --- 2. HOSTILE STREAM (SYNTHETIC SATURATION) ---
    hostile_packets = []
    hostile_packets.append(Packet(
        id="document", version="1.0", name="Boreal Strategic: Hostile Threats",
        clock=Clock(
            interval=TimeInterval(start=START_TIME, end=START_TIME + timedelta(hours=1)),
            currentTime=START_TIME, multiplier=15, range="LOOP_STOP", step="SYSTEM_CLOCK_MULTIPLIER"
        )
    ))

    for i in range(100):
        start_x, start_y = random.uniform(1400, 1600), random.uniform(0, 1300)
        target_x, target_y = random.uniform(0, 400), random.uniform(0, 1300)
        speed_km_s = random.uniform(0.6, 1.2)
        dist = np.hypot(target_x - start_x, target_y - start_y)
        duration_s = dist / speed_km_s
        start_offset = random.uniform(0, 1200)
        h_path = []
        for t_sec in range(0, int(duration_s), 10):
            fract = t_sec / duration_s
            curr_x = start_x + (target_x - start_x) * fract
            curr_y = start_y + (target_y - start_y) * fract
            h_lat, h_lon, _ = get_lat_lon_fixed(curr_x, curr_y)
            h_path.extend([float(start_offset + t_sec), h_lon, h_lat, 6000.0])
        hostile_packets.append(Packet(
            id=f"HOSTILE-{i:03d}", name="HOSTILE INGRESS",
            position=Position(epoch=START_TIME, cartographicDegrees=h_path),
            path=Path(show=True, width=3, material=PolylineMaterial(solidColor=SolidColorMaterial(color=Color(rgba=[243, 139, 168, 255]))), trailTime=60),
            point=Point(pixelSize=6, color=Color(rgba=[243, 139, 168, 255])),
            label=Label(text="THREAT", font="9pt Outfit", fillColor=Color(rgba=[243, 139, 168, 255]), pixelOffset=Cartesian2Value(values=[0, -15]))
        ))

    hostile_doc = Document(packets=hostile_packets)
    with open(HOSTILE_OUT, "w") as f:
        f.write(hostile_doc.dumps())
    print(f"[SUCCESS] Exported Hostile Stream: {HOSTILE_OUT}")

if __name__ == "__main__":
    generate_split_streams()
