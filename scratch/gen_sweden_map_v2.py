"""
Build accurate Sweden tactical map SVG using:
- se.json real GeoJSON coastline (lat/lon paths)
- User's km-mapping formula: scale = SVG_height / 1572 km
- Coordinate system matching existing JS: Stockholm at (538,628), 0.48 px/km
- Dark tactical theme matching Wikipedia SVG aesthetic
"""
import json, math

# ─── Constants ─────────────────────────────────────────────────────────────────
STOCKHOLM_LAT = 59.3293
STOCKHOLM_LON = 18.0686
cos_lat = math.cos(math.radians(STOCKHOLM_LAT))  # ~0.511

# Scale: 1572 km N-to-S, Sweden silhouette height in SVG
# We want the scale to fit Sweden in our 900px tall canvas with Stockholm near y=628
# Northernmost point ~69.06°N → y_km above Stockholm = (69.06-59.33)*111.32 = 1082km north
# Southernmost point ~55.34°N → y_km below Stockholm = (59.33-55.34)*111.32 = 444km south
# Total = 1526 km (slightly less than 1572 because the extreme tip is thin)
# With scale=0.48: north extends 1082*0.48=519px up → y=628-519=109 (fits!)
#                  south extends 444*0.48=213px down → y=628+213=841 (fits in 900!)

SVG_W = 1000
SVG_H = 900
STO_X = 538          # Stockholm SVG x (canvas center-ish)
STO_Y = 628          # Stockholm SVG y
SCALE = 0.48         # px per km  (1 km = 0.48 SVG pixels)

# User's calibration: Sweden N-to-S ≈ 1572 km
# SVG height of silhouette = 1572 * 0.48 ≈ 754 px ← this is the "SVG height" in user's formula
SVG_SWEDEN_HEIGHT = 1572 * SCALE  # = 754.56 px
print(f"km mapping:  scale = {SCALE} px/km")
print(f"Sweden silhouette height = {SVG_SWEDEN_HEIGHT:.1f} px  (= 1572 km × {SCALE})")
print(f"km per SVG unit = {1/SCALE:.4f} km/px")


def latlon_to_km(lat, lon):
    """Convert lat/lon to km east/north relative to Stockholm."""
    x_km = (lon - STOCKHOLM_LON) * 111.32 * cos_lat
    y_km = (lat - STOCKHOLM_LAT) * 111.32
    return x_km, y_km


def latlon_to_svg(lat, lon):
    """Convert lat/lon to SVG pixel coordinate."""
    x_km, y_km = latlon_to_km(lat, lon)
    svg_x = STO_X + x_km * SCALE
    svg_y = STO_Y - y_km * SCALE   # Y inverted: north = up = lower SVG y
    return round(svg_x, 1), round(svg_y, 1)


def km_to_svg(x_km, y_km):
    """Direct km → SVG coordinate (from existing JS formula)."""
    return round(STO_X + x_km * SCALE, 1), round(STO_Y - y_km * SCALE, 1)


# ─── Load GeoJSON ─────────────────────────────────────────────────────────────
with open(r"C:\Users\dhiraj.kumar\Downloads\se.json", encoding="utf-8") as f:
    geojson = json.load(f)

print(f"\nGeoJSON features: {len(geojson['features'])}")

# Find Gotland feature
gotland_idx = None
for i, feat in enumerate(geojson["features"]):
    props = feat.get("properties", {})
    if any("gotland" in str(v).lower() for v in props.values()):
        gotland_idx = i
        print(f"Gotland feature: index={i}, props={props}")
        break


def feature_to_paths(feature):
    """Convert GeoJSON feature to list of SVG path 'd' strings."""
    geom = feature["geometry"]
    polys = []
    if geom["type"] == "Polygon":
        polys = [geom["coordinates"]]
    elif geom["type"] == "MultiPolygon":
        polys = geom["coordinates"]

    paths = []
    for poly in polys:
        outer = poly[0]  # outer ring only
        pts = []
        for lon, lat in outer:
            sx, sy = latlon_to_svg(lat, lon)
            pts.append(f"{sx},{sy}")
        if len(pts) > 2:
            paths.append("M" + " L".join(pts) + " Z")
    return " ".join(paths)


# ─── Military installations ────────────────────────────────────────────────────
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

print("\nBase positions (km → SVG):")
for b in BASES:
    sx, sy = latlon_to_svg(b["lat"], b["lon"])
    xkm, ykm = latlon_to_km(b["lat"], b["lon"])
    print(f"  {b['id']:4s}  km=({xkm:+.0f},{ykm:+.0f})  SVG=({sx},{sy})")


# ─── Marker helpers ────────────────────────────────────────────────────────────
MARKER = {
    "air_base":   {"color": "#00e5ff", "glow": "#006080", "sym": "▲"},
    "naval_base": {"color": "#4499ff", "glow": "#002266", "sym": "◆"},
    "capital":    {"color": "#ffd700", "glow": "#806600", "sym": "★"},
    "major_city": {"color": "#ff9900", "glow": "#804400", "sym": "●"},
}


