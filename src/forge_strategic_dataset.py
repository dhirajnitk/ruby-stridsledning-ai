import os
import numpy as np
import random
import multiprocessing
import time
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from training.mega_data_factory import worker_task, load_real_clutter
from agent_backend import load_battlefield_state, CSV_FILE_PATH

# --- CONFIGURATION ---
BATCH_SIZE = 100
NUM_WORKERS = 4 
OUTPUT_DIR = "data/training/strategic_mega_corpus"

def generate_batch(count, base_state, real_clutter_pool):
    print(f"[FORGE] Generating {count} samples (Workers: {NUM_WORKERS})...", flush=True)
    
    if NUM_WORKERS <= 1:
        # Single-process fallback for debugging
        all_features, all_scores, all_weights = [], [], []
        for i in range(count):
            batch = worker_task(0, 1, base_state, real_clutter_pool)
            for s in batch:
                all_features.append(s["features"])
                all_scores.append(s["score"])
                all_weights.append(s["weights"])
            if (i+1) % 10 == 0:
                print(f"[FORGE] Progress: {i+1}/{count} samples generated...", flush=True)
        return np.array(all_features, dtype=np.float32), \
               np.array(all_scores, dtype=np.float32), \
               np.array(all_weights, dtype=np.float32)

    # Multi-process (Spawn context for Windows)
    from multiprocessing import get_context
    ctx = get_context('spawn')
    with ProcessPoolExecutor(max_workers=NUM_WORKERS, mp_context=ctx) as executor:
        num_batches = max(1, count // BATCH_SIZE)
        futures = {executor.submit(worker_task, i, BATCH_SIZE, base_state, real_clutter_pool): i for i in range(num_batches)}
        
        all_features, all_scores, all_weights = [], [], []
        collected = 0
        for future in as_completed(futures):
            try:
                batch = future.result()
                for s in batch:
                    all_features.append(s["features"])
                    all_scores.append(s["score"])
                    all_weights.append(s["weights"])
                collected += len(batch)
                print(f"[FORGE] Progress: {collected}/{count} samples generated...", flush=True)
            except Exception as e:
                print(f"[ERROR] Worker failed: {e}")
                raise
            
    return np.array(all_features, dtype=np.float32), \
           np.array(all_scores, dtype=np.float32), \
           np.array(all_weights, dtype=np.float32)

def run_mega_forge(phases, total_samples):
    print(f"[LAUNCH] MEGA-CORPUS STRATEGIC FORGE | Workers: {NUM_WORKERS} | Phases: {phases} | Samples: {total_samples}", flush=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    base_state = load_battlefield_state(CSV_FILE_PATH)
    real_clutter_pool = load_real_clutter()
    
    start_time = time.time()

    if "eval" in phases:
        print("\n[PHASE 1] Forging SHARED EVALUATION SET (500 samples)...")
        feat, score, weight = generate_batch(500, base_state, real_clutter_pool)
        np.savez_compressed(os.path.join(OUTPUT_DIR, "eval_shared_gold.npz"), features=feat, scores=score, weights=weight)

    if "ppo" in phases:
        print(f"\n[PHASE 3] Forging PPO MEGA CORPUS ({total_samples} samples)...")
        feat, score, weight = generate_batch(total_samples, base_state, real_clutter_pool)
        np.savez_compressed(os.path.join(OUTPUT_DIR, "ppo_train_100k.npz"), features=feat, scores=score, weights=weight)

    print(f"\n[COMPLETE] FORGE FINISHED | Total Time: {(time.time() - start_time)/60:.1f} minutes")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phases", nargs="+", default=["ppo"])
    parser.add_argument("--samples", type=int, default=100000)
    args = parser.parse_args()
    run_mega_forge(args.phases, args.samples)
