"""
Generate accurate Sweden military map SVG using real geodata from se.json / se.svg
"""
import json, re, xml.etree.ElementTree as ET

# Geographic bounds from se.json analysis
LON_MIN, LON_MAX = 11.108, 24.163
LAT_MIN, LAT_MAX = 55.343, 69.036

# SVG canvas
PAD_L, PAD_R, PAD_T, PAD_B = 30, 30, 30, 30
W, H = 1000, 1000
scale_x = (W - PAD_L - PAD_R) / (LON_MAX - LON_MIN)
scale_y = (H - PAD_T - PAD_B) / (LAT_MAX - LAT_MIN)


def to_svg(lon, lat):
    x = PAD_L + (lon - LON_MIN) * scale_x
    y = PAD_T + (LAT_MAX - lat) * scale_y
    return round(x, 1), round(y, 1)


def coords_to_path(rings):
    """Convert a list of coordinate rings to SVG path data."""
    parts = []
    for ring in rings:
        pts = []
        for lon, lat in ring:
            x, y = to_svg(lon, lat)
            pts.append(f"{x},{y}")
        if pts:
            parts.append("M" + " L".join(pts) + " Z")
    return " ".join(parts)


def geojson_feature_to_path(feature):
    """Convert a GeoJSON feature to an SVG path d attribute."""
    geom = feature["geometry"]
    polygons = []
    if geom["type"] == "Polygon":
        polygons = [geom["coordinates"]]
    elif geom["type"] == "MultiPolygon":
        polygons = geom["coordinates"]
    # Build path from outer rings only (first ring of each polygon)
    parts = []
    for poly in polygons:
        outer = poly[0]
        pts = []
        for lon, lat in outer:
            x, y = to_svg(lon, lat)
            pts.append(f"{x},{y}")
        if pts:
            parts.append("M" + " L".join(pts) + " Z")
    return " ".join(parts)


# Military installations
BASES = [
    {"id": "F21", "name": "Luleå Air Base (F 21)", "type": "air_base",  "lat": 65.5436, "lon": 22.1211},
    {"id": "VID", "name": "Vidsel Air Base",        "type": "air_base",  "lat": 65.8753, "lon": 20.1500},
    {"id": "F16", "name": "Uppsala Air Base (F 16)","type": "air_base",  "lat": 59.8972, "lon": 17.5886},
    {"id": "STO", "name": "Stockholm",              "type": "capital",   "lat": 59.3293, "lon": 18.0686},
    {"id": "MUS", "name": "Muskö Naval Base",       "type": "naval_base","lat": 58.9167, "lon": 18.1333},
    {"id": "F7",  "name": "Såtenäs Air Base (F 7)", "type": "air_base",  "lat": 58.4419, "lon": 12.7108},
    {"id": "MAL", "name": "Malmen Air Base",        "type": "air_base",  "lat": 58.3967, "lon": 15.5261},
    {"id": "F17", "name": "Ronneby Air Base (F 17)","type": "air_base",  "lat": 56.2667, "lon": 15.2653},
    {"id": "KRL", "name": "Karlskrona Naval Base",  "type": "naval_base","lat": 56.1612, "lon": 15.5869},
    {"id": "GOT", "name": "Gotland (Visby Base)",   "type": "major_city","lat": 57.6591, "lon": 18.3458},
    {"id": "GBG", "name": "Gothenburg",             "type": "major_city","lat": 57.7089, "lon": 11.9746},
]

# Marker appearance by type
MARKER_STYLE = {
    "air_base":   {"color": "#00e5ff", "shape": "triangle", "label_color": "#00e5ff"},
    "naval_base": {"color": "#4499ff", "shape": "diamond",  "label_color": "#4499ff"},
    "capital":    {"color": "#ffd700", "shape": "star",     "label_color": "#ffd700"},
    "major_city": {"color": "#ff9900", "shape": "circle",   "label_color": "#ff9900"},
}


def make_marker(x, y, mtype, base_id, name):
    style = MARKER_STYLE.get(mtype, MARKER_STYLE["major_city"])
    color = style["color"]
    lc = style["label_color"]
    shape = style["shape"]
    r = 7

    svg_parts = [f'<g class="base {mtype}" id="base-{base_id}" data-id="{base_id}" data-name="{name}">']

    if shape == "triangle":
        pts = f"{x},{y-r} {x-r},{y+r} {x+r},{y+r}"
        svg_parts.append(f'  <polygon points="{pts}" fill="{color}" stroke="#ffffff" stroke-width="1.5" opacity="0.9"/>')
    elif shape == "diamond":
        pts = f"{x},{y-r} {x+r},{y} {x},{y+r} {x-r},{y}"
        svg_parts.append(f'  <polygon points="{pts}" fill="{color}" stroke="#ffffff" stroke-width="1.5" opacity="0.9"/>')
    elif shape == "star":
        # 5-pointed star
        import math
        outer = r + 2
        inner = (outer) * 0.4
        pts_list = []
        for i in range(10):
            angle = math.pi / 2 + i * math.pi / 5
            ro = outer if i % 2 == 0 else inner
            pts_list.append(f"{round(x + ro*math.cos(angle),1)},{round(y - ro*math.sin(angle),1)}")
        pts = " ".join(pts_list)
        svg_parts.append(f'  <polygon points="{pts}" fill="{color}" stroke="#ffffff" stroke-width="1.2" opacity="0.95"/>')
    else:
        svg_parts.append(f'  <circle cx="{x}" cy="{y}" r="{r}" fill="{color}" stroke="#ffffff" stroke-width="1.5" opacity="0.9"/>')

    # Label with background
    label_x = x + 10
    label_y = y + 4
    svg_parts.append(f'  <text x="{label_x}" y="{label_y}" font-family="monospace,sans-serif" font-size="9" font-weight="bold" fill="{lc}" opacity="0.9">{base_id}</text>')
    svg_parts.append("</g>")
    return "\n".join(svg_parts)


