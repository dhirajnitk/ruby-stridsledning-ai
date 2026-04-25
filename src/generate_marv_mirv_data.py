"""
MARV / MIRV Training Data Generator
====================================
Generates training data that includes MARV, MIRV, and Dogfight threat types
alongside standard threats. This extends the existing 15-D → 18-D feature
vector and produces ground-truth labels via the MCTS Oracle.

NOTE: Does NOT overwrite existing datasets. Produces new files:
  - data/training/strategic_mega_corpus/marv_mirv_train.npz
  - data/training/strategic_mega_corpus/marv_mirv_eval.npz

Run from project root:
    python src/generate_marv_mirv_data.py
"""

import os, sys, math, random, json, time
import numpy as np

os.environ["SAAB_MODE"] = "boreal"
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from core.models import Threat, GameState, Base, load_battlefield_state, EFFECTORS
from core.engine import (
    evaluate_threats_advanced,
    extract_rl_features,
    StrategicMCTS,
    TacticalEngine,
)

CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'input', 'Boreal_passage_coordinates.csv')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'training', 'strategic_mega_corpus')

# ── ANSI ─────────────────────────────────────────────────────────────────────
RST = "\033[0m"; GRN = "\033[92m"; YLW = "\033[93m"; CYN = "\033[96m"
BLD = "\033[1m"; MAG = "\033[95m"

THREAT_TEMPLATES = {
    # Standard threats (unchanged from original generator)
    "ballistic":  {"speed": 4500, "type": "ballistic",      "val_range": (80, 200)},
    "cruise":     {"speed": 900,  "type": "cruise-missile",  "val_range": (40, 100)},
    "hypersonic": {"speed": 6000, "type": "hypersonic-pgm",  "val_range": (90, 200)},
    "drone":      {"speed": 300,  "type": "drone",           "val_range": (15, 40)},
    "fighter":    {"speed": 2200, "type": "fighter",          "val_range": (50, 150)},
    # New: MARV — maneuvering ballistic
    "marv":       {"speed": 4500, "type": "ballistic",      "val_range": (150, 250),
                   "is_marv": True, "marv_pk_penalty": (0.35, 0.65), "marv_trigger_range_km": (60, 120)},
    # New: MIRV — bus with multiple warheads
    "mirv":       {"speed": 4500, "type": "ballistic",      "val_range": (200, 350),
                   "is_mirv": True, "mirv_count": (2, 5), "mirv_release_range_km": (120, 200)},
    # New: Dogfighter — can engage our interceptors
    "dogfighter": {"speed": 2400, "type": "fighter",         "val_range": (100, 180),
                   "can_dogfight": True, "dogfight_win_prob": (0.2, 0.5), "can_rtb": True},
}

# Probability weights: MARV/MIRV/Dogfight appear in ~30% of threats
THREAT_WEIGHTS = {
    "ballistic": 20, "cruise": 20, "hypersonic": 10, "drone": 20, "fighter": 10,
    "marv": 8, "mirv": 5, "dogfighter": 7,
}


def make_threat(idx, bases, template_key):
    """Create a single Threat with randomized position and advanced flags."""
    tmpl = THREAT_TEMPLATES[template_key]
    
    # Randomize spawn position (southern approach into northern territory)
    x = random.uniform(50, 1500)
    y = random.uniform(600, 1400)
    
    # Pick a random target base
    tgt = random.choice(bases)
    
    val = random.uniform(*tmpl["val_range"])
    
    kwargs = {
        "id": f"T{idx}",
        "x": x, "y": y,
        "speed_kmh": tmpl["speed"] + random.uniform(-200, 200),
        "heading": tgt.name,
        "estimated_type": tmpl["type"],
        "threat_value": val,
    }
    
    # MARV flags
    if tmpl.get("is_marv"):
        kwargs["is_marv"] = True
        kwargs["marv_pk_penalty"] = random.uniform(*tmpl["marv_pk_penalty"])
        kwargs["marv_trigger_range_km"] = random.uniform(*tmpl["marv_trigger_range_km"])
    
    # MIRV flags
    if tmpl.get("is_mirv"):
        kwargs["is_mirv"] = True
        kwargs["mirv_count"] = random.randint(*tmpl["mirv_count"])
        kwargs["mirv_release_range_km"] = random.uniform(*tmpl["mirv_release_range_km"])
    
    # Dogfight flags
    if tmpl.get("can_dogfight"):
        kwargs["can_dogfight"] = True
        kwargs["dogfight_win_prob"] = random.uniform(*tmpl["dogfight_win_prob"])
        kwargs["can_rtb"] = tmpl.get("can_rtb", False)
    
    return Threat(**kwargs)


