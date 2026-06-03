# Gate status — what to read (June 2026)

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
| 6 | **`report/phase1_results.json`** / **`phase2_results.json`** | Full numbers (re-run from traces in repo) |
| 7 | **`docs/COLAB.md`** | Re-run commands |

## Corpus (verified in-repo)

| Metric | Value |
|--------|--------|
| **`data/traces/*.jsonl`** | **4576** files on branch (pushed from PC) |
| Physical base captures (evaluate) | **4576** |
| Distinct `architecture_id` | **12** |
| Stochastic observation draws (40×) | 183040 |

**JSON on `main`:** Your Colab upload was **not outdated** for the key gates (same physical count, held-out **0.0**, same qualitative verdict). This branch now has JSON **re-generated from the committed traces** (small numeric drift on `architecture_id` single-draw: ~0.008 Colab vs ~0.040 in-repo re-run — still **FAIL**).

## Phase 1 — headline (`host_observer_realistic_single_draw`)

| Axis | Accuracy | PASS | Claim |
|------|----------|------|--------|
| mode | ~1.00 | YES | PRELIMINARY (volume/mode channel) |
| **architecture_id** | **~0.04** | **NO** | Does **not** support fingerprinting |
| model_class | ~0.84 | NO | **RETRACTED** |
| batch_size | ~0.95 | YES | PRELIMINARY |

## Held-out-model (unseen architectures)

| Axis | Test accuracy | PASS |
|------|---------------|------|
| **architecture_id** | **0.0** | **NO** |
| model_class | 1.0 | NO (retracted) |

**Honest headline:** No external **“model fingerprinting”** claim. Bounding / negative result is valid and valuable.

## Phase 2 — detector (headline = hard suites only)

| Suite | ROC AUC | n_test | Headline? |
|-------|---------|--------|-----------|
| trivial_mode_change | ~1.00 | ~915 | **No** |
| **hard_unauthorized_architecture** | **~0.99** | ~321 | **Yes** |
| **hard_covert_modulator** | **~1.00** | ~64 | **Yes** |

Do **not** equate hard-detector ROC with architecture inference success.

## Gate checklist

| Gate | Status |
|------|--------|
| Methodology v1.3 | OK |
| Traces in GitHub | **PASS** (4576 jsonl) |
| ≥8 architectures | **PASS** (12) |
| Held-out-model fingerprint | **FAIL** |
| Architecture single-draw inference | **FAIL** |
| Hard detector (volume-matched violations) | **PRELIMINARY PASS** |
| Phase 3 mitigation | **Blocked** |
