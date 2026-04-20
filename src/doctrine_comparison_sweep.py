import json
import os
import glob
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')  # headless-safe
import matplotlib.pyplot as plt
from agent_backend import load_battlefield_state, CSV_FILE_PATH
from engine import evaluate_threats_advanced
from models import Threat

# Config
MCTS_ITERATIONS = 100
DOCTRINES = ["balanced", "aggressive", "fortress", "economy", "ambush", "saturation", "scout"]

def run_doctrine_sweep():
    print("="*70)
    print("  BOREAL CHESSMASTER — COMPETITIVE DOCTRINE SWEEP")
    print("="*70)

    base_state = load_battlefield_state(CSV_FILE_PATH)
    INPUT_DIR = "data/input"
    RESULTS_DIR = "data/results"
    os.makedirs(RESULTS_DIR, exist_ok=True)

    batch_files = sorted(glob.glob(os.path.join(INPUT_DIR, "simulated_campaign_batch_*.json")))
    if not batch_files:
        print("Error: No scenarios found in data/input/!")
        return

    doctrine_stats = {d: {"survived": 0, "total": 0, "scores": []} for d in DOCTRINES}
    per_scenario_log = []

    for file in batch_files:
        print(f"Processing {os.path.basename(file)}...")
        with open(file, 'r') as f: batch_data = json.load(f)

        for scenario_id, threats_data in batch_data.items():
            active_threats = [Threat(t["id"], t["start_x"], t["start_y"], t["speed"],
                                     "Capital X", t["type"], t["threat_value"])
                              for t in threats_data]

            for doctrine in DOCTRINES:
                res = evaluate_threats_advanced(base_state, active_threats,
                                                mcts_iterations=MCTS_ITERATIONS,
                                                doctrine_primary=doctrine)
                score = res["strategic_consequence_score"]
                doctrine_stats[doctrine]["total"] += 1
                doctrine_stats[doctrine]["scores"].append(score)
                if score > -100: doctrine_stats[doctrine]["survived"] += 1
                per_scenario_log.append((os.path.basename(file), scenario_id, doctrine,
                                         score, len(res["tactical_assignments"])))

    # --- Analysis & Visualization ---
    labels = [d.upper() for d in DOCTRINES]
    survival_rates = [(doctrine_stats[d]["survived"] / doctrine_stats[d]["total"]) * 100 for d in DOCTRINES]
    avg_scores = [np.mean(doctrine_stats[d]["scores"]) for d in DOCTRINES]

    print("\n" + "="*75)
    print(f"{'DOCTRINE':<12} | {'SURVIVAL':<10} | {'AVG':<10} | {'MIN':<10} | {'MAX':<10} | {'STD':<8}")
    print("-" * 75)
    for i, d in enumerate(DOCTRINES):
        s = doctrine_stats[d]["scores"]
        print(f"{d.upper():<12} | {survival_rates[i]:<9.1f}% | {avg_scores[i]:<10.2f} | "
              f"{np.min(s):<10.1f} | {np.max(s):<10.1f} | {np.std(s):<8.2f}")
    print("="*75)

    # Diagnostic: how many scenarios genuinely differentiate the doctrines?
    from collections import defaultdict
    scen_scores = defaultdict(dict)
    for fn, sid, doc, score, _ in per_scenario_log:
        scen_scores[(fn, sid)][doc] = score
    unique_counts = [len(set(v.values())) for v in scen_scores.values()]
    print(f"\nScenarios where all 7 doctrines gave IDENTICAL score: "
          f"{sum(1 for u in unique_counts if u == 1)} / {len(unique_counts)}")
    print(f"Scenarios with >=2 distinct scores across doctrines:  "
          f"{sum(1 for u in unique_counts if u >= 2)} / {len(unique_counts)}")
    print(f"Max distinct scores seen in one scenario: {max(unique_counts)}")

    # 1. Survival Rate Chart
    plt.figure(figsize=(12, 6))
    bars = plt.bar(labels, survival_rates,
                   color=['#89b4fa', '#f38ba8', '#a6e3a1', '#fab387', '#cba6f7', '#f9e2af', '#94e2d5'])
    plt.title(f'Boreal Chessmaster: Doctrine Survival Rates ({len(scen_scores)} scenarios)', fontsize=14)
    plt.ylabel('Capital Survival Rate (%)')
    plt.ylim(0, 110)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 2, f'{yval:.1f}%', ha='center', fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'doctrine_survival_comparison.png'), dpi=150)
    print(f"\n[OK] Comparison chart saved to {RESULTS_DIR}/doctrine_survival_comparison.png")

    # 2. Avg-score chart (new)
    plt.figure(figsize=(12, 6))
    bars = plt.bar(labels, avg_scores,
                   color=['#89b4fa', '#f38ba8', '#a6e3a1', '#fab387', '#cba6f7', '#f9e2af', '#94e2d5'])
    plt.title(f'Boreal Chessmaster: Avg Strategic Score by Doctrine ({len(scen_scores)} scenarios)', fontsize=14)
    plt.ylabel('Average Strategic Consequence Score')
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + (5 if yval >= 0 else -15),
                 f'{yval:.0f}', ha='center', fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'doctrine_score_comparison.png'), dpi=150)
    print(f"[OK] Score chart saved to {RESULTS_DIR}/doctrine_score_comparison.png")

    # 3. Export Detailed CSV
    with open(os.path.join(RESULTS_DIR, 'doctrine_comparison_data.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Doctrine", "Survival Rate %", "Avg Score", "Min Score", "Max Score", "Std"])
        for i, d in enumerate(DOCTRINES):
            s = doctrine_stats[d]["scores"]
            writer.writerow([d, f"{survival_rates[i]:.2f}", f"{avg_scores[i]:.2f}",
                             f"{np.min(s):.2f}", f"{np.max(s):.2f}", f"{np.std(s):.2f}"])

    # 4. Per-scenario log
    with open(os.path.join(RESULTS_DIR, 'doctrine_per_scenario.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["batch", "scenario", "doctrine", "score", "assignments"])
        for row in per_scenario_log: writer.writerow(row)
    print(f"[OK] Per-scenario log saved to {RESULTS_DIR}/doctrine_per_scenario.csv")

if __name__ == "__main__":
    run_doctrine_sweep()
