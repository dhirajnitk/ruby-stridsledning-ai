"""
Build accurate Sweden tactical map SVG using Wikipedia polar-stereographic SVG.
- Extract Sveriges_kust (mainland) + island paths
- Calibrate lat/lon -> SVG affine transform from city text anchors
- Place military bases correctly
- Dark tactical theme
"""
import re, numpy as np

# ─── Load the Wikipedia SVG ───────────────────────────────────────────────────
with open("scratch/sweden_wiki.svg", encoding="utf-8") as f:
    raw = f.read()

print(f"SVG loaded: {len(raw)} chars  (W=1000, H=2387)")

# ─── Extract land / island path data ─────────────────────────────────────────
# Layer7 (Land) and Layer8 (Islands) both have the same transform
LAYER_TRANSFORM = "translate(-11.991744,470.97414)"

# Get the Sweden mainland path (id=Sveriges_kust)
mainland_match = re.search(r'<path[^>]*id="Sveriges_kust"[^/]*/>', raw, re.DOTALL)
if not mainland_match:
    # Try multi-line path element
    mainland_match = re.search(
        r'(<path[^>]*id="Sveriges_kust"[^>]*>.*?</path>)', raw, re.DOTALL)
if not mainland_match:
    # Get just the path tag up to end
    m = re.search(r'id="Sveriges_kust"', raw)
    if m:
        start = raw.rfind('<path', 0, m.start())
        end = raw.find('/>', start) + 2
        mainland_match = type('M', (), {'group': lambda s, x: raw[start:end]})()
        mainland_d = re.search(r'\bd="([^"]+)"', raw[start:end])
        mainland_path_d = mainland_d.group(1) if mainland_d else ""
        print(f"Mainland path d: {len(mainland_path_d)} chars")
        # Get style
        style_m = re.search(r'style="([^"]+)"', raw[start:end])
        mainland_style = style_m.group(1) if style_m else ""

# Get ALL island paths from layer8 (between layer8 start and next group end)
layer8_start = raw.find('id="layer8"')
layer8_region = raw[layer8_start:layer8_start + 80000]

# Find all <path .../> or <path ...>...</path> in layer8
island_paths_raw = re.findall(r'<path[^>]*/>', layer8_region)
print(f"Island paths found: {len(island_paths_raw)}")

# ─── City text anchor points for calibration ─────────────────────────────────
# Format: (lat, lon, SVG_x, SVG_y) – from Wikipedia SVG text elements
# Text has scale(1.0001564,0.99984362) ≈ 1, so we use values as-is
CITY_ANCHORS = [
    # name           lat       lon       svgX      svgY
    ("Stockholm",   59.3293, 18.0686,  651.64,  1159.99),
    ("Gothenburg",  57.7089, 11.9746,   45.78,  1425.26),
    ("Uppsala",     59.8972, 17.5886,  549.61,  1033.87),
    ("Visby",       57.6591, 18.3458,  649.32,  1395.35),
    ("Karlskrona",  56.1612, 15.5869,  457.46,  1674.02),
    ("Sundsvall",   62.3908, 17.3069,  450.00,   660.00),  # approximate from SVG
    ("Umeå",        63.8258, 20.2630,  626.00,   514.00),  # approximate
    ("Luleå",       65.5848, 22.1567,  786.00,   303.00),  # approximate - we'll verify
    ("Malmö",       55.6059, 13.0358,  225.00,  1766.00),  # approximate
]

# Let me get exact positions for more cities from the SVG
extra_cities_raw = re.findall(
    r'x="([0-9.]+)"\s+y="([0-9.]+)"[^>]*>([A-ZÅÄÖ][a-zA-ZåäöÅÄÖ ]+)</tspan>',
    raw
)
city_map_svg = {}
for x, y, name in extra_cities_raw:
    city_map_svg[name.strip()] = (float(x), float(y))

print("\nSVG city positions found:")
for city_name in ["Sundsvall", "Umeå", "Luleå", "Malmö", "Östersund", "Gävle"]:
    if city_name in city_map_svg:
        print(f"  {city_name}: SVG {city_map_svg[city_name]}")

# Update anchors with exact positions from SVG
# Add verified ones
EXTRA_ANCHORS = [
    ("Sundsvall",  62.3908, 17.3069),
    ("Umeå",       63.8258, 20.2630),
    ("Gävle",      60.6749, 17.1413),
    ("Östersund",  63.1791, 14.6357),
    ("Malmö",      55.6059, 13.0358),
]
CITY_ANCHORS_VERIFIED = [
    ("Stockholm",  59.3293, 18.0686,  651.64,  1159.99),
    ("Gothenburg", 57.7089, 11.9746,   45.78,  1425.26),
    ("Uppsala",    59.8972, 17.5886,  549.61,  1033.87),
    ("Visby",      57.6591, 18.3458,  649.32,  1395.35),
    ("Karlskrona", 56.1612, 15.5869,  457.46,  1674.02),
]
for cname, lat, lon in EXTRA_ANCHORS:
    if cname in city_map_svg:
        sx, sy = city_map_svg[cname]
        CITY_ANCHORS_VERIFIED.append((cname, lat, lon, sx, sy))
        print(f"  Added anchor: {cname} lat={lat} lon={lon} SVG=({sx:.1f},{sy:.1f})")