def generate_scenario(state):
    """Generate a randomized scenario with MARV/MIRV/Dogfight threats mixed in."""
    n_threats = random.randint(5, 25)
    
    # Weighted random selection of threat types
    keys = list(THREAT_WEIGHTS.keys())
    weights = [THREAT_WEIGHTS[k] for k in keys]
    
    threats = []
    for i in range(n_threats):
        template = random.choices(keys, weights=weights, k=1)[0]
        threats.append(make_threat(i, state.bases, template))
    
    weather = random.choice(["clear", "clear", "fog", "storm"])
    doctrine = random.choice(["balanced", "fortress", "aggressive"])
    blend = random.uniform(0.2, 0.8)
    
    return threats, weather, doctrine, blend


def collect_dataset(state, n_samples, label):
    """Generate n_samples training examples using the MCTS Oracle."""
    print(f"\n{CYN}{BLD}[FORGE] Generating {n_samples} {label} samples with MARV/MIRV/Dogfight...{RST}")
    
    all_features = []
    all_scores = []
    all_weights = []
    
    # Track MARV/MIRV/Dogfight distribution
    marv_total, mirv_total, dog_total, standard_total = 0, 0, 0, 0
    
    t0 = time.time()
    for i in range(n_samples):
        threats, weather, doctrine, blend = generate_scenario(state)
        
        # Count advanced threats
        for t in threats:
            if getattr(t, "is_marv", False): marv_total += 1
            elif getattr(t, "is_mirv", False): mirv_total += 1
            elif getattr(t, "can_dogfight", False): dog_total += 1
            else: standard_total += 1
        
        # Get Oracle ground truth
        try:
            score, details, rl_val = evaluate_threats_advanced(
                state, threats,
                mcts_iterations=200,
                weather=weather,
                doctrine_primary=doctrine,
                doctrine_blend=blend,
                use_rl=False
            )
        except Exception as e:
            continue
        
        # Extract 18-D features
        features = extract_rl_features(state, threats, weather, doctrine, blend, for_value=True)
        
        sample_score = score
        # Get doctrine weights from the assignments if available
        sample_weights = [0.5] * 11  # Default balanced weights
        
        all_features.append(features)
        all_scores.append(sample_score)
        all_weights.append(sample_weights[:11])  # Ensure consistent 11-D output
        
        if (i + 1) % 100 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (n_samples - i - 1) / rate if rate > 0 else 0
            print(f"  {GRN}[{i+1}/{n_samples}]{RST} Rate: {rate:.1f} samples/s | "
                  f"ETA: {eta:.0f}s | MARV:{marv_total} MIRV:{mirv_total} DOG:{dog_total}")
    
    print(f"\n{MAG}  Distribution: MARV={marv_total} MIRV={mirv_total} "
          f"Dogfight={dog_total} Standard={standard_total}{RST}")
    
    return (np.array(all_features, dtype=np.float32),
            np.array(all_scores, dtype=np.float32),
            np.array(all_weights, dtype=np.float32))


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    state = load_battlefield_state(CSV_PATH)
    
    print(f"{GRN}{BLD}╔══════════════════════════════════════════════════════════╗")
    print(f"║  MARV / MIRV TRAINING DATA GENERATOR                     ║")
    print(f"║  18-D Feature Vector × MCTS Oracle Ground Truth           ║")
    print(f"╚══════════════════════════════════════════════════════════╝{RST}")
    print(f"  Bases loaded: {len(state.bases)}")
    print(f"  Output: {OUTPUT_DIR}")
    
    # Phase 1: Training set (2000 samples — fast enough to run locally)
    feat, scores, weights = collect_dataset(state, 2000, "TRAINING")
    train_path = os.path.join(OUTPUT_DIR, "marv_mirv_train.npz")
    np.savez_compressed(train_path, features=feat, scores=scores, weights=weights)
    print(f"  {GRN}✓ Saved: {train_path} ({feat.shape[0]} × {feat.shape[1]}){RST}")
    
    # Phase 2: Evaluation set (500 samples — held out)
    feat_e, scores_e, weights_e = collect_dataset(state, 500, "EVALUATION")
    eval_path = os.path.join(OUTPUT_DIR, "marv_mirv_eval.npz")
    np.savez_compressed(eval_path, features=feat_e, scores=scores_e, weights=weights_e)
    print(f"  {GRN}✓ Saved: {eval_path} ({feat_e.shape[0]} × {feat_e.shape[1]}){RST}")
    
    print(f"\n{GRN}{BLD}[COMPLETE] MARV/MIRV dataset generation finished.{RST}")
    print(f"  Next step: python src/neural_trainer.py")
