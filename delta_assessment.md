# Delta Assessment — D1–D4 vs. Prior Work (especially arXiv:2507.02770)

**Project:** Host-observable I/O metadata leakage and policy-violation detection at the NVIDIA H100 Confidential Computing boundary — SL5-oriented evaluation.  
**Assessment date:** 2026-06-03  
**Posture:** Defensive research; extend, do not overclaim.

---

## Anchor prior work

**Primary:** *Blueprint, Bootstrap, and Bridge: A Security Look at NVIDIA GPU Confidential Computing* (arXiv:2507.02770, 2025).  
**Link:** https://arxiv.org/abs/2507.02770  

**What they already established (we accept, do not rediscover):**

- Reverse-engineered GPU-CC on H100-class hardware with AMD SEV-SNP CVMs.
- CPU–GSP memory moves use **staging buffers** in **unprotected** host memory; payloads encrypted; **host can observe timing and transfer sizes** on the RPC/DMA path.
- **Bimodal timing:** small transfers (8–256 B) dominated by RPC overhead; **large (e.g., 4 KiB) transfers show size-dependent latency**—a **timing side channel** on **activity/size**.
- **Recommendations (not evaluated):** constant-time RPC handling; statistical noise on CPU–GSP transfers.
- Responsible disclosure to **NVIDIA PSIRT** (stated on arXiv).

**Threat model alignment:** Malicious **host** (hypervisor, operator) with PCIe/staging visibility; **not** ciphertext recovery.

---

## D1 — Workload inference from host-visible I/O metadata

| Question | Answer |
|----------|--------|
| **What 2507.02770 does** | Demonstrates **size-dependent timing** and transfer counts on CPU–GSP path; argues leakage of **transfer size / activity level**. |
| **What they do not do** | Train classifiers for **AI workload semantics**: model/architecture family, batch size, sequence length, **training vs inference**, **prefill vs decode**, token cadence. |
| **What pre-CC work does** | *Invisible Probe* (S&P 2021): ML **model** among victims via **PCIe congestion**—coarse, not CC, not LLM phases. *LockedDown* (EuroS&P 2022): website fingerprint via contention. |
| **Our genuine delta** | **Supervised workload inference** from a **feature vector restricted to host-legitimate signals** (per `observer_feasibility.md`), evaluated on a **labeled corpus** with train/test hygiene—under **CC threat model**, developed on non-CC GPU + **simulate**, validated briefly on Azure CC. |
| **Verdict** | **Appears open** if framed as *“from size/activity to workload semantics”*—not *“discovery of timing channel.”* |
| **Scoop risk** | **Medium:** reviewers may say 2507.02770 already proves leakage of activity; we must show **incremental information** (MI, accuracy above chance on fine labels). |
| **If weak** | Narrow labels to **{train vs infer}** and **{small vs large model class}** first; add **prefill vs decode** only if signal supports it. |

---

## D2 — Policy-deviation / covert-modulation detector (defender)

| Question | Answer |
|----------|--------|
| **What 2507.02770 does** | Attack-minded analysis; **no** defender trained on attested baseline vs violation. |
| **Adjacent work** | Cryptojacking detectors (PMU, magnetic); ShadowScope (kernel PMU/side-channel golden traces); runtime CVM attestation (event log, not GPU I/O cadence). |
| **Our genuine delta** | **Same telemetry as D1**, but **defender role:** model **benign attested workload class**; alert on **different workload** or **scripted covert modulator** (Tier-Red, private); metrics: ROC/AUC, FP per node per day, detection latency. |
| **Verdict** | **Appears open** for *attested-policy deviation on CC host-visible I/O metadata*—distinct from cryptojacking (mining) and from kernel integrity checking. |
| **Scoop risk** | **Low–medium** if we clearly separate **policy** (expected ML job profile) from generic anomaly. |
| **If weak** | Frame as **SI-4 / AU-6 style monitoring primitive** with published **false-positive budget** rather than “ML security product.” |

---

## D3 — Mitigation evaluation (constant-time RPC / noise)

| Question | Answer |
|----------|--------|
| **What 2507.02770 does** | **Recommends** constant-time RPC and noise; **does not report** accuracy/overhead tradeoffs. |
| **Our genuine delta** | **Implement or replay** mitigations (shim or trace transformation); measure **D1 classifier accuracy drop** (leakage reduction) vs **runtime overhead**; document in `mitigation_table.md`. |
| **Verdict** | **Appears open** as **measurement contribution**—low novelty, high value for defenders. |
| **Scoop risk** | **Low** if we cite their recommendation explicitly. |
| **If weak** | Limit to **trace-level noise** simulation if driver shim infeasible on laptop; label as **lower external validity** until CC validation. |

---

## D4 — SL5-focused NIST SP 800-53 overlay diff

| Question | Answer |
|----------|--------|
| **What exists** | **SL5 Standard for AI Security** v0.1 — NIST SP 800-53 overlay (43 controls) — https://standard.sl5.org/ |
| **Our genuine delta** | **Supplemental “diff”** controls for **CC I/O-boundary observability** (SC-7 / SI-4 style): monitoring host-visible staging metadata, attested workload profiles, response to deviation—**citing SL5 v0.1 as parent**, not replacing it. |
| **“AI705-style”** | **UNVERIFIED** as a published NIST doc named AI705. Likely **ICD 705**-inspired physical controls in SL5 stream—not this repo’s D4 unless stakeholder defines otherwise. |
| **Verdict** | **Partially scooped** by SL5 v0.1 existence; **open** only for **narrow GPU-CC I/O diff**. |
| **If weak** | Publish as **`docs/cc_io_overlay.md`** appendix to SL5 mapping table, not standalone “new standard.” |

---

## Overall recommendation

| Option | Recommendation |
|--------|----------------|
| **Proceed?** | **Yes**, with **explicit 2507.02770 delta language** in every artifact. |
| **Scope changes** | (1) Never claim “first timing channel under CC.” (2) Pair D1+D2 on **one feature schema**. (3) D3 required for defensive story. (4) D4 = diff only. |
| **Pivot if Phase 1 MI is near zero** | Collapse to **D2-only** operational detector + **D3** mitigations; publish negative result on fine-grained D1. |

**Confidence:** **Medium-high** on 2507.02770 overlap; **medium** on whether fine-grained D1 labels are feasible without privileged telemetry.

**Main uncertainty:** Whether host-visible features on **real** CC-On H100 (Azure) retain enough signal after CC-On counter restrictions and driver differences vs non-CC dev traces.

---

*Read-only assessment. No pipeline code in Phase 0.5.*
