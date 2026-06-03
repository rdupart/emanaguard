# CC Tenancy on NVIDIA H100 (and notes on Blackwell) — Configuration vs. Experiments

**Assessment date:** 2026-06-03  
**Question:** In **current shipping** NVIDIA H100 Confidential Computing, is the GPU **single-VM passthrough (single tenant)** or can **MIG** provide **multi-tenant CC** simultaneously?

**Short answer:** **Single-tenant passthrough per confidential workload** is the supported model. **MIG cannot be used together with Confidential Computing on Hopper H100** in current NVIDIA documentation and forum guidance. A physical host may run **multiple CVMs each with their own passthrough GPU** (one GPU per CVM in typical single-GPU passthrough mode), but that is **multi-tenant at the node level**, not MIG-partitioned CC on one GPU.

---

## 1. Official and primary sources

| Source | What it states | Link |
|--------|----------------|------|
| *NVIDIA Secure AI* operations guide (unsupported features) | Lists **Multi-Instance GPU (MIG)** under features **not** supported for NVIDIA Secure AI / CC | https://docs.nvidia.com/nvidia-secure-ai-operations-guide.pdf |
| NVIDIA Developer Forums (employee response, Feb 2025) | **“MIG + CC is not currently supported”** on Hopper | https://forums.developer.nvidia.com/t/mig-confidential-computing/360895 |
| *Confidential Compute on NVIDIA Hopper H100* whitepaper | Describes **CVM + passthrough GPU** TEE extension; does not describe MIG+CC | https://images.nvidia.com/aem-dam/en-zz/Solutions/data-center/HCC-Whitepaper-v1.0.pdf |
| *Creating the First Confidential GPUs* (CACM 2024) | GPU assigned into CVM trust boundary via passthrough-style model | https://doi.org/10.1145/3626827 |
| NVIDIA Confidential Containers — supported platforms | **Single-GPU passthrough** for H100/H200; **Multi-GPU passthrough** via Protected PCIe (PPCIe) on Hopper HGX; **all GPUs on host must be CC-configured and assigned to one confidential VM** for multi-GPU case | https://docs.nvidia.com/datacenter/cloud-native/confidential-containers/latest/supported-platforms.html |
| Trusted Computing Solutions release notes (590 series) | **SPT CC:** one GPU per CVM; multiple CVMs per node each with one GPU; **PPCIe:** multiple Hopper GPUs + NVSwitch to **one** CVM; notes **GPU–GPU traffic over NVLink/NVSwitch not encrypted** in PPCIe mode | https://docs.nvidia.com/590trd1-trusted-computing-solutions-release-notes.pdf |
| *NVIDIA Secure AI with Blackwell and Hopper GPUs* whitepaper | Hopper + Blackwell CC modes: single- and multi-GPU **passthrough** (not MIG+CC) | https://docs.nvidia.com/nvidia-secure-ai-with-blackwell-and-hopper-gpus-whitepaper.pdf |

### Hopper architecture marketing vs. shipping CC

The *NVIDIA H100 Tensor Core GPU Architecture* (GTC 2022) whitepaper discusses **MIG-level TEE** as a Hopper capability in a **general architecture** sense:

- https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/h100/pdf/NVIDIA-H100-TC-Architecture-Whitepaper-V2.pdf (**UNVERIFIED in this session** — link pattern from NVIDIA; use official NVIDIA H100 architecture PDF on developer site if this redirect fails)

**Important distinction:** Architectural mention of “MIG-level TEE” **does not** contradict shipping guidance that **MIG + CC are not simultaneously supported** today. Tenancy conclusions below follow **deployment/Secure AI** documents, not architecture slides alone.

---

## 2. Tenancy model (H100 CC, shipping)

### 2.1 Single-GPU passthrough (SPT CC)

- **One whole GPU** is passed through to **one** confidential VM (CVM) / confidential container pod.
- Documented explicitly in release notes: multiple CVMs may exist on a node, **each with one GPU** — still **one tenant per GPU**.
- Source: https://docs.nvidia.com/590trd1-trusted-computing-solutions-release-notes.pdf

### 2.2 Multi-GPU passthrough (Hopper PPCIe)

- **Multiple physical GPUs** (and NVSwitch resources on HGX) passed to **a single** CVM.
- **Not** multi-tenant sharing of one GPU via MIG.
- **NVLink/NVSwitch GPU–GPU traffic is not encrypted** in PPCIe mode (per NVIDIA release notes) — relevant to threat model for cross-GPU leakage experiments.
- Source: same release notes; https://docs.nvidia.com/datacenter/cloud-native/confidential-containers/latest/supported-platforms.html

### 2.3 MIG + CC

- **Not supported** (NVIDIA Secure AI guide; forum confirmation).
- Enabling MIG while CC is on reports unsupported behavior; employee guidance: not a supported combination.
- Sources: https://docs.nvidia.com/nvidia-secure-ai-operations-guide.pdf ; https://forums.developer.nvidia.com/t/mig-confidential-computing/360895

### 2.4 “Multi-tenant CC” interpretation

| Interpretation | Supported on H100 CC? |
|----------------|------------------------|
| Several tenants **sharing one GPU via MIG** with CC on | **No** (per docs above) |
| Several tenants on one **host**, each with **dedicated passthrough GPU** | **Yes** (one GPU per CVM in SPT model) |
| One tenant with **multiple GPUs** in one CVM (PPCIe / future MPT) | **Yes** (one CVM; not multi-tenant on one GPU) |

