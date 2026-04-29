import numpy as np
data = np.load('data/training/strategic_mega_corpus/high_prec_signal_1k.npz')
scores = data['scores']
print(f"Min: {scores.min()}, Max: {scores.max()}, Mean: {scores.mean()}, Std: {scores.std()}")
