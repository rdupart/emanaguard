# Observer Feasibility — Host-Side Measurement under the GPU-CC Threat Model

**Assessment date:** 2026-06-03  
**Purpose:** Define what a **host-side observer** can measure, how we obtain signals for **Phases 1–3** without deep kernel instrumentation, and what **requires Azure H100 CC** validation (Phase 4).

---

## 1. Threat model (observer legality)

From NVIDIA GPU-CC and arXiv:2507.02770:

| Actor | Capability |
|-------|------------|
| **Malicious host** | Controls hypervisor/OS; can read **unprotected staging memory** metadata patterns; observe **PCIe traffic timing**; interpose on **encrypted RPC** queues; configure GPU via in-band/OOB within product rules |
| **Not granted** | Decrypt CPR contents; read plaintext weights from GPU memory; use **GPU performance counters in CC-On** (disabled per NVIDIA blog/whitepaper) |
| **In scope for us** | **Ciphertext** on wire/buffer + **metadata**: per-transfer **timestamp**, **size**, **direction** (H→D / D→H), **aggregate volume**, **RPC/command cadence**, inter-transfer **gaps** |

**SL5 framing:** Host operator or compromised cloud control plane is in scope for **operational metadata** leakage that could inform weight-exfil **planning** (correlate training bursts, checkpoint sizes) even if bytes remain encrypted.

**Sources:** https://arxiv.org/abs/2507.02770 ; https://developer.nvidia.com/blog/confidential-computing-on-h100-gpus-for-secure-and-trustworthy-ai/ ; https://images.nvidia.com/aem-dam/en-zz/Solutions/data-center/HCC-Whitepaper-v1.0.pdf

---

## 2. Observer feature vector (target schema)

All features must be derivable without decrypting staging buffer **payloads**.

| Feature family | Examples | Host-visible under CC? |
|----------------|----------|-------------------------|
| **Transfer events** | `(t, size_bytes, direction, duration_ms)` per CPU–GSP or memcpy-equivalent episode | **Yes** (2507.02770 methodology); exact hook TBD |
| **Volume** | Bytes/sec in sliding windows; burst count | **Yes** |
| **Cadence** | Inter-arrival time distribution; RPC rate | **Yes** (RPC channel in untrusted memory per 2507.02770) |
| **Sequence** | Order of size buckets (8B…4KiB histogram over windows) | **Yes** (inference target for D1) |
| **Contention proxy** | Probe latency while victim runs (Invisible Probe style) | **Yes** on shared PCIe tree—optional Tier-Red channel |
| **GPU PMU / NVML internals** | SM util, perf counters | **CC-On: No** (counters disabled); **CC-DevTools: Yes** (not production posture) |

**Phase 1 rule:** Collect **rich traces** on **local-gpu** for ground truth; **project** to observer features via documented **reduction map** (drop PMU-only fields).

---

## 3. How we obtain signals (three backends)

### 3.1 `simulate` (laptop, no GPU) — **Phase 1 default**

| Item | Approach |
|------|----------|
| **Input** | Recorded trace files **or** generative model of transfer events parameterized by workload class |
| **Output** | Same feature schema + labels as other backends |
| **Use** | End-to-end pipeline, classifier training, detector logic, mitigation replay |
| **Limitation** | External validity depends on calibration from **local-gpu** captures |

### 3.2 `local-gpu` (non-CC GPU, Colab/RunPod) — **Phase 1–3 development**

| Source | Maps to host-visible? | Privilege |
|--------|----------------------|-----------|
| **CUDA events** around `cudaMemcpy` / async copies | **Partial** — measures end-to-end copy latency from user process; approximates transfer **timing** and **size** | User space in victim process |
| **Nsight Systems / CUPTI** (optional) | **Superset** — used to build reduction map; **not** all fields allowed in observer features | User/admin on dev machine |
| **NVML PCIe throughput** (`nvmlDeviceGetPcieThroughput`) | **Partial** — 20 ms granularity (Veiled Pathways); coarse volume | User with NVML access |
| **Synthetic probe** (`cudaMemcpy` loop) | **Contention timing** — optional adversary simulation | Tier-Red experiments |

**Minimum without kernel modules:**  
1. **Instrumented victim runner** (Python) that logs every H↔D copy: `timestamp`, `num_bytes`, `direction`, `stream`, `op_name` (e.g., `load_weights`, `forward`, `backward`).  
2. **Derive observer features** in post-processing (histograms, rates, sequences)—**no** `/proc` driver hacking required for MVP.

**Honest gap:** True **CPU–GSP RPC** timestamps may differ slightly from user-level memcpy events; **Azure CC** validates top features still rank-correlate.

### 3.3 `azure-cc` (short validation only) — **Phase 4**

| Goal | Method |
|------|--------|
| Confirm signals exist **CC-On** | Same victim scripts inside **CVM**; observer on **host** or approved side channel per lab policy |
| Compare D1/D2 metrics | Same classifiers/features; report **delta** vs local-gpu |
| **Constraints** | Deallocate VM immediately; no proprietary weights; open/stand-in models only |

**Likely needs Azure (cannot fully simulate):**

- Attestation-gated **ReadyState** / CC mode interactions affecting transfer patterns  
- Driver path differences inside CVM vs bare-metal dev GPU  
- Confirmation that **CC-On** disables counters but **staging timing** remains (2507.02770 implies yes)

**Does not need Azure for MVP:**

- Classifier architecture, train/test protocol, mitigation **replay on traces**, overlay text, simulate backend

---

## 4. What we will NOT do (scope fence)

| Out of scope | Reason |
|--------------|--------|
| Custom **kernel module** / eBPF on production NVIDIA driver | Budget; reproducibility |
| **Decrypting** staging buffers | Not threat-model legitimate |
| **MIG + CC** multi-tenant on one GPU | Not supported on H100 CC (`cc_tenancy.md`) |
| Publishing **Tier-Red** covert modulator source | Private; methodology only |

---

## 5. Measurement vantage diagram (logical)

```text
┌─────────────────────────────────────────────────────────────┐
│  Untrusted host (observer)                                   │
│  Sees: staging buffer ciphertext, timing, sizes, RPC cadence │
│        [optional: PCIe contention probe]                     │
└───────────────────────────┬─────────────────────────────────┘
                            │ encrypted CPU↔GSP DMA + RPC
┌───────────────────────────▼─────────────────────────────────┐
│  CVM (victim workload — stand-in models only)                  │
│  Thinks: weights/activations confidential inside CVM+GPU TCB  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  H100 GPU (CC-On) — CPR plaintext inside trust boundary      │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Feasibility verdict

| Phase | Backend | Feasible? |
|-------|---------|-----------|
| 0.5 | Docs only | **Done** |
| 1 | `simulate` + `local-gpu` | **Yes** |
| 2 | Same features + Tier-Red modulator (private) | **Yes** on simulate/local |
| 3 | Trace shim mitigations | **Yes** on simulate |
| 4 | `azure-cc` validation | **Yes**, short window; **after** human approval of Phases 1–3 |

**Risk:** If observer projection from `local-gpu` traces **fails** rank correlation with published 2507.02770 patterns, prioritize **contention + volume** features only before Azure spend.

---

*No pipeline code in Phase 0.5.*
