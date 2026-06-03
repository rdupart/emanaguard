# architecture_id vs model_class — labeling audit

## Why they disagreed (0.946 vs 0.500 on the 96-capture corpus)

| Label | What it actually was | Classes in data |
|-------|----------------------|-----------------|
| **`architecture_id`** | Intended fingerprint: `hidden × layers` template (e.g. `arch_mlp_256x4`) | **2** values after legacy import: `arch_legacy_small`, `arch_legacy_large` |
| **`model_class`** | Coarse bucket (`small` / `large`) **derived from similar hidden sizes** | **2** values, **aligned with train vs infer volume** |

On this corpus, **`model_class` ≈ proxy for mode/volume** (train runs use larger batches → more bytes → labeled `large` or `small` inconsistently). **`architecture_id`** on a **config-group holdout** can still separate the two legacy templates because configs bundle mode + arch.

That is **not** independent evidence of two label axes. It is **one volume/mode channel** seen through two labelings.

## Resolution (gate policy)

| Label | Status in reports |
|-------|-------------------|
| **`architecture_id`** | **Canonical** fingerprint axis — but **RETRACTED** as a positive result unless **≥8 distinct `architecture_id` values** appear in **physical base captures** |
| **`model_class`** | **Retracted** from headline / external claims — legacy coarse bucket, confounded |

Do **not** claim “architecture inference” or “model fingerprinting” until held-out-model passes on **≥8 architectures** with **single-draw realistic** observer.