def make_marker(x, y, mtype, bid, name):
    c = MARKER[mtype]["color"]
    g = MARKER[mtype]["glow"]
    r = 7
    parts = [f'<g id="base-{bid}" class="base {mtype}" data-id="{bid}" data-name="{name}">']

    if mtype == "air_base":
        pts = f"{x},{y-r} {x-r},{y+r} {x+r},{y+r}"
        parts.append(f'  <polygon points="{pts}" fill="{c}" stroke="{g}" stroke-width="1.5" opacity="0.92"/>')
    elif mtype == "naval_base":
        pts = f"{x},{y-r} {x+r},{y} {x},{y+r} {x-r},{y}"
        parts.append(f'  <polygon points="{pts}" fill="{c}" stroke="{g}" stroke-width="1.5" opacity="0.92"/>')
    elif mtype == "capital":
        # Star
        outer, inner = r+2, (r+2)*0.42
        star_pts = []
        for i in range(10):
            ang = math.pi/2 + i * math.pi/5
            ro = outer if i%2==0 else inner
            star_pts.append(f"{x+ro*math.cos(ang):.1f},{y-ro*math.sin(ang):.1f}")
        parts.append(f'  <polygon points="{" ".join(star_pts)}" fill="{c}" stroke="{g}" stroke-width="1.2" opacity="0.95"/>')
    else:
        parts.append(f'  <circle cx="{x}" cy="{y}" r="{r}" fill="{c}" stroke="{g}" stroke-width="1.5" opacity="0.92"/>')

    # Label
    parts.append(f'  <text x="{x+9}" y="{y+4}" font-family="monospace" font-size="9" font-weight="bold" fill="{c}" opacity="0.9">{bid}</text>')
    parts.append("</g>")
    return "\n".join(parts)


# ─── Build SVG ────────────────────────────────────────────────────────────────
svg_parts = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<!-- Sweden Military Theater Map -->',
    '<!-- km mapping: 1 km = 0.48 px | Stockholm origin at SVG(538,628) -->',
    '<!-- Sweden N-to-S = 1572 km → silhouette height = 754 px -->',
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_W} {SVG_H}" '
    f'width="100%" height="100%">',
    '<defs>',
    '  <style>',
    '    svg { background: #0a1826; }',
    '    .land { fill: #1a2e1a; stroke: #2a4a2a; stroke-width: 0.7; }',
    '    .gotland { fill: #223822; stroke: #5aaa5a; stroke-width: 1.5; stroke-dasharray: 3,1.5; }',
    '    .grid-line { stroke: #152235; stroke-width: 0.5; }',
    '    .base text { pointer-events: none; }',
    '    .base polygon, .base circle { cursor: pointer; }',
    '    .base polygon:hover, .base circle:hover { opacity: 1 !important; }',
    '  </style>',
    '  <!-- Glow filter for bases -->',
    '  <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">',
    '    <feGaussianBlur stdDeviation="2.5" result="blur"/>',
    '    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>',
    '  </filter>',
    '  <!-- Subtle grid glow -->',
    '  <filter id="grid-glow" x="-5%" y="-5%" width="110%" height="110%">',
    '    <feGaussianBlur stdDeviation="0.5"/>',
    '  </filter>',
    '</defs>',
]

# Ocean background
svg_parts.append(f'<rect width="{SVG_W}" height="{SVG_H}" fill="#0a1826"/>')

# Grid lines (every 100 km)
svg_parts.append('<g class="grid">')
# Vertical lines (longitude bands at 100km intervals in x)
for x_km in range(-600, 400, 100):
    sx = STO_X + x_km * SCALE
    if 0 <= sx <= SVG_W:
        svg_parts.append(f'  <line x1="{sx:.0f}" y1="0" x2="{sx:.0f}" y2="{SVG_H}" class="grid-line"/>')
# Horizontal lines (latitude bands at 100km intervals in y)
for y_km in range(-500, 1200, 100):
    sy = STO_Y - y_km * SCALE
    if 0 <= sy <= SVG_H:
        svg_parts.append(f'  <line x1="0" y1="{sy:.0f}" x2="{SVG_W}" y2="{sy:.0f}" class="grid-line"/>')
svg_parts.append('</g>')

# Land regions from GeoJSON
svg_parts.append('<g id="regions">')
for i, feature in enumerate(geojson["features"]):
    path_d = feature_to_paths(feature)
    if not path_d.strip():
        continue
    if i == gotland_idx:
        css = "gotland"
    else:
        css = "land"
    props = feature.get("properties", {})
    region_name = props.get("name", f"region{i}")
    svg_parts.append(f'  <path class="{css}" d="{path_d}"/>')
svg_parts.append('</g>')

