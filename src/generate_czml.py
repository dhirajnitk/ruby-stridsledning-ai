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
START_TIME = datetime(2026, 4, 25, 10, 0, 0)
CSV_PATH = "data/input/Boreal_passage_coordinates.csv"
REAL_DATA_PATH = "data/raw/real_baltic_traffic.json"
OUTPUT_PATH = "frontend/scenario_real_world.czml"

def get_lat_lon_fixed(x_km, y_km):
    origin = (ANCHOR_LAT, ANCHOR_LON)
    pos = geodesic(kilometers=x_km).destination(origin, bearing=90)
    pos = geodesic(kilometers=y_km).destination((pos.latitude, pos.longitude), bearing=180)
    return pos.latitude, pos.longitude, 0.0

def generate_tactical_czml():
    print(f"Loading map data...")
    df = pd.read_csv(CSV_PATH)
    
    packets = []
    
    # 1. Document Packet
    packets.append(Packet(
        id="document",
        version="1.0",
        name="Boreal Chessmaster: REAL-WORLD STRATEGIC OVERLAY",
        clock=Clock(
            interval=TimeInterval(start=START_TIME, end=START_TIME + timedelta(hours=1)),
            currentTime=START_TIME,
            multiplier=15,
            range="LOOP_STOP",
            step="SYSTEM_CLOCK_MULTIPLIER"
        )
    ))
    
    # 2. Add Bases as Static Points
    bases = df[df['record_type'] == 'location']
    for _, b in bases.iterrows():
        lat, lon, alt = get_lat_lon_fixed(b['x_km'], b['y_km'])
        color_rgba = [255, 204, 0, 255] if b['subtype'] == 'capital' else [63, 193, 255, 255]
        packets.append(Packet(
            id=f"base-{b['feature_name']}",
            name=b['feature_name'],
            position=Position(cartographicDegrees=[lon, lat, alt]),
            label=Label(text=b['feature_name'], font="12pt Outfit", fillColor=Color(rgba=color_rgba), outlineWidth=2, pixelOffset=Cartesian2Value(values=[0, -20])),
            point=Point(pixelSize=8, color=Color(rgba=color_rgba), outlineColor=Color(rgba=[255, 255, 255, 255]), outlineWidth=2)
        ))

    # 3. REAL-WORLD CLUTTER (From OpenSky Harvest)
    if os.path.exists(REAL_DATA_PATH):
        print(f"Fusing {REAL_DATA_PATH} into strategic hub...")
        with open(REAL_DATA_PATH, "r") as f:
            real_traffic = json.load(f)
        
        for i, f in enumerate(real_traffic):
            f_id = f"REAL-{f['icao24']}"
            lat, lon, alt = f['lat'], f['lon'], f['alt'] or 10000
            
            # Skip if coords are invalid
            if lat is None or lon is None: continue
            
            # Color coding based on Tactical Profile
            color = [137, 180, 250, 180] # Blue (Easy)
            if f['profile'] == "HARD": color = [249, 226, 175, 200] # Yellow
            if f['profile'] == "RARE": color = [203, 166, 247, 255] # Purple/Military
            
            # Create a simple 30-min straight-line path based on real heading/velocity for demo
            path_coords = []
            heading = f['heading'] or random.uniform(0, 360)
            velocity_ms = f['velocity'] or 250 # approx 900kmh
            
            for t_sec in range(0, 1800, 60):
                # Calculate future position using geopy
                future_pos = geodesic(meters=velocity_ms * t_sec).destination((lat, lon), bearing=heading)
                path_coords.extend([float(t_sec), future_pos.longitude, future_pos.latitude, alt])

            packets.append(Packet(
                id=f_id,
                name=f"Real Traffic: {f['callsign']} ({f['country']})",
                position=Position(epoch=START_TIME, cartographicDegrees=path_coords),
                point=Point(pixelSize=4, color=Color(rgba=color)),
                label=Label(text=f['callsign'], font="9pt monospace", fillColor=Color(rgba=color), pixelOffset=Cartesian2Value(values=[0, 15]))
            ))

    # 4. MASSIVE HOSTILE WAVE (Synthetic Saturation)
    print("Overlaying 100 Hostile Tactical Vectors...")
    for i in range(100):
        h_id = f"HOSTILE-{i:03d}"
        start_x, start_y = random.uniform(1400, 1600), random.uniform(0, 1300)
        target_x, target_y = random.uniform(0, 400), random.uniform(0, 1300)
        speed_km_s = random.uniform(0.5, 0.9)
        dist = np.hypot(target_x - start_x, target_y - start_y)
        duration_s = dist / speed_km_s
        start_offset = random.uniform(300, 900)
        
        h_path = []
        for t_sec in range(0, int(duration_s), 10):
            fract = t_sec / duration_s
            curr_x = start_x + (target_x - start_x) * fract
            curr_y = start_y + (target_y - start_y) * fract
            curr_x += 5 * np.sin(t_sec/50.0)
            h_lat, h_lon, _ = get_lat_lon_fixed(curr_x, curr_y)
            h_path.extend([float(start_offset + t_sec), h_lon, h_lat, 5000.0])

        packets.append(Packet(
            id=h_id,
            name="HOSTILE INGRESS",
            position=Position(epoch=START_TIME, cartographicDegrees=h_path),
            path=Path(
                show=True, width=2,
                material=PolylineMaterial(solidColor=SolidColorMaterial(color=Color(rgba=[243, 139, 168, 255]))),
                leadTime=0, trailTime=60, resolution=1
            ),
            point=Point(pixelSize=5, color=Color(rgba=[243, 139, 168, 255]))
        ))

    # 5. Initialize Document
    doc = Document(packets=packets)
    with open(OUTPUT_PATH, "w") as f:
        f.write(doc.dumps())
    print(f"Successfully generated REAL-WORLD tactical CZML at {OUTPUT_PATH}")

if __name__ == "__main__":
    generate_tactical_czml()