---

## 3. Blackwell and newer (brief)

| Topic | Hopper H100 | Blackwell (B200, etc.) |
|-------|-------------|-------------------------|
| Single-GPU passthrough CC | Supported | Supported (per confidential-containers platform table) |
| Multi-GPU passthrough | PPCIe (Hopper HGX); NVLink between GPUs **not encrypted** in PPCIe | **MPT CC** mode: up to 8 GPUs per CVM; release notes state **encrypted NVLink** between GPUs **in same CVM** for MPT CC | 
| MIG + CC | **Not supported** | **UNVERIFIED — could not confirm** MIG+CC on Blackwell from primary doc read in this session; Secure AI guide excerpt reviewed was Hopper/Blackwell general unsupported list including MIG |

**Primary Blackwell/Hopper CC mode doc:** https://docs.nvidia.com/nvidia-secure-ai-with-blackwell-and-hopper-gpus-whitepaper.pdf  
**Release notes (SPT / PPCIe / MPT):** https://docs.nvidia.com/590trd1-trusted-computing-solutions-release-notes.pdf

**arXiv:2507.02770** notes **Trusted I/O** planned for Blackwell and that multi-GPU CC features were disabled/unavailable on their Hopper testbed — treat as research snapshot, not product spec.

---

## 4. Implications for planned experiments

Legend: **Configurable** = feasible on shipping H100 CC without unsupported mode; **Not configurable** = blocked by product mode; **Partial** = only in CC-DevTools or specific multi-GPU mode.

| Planned experiment (from project brief) | Configurable on shipping H100 CC? | Notes |
|----------------------------------------|-----------------------------------|--------|
| **(1)** Open attestation verifier + mock weight-release gate on **one passthrough GPU** in a CVM | **Configurable** | Matches SPT CC; use NVAT/nvTrust + ReadyState workflow per deployment guide — https://docs.nvidia.com/cc-deployment-guide-snp.pdf |
| **(1)** Same gate with **multiple tenants on one GPU (MIG partitions)** | **Not configurable** | MIG + CC unsupported |
| **(2)** Leakage of **bounce-buffer transfer timing/volume** (host–GPU PCIe path) | **Configurable** | Core SPT model; staging in shared memory — CACM / HCC whitepaper |
| **(2)** Leakage across **encrypted NVLink** between two GPUs in one job | **Not configurable on Hopper PPCIe** (NVLink not encrypted) | PPCIe release-note limitation; Blackwell **MPT CC** may differ — https://docs.nvidia.com/590trd1-trusted-computing-solutions-release-notes.pdf |
| **(2)** Compare leakage **CC-On vs CC-DevTools** (perf counters on) | **Partial / Configurable** | CC-DevTools explicitly enables counters while keeping encryption paths — NVIDIA blog |
| **(2)** **Perf-counter-based** spy on victim on **same GPU** under CC-On | **Not configurable** (counters disabled) | CC-On disables performance counters — https://developer.nvidia.com/blog/confidential-computing-on-h100-gpus-for-secure-and-trustworthy-ai/ |
| **(3)** Detect **covert modulation** on host–GPU staging / RPC path | **Configurable** (host-side observer) | Aligns with threat model (malicious host sees ciphertext sizes/timing) |
| **(3)** Cross-tenant spy on **same GPU via MIG** under CC | **Not configurable** | No MIG+CC |
| **(3)** Cross-tenant spy: **Tenant A’s CVM** vs **Tenant B’s CVM** on **different passthrough GPUs** same server | **Configurable** (node multi-tenancy) | Different threat story (co-residency on PCIe tree / NUMA / IOMMU), not GPU-internal MIG |
| **(4)** Overlay controls for **passthrough CC weight protection** | **Configurable** (documentation) | No special hardware beyond supported CC stack |
| Multi-GPU **weight sharding** training attestation story | **Partial** | PPCIe multi-GPU to **one** CVM only; encryption scope per NVIDIA notes |

---

## 5. Practical experimental placement

**Recommended default testbed (shipping H100 CC):**

1. **One CVM (TDX or SNP)** + **one H100 passthrough** (SPT CC).  
2. **CC-On** for production-like tests; **CC-DevTools** only for counter-survival / profiling sub-studies (attestation report reflects DevTools — CACM).  
3. **Do not plan MIG partition experiments** unless product support changes.

**If multi-GPU required:**

- Use **PPCIe** only with eyes open: **NVLink between GPUs not encrypted** on Hopper — leakage experiments on inter-GPU links are **in scope for that mode**, not a violation of “all links encrypted.”

---

## 6. CC mode controls (for experiment planning)

From NVIDIA Technical Blog (CC-Off / CC-On / CC-DevTools):

- https://developer.nvidia.com/blog/confidential-computing-on-h100-gpus-for-secure-and-trustworthy-ai/

| Mode | Use in experiments |
|------|-------------------|
| CC-Off | Baseline (no CC protections) |
| CC-On | Production-like; counters off |
| CC-DevTools | Profiling / counter-survival studies; differs in attestation posture |

---

*End of tenancy assessment. No project code was produced.*
