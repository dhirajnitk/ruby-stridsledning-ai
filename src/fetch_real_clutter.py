import requests
import json
import os
import time

# --- CONFIGURATION ---
# Stockholm-Baltic Bounding Box
# Lat: 54 to 64, Lon: 10 to 25
BBOX = {
    "lamin": 54.0,
    "lomin": 10.0,
    "lamax": 64.0,
    "lomax": 25.0
}
OUTPUT_PATH = "data/raw/real_baltic_traffic.json"

def fetch_baltic_clutter():
    """Returns the list of processed real-world Baltic traffic."""
    print(f"[SYSTEM] Fetching Live Baltic SITREP...")
    url = "https://opensky-network.org/api/states/all"
    try:
        response = requests.get(url, params=BBOX, timeout=15)
        if response.status_code == 200:
            data = response.json()
            states = data.get("states", [])
            processed = []
            for s in states:
                callsign = (s[1] or "UNKNOWN").strip()
                profile = "EASY"
                if not callsign or callsign == "UNKNOWN": profile = "HARD"
                elif any(x in callsign for x in ["SAR", "NAVY", "MIL", "COAST"]): profile = "RARE"
                elif s[9] is not None and s[9] > 300: profile = "HARD"
                processed.append({
                    "icao24": s[0], "callsign": callsign, "country": s[2],
                    "lon": s[5], "lat": s[6], "alt": s[7], "velocity": s[9],
                    "heading": s[10], "profile": profile
                })
            return processed
    except Exception as e:
        print(f"[ERROR] Live Harvest Failed: {e}")
def fetch_real_traffic():
    data = fetch_baltic_clutter()
    if data:
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[SUCCESS] Ingested {len(data)} flights. Strategic Cache saved to {OUTPUT_PATH}")
        return True
    return False

if __name__ == "__main__":
    fetch_real_traffic()
