"""Quick integration test for multi-doctrine engine."""
import sys
sys.path.insert(0, 'ruby-stridsledning-ai/src')
from engine import evaluate_threats_advanced
from models import Threat, Base, GameState

# Mini scenario: 3 threats heading to Capital
state = GameState(bases=[
    Base('Capital Arktholm', 418.3, 95.0, {'SAM': 4}),
    Base('Northern Vanguard Base', 198.3, 335.0, {'Fighter': 4, 'Drone': 10, 'SAM': 0}),
    Base('Highridge Command', 838.3, 75.0, {'Fighter': 4, 'Drone': 10, 'SAM': 0}),
], blind_spots=[(656.7, 493.3)])

threats = [
    Threat('T-1', 600.0, 400.0, 2500.0, 'Capital X', 'fast-mover', 100.0),
    Threat('T-2', 500.0, 500.0, 1000.0, 'Capital X', 'bomber', 90.0),
    Threat('T-3', 700.0, 300.0, 1800.0, 'Capital X', 'decoy', 15.0),
]

print("=" * 70)
print("  DOCTRINE ENGINE INTEGRATION TEST")
print("=" * 70)

# Test pure profiles
for doctrine in ['balanced', 'aggressive', 'fortress', 'economy', 'ambush']:
    result = evaluate_threats_advanced(state, threats, mcts_iterations=10, max_time_sec=1.0, doctrine_primary=doctrine)
    d = result['active_doctrine']
    assigns = len(result['tactical_assignments'])
    score = result['strategic_consequence_score']
    ignored = result['triage_ignored_threats']
    blend = d['blend_ratio']
    print(f"  {doctrine.upper():<12} | Assignments: {assigns} | Ignored: {ignored} | Score: {score:>7.1f} | Blend: {blend}")

print("-" * 70)

# Test blended profiles
blends = [
    ("fortress", "economy", 0.7),
    ("aggressive", "economy", 0.7),
]
for primary, secondary, blend_ratio in blends:
    result = evaluate_threats_advanced(state, threats, mcts_iterations=10, max_time_sec=1.0,
                                       doctrine_primary=primary, doctrine_secondary=secondary, doctrine_blend=blend_ratio)
    d = result['active_doctrine']
    assigns = len(result['tactical_assignments'])
    score = result['strategic_consequence_score']
    label = f"{primary}+{secondary}"
    print(f"  {label.upper():<12} | Assignments: {assigns} | Ignored: {result['triage_ignored_threats']} | Score: {score:>7.1f} | Blend: {d['blend_ratio']}")

print("=" * 70)

# Verify active_doctrine metadata is present
result = evaluate_threats_advanced(state, threats, mcts_iterations=5, max_time_sec=1.0,
                                   doctrine_primary='fortress', doctrine_secondary='economy', doctrine_blend=0.7)
ad = result['active_doctrine']
print(f"\n  Active Doctrine Metadata:")
print(f"    Primary:  {ad['primary']}")
print(f"    Secondary: {ad['secondary']}")
print(f"    Blend:    {ad['blend_ratio']}")
print(f"    Flags:    {sum(1 for v in ad['active_flags'].values() if v)}/{len(ad['active_flags'])} enabled")
print(f"    Weights:  capital_reserve={ad['blended_weights']['capital_reserve']}, economy_force={ad['blended_weights']['economy_force']}")
print("\n  [OK] All tests passed!")
