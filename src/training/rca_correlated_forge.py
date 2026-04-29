import numpy as np
import os
import torch

def generate_correlated_data(num_samples=1000, output_path="data/training/strategic_mega_corpus/correlated_signal.npz"):
    print(f"Generating {num_samples} SIGNAL-LOCKED samples...")
    
    # 25-D Features
    # index 0: distance, index 1: speed, index 2: altitude
    features = np.random.rand(num_samples, 25).astype(np.float32)
    
    # 24-D Weights
    weights = np.zeros((num_samples, 24)).astype(np.float32)
    
    for i in range(num_samples):
        dist = features[i, 0] * 300.0 # 0-300km
        speed = features[i, 1] * 5000.0 # 0-5000kmh
        
        # LOGIC:
        # If very far and fast -> SM-6 (index 14) or THAAD (index 6)
        if dist > 200 and speed > 3000:
            best_idx = 14 # sm-6
        # If medium range and fast -> Patriot (index 4)
        elif dist > 100 and speed > 2000:
            best_idx = 4 # patriot-pac3
        # If short range -> Skynex (index 19) or Nimbrix (index 20)
        elif dist < 10:
            best_idx = 19 # skynex
        else:
            best_idx = 0 # meteor (default)
            
        weights[i, best_idx] = 1.0
        
    scores = np.random.rand(num_samples).astype(np.float32)
    
    np.savez_compressed(output_path, features=features, weights=weights, scores=scores)
    print("Signal-Locked Data Generated.")

if __name__ == "__main__":
    generate_correlated_data()
