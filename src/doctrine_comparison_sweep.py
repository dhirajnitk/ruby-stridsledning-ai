import json
import os
import glob
import csv
import numpy as np
import matplotlib.pyplot as plt
from agent_backend import load_battlefield_state, CSV_FILE_PATH
from engine import evaluate_threats_advanced
from models import Threat

# Config
MCTS_ITERATIONS = 500 # Balanced for speed vs fidelity in a large sweep
DOCTRINES = ["balanced", "aggressive", "fortress", "economy", "ambush", "saturation", "scout"]

def run_doctrine_sweep():
    print("="*60)
    print("  BOREAL CHESSMASTER — COMPETITIVE DOCTRINE SWEEP")
    print("="*60)
    
    base_state = load_battlefield_state(CSV_FILE_PATH)
    INPUT_DIR = "data/input"
    RESULTS_DIR = "data/results"
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    batch_files = sorted(glob.glob(os.path.join(INPUT_DIR, "simulated_campaign_batch_*.json")))
    if not batch_files:
        print("Error: No scenarios found in data/input/!")
        return

    # Master results container
    doctrine_stats = {d: {"survived": 0, "total": 0, "scores": []} for d in DOCTRINES}

    for file in batch_files:
        print(f"Processing {os.path.basename(file)}...")
        with open(file, 'r') as f: batch_data = json.load(f)
        
        for scenario_id, threats_data in batch_data.items():
            active_threats = []
            for t in threats_data:
                active_threats.append(Threat(t["id"], t["start_x"], t["start_y"], t["speed"], "Capital X", t["type"], t["threat_value"]))
            
            for doctrine in DOCTRINES:
                res = evaluate_threats_advanced(base_state, active_threats, mcts_iterations=MCTS_ITERATIONS, doctrine_primary=doctrine)
                score = res["strategic_consequence_score"]
                doctrine_stats[doctrine]["total"] += 1
                doctrine_stats[doctrine]["scores"].append(score)
                if score > -100: doctrine_stats[doctrine]["survived"] += 1

    # --- Analysis & Visualization ---
    labels = [d.upper() for d in DOCTRINES]
    survival_rates = [(doctrine_stats[d]["survived"] / doctrine_stats[d]["total"]) * 100 for d in DOCTRINES]
    avg_scores = [np.mean(doctrine_stats[d]["scores"]) for d in DOCTRINES]

    print("\n" + "="*60)
    print(f"{'DOCTRINE':<15} | {'SURVIVAL RATE':<15} | {'AVG MCTS SCORE'}")
    print("-" * 60)
    for i, d in enumerate(DOCTRINES):
        print(f"{d.upper():<15} | {survival_rates[i]:<14.1f}% | {avg_scores[i]:<15.2f}")
    print("="*60)

    # 1. Survival Rate Chart
    plt.figure(figsize=(12, 6))
    bars = plt.bar(labels, survival_rates, color=['#89b4fa', '#f38ba8', '#a6e3a1', '#fab387', '#cba6f7', '#f9e2af', '#94e2d5'])
    plt.title('Boreal Chessmaster: Doctrine Survival Rates (100 Scenarios)', fontsize=14)
    plt.ylabel('Capital Survival Rate (%)')
    plt.ylim(0, 110)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 2, f'{yval:.1f}%', ha='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'doctrine_survival_comparison.png'), dpi=300)
    print(f"\n[OK] Comparison chart saved to data/results/doctrine_survival_comparison.png")
    
    # 2. Export Detailed CSV
    with open(os.path.join(RESULTS_DIR, 'doctrine_comparison_data.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Doctrine", "Survival Rate", "Avg Score"])
        for i, d in enumerate(DOCTRINES):
            writer.writerow([d, survival_rates[i], avg_scores[i]])

if __name__ == "__main__":
    run_doctrine_sweep()
