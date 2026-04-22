import pandas as pd
import numpy as np
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
OUTPUT_PATH = "frontend/scenario_massive_saturation.czml"

def get_lat_lon_fixed(x_km, y_km):
    origin = (ANCHOR_LAT, ANCHOR_LON)
    pos = geodesic(kilometers=x_km).destination(origin, bearing=90)
    pos = geodesic(kilometers=y_km).destination((pos.latitude, pos.longitude), bearing=180)
    return pos.latitude, pos.longitude, 0.0

def generate_massive_czml():
    print(f"Loading map data...")
    df = pd.read_csv(CSV_PATH)
    packets = []
    
    # 1. Document Packet
    packets.append(Packet(
        id="document",
        version="1.0",
        name="Boreal Chessmaster: MASSIVE SATURATION",
        clock=Clock(
            interval=TimeInterval(start=START_TIME, end=START_TIME + timedelta(hours=1)),
            currentTime=START_TIME,
            multiplier=15,
            range="LOOP_STOP",
            step="SYSTEM_CLOCK_MULTIPLIER"
        )
    ))
    
    # 2. Add Bases
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

    # 3. MASSIVE HOSTILE SATURATION (200 Tracks)
    print("Generating 200 Hostile Tracks...")
    for i in range(200):
        h_id = f"HOSTILE-{i:03d}"
        start_x, start_y = random.uniform(1400, 1600), random.uniform(0, 1300)
        target_x, target_y = random.uniform(0, 400), random.uniform(0, 1300)
        speed_km_s = random.uniform(0.3, 0.9)
        dist = np.hypot(target_x - start_x, target_y - start_y)
        duration_s = dist / speed_km_s
        start_offset = random.uniform(0, 600)
        
        h_path = []
        for t_sec in range(0, int(duration_s), 10):
            fract = t_sec / duration_s
            curr_x = start_x + (target_x - start_x) * fract
            curr_y = start_y + (target_y - start_y) * fract
            lat_p, lon_p, _ = get_lat_lon_fixed(curr_x, curr_y)
            h_path.extend([float(start_offset + t_sec), lon_p, lat_p, random.uniform(5000, 8000)])

        packets.append(Packet(
            id=h_id,
            name="Hostile Fast Mover",
            position=Position(epoch=START_TIME, cartographicDegrees=h_path),
            path=Path(
                show=True, width=2,
                material=PolylineMaterial(solidColor=SolidColorMaterial(color=Color(rgba=[243, 139, 168, 255]))),
                leadTime=0, trailTime=60, resolution=1
            ),
            point=Point(pixelSize=4, color=Color(rgba=[243, 139, 168, 255]))
        ))

    # 4. MASSIVE COMMERCIAL CLUTTER (800 Tracks)
    print("Generating 800 Commercial Clutter Tracks...")
    for i in range(800):
        c_id = f"COMMERCIAL-{i:03d}"
        start_x, start_y = random.uniform(0, 1600), random.uniform(0, 1300)
        end_x, end_y = random.uniform(0, 1600), random.uniform(0, 1300)
        
        c_path = []
        c_duration = 3600
        for t_sec in range(0, c_duration, 60):
            fract = t_sec / c_duration
            curr_x = start_x + (end_x - start_x) * fract
            curr_y = start_y + (end_y - start_y) * fract
            lat_p, lon_p, _ = get_lat_lon_fixed(curr_x, curr_y)
            c_path.extend([float(t_sec), lon_p, lat_p, random.uniform(9000, 11000)])
            
        packets.append(Packet(
            id=c_id,
            name="Commercial Aviation",
            position=Position(epoch=START_TIME, cartographicDegrees=c_path),
            point=Point(pixelSize=2, color=Color(rgba=[137, 180, 250, 100]))
        ))

    # 5. Export
    doc = Document(packets=packets)
    with open(OUTPUT_PATH, "w") as f:
        f.write(doc.dumps())
    print(f"Successfully generated MASSIVE tactical CZML at {OUTPUT_PATH}")

if __name__ == "__main__":
    generate_massive_czml()
