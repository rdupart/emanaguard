# Related Work Survey — H100 CC Trust Boundary for AI Model-Weight Protection

**Assessment date:** 2026-06-03  
**Scope:** NVIDIA H100/Hopper confidential computing (CC), GPU/PCIe/NVLink I/O side channels, model extraction via system channels, attestation-gated secret release, SL5 / frontier weight-protection framing.

**Verification policy:** Each entry below was checked against a primary landing page (publisher, arXiv, NVIDIA docs, or RAND). Entries marked **UNVERIFIED** could not be fully confirmed from primary metadata during this review.

---

## 1. Threat-model and policy framing (SL5 / frontier weights)

| Title | Authors | Venue / year | Link |
|-------|---------|--------------|------|
| *Securing AI Model Weights: Preventing Theft and Misuse of Frontier Models* | Sella Nevo, Dan Lahav, Ajay Karpur, Yogev Bar-On, Henry Alexander Bradley, Jeff Alstott | RAND Research Report RRA2849-1, May 2024 | https://www.rand.org/pubs/research_reports/RRA2849-1.html |
| *SL5 Standard for AI Security* (v0.1; NIST SP 800-53 overlay) | SL5 Task Force / Institute for Security and Technology (organizational authorship on site) | Web standard, January 2026 (per site) | https://standard.sl5.org/ |
| *Artificial Intelligence Risk Management Framework (AI RMF 1.0)* | NIST (organizational) | NIST AI 100-1, January 2023 | https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf |
| *Why is Attestation Required for Confidential Computing?* | Mark Overby (NVIDIA); CCC blog | Confidential Computing Consortium, April 2023 | https://confidentialcomputing.io/2023/04/06/why-is-attestation-required-for-confidential-computing/ |

**Note on “AI705”:** The project brief references “AI705-style” control text. **UNVERIFIED — could not confirm** a published NIST or industry document literally titled “AI705.” Public SL5 materials reference **ICD 705** (SCIF physical-security construction) as a *basis* for physical controls, not “AI705.” See `novelty_assessment.md` § Contribution 4.

---

## 2. NVIDIA H100 / Hopper CC architecture, attestation, deployment

| Title | Authors | Venue / year | Link |
|-------|---------|--------------|------|
| *Creating the First Confidential GPUs* | Gobikrishna Dhanuskodi, Sudeshna Guha, Vidhya Krishnan, Aruna Manjunatha, Rob Nertney, Michael O'Connor, Phil Rogers | *Communications of the ACM*, Vol. 67 No. 1, January 2024 | https://doi.org/10.1145/3626827 (ACM); https://queue.acm.org/detail.cfm?id=3623391 |
| *Confidential Compute on NVIDIA Hopper H100* (whitepaper WP-11459-001) | NVIDIA (organizational) | NVIDIA whitepaper | https://images.nvidia.com/aem-dam/en-zz/Solutions/data-center/HCC-Whitepaper-v1.0.pdf |
| *Confidential Computing on NVIDIA H100 GPUs for Secure and Trustworthy AI* | NVIDIA engineers (blog) | NVIDIA Technical Blog | https://developer.nvidia.com/blog/confidential-computing-on-h100-gpus-for-secure-and-trustworthy-ai/ |
| *NVIDIA Secure AI with Blackwell and Hopper GPUs* | NVIDIA (organizational) | NVIDIA whitepaper | https://docs.nvidia.com/nvidia-secure-ai-with-blackwell-and-hopper-gpus-whitepaper.pdf |
| *Deployment Guide for Confidential Computing with Hopper and Blackwell GPUs* | NVIDIA (organizational) | NVIDIA documentation (PDF) | https://docs.nvidia.com/cc-deployment-guide-snp.pdf |
| *NVIDIA Trusted Computing Solutions* (hub: attestation, deployment, NRAS) | NVIDIA (organizational) | NVIDIA Docs | https://docs.nvidia.com/nvtrust/index.html |
| *NVIDIA Attestation SDK (NVAT)* — open-source verifier/tooling | NVIDIA (organizational) | GitHub + docs | https://github.com/NVIDIA/attestation-sdk ; https://docs.nvidia.com/attestation/nv-attestation-sdk-cpp/latest/overview.html |
| *Blueprint, Bootstrap, and Bridge: A Security Look at NVIDIA GPU Confidential Computing* (also circulated on arXiv) | **Anonymous authors** (preprint); under review per arXiv | arXiv preprint / MLSys submission (status per arXiv) | https://arxiv.org/abs/2507.02770 |
| *Characterization of GPU TEE Overheads in Distributed Data Parallel ML Training* | Jonghyun Lee, Yongqin Wang, Rachit Rajat, Mengyuan Li, Murali Annavaram | arXiv, 2025 | https://arxiv.org/abs/2501.11771 |
| *Confidential Computing on Heterogeneous CPU-GPU Systems: Survey and Future Directions* | **UNVERIFIED — could not confirm** full author list from this session; cited as survey in arXiv:2507.02770 | arXiv | https://arxiv.org/pdf/2408.11601 (linked from related survey references) |