# Load GeoJSON
with open(r"C:\Users\dhiraj.kumar\Downloads\se.json", encoding="utf-8") as f:
    geojson = json.load(f)

# Gotland feature ID for special handling (highlight as island)
# Find which feature is Gotland
GOTLAND_ID = None
for i, feat in enumerate(geojson["features"]):
    props = feat.get("properties", {})
    name = str(props).lower()
    if "gotland" in name:
        GOTLAND_ID = i
        print(f"Found Gotland at feature index {i}: {props}")
        break

# Build SVG
lines = []
lines.append('<?xml version="1.0" encoding="UTF-8"?>')
lines.append('<!-- Sweden Military Theater Map - generated from se.json real geodata -->')
lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" width="100%" height="100%" style="background:#0a1826">')
lines.append('<defs>')
lines.append('  <style>')
lines.append('    .land { fill: #1e3020; stroke: #2d4a2d; stroke-width: 0.8; }')
lines.append('    .gotland { fill: #1e3020; stroke: #2d4a2d; stroke-width: 1.5; }')
lines.append('    .grid { stroke: #1a2a3a; stroke-width: 0.5; }')
lines.append('    .base text { pointer-events: none; }')
lines.append('  </style>')
# Glow filter for markers
lines.append('  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">')
lines.append('    <feGaussianBlur stdDeviation="2" result="coloredBlur"/>')
lines.append('    <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>')
lines.append('  </filter>')
lines.append('</defs>')

# Ocean background
lines.append('<rect width="1000" height="1000" fill="#0a1826"/>')

# Subtle grid lines
for lon in range(12, 25, 2):
    x, _ = to_svg(lon, LAT_MIN)
    _, y0 = to_svg(lon, LAT_MAX)
    _, y1 = to_svg(lon, LAT_MIN)
    lines.append(f'<line x1="{x}" y1="{y0}" x2="{x}" y2="{y1}" class="grid"/>')
for lat in range(56, 70, 2):
    _, y = to_svg(LON_MIN, lat)
    x0, _ = to_svg(LON_MIN, lat)
    x1, _ = to_svg(LON_MAX, lat)
    lines.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" class="grid"/>')

# Land regions
lines.append('<g id="regions">')
for i, feature in enumerate(geojson["features"]):
    path_d = geojson_feature_to_path(feature)
    css_class = "gotland" if i == GOTLAND_ID else "land"
    props = feature.get("properties", {})
    name = list(props.values())[0] if props else f"region{i}"
    lines.append(f'  <path class="{css_class}" d="{path_d}" title="{name}"/>')
lines.append('</g>')

# Subtle coastline highlight
lines.append('<g id="regions-outline">')
for i, feature in enumerate(geojson["features"]):
    path_d = geojson_feature_to_path(feature)
    lines.append(f'  <path fill="none" stroke="#3a5a3a" stroke-width="1.2" d="{path_d}"/>')
lines.append('</g>')

# Military bases layer
lines.append('<g id="bases" filter="url(#glow)">')
for base in BASES:
    x, y = to_svg(base["lon"], base["lat"])
    marker = make_marker(x, y, base["type"], base["id"], base["name"])
    lines.append(marker)
lines.append('</g>')

# Legend
legend_x, legend_y = 820, 40
lines.append(f'<rect x="{legend_x-10}" y="{legend_y-20}" width="185" height="160" rx="4" fill="#0d1e2d" stroke="#2a4a2a" stroke-width="1" opacity="0.9"/>')
lines.append(f'<text x="{legend_x}" y="{legend_y}" font-family="monospace" font-size="11" font-weight="bold" fill="#7acc7a">SWEDEN AOR</text>')
legend_items = [
    ("▲", "#00e5ff", "Air Base"),
    ("◆", "#4499ff", "Naval Base"),
    ("★", "#ffd700", "Capital"),
    ("●", "#ff9900", "Major City"),
]
for j, (sym, col, lbl) in enumerate(legend_items):
    iy = legend_y + 22 + j * 22
    lines.append(f'<text x="{legend_x}" y="{iy}" font-family="monospace" font-size="12" fill="{col}">{sym}</text>')
    lines.append(f'<text x="{legend_x+18}" y="{iy}" font-family="monospace" font-size="10" fill="#aaccaa">{lbl}</text>')

# Theater label
lines.append('<text x="20" y="985" font-family="monospace" font-size="9" fill="#3a5a3a">SWEDEN MILITARY THEATER | lat 55-69N | lon 11-24E</text>')

lines.append('</svg>')

svg_content = "\n".join(lines)
out_path = r"c:\Users\dhiraj.kumar\Downloads\Saab\ruby-stridsledning-ai\data\input\sweden-military-map.svg"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(svg_content)

print(f"Generated SVG -> {out_path}")
print(f"Features rendered: {len(geojson['features'])}")
print(f"Bases plotted: {len(BASES)}")
print("\nBase SVG coordinates:")
for base in BASES:
    x, y = to_svg(base["lon"], base["lat"])
    print(f"  {base['id']:4s} ({base['lon']:.4f}E, {base['lat']:.4f}N) -> SVG({x}, {y})")
