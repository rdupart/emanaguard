# Novelty Assessment — H100 CC Trust Boundary for AI Model-Weight Protection

**Assessment date:** 2026-06-03  
**Assessor stance:** Read-only literature/doc review; no experimental validation of claims in this document.

---

## Executive summary

| Contribution | Verdict (short) |
|--------------|-----------------|
| **(1)** Open H100 CC attestation verifier + mock weight-release gate | **Partially scooped** — adjust scope to *reproducible SL5 evaluation artifact* + policy-gated mock release, not “first GPU verifier” |
| **(2)** Measured leakage at CC I/O boundary (timing/volume/metadata; perf counters) | **Partially scooped / high collision risk** — arXiv:2507.02770 already reports CPU–GSP DMA timing under CC; narrow to SL5-operational metadata + systematic matrix CC-On vs DevTools |
| **(3)** Detector for unapproved workloads / covert modulation on boundary | **Partially scooped** — fingerprinting/cryptojacking literature exists; novelty only if **CC-enabled** host–GPU staging path + defined SL5 adversary |
| **(4)** NIST SP 800-53 overlay + “AI705-style” control text | **Partially scooped** — SL5 v0.1 overlay exists; clarify delta; **AI705** name **UNVERIFIED** as formal publication |

**Overall recommendation:** **Proceed with named scope changes** (not proceed-as-is).  
**Confidence:** **Medium** — strong NVIDIA/SL5 public docs; highest uncertainty on unpublished “Blueprint” paper final version and on whether **AI705** refers to a specific internal control catalog.