---

## 3. Pre-commercial / research GPU confidential execution (context for CC)

| Title | Authors | Venue / year | Link |
|-------|---------|--------------|------|
| *Graviton: Trusted Execution Environments on GPUs* | M. Volos, K. Vaswani, R. Bruno, et al. | NSDI 2018 | **UNVERIFIED — could not confirm** DOI in this session; widely cited as NSDI’18 — verify at https://www.usenix.org/conference/nsdi18 |
| *HIX: Hypervisor Extension for Intel SGX to Support High-performance GPU-accelerated Enclaves* | Jang et al. | USENIX ATC 2019 | **UNVERIFIED — could not confirm** full citation in this session |
| *SAGE: Software-based Attestation for GPU Execution* | Ivanov et al. (per arXiv PDF) | arXiv, 2022 | https://arxiv.org/pdf/2209.03125 |
| *Honeycomb: Secure and Efficient GPU Executions via Static Validation* | Mai et al. | **UNVERIFIED — venue not re-checked** | **UNVERIFIED** — cited in arXiv:2507.02770 only |

---

## 4. GPU / PCIe / NVLink I/O traffic analysis and interconnect side channels

| Title | Authors | Venue / year | Link |
|-------|---------|--------------|------|
| *Invisible Probe: Timing Attacks with PCIe Congestion Side-channel* | Mingtian Tan, Junpeng Wan, Zhe Zhou, Zhou Li | IEEE S&P 2021 | https://doi.org/10.1109/SP40001.2021.00030 (per IEEE); PDF: https://stefan1wan.github.io/files/InvisibleProbe.pdf |
| *LockedDown: Exploiting Contention on Host-GPU PCIe Bus for Fun and Profit* | Mert Side, Fan Yao, Zhenkai Zhang | EuroS&P 2022 | https://www.mertside.com/documents/lockeddown/2022-EuroSP-LockedDown.pdf |
| *Leaky Buddies: Cross-Component Covert Channels on Integrated CPU-GPU Systems* | Sankha Baran Dutta, Hoda Naghibijouybari, Nael Abu-Ghazaleh, Andres Marquez, Kevin Barker | ISCA 2021 | **UNVERIFIED — could not confirm** DOI; arXiv/institutional copies exist |
| *Spy in the GPU-box: Covert and Side Channel Attacks on Multi-GPU Systems* | Sankha Baran Dutta, Hoda Naghibijouybari, Arjun Gupta, Nael Abu-Ghazaleh, Andres Marquez, Kevin Barker | ISCA 2023 | https://doi.org/10.1145/3579371.3589080 |
| *Beyond the Bridge: Contention-Based Covert and Side Channel Attacks on Multi-GPU Interconnect* | Yicheng Zhang, Ravan Nazaraliyev, Sankha Baran Dutta, Nael Abu-Ghazaleh, Andres Marquez, Kevin Barker | arXiv (WEI), 2024 | https://arxiv.org/abs/2404.03877 |
| *NVBleed: Covert and Side-Channel Attacks on NVIDIA Multi-GPU Systems* | **UNVERIFIED — full author list not confirmed** | arXiv, 2025 | https://arxiv.org/pdf/2503.17847 |
| *Veiled Pathways: Investigating Covert and Side Channels within GPU Uncore* | Yuanqing Miao, Yingtian Zhang, Dinghao Wu, Danfeng Zhang, Gang Tan, Rui Zhang, Mahmut Taylan Kandemir | MICRO 2024 | https://doi.ieeecomputersociety.org/10.1109/MICRO61859.2024.00088 |
| *PCIe Guard: A Virtualization-based Framework to Restrict PCIe Traffic for Secure GPUs* | Ilias Giechaskiel et al. | **UNVERIFIED — venue not re-checked in this session** | https://ilias.giechaskiel.com/papers/2021_4_pcie_host.pdf |

