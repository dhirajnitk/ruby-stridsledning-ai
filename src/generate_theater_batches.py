"""
Boreal Tactical Batch Generator v2
====================================
Regenerates all 20 campaign batch files with threats that:
  1. Spawn within engagement range (50-140km) of at least one base
  2. Have realistic approach vectors pointing TOWARD that base
  3. Use real-world threat kinematics (speed, type, threat_value)
  4. Include mixed swarm compositions (drones, cruise, fighters, hypersonics)
"""

import json, math, random, csv, os, glob

random.seed(42)

# ── Load real base positions from CSV ──────────────────────────────────────
BASES = []
with open('data/input/Boreal_passage_coordinates.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['subtype'] in ['air_base', 'capital', 'major_city']:
            BASES.append({
                'name': row['feature_name'],
                'x': float(row['x_km']),
                'y': float(row['y_km'])
            })

print(f"[INIT] Loaded {len(BASES)} bases from theater CSV.")

# ── Real-world threat profiles (kinematics matched to EFFECTORS) ────────────
THREAT_PROFILES = [
    # type,               speed_kmh, threat_value, min_per_wave, max_per_wave
    ("drone",             150,       25,            2,  6),   # Shahed-style
    ("loiter",            200,       40,            1,  4),   # Loitering munition
    ("cruise-missile",    900,       250,           1,  3),   # Kalibr / Taurus
    ("fighter",           1800,      350,           1,  2),   # 4th-gen fast mover
    ("hypersonic-pgm",    7000,      500,           1,  2),   # Kinzhal / Zircon
    ("ballistic",         3000,      400,           1,  2),   # SRBM
    ("decoy",             200,       15,            1,  4),   # Electronic decoy
]

def spawn_threat_near_base(base, min_dist=60, max_dist=140):
    """
    Spawn a threat at a random bearing, between min_dist and max_dist km
    from the given base. Heading vector points back toward the base.
    """
    bearing = random.uniform(0, 2 * math.pi)
    dist    = random.uniform(min_dist, max_dist)
    sx = base['x'] + dist * math.cos(bearing)
    sy = base['y'] + dist * math.sin(bearing)
    return sx, sy, base['x'], base['y']  # start_x, start_y, target_x, target_y


def generate_scenario(scenario_id, num_threats_min=3, num_threats_max=25):
    """Generate one realistic scenario with mixed threat composition."""
    threats = []
    tick = 0

    # Pick 1-3 target bases for this scenario
    target_bases = random.sample(BASES, k=random.randint(1, min(3, len(BASES))))

    for i in range(random.randint(num_threats_min, num_threats_max)):
        profile = random.choices(
            THREAT_PROFILES,
            weights=[30, 20, 15, 10, 5, 5, 15],   # weighted toward drones / cruise
            k=1
        )[0]
        ttype, speed, tval, _, _ = profile

        # Spawn within engagement range of a randomly chosen target base
        base = random.choice(target_bases)
        sx, sy, tx, ty = spawn_threat_near_base(base)

        # Small offset so multiple threats don't all spawn at exact same point
        sx += random.uniform(-5, 5)
        sy += random.uniform(-5, 5)

        threats.append({
            "id":          f"{scenario_id}-{ttype.upper()[:4]}-{i+1:02d}",
            "type":        ttype,
            "start_x":     round(sx, 1),
            "start_y":     round(sy, 1),
            "target_x":    round(tx, 1),
            "target_y":    round(ty, 1),
            "speed":       speed + random.randint(-20, 20),   # ±20 km/h variance
            "threat_value": tval + random.uniform(-5, 5),
            "spawn_tick":  tick
        })
        tick += random.randint(0, 3)

    return threats


def generate_batch(batch_id, scenarios_per_batch=50):
    """Generate one batch file containing multiple scenarios."""
    batch = {}
    for i in range(scenarios_per_batch):
        sid = f"{batch_id:03d}-{i+1:03d}"
        # Vary scenario intensity: light (3-8), medium (8-18), heavy (18-30)
        intensity = random.choices(
            [("light", 3, 8), ("medium", 8, 18), ("heavy", 18, 30)],
            weights=[40, 40, 20], k=1
        )[0]
        _, mn, mx = intensity
        batch[sid] = generate_scenario(sid, mn, mx)
    return batch


# ── Generate all 20 batch files ─────────────────────────────────────────────
OUTPUT_DIR = 'data/input'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Archive old batches
old_files = glob.glob(f'{OUTPUT_DIR}/simulated_campaign_batch_*.json')
if old_files:
    archive_dir = f'{OUTPUT_DIR}/archive_old_batches'
    os.makedirs(archive_dir, exist_ok=True)
    for f in old_files:
        fname = os.path.basename(f)
        os.rename(f, os.path.join(archive_dir, fname))
    print(f"[ARCHIVE] Moved {len(old_files)} old batch files to {archive_dir}/")

print("[GEN] Generating 20 theater-aware campaign batches...")
total_threats = 0
total_scenarios = 0

for batch_num in range(1, 21):
    batch_data = generate_batch(batch_num, scenarios_per_batch=50)
    out_path = f'{OUTPUT_DIR}/simulated_campaign_batch_{batch_num}.json'
    with open(out_path, 'w') as f:
        json.dump(batch_data, f, indent=2)
    
    t_count = sum(len(v) for v in batch_data.values())
    total_threats += t_count
    total_scenarios += len(batch_data)
    print(f"  Batch {batch_num:>2}: {len(batch_data)} scenarios | {t_count} threats -> {out_path}")

print(f"\n[DONE] Generated {total_scenarios} scenarios, {total_threats} threats across 20 batch files.")
print(f"[DONE] All threats spawn within 60-140km of real Boreal theater bases.")

# ── Quick validation: verify coverage ──────────────────────────────────────
print("\n[VALIDATE] Spot-checking range coverage...")
with open(f'{OUTPUT_DIR}/simulated_campaign_batch_1.json') as f:
    sample = json.load(f)

PATRIOT_RANGE = 120
total, covered = 0, 0
for threats in sample.values():
    for t in threats:
        total += 1
        dists = [math.hypot(b['x'] - t['start_x'], b['y'] - t['start_y']) for b in BASES]
        if min(dists) <= PATRIOT_RANGE:
            covered += 1

print(f"  Batch 1: {covered}/{total} threats within Patriot range ({100*covered/total:.1f}%)")
print(f"  Expected: ~85-95% (some spawn 120-140km away, in Meteor/NASAMS envelope)")
