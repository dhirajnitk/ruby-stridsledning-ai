import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os

def plot_3d_samples():
    print("====================================================")
    print("   BOREAL 3D VISUALIZER: KINETIC TRACK RENDERING    ")
    print("====================================================")
    
    path = "data/training/strategic_mega_corpus/boreal_object_hard_train.npz"
    if not os.path.exists(path):
        print(f"[ERROR] Dataset {path} not found. Generate it first.")
        return
        
    data = np.load(path)
    features = data['features'] # (Samples, Threats, Time, Features)
    
    # Pick 3 interesting samples from the first batch
    sample_indices = [0, 5, 10]
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    colors = ['red', 'blue', 'green']
    labels = ['Hypersonic PGM', 'Stealth Aircraft', 'Drone Swarm']
    
    for idx, (s_idx, color, label) in enumerate(zip(sample_indices, colors, labels)):
        # Extract X, Y, Z for the first threat in each sample
        # Features: [X, Y, Z, Vx, Vy, Vz, Val, RCS]
        track = features[s_idx, 0, :, 0:3] 
        
        ax.plot(track[:, 0], track[:, 1], track[:, 2], color=color, label=label, linewidth=2)
        ax.scatter(track[0, 0], track[0, 1], track[0, 2], color=color, marker='o', s=50) # Start
        ax.scatter(0, 0, 0, color='black', marker='^', s=100) # Radar Origin
        
    ax.set_xlabel('Downrange X (m)')
    ax.set_ylabel('Altitude Y (m)')
    ax.set_zlabel('Crossrange Z (m)')
    ax.set_title('Boreal AI: 3D Object-Level Kinetic Tracks (Physics-Grounded)')
    ax.legend()
    ax.grid(True)
    
    output_img = "docs/3d_track_visualization.png"
    plt.savefig(output_img)
    print(f"[COMPLETE] Visualization saved to: {output_img}")
    plt.show()

if __name__ == "__main__":
    plot_3d_samples()
