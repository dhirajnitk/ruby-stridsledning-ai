# Boreal Command Suite: Multi-Effector Neural Retraining Walkthrough

As we move from a single "SAM" inventory to a layered defense (Patriot, IRIS-T, Laser, etc.), our neural models must be retrained to understand **Economic Triage**.

## 1. The Action Space Expansion
Previously, the AI's action was a simple `Discrete(N_Bases)`. Now, the action space is `Discrete(N_Bases * N_Effectors)`.
*   **Total Actions**: 21 Bases * 5 Effectors = 105 possible assignment combinations per threat.

## 2. Cost-Aware Reward Function
To prevent the AI from wasting a **$5M THAAD** on a **$50k Loitering Munition**, we implement a tiered reward penalty:

| Outcome | Reward | Note |
| :--- | :--- | :--- |
| **Successful Intercept** | `+100` | Target Neutralized |
| **Defense Breach (HVA)** | `-500` | Critical Impact |
| **Effector Cost (C)** | `-C/100,000` | Penalty per $100k spent |
| **Inventory Depletion** | `-20` | Penalty for empty bins |

## 3. Training Scenario Proportions
The `mega_data_factory.py` now generates datasets with the following proportions to ensure a balanced learning rate:
*   **40% Low-Tier (Loiter/Cruise)**: AI learns to prioritize C-RAM and IRIS-T.
*   **40% High-Tier (Ballistic)**: AI learns to prioritize Patriot/THAAD.
*   **20% Hypersonic**: AI learns that only specific "Direct Action" models can succeed.

## 4. How it Works (Proportional Scaling)
- **Patriot/THAAD**: Allocated at 5-10% of total inventory.
- **IRIS-T/NASAMS**: Allocated at 30-40% of total inventory.
- **C-RAM/MANPADS**: Allocated at 50-60% of total inventory.

**Status: SYSTEM READY FOR RE-TRAINING**
