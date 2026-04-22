import numpy as np
import os

def fuse_strategic_master():
    print("====================================================")
    print("   BOREAL GLOBAL FUSION: SECURING THE MASTER CORPUS ")
    print("====================================================")
    
    files = [
        "data/training/strategic_mega_corpus/boreal_object_level_train.npz",
        "data/training/strategic_mega_corpus/grounded_ukraine_v1.npz",
        "data/training/strategic_mega_corpus/osint_er2_hypersonic.npz"
    ]
    
    all_f, all_s, all_w = [], [], []
    
    for f in files:
        if os.path.exists(f):
            print(f"[LOAD] Fusing {os.path.basename(f)}...")
            data = np.load(f)
            all_f.append(data['features'])
            all_s.append(data['scores'])
            all_w.append(data['weights'])
        else:
            print(f"[SKIP] {f} not found.")
            
    if not all_f:
        print("[ERROR] No data found to fuse.")
        return
        
    master_f = np.concatenate(all_f, axis=0)
    master_s = np.concatenate(all_s, axis=0)
    master_w = np.concatenate(all_w, axis=0)
    
    output_path = "data/training/strategic_mega_corpus/global_fused_master_v1.npz"
    np.savez_compressed(output_path, features=master_f, scores=master_s, weights=master_w)
    
    print(f"====================================================")
    print(f"[COMPLETE] GLOBAL MASTER SECURED: {len(master_f)} Samples")
    print(f"PATH: {output_path}")
    print("====================================================")

def split_strategic_datasets():
    print("====================================================")
    print("   BOREAL STRATEGIC SPLITTER: SECURING THE TRINITY  ")
    print("====================================================")
    
    targets = [
        ("data/training/strategic_mega_corpus/boreal_object_gold_full.npz", "gold"),
        ("data/training/strategic_mega_corpus/boreal_object_hard_full.npz", "hard")
    ]
    
    for path, name in targets:
        if not os.path.exists(path):
            print(f"[SKIP] {path} not found.")
            continue
            
        print(f"[SPLIT] Partitioning {name} Master Corpus...")
        data = np.load(path)
        feat, scor, weig = data['features'], data['scores'], data['weights']
        
        # Train: 0-1000 | Eval: 1000-1200 | Test: 1200-1400
        splits = {
            "train": (0, 1000),
            "eval": (1000, 1200),
            "test": (1200, 1400)
        }
        
        for s_name, (start, end) in splits.items():
            out_path = f"data/training/strategic_mega_corpus/boreal_object_{name}_{s_name}.npz"
            np.savez_compressed(
                out_path, 
                features=feat[start:end], 
                scores=scor[start:end], 
                weights=weig[start:end]
            )
            print(f"  -> Saved {s_name.upper()}: {out_path} ({end-start} samples)")

    print("====================================================")
    print("[COMPLETE] STRATEGIC TRINITY SECURED.")
    print("====================================================")

if __name__ == "__main__":
    # fuse_strategic_master()
    split_strategic_datasets()
