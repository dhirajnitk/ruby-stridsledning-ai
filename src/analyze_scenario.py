import json, math, csv

# Load bases
bases = []
with open('data/input/Boreal_passage_coordinates.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['subtype'] in ['air_base', 'capital', 'major_city']:
            bases.append({'name': row['feature_name'], 'x': float(row['x_km']), 'y': float(row['y_km'])})

# Load scenario 001-014
with open('data/input/simulated_campaign_batch_1.json') as f:
    batch = json.load(f)
    s = batch['001-014']

print(f"Scenario 001-014: {len(s)} threats")
for t in s:
    sx, sy = t['start_x'], t['start_y']
    tx, ty = t['target_x'], t['target_y']
    
    # Find nearest base to start point
    dists = [(b['name'], math.hypot(b['x']-sx, b['y']-sy)) for b in bases]
    nearest_name, nearest_dist = min(dists, key=lambda x: x[1])
    
    # Find target base
    target_name = "Unknown"
    for b in bases:
        if abs(b['x']-tx) < 1 and abs(b['y']-ty) < 1:
            target_name = b['name']
            break
            
    print(f"  T:{t['id']:<15} Pos:({sx:>6.1f},{sy:>6.1f}) -> Target:{target_name:<25} dist={nearest_dist:>5.1f}km to {nearest_name}")