**Main uncertainty:** Whether arXiv:2507.02770 will publish before or in parallel with your work, and whether reviewers treat “open verifier” as novel given NVIDIA’s **NVAT** (https://github.com/NVIDIA/attestation-sdk).

---

## Contribution 1 — Open, reproducible H100 CC attestation verifier + weight-release gate

### Closest existing work

| Work | What it already provides |
|------|---------------------------|
| *NVIDIA Attestation SDK (NVAT)* + `nvattest` CLI | Open-source (Apache-2.0) GPU attestation, local verifier, RATS-oriented APIs — https://github.com/NVIDIA/attestation-sdk |
| *NVIDIA Trusted Computing Solutions* / nvTrust docs | Deployment, golden measurements, NRAS remote verification — https://docs.nvidia.com/nvtrust/index.html |
| *Creating the First Confidential GPUs* (CACM 2024) | End-to-end attestation narrative (SPDM, reports, ReadyState) — https://doi.org/10.1145/3626827 |
| Keylime (ACSAC 2016) + RATS key-integration draft | Generic **attestation-gated key release** pattern — https://doi.org/10.1145/2991079.2991104 ; https://www.ietf.org/archive/id/draft-xia-rats-key-negotiation-integration-02.html |
| arXiv:2507.02770 | Detailed GPU-CC attestation flow reverse-engineering | https://arxiv.org/abs/2507.02770 |

### Verdict

**Partially scooped by NVAT/nvTrust + attestation-gated release literature; recommend adjustment.**

- **Not defensible as:** “First open H100 attestation verifier.” NVAT is already open and documented.
- **Defensible if reframed as:**
  - **Reproducible research harness** (pinned firmware/driver policy, golden measurements, CI fixtures) for SL5 evaluation;
  - **Explicit mock weight-release gate** with published policy language (measurements + driver branch + CC mode + DevTools flag) and threat-model diagram tying release to CVM+GPU TCB;
  - **Gap analysis** vs NRAS-only enterprise flows (what a lab without NRAS contract can still verify).

### Where we looked

NVIDIA GitHub/docs, CACM CC article, Keylime/RATS drafts, CCC secure key release blog, arXiv:2507.02770 abstract and Bridge/attestation sections.

### Why gap may still be real (narrow)

End-to-end **documented, repeatable “weights only after GPU+CPU policy pass” demo** aimed at **frontier SL5 audiences**, integrating CPU TDX/SNP + GPU evidence in one artifact, is still useful as **engineering/science communication**, not as cryptographic novelty.

---

## Contribution 2 — Leakage analysis: CC encrypts bounce-buffer *content* but not timing/volume/metadata (+ perf counters)

### Closest existing work

| Work | Overlap |
|------|---------|
| **arXiv:2507.02770** (“Blueprint, Bootstrap, Bridge”) | **Direct:** intercepts CPU–GSP transfers; correlates **transfer size with execution time** on RPC/staging path under GPU-CC; recommends constant-time RPC or noise — https://arxiv.org/abs/2507.02770 |
| *Invisible Probe* (S&P 2021) | PCIe congestion → infer GPU ML workload class — https://doi.org/10.1109/SP40001.2021.00030 |
| *LockedDown* (EuroS&P 2022) | Host–GPU PCIe contention covert channel + website fingerprinting — https://www.mertside.com/documents/lockeddown/2022-EuroSP-LockedDown.pdf |
| *Creating the First Confidential GPUs* / HCC whitepaper | States **content** encrypted over PCIe; **perf counters disabled in CC-On**; CC-DevTools re-enables counters for profiling — https://developer.nvidia.com/blog/confidential-computing-on-h100-gpus-for-secure-and-trustworthy-ai/ ; https://images.nvidia.com/aem-dam/en-zz/Solutions/data-center/HCC-Whitepaper-v1.0.pdf |
| Lee et al. arXiv:2501.11771 | Encrypted PCIe/NVLink traffic volume/timing in **training** (performance, not covert channel evaluation) — https://arxiv.org/abs/2501.11771 |

### Verdict

**Partially scooped by arXiv:2507.02770 for timing on the CC CPU–GSP staging path; recommend major scope tightening.**

- **Already done (or claimed in preprint):** Timing side channel on CPU–GSP memory transfers through staging buffers with CC enabled; measurement campaign across transfer sizes.
- **Still open if you:**
  1. **Systematize SL5-relevant metadata** beyond single-path timing—e.g., cross-layer observables (RPC counts, UVM faults, scrub events, power/EM if in scope), **CC-On vs CC-DevTools vs CC-Off** matrix, and **operational** adversary (malicious hypervisor + co-tenant on I/O tree, not ciphertext recovery).
  2. **Quantify “volume” channels** explicitly (ciphertext sizes, transfer counts, burst patterns) as **information-theoretic** bounds on weight exfil *indirectly*—without claiming byte recovery.
  3. **Perf-counter survival:** Document what remains observable when counters are **disabled** (CC-On) vs **enabled** (CC-DevTools)—NVIDIA already states counters are blocked in CC-On; contribution is **measurement**, not discovery of the policy.
  4. **Compare to pre-CC PCIe papers** with **same workloads** (A/B) to isolate what CC removes vs leaves.

### Scoop risk

**High** if marketed as “first to show CC I/O timing leakage.” **Moderate** if marketed as “SL5-oriented measurement methodology + operational risk bounds.”

### Where we looked

arXiv:2507.02770 (full intro/method/Bridge excerpts), NVIDIA CC blogs/whitepapers, Invisible Probe, LockedDown, Lee et al. 2025.

---

## Contribution 3 — Detector for unapproved workloads / covert modulation on CC boundary

### Closest existing work

| Work | Overlap |
|------|---------|
| Invisible Probe; LockedDown; Spy in the GPU-box; Beyond the Bridge | Application / workload **fingerprinting** via interconnect contention or NVLink — see `related_work.md` |
| ShadowScope (arXiv:2509.00300) | GPU kernel validation via composable side-channel traces — https://arxiv.org/abs/2509.00300 |
| GPU cryptojacking detection (ACM 2023); MagTracer | Unauthorized GPU use detection — **UNVERIFIED** full cites |
| Veiled Pathways (MICRO 2024) | Covert channels on GPU uncore / PCIe allocation under MIG — https://doi.ieeecomputersociety.org/10.1109/MICRO61859.2024.00088 |
| arXiv:2507.02770 | Discusses host-visible RPC/staging observability | https://arxiv.org/abs/2507.02770 |

### Verdict

**Partially scooped; recommend pivot to “CC-boundary telemetry + policy violation detection” with explicit false-positive model.**

- **Not novel:** ML classifier on PCIe/NVLink timing to distinguish apps (pre-CC literature).
- **Potentially novel (narrow):** Detector operating only on **host-visible signals legal under CC threat model** (staging traffic timing/size, driver RPC patterns) that flags **deviation from attested policy class** (expected training vs mining vs debugger), evaluated on **CC-On** systems with **perf counters off**.

### Where we looked

ISCA 2023 Spy paper metadata, arXiv WEI NVLink paper, MICRO 2024 Veiled Pathways, ShadowScope abstract, NVIDIA CC threat-model docs.

### Risk

Without ground-truth policy labels and CC-specific baselines, reads as **incremental ML on known channels**.

---

## Contribution 4 — Proposed NIST SP 800-53 overlay + AI705-style control text

### Closest existing work

| Work | Overlap |
|------|---------|
| *SL5 Standard for AI Security* v0.1 | Already a **NIST SP 800-53 overlay** (43 controls, 10 families) for frontier AI — https://standard.sl5.org/ |
| RAND RRA2849-1 | SL1–SL5 definitions, weight-protection playbook — https://www.rand.org/pubs/research_reports/RRA2849-1.html |
| NIST AI RMF 1.0 | Voluntary AI risk management (not 800-53 overlay) — https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf |
| ICD 705 (referenced by SL5 site) | Physical SCIF construction — **not** a GPU CC control spec |

### Verdict

**Partially scooped by SL5 Task Force overlay; “AI705” label UNVERIFIED.**

- **If deliverable = another full SL5 overlay:** **Low novelty** unless diff is sharply **GPU CC / attestation / weight-release / I/O metadata** controls with traceability to contributions (1)–(3).
- **If “AI705-style” = ICD 705–inspired physical controls for AI facilities:** SL5 v0.1 already maps ICD 705–style physical requirements — coordinate to avoid duplication.
- **Action:** Rename/clarify target artifact (e.g., “**H100-CC-OVL**: supplemental 800-53 controls for GPU confidential passthrough and weight-release gates”) and cite SL5 as parent baseline.

### Where we looked

https://standard.sl5.org/, RAND report, NIST AI RMF, MATS/IST public descriptions mentioning ICD 705 and “AI705 research” (**internal name only — UNVERIFIED** as published standard).

---

## Overall recommendation

### Proceed with named scope changes

1. **Reframe (1)** as reproducible SL5 **evaluation artifact** + mock release gate, not novel verifier.  
2. **Reframe (2)** as SL5 **operational metadata** study with CC-On/DevTools/Off matrix; cite and extend arXiv:2507.02770 explicitly.  
3. **Reframe (3)** as **policy-deviation detection on CC-visible staging telemetry**, with cryptojacking papers as baselines.  
4. **Reframe (4)** as **supplemental overlay** to SL5 v0.1 focused on GPU CC weight protection; resolve **AI705** naming with stakeholders.

### If pivot required — two defensible fallback framings

**Fallback A — “CC I/O observability & SL5 gap analysis” (measurement-only)**  
Single paper/report: systematic taxonomy of host-observable signals when CC-On; no new crypto; positions SL5 labs on what CC does **not** hide.

**Fallback B — “Attestation-gated weight release reference implementation” (systems)**  
Minimal open harness: NVAT + policy file + mock key wrap + published test vectors; contributions (2)(3) become evaluation sections of that artifact.

---

## Confidence and uncertainties

| Topic | Confidence | Uncertainty |
|-------|------------|-------------|
| NVIDIA ships NVAT + docs | **High** | Future API churn |
| MIG unsupported with CC on Hopper | **High** | Product marketing vs docs drift |
| arXiv:2507.02770 timing channel claim | **High** (for preprint content) | Publication venue/date; anonymous authors |
| “AI705” as formal control doc | **Low** | May be internal SL5 stream conflated with ICD 705 |
| Blackwell multi-GPU encrypted NVLink (MPT CC) | **Medium** | Hopper PPCIe NVLink not encrypted per NVIDIA release notes — verify for your target GPU generation |

---

*End of novelty assessment. No project code was produced.*
