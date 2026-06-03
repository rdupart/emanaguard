# Gate status — what to read after Colab (June 2026)

**Branch:** `cursor/phase-2-detector-c1b3`  
**Phase 3 / Azure:** still **not approved**

## Reading order

| Order | File | Purpose |
|-------|------|---------|
| 1 | **`docs/GATE_STATUS.md`** (this file) | Executive gate summary |
| 2 | **`PHASE_1_REPORT.md`** | Workload inference gates (single-draw, held-out-model, labeling) |
| 3 | **`PHASE_2_REPORT.md`** | Detector D2 (hard vs trivial suites) |
| 4 | **`docs/architecture_labeling_audit.md`** | Why `architecture_id` ≠ `model_class` |
| 5 | **`docs/PRELIMINARY_CAVEATS.md`** | What you cannot claim externally yet |
| 6 | **`report/phase1_results.json`** / **`phase2_results.json`** | Full numbers for reviewers |
| 7 | **`docs/COLAB.md`** | Re-run commands |
| 8 | **`docs/TRACES_WINDOWS_UPLOAD.md`** | Push `data/traces` from your PC |

## Colab corpus (from your uploaded JSON on `main`)

| Metric | Value |
|--------|--------|
| Physical base captures | **4576** |
| Distinct `architecture_id` in traces | **12** |
| Stochastic observation draws (40×) | 183040 |

## Phase 1 — headline (`host_observer_realistic_single_draw`)

| Axis | Accuracy | PASS (CI > chance) | Claim |
|------|----------|-------------------|--------|
| mode | 1.00 | YES | PRELIMINARY (trivial volume channel) |
| **architecture_id** | **0.008** | **NO** | Canonical axis but **does not infer** on single-draw |
| model_class | 0.86 | NO | **RETRACTED** (confounded) |
| batch_size | 0.95 | YES | PRELIMINARY |

## Held-out-model (single-draw, unseen architectures)

| Axis | Test accuracy | PASS |
|------|---------------|------|
| **architecture_id** | **0.0** | **NO** |
| model_class | 1.0 | NO (retracted) |

**Honest headline:** Host realistic observer **does not generalize** to unseen architectures under this protocol → **no external “model fingerprinting” claim**. This is a valid bounding/negative result.

## Phase 2 — detector (headline = hard suites only)

| Suite | ROC AUC | n_test | Headline? |
|-------|---------|--------|-----------|
| trivial_mode_change | 1.00 | 915 | **No** (not a result) |
| **hard_unauthorized_architecture** | **0.987** | 321 | **Yes** |
| **hard_covert_modulator** | **1.00** | 64 | **Yes** |

Hard-case detection is strong **when violations are defined at fixed train volume**; Phase 1 **inference** on unseen archs still fails. Do not conflate detector ROC with architecture fingerprinting.

## Traces on GitHub

- **`report/*.json`** — on `main` / branch (from your upload).
- **`data/traces/*.jsonl`** — **not** in GitHub yet unless you push from `C:\Users\rsocc\Downloads\traces` (see **`docs/TRACES_WINDOWS_UPLOAD.md`**).

## Next decision

| Gate | Status |
|------|--------|
| Methodology v1.3 | OK |
| ≥8 architectures in corpus | **PASS** (12) |
| Held-out-model fingerprint | **FAIL** (acc 0) |
| Architecture single-draw inference | **FAIL** (acc ≈ 0) |
| Hard detector | **PRELIMINARY PASS** (replicate after traces in repo) |
| Phase 3 mitigation | **Blocked** pending your call on negative inference vs detector scope |