---

## 5. GPU microarchitectural side channels and model structure/weight leakage

| Title | Authors | Venue / year | Link |
|-------|---------|--------------|------|
| *Rendered Insecure: GPU Side Channel Attacks are Practical* | Hoda Naghibijouybari, Avesta Sasan, Khaled N. Khasawneh, Nael Abu-Ghazaleh | CCS 2018 | **UNVERIFIED — could not confirm** DOI in this session |
| *Leaky DNN: Stealing Deep-Learning Model Secret with GPU Context-Switching Side-channel* | Jiacheng Wei, Yicheng Zhang, Zhe Zhou, Zhou Li, Mohammad Abdullah Al Faruque | DSN 2020 | **UNVERIFIED — could not confirm** DOI in this session |
| *Neural Network Model Extraction Attacks in Edge Devices by Hearing Architectural Hints* | Xu Zhang, H. Li, et al. | **UNVERIFIED — venue** | https://arxiv.org/abs/1903.03916 |
| *Bandwidth Utilization Side-Channel on ML Inference Accelerators* | **UNVERIFIED — full author list** | SPSML / arXiv 2021 | https://arxiv.org/abs/2110.07157 |
| *BarraCUDA: Edge GPUs do Leak DNN Weights* | **UNVERIFIED — confirm author list on camera-ready** | USENIX Security 2025 (per NVIDIA/USENIX hosting) | https://www.usenix.org/system/files/usenixsecurity25-horvath.pdf |
| *ShadowScope: GPU Monitoring and Validation via Composable Side Channel Signals* | **UNVERIFIED — full author list** | arXiv, 2025 | https://arxiv.org/abs/2509.00300 |

---

## 6. Attestation-gated key / secret release (general CC, not GPU-specific)

| Title | Authors | Venue / year | Link |
|-------|---------|--------------|------|
| *Bootstrapping and Maintaining Trust in the Cloud* (Keylime) | Nabil Schear, Patrick T. Cable II, Thomas M. Moyer, Bryan Richard, Robert Rudd | ACSAC 2016 | https://doi.org/10.1145/2991079.2991104 |
| *Attestation in confidential computing* (Key Broker pattern) | Red Hat (organizational) | Red Hat blog | https://www.redhat.com/en/blog/attestation-confidential-computing |
| *Integration of Remote Attestation with Key Negotiation and Key Distribution mechanisms* (IETF draft) | Xia et al. | Internet-Draft | https://www.ietf.org/archive/id/draft-xia-rats-key-negotiation-integration-02.html |
| Azure / industry “secure key release” product narratives | Various vendors | Product docs / blogs | e.g. Fortanix SKR overview: https://www.fortanix.com/blog/securing-enterprise-applications-and-ai-pipelines-with-attestation-gated-secure-key-release |

---

## 7. GPU workload misuse detection (adjacent to “unapproved workload” contribution)

| Title | Authors | Venue / year | Link |
|-------|---------|--------------|------|
| *MagTracer: Detecting GPU Cryptojacking via Magnetic Leakage Signals* | **UNVERIFIED — full author list** | MobiCom 2023 (per author PDF path) | https://ruixiao24.github.io/files/magtracer-mobicom23.pdf |
| *GPU Cryptojacking Detection* (ACM) | **UNVERIFIED** | ACM, 2023 | https://dl.acm.org/doi/10.1145/3577923.3583655 (landing page not fully parsed) |

---

## 8. Comparative table — prior work vs. four planned contributions

