# Boreal Chessmaster: Final MARV/MIRV Architecture Audit

## 1. Feature Variable Consistency
**Issue:** While the backend engine was transitioned to 18-D, there was a discrepancy in the requested advanced threat features. The initial iteration used `marv_count`, `mirv_warheads`, and `dogfight_count`, but the requested spec required `has_marv`, `has_mirv`, and `total_mirv_warheads`.
**Fix:**
*   Updated `extract_rl_features()` in `src/core/engine.py` to correctly map `has_marv` (binary 1.0/0.0), `has_mirv` (binary 1.0/0.0), and `total_mirv_warheads` (float sum).
*   Aligned the dataset generator (`rl_data_collector.py` / `generate_marv_mirv_data.py`) to harvest these exact features.
*   Updated `docs/MARV_MIRV_TECHNICAL_DEEPDIVE.md` to reflect the correct feature list and indices.

## 2. Neural Architecture Synchronization
**Issue:** The training pipeline (`neural_trainer.py`) and the inference pipeline (`inference.py`) were using mismatched architectures for the same models. For example, the trainer was training an `EliteTransformer` class, while inference was trying to load it into a `TransformerResNet` class, leading to `state_dict` loading errors and the models falling back to random initializations.
**Fix:**
*   Refactored `src/neural_trainer.py` to completely eliminate duplicate class definitions.
*   The trainer now directly imports the exact production architectures from `src/core/inference.py` (e.g., `TransformerResNet`, `ChronosGRU`, `StandardResNet`, `GeneralistMLP`) and `ppo_titan_transformer.py` (`BorealTitanEngine`).
*   This ensures 1:1 structural parity between training and deployment.

## 3. Training Loop Target Padding Bug
**Issue:** The legacy training loop forcefully padded target arrays to 231 dimensions (assuming a global tactical array of 21 bases × 11 effectors). Since the production 18-D models now output exactly 11 doctrine weights, this caused a dimensional mismatch exception during the backward pass (`[32, 11]` vs `[32, 231]`).
**Fix:**
*   Removed the destructive `Y.repeat` padding logic.
*   Updated the criterion from `BCEWithLogitsLoss` to `MSELoss`, as the imported production models inherently apply a terminal sigmoid layer to clamp outputs to `[0, 1]`.
*   Added logic to correctly handle tuple returns from PPO models (extracting the policy tensor while ignoring the value tensor during supervised behavioral cloning).

## 4. Obsolete Model Cleanup
**Issue:** During the previous integration phase, models were saved as `boreal_*_v2.pth` which bypassed the standard naming scheme expected by `inference.py` (which looked for `elite_v3_5.pth`, `supreme_v3_1.pth`, etc.).
**Fix:**
*   Deleted the obsolete `_v2` model weights from the `models/` directory.
*   The `neural_trainer.py` now targets the direct production filenames, overwriting them properly.
*   The `models/` directory now strictly contains the canonical 18-D weights ready for deployment:
    *   `elite_v3_5.pth`
    *   `supreme_v3_1.pth`
    *   `supreme_v2.pth`
    *   `titan.pth`
    *   `hybrid_rl.pth`
    *   `generalist_e10.pth`

## Status
All architectural discrepancies have been eradicated, the models are stored in the correct directory under their expected names, and the end-to-end integration is robust.
