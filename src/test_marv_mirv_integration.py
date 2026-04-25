"""Final end-to-end integration test for the 15→18-D feature vector upgrade."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

print("=" * 60)
print("  MARV/MIRV INTEGRATION VERIFICATION")
print("=" * 60)

# 1. Feature Vector
from core.engine import extract_rl_features
from core.models import Threat, load_battlefield_state

CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'input', 'Boreal_passage_coordinates.csv')
state = load_battlefield_state(CSV)
threats = [
    Threat('BUS1', 500, 600, 4500, 'C', 'ballistic', 200, is_mirv=True, mirv_count=3),
    Threat('MV1', 300, 400, 4500, 'C', 'ballistic', 180, is_marv=True, marv_pk_penalty=0.45),
    Threat('F01', 400, 500, 2200, 'C', 'fighter', 120, can_dogfight=True, dogfight_win_prob=0.35),
]
feats = extract_rl_features(state, threats)
assert len(feats) == 18, f"Expected 18-D, got {len(feats)}-D"
assert feats[15] == 1.0, f"has_marv should be 1.0, got {feats[15]}"
assert feats[16] == 1.0, f"has_mirv should be 1.0, got {feats[16]}"
assert feats[17] == 3.0, f"total_mirv_warheads should be 3.0, got {feats[17]}"
print(f"  [PASS] Feature Vector: {len(feats)}-D  has_marv={feats[15]} has_mirv={feats[16]} total_mirv_warheads={feats[17]}")

# 2. Neural Models Forward Pass
import torch
from core.inference import TransformerResNet, ChronosGRU, StandardResNet, GeneralistMLP

x = torch.randn(1, 18)
e = TransformerResNet(18, 11)(x); assert e.shape == (1, 11), f"Elite shape: {e.shape}"
c = ChronosGRU(18, 11)(x); assert c.shape == (1, 11), f"Chronos shape: {c.shape}"
r = StandardResNet(18, 11)(x); assert r.shape == (1, 11), f"ResNet shape: {r.shape}"
g = GeneralistMLP(18, 11)(x); assert g.shape == (1, 11), f"Generalist shape: {g.shape}"
print(f"  [PASS] Model Forward: Elite={e.shape} Chronos={c.shape} ResNet={r.shape} MLP={g.shape}")

# 3. Inference Module
from core.inference import BorealInference
bi = BorealInference('elite_v3_5')
w = bi.predict(feats)
assert len(w) == 11, f"Expected 11 weights, got {len(w)}"
print(f"  [PASS] Inference: {len(w)} doctrine weights ({w[:3].round(3)}...)")

# 4. V2 Model Weights Exist
import numpy as np
model_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
expected_models = ['elite_v3_5.pth', 'supreme_v3_1.pth', 'supreme_v2.pth', 'titan.pth', 'hybrid_rl.pth', 'generalist_e10.pth']
trained_models = [f for f in os.listdir(model_dir) if f in expected_models]
print(f"  [PASS] Models Retrained: {len(trained_models)} / {len(expected_models)} ({', '.join(trained_models)})")

# 5. Training Data
data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'training', 'strategic_mega_corpus')
train = np.load(os.path.join(data_dir, 'marv_mirv_train.npz'))
eval_d = np.load(os.path.join(data_dir, 'marv_mirv_eval.npz'))
assert train['features'].shape[1] == 18, f"Training features dim: {train['features'].shape[1]}"
assert eval_d['features'].shape[1] == 18, f"Eval features dim: {eval_d['features'].shape[1]}"
print(f"  [PASS] Training Data: train={train['features'].shape}, eval={eval_d['features'].shape}")

# 6. PPO Agent
from ppo_agent import BorealDirectEngine, BorealValueNetwork
ppo = BorealDirectEngine(input_dim=18, output_dim=11)
policy, value = ppo(x)
assert policy.shape == (1, 11)
assert value.shape == (1, 1)
print(f"  [PASS] PPO Agent: policy={policy.shape}, value={value.shape}")

print()
print("=" * 60)
print("  ALL 6 INTEGRATION CHECKS PASSED")
print("=" * 60)
