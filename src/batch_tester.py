import json
import os
import sys

# Auto-correct working directory if the user runs the script from inside 'src/'
if os.path.basename(os.getcwd()) == "src":
    os.chdir("..")
    
import glob
import csv
import numpy as np
import matplotlib.pyplot as plt
from agent_backend import load_battlefield_state, CSV_FILE_PATH
from engine import evaluate_threats_advanced
from models import Threat

# Tune this parameter to test MCTS depth (e.g., 100, 500, 1000, 2000)
MCTS_ITERATIONS = 1000

def run_batch_tests():
    print("Loading base battlefield state...")
    # Load the initial ground truth from your CSV
    base_state = load_battlefield_state(CSV_FILE_PATH)
    
    total_scenarios = 0
    survived_scenarios = 0
    total_tactical_score = 0.0
    
    # Data arrays for plotting
    scenario_ids = []
    scores = []
    bar_colors = []
    csv_data = [["Scenario ID", "Threat Count", "MCTS Score", "Survival Status"]]

    # Find all 20 batch files in the new data directory
    INPUT_DIR = "data/input"
    RESULTS_DIR = "data/results"
    
    batch_files = sorted(glob.glob(os.path.join(INPUT_DIR, "simulated_campaign_batch_*.json")))
    
    if not batch_files:
        print("No batch files found! Make sure they are in the same folder.")
        return

    print(f"Found {len(batch_files)} batch files. Initiating Boreal Chessmaster evaluation...\n")
    print(f"{'SCENARIO':<10} | {'THREATS':<10} | {'MCTS SCORE':<12} | {'CAPITAL SURVIVAL'}")
    print("-" * 60)
    
    for file in batch_files:
        with open(file, 'r') as f:
            batch_data = json.load(f)
            
        for scenario_id, threats_data in batch_data.items():
            total_scenarios += 1
            
            # Convert the Red Team JSON payload into your Engine's data classes
            active_threats = []
            for t in threats_data:
                # Map target coordinates to Base Names for Self-Defense Doctrine
                target_x, target_y = t.get("target_x"), t.get("target_y")
                if target_x == 198.3 and target_y == 335.0:
                    heading = "Northern Vanguard Base"
                elif target_x == 838.3 and target_y == 75.0:
                    heading = "Highridge Command"
                elif target_x == 418.3 and target_y == 95.0:
                    heading = "Capital X"
                else:
                    heading = f"Targeting x:{target_x}, y:{target_y}"

                active_threats.append(Threat(
                    id=t["id"],
                    x=t["start_x"],
                    y=t["start_y"],
                    speed_kmh=t["speed"],
                    heading=heading,
                    estimated_type=t["type"],
                    threat_value=t["threat_value"]
                ))
            
            # ADVANCED ENGINE: Run the Hungarian Matcher and MCTS Rollouts
            decision = evaluate_threats_advanced(
                base_state, 
                active_threats, 
                mcts_iterations=MCTS_ITERATIONS, 
                max_time_sec=30.0,
                doctrine_primary="balanced"
            )
            
            score = decision["strategic_consequence_score"]
            is_safe = score > -100 # Capital survives if penalty doesn't nuke the score
            
            if is_safe:
                survived_scenarios += 1
                
            total_tactical_score += score
            
            # Store data for the visualization
            scenario_ids.append(scenario_id)
            scores.append(score)
            bar_colors.append('#a6e3a1' if is_safe else '#f38ba8')  # Green if safe, Red if destroyed
            
            status = 'SAFE' if is_safe else 'DESTROYED'
            csv_data.append([scenario_id, len(active_threats), round(score, 2), status])
            print(f"{scenario_id:<10} | {len(active_threats):<10} | {score:<12.2f} | {status}")

    # Calculate final metrics
    survival_rate = (survived_scenarios / total_scenarios) * 100 if total_scenarios > 0 else 0
    avg_score = total_tactical_score / total_scenarios if total_scenarios > 0 else 0

    print("\n" + "="*50)
    print("====== GRAND CAMPAIGN RESULTS ======")
    print("="*50)
    print(f"Total Scenarios Evaluated : {total_scenarios}")
    print(f"Capital Survival Rate     : {survival_rate:.1f}%")
    print(f"Average Tactical Score    : {avg_score:.2f}")
    print("="*50)
    
    # --- Output Top 5 Worst Scenarios ---
    # Skip the header row (csv_data[1:]), sort by the score column (index 2), and slice the first 5
    worst_scenarios = sorted(csv_data[1:], key=lambda x: x[2])[:5]
    print("\n" + "="*50)
    print("====== TOP 5 WORST SCENARIOS ======")
    print("="*50)
    print(f"{'SCENARIO':<10} | {'THREATS':<10} | {'SCORE':<12} | {'STATUS'}")
    print("-" * 50)
    for row in worst_scenarios:
        print(f"{row[0]:<10} | {row[1]:<10} | {row[2]:<12.2f} | {row[3]}")
    print("="*50)

    # --- Generate Visualization ---
    print("\nGenerating performance bar chart...")
    plt.figure(figsize=(18, 6))
    plt.bar(scenario_ids, scores, color=bar_colors)
    plt.axhline(y=-100, color='#f38ba8', linestyle='--', linewidth=2, label='Capital Destroyed Threshold (-100)')
    
    # Calculate and plot the trend line
    if len(scores) > 1:
        x_indices = np.arange(len(scores))
        z = np.polyfit(x_indices, scores, 1)
        p = np.poly1d(z)
        plt.plot(scenario_ids, p(x_indices), color='#89b4fa', linestyle='-', linewidth=3, label='Performance Trend')
    
    plt.title(f'Boreal Chessmaster: Tactical AI Performance (MCTS Iterations: {MCTS_ITERATIONS})', fontsize=16)
    plt.xlabel('Scenario ID', fontsize=12)
    plt.ylabel('MCTS Evaluation Score', fontsize=12)
    plt.xticks(rotation=90, fontsize=8)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, f'campaign_results_{MCTS_ITERATIONS}_iters.png'), dpi=300)
    print(f"Chart successfully saved as 'campaign_results_{MCTS_ITERATIONS}_iters.png' in data/results!")
    plt.show()
    
    # --- Export to CSV ---
    csv_filename = os.path.join(RESULTS_DIR, f'campaign_results_{MCTS_ITERATIONS}_iters.csv')
    print(f"Exporting detailed results to '{csv_filename}'...")
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)

if __name__ == "__main__":
    run_batch_tests()