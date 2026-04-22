import json, math, csv, os, glob

# 1. Load bases from CSV
bases = []
with open('data/input/Boreal_passage_coordinates.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['subtype'] in ['air_base', 'capital', 'major_city']:
            bases.append({'name': row['feature_name'], 'x': float(row['x_km']), 'y': float(row['y_km'])})

print("=== 12 BASES LOADED ===")
for b in bases:
    print(f"  {b['name']:<30} ({b['x']:>7.1f}, {b['y']:>7.1f})")

# 2. Check if batch_tester loads ALL bases or just some
# Replicate load_battlefield_state logic
import sys
sys.path.insert(0, '.')
os.environ['SAAB_MODE'] = 'sweden'
from src.models import load_battlefield_state
state = load_battlefield_state('data/input/Boreal_passage_coordinates.csv')
print(f"\n=== BASES ACTUALLY LOADED IN ENGINE: {len(state.bases)} ===")
total_ammo = 0
for b in state.bases:
    ammo = sum(b.inventory.values())
    total_ammo += ammo
    print(f"  {b.name:<30} ammo={ammo}")
print(f"\n  TOTAL AMMO ACROSS ALL BASES: {total_ammo}")

# 3. Full range audit - use start_x/start_y from batch JSON
print("\n=== RANGE COVERAGE AUDIT (All Batch 1 threats) ===")
batch_files = sorted(glob.glob('data/input/simulated_campaign_batch_*.json'))[:3]

PATRIOT_RANGE = 120  # km
METEOR_RANGE = 150   # km

total, in_patriot, in_meteor, out_all = 0, 0, 0, 0
for bf in batch_files:
    with open(bf) as f:
        batch = json.load(f)
    for scenario_threats in batch.values():
        for t in scenario_threats:
            tx, ty = t['start_x'], t['start_y']
            total += 1
            dists = [math.hypot(b['x'] - tx, b['y'] - ty) for b in bases]
            min_dist = min(dists)
            nearest_base = bases[dists.index(min_dist)]['name']
            if min_dist <= PATRIOT_RANGE:
                in_patriot += 1
            elif min_dist <= METEOR_RANGE:
                in_meteor += 1
            else:
                out_all += 1
                if out_all <= 5:
                    print(f"  DEAD ZONE: {t['id']} at ({tx:.0f},{ty:.0f}) "
                          f"-> nearest base: {nearest_base} at {min_dist:.0f}km")

print(f"\n  Threats analyzed:      {total}")
print(f"  Within Patriot (120km): {in_patriot} ({100*in_patriot/total:.1f}%)")
print(f"  Within Meteor  (150km): {in_meteor}  ({100*in_meteor/total:.1f}%)")
print(f"  Out of ALL range:       {out_all}   ({100*out_all/total:.1f}%)")

# 4. Show score equation
print("\n=== ROOT CAUSE SUMMARY ===")
print(f"  Map scale: threats range from approx 100-1500 km in x/y")
print(f"  Effector ranges: 3-150 km")
print(f"  Bases armed: {len(state.bases)} of {len(bases)} nodes")
covg = round(100*(in_patriot+in_meteor)/total, 1)
print(f"  Coverage with best effector: {covg}%")
print(f"  => Max achievable survival rate WITHOUT base repositioning: ~{covg}%")