# ─── Fit affine transform (lat, lon) → (SVG_x, SVG_y) ───────────────────────
# SVG_x = a0 + a1*lat + a2*lon
# SVG_y = b0 + b1*lat + b2*lon
A_rows = [[1, lat, lon] for _, lat, lon, _, _ in CITY_ANCHORS_VERIFIED]
Yx = [svgx for _, _, _, svgx, _ in CITY_ANCHORS_VERIFIED]
Yy = [svgy for _, _, _, _, svgy in CITY_ANCHORS_VERIFIED]

A = np.array(A_rows, dtype=float)
Yx = np.array(Yx, dtype=float)
Yy = np.array(Yy, dtype=float)

# Least squares
ax, _, _, _ = np.linalg.lstsq(A, Yx, rcond=None)
ay, _, _, _ = np.linalg.lstsq(A, Yy, rcond=None)

print(f"\nAffine transform:")
print(f"  SVG_x = {ax[0]:.2f} + {ax[1]:.4f}*lat + {ax[2]:.4f}*lon")
print(f"  SVG_y = {ay[0]:.2f} + {ay[1]:.4f}*lat + {ay[2]:.4f}*lon")

# Verify accuracy
print("\nCalibration accuracy (anchor points):")
for name, lat, lon, sx, sy in CITY_ANCHORS_VERIFIED:
    px = ax[0] + ax[1]*lat + ax[2]*lon
    py = ay[0] + ay[1]*lat + ay[2]*lon
    print(f"  {name:12s}: true=({sx:6.1f},{sy:6.1f})  pred=({px:6.1f},{py:6.1f})  err=({px-sx:+.1f},{py-sy:+.1f})")

def latlon_to_svg(lat, lon):
    x = ax[0] + ax[1]*lat + ax[2]*lon
    y = ay[0] + ay[1]*lat + ay[2]*lon
    return round(float(x), 1), round(float(y), 1)

# ─── Military installation positions ─────────────────────────────────────────
BASES = [
    {"id": "F21", "name": "Luleå Air Base (F 21)", "type": "air_base",   "lat": 65.5436, "lon": 22.1211},
    {"id": "VID", "name": "Vidsel Air Base",        "type": "air_base",   "lat": 65.8753, "lon": 20.1500},
    {"id": "F16", "name": "Uppsala Air Base (F 16)","type": "air_base",   "lat": 59.8972, "lon": 17.5886},
    {"id": "STO", "name": "Stockholm (Capital)",    "type": "capital",    "lat": 59.3293, "lon": 18.0686},
    {"id": "MUS", "name": "Muskö Naval Base",       "type": "naval_base", "lat": 58.9167, "lon": 18.1333},
    {"id": "F7",  "name": "Såtenäs Air Base (F 7)", "type": "air_base",   "lat": 58.4419, "lon": 12.7108},
    {"id": "MAL", "name": "Malmen Air Base",        "type": "air_base",   "lat": 58.3967, "lon": 15.5261},
    {"id": "F17", "name": "Ronneby Air Base (F 17)","type": "air_base",   "lat": 56.2667, "lon": 15.2653},
    {"id": "KRL", "name": "Karlskrona Naval Base",  "type": "naval_base", "lat": 56.1612, "lon": 15.5869},
    {"id": "GOT", "name": "Gotland (Visby Base)",   "type": "major_city", "lat": 57.6591, "lon": 18.3458},
    {"id": "GBG", "name": "Gothenburg",             "type": "major_city", "lat": 57.7089, "lon": 11.9746},
]

print("\nMilitary base SVG positions:")
for b in BASES:
    x, y = latlon_to_svg(b["lat"], b["lon"])
    print(f"  {b['id']:4s} ({b['lat']:.4f}N, {b['lon']:.4f}E) → SVG({x}, {y})")

# ─── User's km-calibration method ─────────────────────────────────────────────
# Sweden N-to-S = 1572 km
# SVG height of Sweden silhouette ≈ (southernmost - northernmost SVG y)
# Northernmost ≈ Treriksröset ~69.06°N → SVG y?
north_svg_y = ay[0] + ay[1]*69.06 + ay[2]*20.0   # ~Treriksröset lon ~20°E
south_svg_y = ay[0] + ay[1]*55.34 + ay[2]*14.0   # ~Smygehuk lon ~14°E (southernmost)
svg_height_of_sweden = south_svg_y - north_svg_y
km_per_svgunit = 1572 / svg_height_of_sweden
print(f"\nUser's km-calibration:")
print(f"  North (69.06N) → SVG y = {north_svg_y:.1f}")
print(f"  South (55.34N) → SVG y = {south_svg_y:.1f}")
print(f"  SVG height of Sweden = {svg_height_of_sweden:.1f} px")
print(f"  km per SVG unit = {km_per_svgunit:.4f} km/px")
print(f"  SVG units per km = {1/km_per_svgunit:.4f} px/km")

# Stockholm SVG position
sto_x, sto_y = latlon_to_svg(59.3293, 18.0686)
print(f"\n  Stockholm SVG anchor: ({sto_x}, {sto_y})")
print(f"  Using km formula vs affine:")
for b in BASES:
    km_x = b.get("x_km", 0)
    km_y = b.get("y_km", 0)
    ax_pos, ay_pos = latlon_to_svg(b["lat"], b["lon"])
    print(f"    {b['id']:4s}: affine=({ax_pos}, {ay_pos})")
