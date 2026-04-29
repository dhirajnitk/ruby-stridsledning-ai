import numpy as np
import os
import random

def generate_synthetic_data(num_samples=1000, output_path="data/training/strategic_mega_corpus/ppo_train_hard_24d_100k.npz"):
    print(f"Generating {num_samples} synthetic samples (No-Torch mode)...")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 25-D features
    features = np.random.randn(num_samples, 25).astype(np.float32)
    # 24-D weights (priorities)
    weights = np.random.dirichlet(np.ones(24), size=num_samples).astype(np.float32)
    # 1-D scores
    scores = np.random.rand(num_samples).astype(np.float32) * 500.0
    
    np.savez_compressed(output_path, features=features, weights=weights, scores=scores)
    print(f"Success: {output_path} generated.")

if __name__ == "__main__":
    generate_synthetic_data(num_samples=5000)
