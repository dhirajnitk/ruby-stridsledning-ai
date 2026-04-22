import numpy as np
import os
import random
import multiprocessing
import time
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from mega_data_factory import worker_task, load_real_clutter
from agent_backend import load_battlefield_state, CSV_FILE_PATH

# --- CONFIGURATION ---
BATCH_SIZE = 500
NUM_WORKERS = multiprocessing.cpu_count()
OUTPUT_DIR = "data/training/strategic_mega_corpus"

def generate_batch(count, base_state, real_clutter_pool):
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        num_batches = count // BATCH_SIZE
        futures = {executor.submit(worker_task, i, BATCH_SIZE, base_state, real_clutter_pool): i for i in range(num_batches)}
        
        all_features, all_scores, all_weights = [], [], []
        collected = 0
        for future in as_completed(futures):
            batch = future.result()
            for s in batch:
                all_features.append(s["features"])
                all_scores.append(s["score"])
                all_weights.append(s["weights"])
            collected += len(batch)
            print(f"[FORGE] Progress: {collected}/{count} samples generated...")
            
    return np.array(all_features, dtype=np.float32), \
           np.array(all_scores, dtype=np.float32), \
           np.array(all_weights, dtype=np.float32)

def run_mega_forge(phases):
    print(f"[LAUNCH] MEGA-CORPUS STRATEGIC FORGE | Workers: {NUM_WORKERS} | Phases: {phases}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    base_state = load_battlefield_state(CSV_FILE_PATH)
    real_clutter_pool = load_real_clutter()
    
    start_time = time.time()

    if "eval" in phases:
        print("\n[PHASE 1] Forging SHARED EVALUATION SET (5,000 samples)...")
        feat, score, weight = generate_batch(5000, base_state, real_clutter_pool)
        np.savez_compressed(os.path.join(OUTPUT_DIR, "eval_shared_gold.npz"), features=feat, scores=score, weights=weight)

    if "rl" in phases:
        print("\n[PHASE 2] Forging RL HEURISTIC TRAINING SET (20,000 samples)...")
        feat, score, weight = generate_batch(20000, base_state, real_clutter_pool)
        np.savez_compressed(os.path.join(OUTPUT_DIR, "rl_train_20k.npz"), features=feat, scores=score, weights=weight)

    if "ppo" in phases:
        print("\n[PHASE 3] Forging PPO MEGA CORPUS (100,000 samples)...")
        feat, score, weight = generate_batch(100000, base_state, real_clutter_pool)
        np.savez_compressed(os.path.join(OUTPUT_DIR, "ppo_train_100k.npz"), features=feat, scores=score, weights=weight)

    print(f"\n[COMPLETE] FORGE FINISHED | Total Time: {(time.time() - start_time)/60:.1f} minutes")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phases", nargs="+", default=["eval", "rl", "ppo"])
    args = parser.parse_args()
    run_mega_forge(args.phases)