# Coastline highlight
svg_parts.append('<g id="coastlines">')
for i, feature in enumerate(geojson["features"]):
    path_d = feature_to_paths(feature)
    if not path_d.strip():
        continue
    if i == gotland_idx:
        color, width = "#5aaa5a", "1.5"
    else:
        color, width = "#2a4a2a", "0.7"
    svg_parts.append(f'  <path fill="none" stroke="{color}" stroke-width="{width}" d="{path_d}"/>')
svg_parts.append('</g>')

# Baltic sea label (east of mainland coast)
bsx, bsy = km_to_svg(200, -230)
svg_parts.append(f'<text x="{bsx}" y="{bsy}" font-family="monospace" font-size="8" fill="#1a3a5a" '
                 f'text-anchor="middle" opacity="0.7">BALTIC SEA</text>')

# Gotland island label
got_lx, got_ly = latlon_to_svg(57.35, 18.55)  # center-south of Gotland
svg_parts.append(f'<text x="{got_lx+12}" y="{got_ly}" font-family="monospace" font-size="7.5" '
                 f'fill="#5aaa5a" text-anchor="start" font-weight="bold" opacity="0.85">GOTLAND</text>')

# Military bases (with glow)
svg_parts.append('<g id="bases" filter="url(#glow)">')
for b in BASES:
    sx, sy = latlon_to_svg(b["lat"], b["lon"])
    svg_parts.append(make_marker(sx, sy, b["type"], b["id"], b["name"]))
svg_parts.append('</g>')

# Legend box
lx, ly = SVG_W - 175, 20
svg_parts.append(f'<rect x="{lx-8}" y="{ly-15}" width="170" height="110" rx="3" '
                 f'fill="#071118" stroke="#1e3a1e" stroke-width="1" opacity="0.92"/>')
svg_parts.append(f'<text x="{lx}" y="{ly}" font-family="monospace" font-size="10" '
                 f'font-weight="bold" fill="#5a9a5a">SWEDEN AOR</text>')
legend = [
    ("▲", "#00e5ff", "Air Base"),
    ("◆", "#4499ff", "Naval Base"),
    ("★", "#ffd700", "Capital"),
    ("●", "#ff9900", "Major City"),
]
for j, (sym, col, lbl) in enumerate(legend):
    iy = ly + 20 + j*20
    svg_parts.append(f'<text x="{lx}" y="{iy}" font-family="monospace" font-size="13" fill="{col}">{sym}</text>')
    svg_parts.append(f'<text x="{lx+18}" y="{iy}" font-family="monospace" font-size="9" fill="#8aaa8a">{lbl}</text>')

# Scale indicator
scale_x0, scale_y0 = 20, SVG_H - 30
scale_km = 200
scale_px = scale_km * SCALE
svg_parts.append(f'<line x1="{scale_x0}" y1="{scale_y0}" x2="{scale_x0+scale_px:.0f}" '
                 f'y2="{scale_y0}" stroke="#3a6a3a" stroke-width="2"/>')
svg_parts.append(f'<line x1="{scale_x0}" y1="{scale_y0-4}" x2="{scale_x0}" y2="{scale_y0+4}" '
                 f'stroke="#3a6a3a" stroke-width="1.5"/>')
svg_parts.append(f'<line x1="{scale_x0+scale_px:.0f}" y1="{scale_y0-4}" x2="{scale_x0+scale_px:.0f}" '
                 f'y2="{scale_y0+4}" stroke="#3a6a3a" stroke-width="1.5"/>')
svg_parts.append(f'<text x="{scale_x0+scale_px/2:.0f}" y="{scale_y0-6}" font-family="monospace" '
                 f'font-size="8" fill="#5a8a5a" text-anchor="middle">{scale_km} km</text>')

# Footer: km calibration info
svg_parts.append(f'<text x="{SVG_W-8}" y="{SVG_H-6}" font-family="monospace" font-size="7" '
                 f'fill="#1a3a1a" text-anchor="end">'
                 f'1 km = {SCALE} px | Sweden 1572km → {SVG_SWEDEN_HEIGHT:.0f}px | '
                 f'Stockholm ({STO_X},{STO_Y})</text>')

svg_parts.append('</svg>')

svg_content = "\n".join(svg_parts)

# Save
out1 = r"c:\Users\dhiraj.kumar\Downloads\Saab\ruby-stridsledning-ai\data\input\sweden-military-map.svg"
out2 = r"c:\Users\dhiraj.kumar\Downloads\Saab\ruby-stridsledning-ai\frontend\sweden-military-map.svg"
for path in [out1, out2]:
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"\nSaved → {path}")

print(f"SVG size: {len(svg_content):,} chars")
print(f"\nKm-to-SVG formula:")
print(f"  scale = Sweden_silhouette_height / 1572 km")
print(f"       = {SVG_SWEDEN_HEIGHT:.1f} / 1572 = {SCALE} px/km")
print(f"  SVG_x = {STO_X} + x_km × {SCALE}")
print(f"  SVG_y = {STO_Y} − y_km × {SCALE}")