| Prior work (representative) | A: What prior work already does | B: Relation to our 4 contributions | C: Scoops us? |
|-----------------------------|----------------------------------|--------------------------------------|---------------|
| NVIDIA NVAT / nvTrust / NRAS + CACM’24 CC article | Production attestation chain, deployment guides, CC-Off/On/DevTools modes | **(1)** Official verification paths exist; **(2–4)** define threat model & bounce-buffer encryption | **(1) partial** — verifier exists; gap is *open reproducible SL5 prototype gate* |
| arXiv:2507.02770 (“Blueprint, Bootstrap, Bridge”) | Reverse-engineers GPU-CC; reports CPU–GSP DMA **timing** side channel on RPC/staging path; attestation walkthrough | **(2)** Direct overlap on timing at CC I/O boundary; **(1)** attestation detail | **(2) partial–yes** for timing leakage *under CC*; **(1) partial** |
| Invisible Probe; LockedDown | PCIe **congestion timing** → fingerprint GPU workloads (web, ML, keys) without CC | **(2)** Same *class* of channel (volume/timing metadata at host–GPU link) | **(2) partial** — pre-CC; our angle must be **with CC enabled** + bounce-buffer path |
| Lee et al. arXiv:2501.11771 | GPU TEE/CC **performance** of encrypted PCIe/NVLink in DDP | Informs threat model; not leakage-focused | **no** for leakage; **partial** if we claim first CC perf study |
| Spy in the GPU-box; Beyond the Bridge; NVBleed | NVLink/multi-GPU **contention** covert/side channels (mostly non-CC) | **(2)** Inter-GPU metadata; **(3)** fingerprinting | **(3) partial** for fingerprinting; **no** if scoped to **CC host–GPU staging** only |
| Veiled Pathways | GPU uncore + PCIe allocation channels; breaks **MIG** isolation (non-CC) | **(3)** Covert channels on GPU | **(3) partial** — different isolation mechanism (MIG vs CC) |
| BarraCUDA; Leaky DNN; model-extraction bus papers | Extract **weights/structure** via EM, context switch, or **unencrypted** bus observation | Motivates weight protection; CC encrypts **content** | **no** for encrypted-content claim; **partial** if we imply first weight theft risk |
| Keylime; RATS key draft; SKR blogs | **Attestation-gated** key release to VMs/enclaves | **(1)** Same pattern for mock weights | **(1) partial** — pattern is standard; GPU-specific open tooling is narrower novelty |
| SL5 standard v0.1 | SP 800-53 **overlay** for frontier AI facilities | **(4)** Same *genre* of deliverable | **(4) partial** — SL5 exists; overlap if we duplicate without CC-specific delta |
| ShadowScope; cryptojacking detectors | Detect anomalous GPU execution via side channels / PMU | **(3)** Unapproved workload detection | **(3) partial** — not CC-boundary-specific |

---

## 9. Three–four most relevant papers (quick human spot-check)

1. **Blueprint, Bootstrap, and Bridge / GPU CC Demystified (arXiv:2507.02770, 2025)**  
   **What it did:** Independent security analysis of shipping NVIDIA GPU-CC on H100-class systems: architecture reconstruction, boot/attestation path, and experimental evaluation of data paths over PCIe—including **size-dependent timing** on CPU–GSP memory transfers via staging buffers, with responsible disclosure to NVIDIA PSIRT.  
   **Why spot-check:** Closest direct overlap with contributions **(1)** and **(2)**; read §Bridge / CPU–GSP DMA timing before claiming novelty on CC I/O metadata leakage.

2. **Creating the First Confidential GPUs (Dhanuskodi et al., CACM 2024)**  
   **What it did:** Authoritative NVIDIA description of Hopper CC: RoT, SPDM session, attestation reports, bounce-buffer model, **performance counters disabled in CC-On**, CC-DevTools mode, and threat-model scope.  
   **Why spot-check:** Baseline for what H100 CC *claims* to protect; essential for scoping experiments (what is in vs out of threat model).

3. **Invisible Probe (Tan et al., IEEE S&P 2021)**  
   **What it did:** Showed PCIe congestion timing reveals GPU workload class (including ML model activity) from a co-located device; high-accuracy website/keystroke/ML inference scenarios.  
   **Why spot-check:** Canonical “I/O metadata over PCIe” reference—compare attack surface **before** vs **after** CC bounce-buffer encryption.

4. **Securing AI Model Weights (Nevo et al., RAND RRA2849-1, 2024)**  
   **What it did:** Defined SL1–SL5, attack vectors on weights, and honest statement that **SL5 is not achievable with public technology today**; frames organizational controls needed.  
   **Why spot-check:** Grounds the project’s SL5 narrative and sets expectations for what a *research prototype* can vs cannot prove.

---

*End of related work survey. No project code was produced as part of this assessment.*
