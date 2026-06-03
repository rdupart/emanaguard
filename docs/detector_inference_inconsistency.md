# Detector vs architecture inference inconsistency

## Observation

| Task | Metric | Typical result |
|------|--------|----------------|
| 12-way `architecture_id` inference (realistic single-draw) | Balanced accuracy | ~0.04 (fails majority + MI gate) |
| Held-out unseen architectures | Test accuracy | 0.0 |
| Binary `hard_unauthorized_architecture` detector | ROC AUC | ~0.99 |

## Volume matching audit

For the hard detector suite we only include **train** rows with:

- `batch_size = 4`, `seq_length = 128` (volume-matched profile)
- Benign = attested architecture; violation = any other architecture at the **same** profile

`detector_inference_audit.feature_distributions` in `phase2_results.json` reports mean
`n_events`, `total_bytes`, and `bytes_per_sec` for benign vs violation clouds. If
`volume_matched_on_coarse_features` is true, coarse volume is not the separator.

## Why binary detection can succeed when 12-way inference fails

1. **Task difficulty:** Inference must assign one of 12 architecture labels under observer noise; the detector only asks “attested vs not” at a fixed operating point.
2. **Class overlap:** Many architectures share similar transfer statistics at matched batch/seq; multiclass boundaries are weak (low MI).
3. **Not a contradiction:** A linear probe can separate two clouds (wrong arch vs attested) while failing to partition 12 classes.

## Leakage controls (v1.4)

- Train/test split by **config** (Phase 1) or **physical base_run_id** (Phase 2).
- Covert modulator: benign and modulated rows share the same `base_run_id` for splitting (`split_group_id` strips `:covert` suffix) so pairs do not leak across folds.

## Covert modulator subtlety

| Preset | Role |
|--------|------|
| `heavy` | Strong cadence quantization — AUC≈1 is **not** a strong security claim |
| `light` | Subtle perturbation |
| `adaptive` | Picks weakest preset that changes features while minimizing L2 distance to benign — estimates covert capacity **below** the detector threshold |

Headline covert metric: **`hard_covert_modulator_adaptive`**, not heavy alone.
