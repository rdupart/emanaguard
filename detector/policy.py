"""Attested workload policy for D2 policy-deviation detection."""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.trace.events import RunLabels


@dataclass(frozen=True)
class AttestedPolicy:
    """Expected benign ML job profile inside the CVM."""

    name: str
    allowed_modes: frozenset[str]
    allowed_architectures: frozenset[str]

    def is_compliant(self, labels: RunLabels) -> bool:
        arch = labels.architecture_id or labels.model_class
        return labels.mode in self.allowed_modes and arch in self.allowed_architectures


# Default: attested training on two collected architectures only
DEFAULT_TRAIN_POLICY = AttestedPolicy(
    name="train_only_arch_256x4_1024x8",
    allowed_modes=frozenset({"train"}),
    allowed_architectures=frozenset(
        {"arch_mlp_256x4", "arch_mlp_1024x8", "arch_legacy_small", "arch_legacy_large"}
    ),
)


def violation_label(labels: RunLabels, policy: AttestedPolicy) -> int:
    """0 = in-policy (benign), 1 = policy deviation."""
    return 0 if policy.is_compliant(labels) else 1
