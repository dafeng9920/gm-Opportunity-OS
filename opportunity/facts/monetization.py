"""Deterministic measurement contract for ``monetization_path@0.1``."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping


class MonetizationPath(StrEnum):
    AFFILIATE = "AFFILIATE"
    DIGITAL_PRODUCT = "DIGITAL_PRODUCT"
    SAAS = "SAAS"
    SERVICE = "SERVICE"
    ADS = "ADS"
    MARKETPLACE = "MARKETPLACE"
    UNKNOWN = "UNKNOWN"


class MonetizationEvidenceKind(StrEnum):
    AFFILIATE_PROGRAM = "AFFILIATE_PROGRAM"
    PRODUCT_CATALOG = "PRODUCT_CATALOG"
    SAAS_PRICING = "SAAS_PRICING"
    SERVICE_CATALOG = "SERVICE_CATALOG"
    PLATFORM_AD_PROGRAM = "PLATFORM_AD_PROGRAM"
    MARKETPLACE_LISTING = "MARKETPLACE_LISTING"


_ALLOWED_EVIDENCE_KINDS = {
    MonetizationPath.AFFILIATE: MonetizationEvidenceKind.AFFILIATE_PROGRAM,
    MonetizationPath.DIGITAL_PRODUCT: MonetizationEvidenceKind.PRODUCT_CATALOG,
    MonetizationPath.SAAS: MonetizationEvidenceKind.SAAS_PRICING,
    MonetizationPath.SERVICE: MonetizationEvidenceKind.SERVICE_CATALOG,
    MonetizationPath.ADS: MonetizationEvidenceKind.PLATFORM_AD_PROGRAM,
    MonetizationPath.MARKETPLACE: MonetizationEvidenceKind.MARKETPLACE_LISTING,
}


@dataclass(frozen=True, slots=True)
class MonetizationPathMeasurement:
    source_reference: str
    path: MonetizationPath
    evidence_kind: MonetizationEvidenceKind
    validation_rule: str
    result: MonetizationPath

    validation_rule_id = "recognized_monetization_path_v1"

    def __post_init__(self) -> None:
        if not isinstance(self.source_reference, str) or not self.source_reference:
            raise ValueError("monetization measurement requires source reference")
        if self.path is MonetizationPath.UNKNOWN or self.result is MonetizationPath.UNKNOWN:
            raise ValueError("unknown monetization path must not become a fact")
        if self.validation_rule != self.validation_rule_id:
            raise ValueError("monetization validation rule is not supported")
        if self.result is not self.path:
            raise ValueError("monetization measurement result must match controlled path")
        if _ALLOWED_EVIDENCE_KINDS.get(self.path) is not self.evidence_kind:
            raise ValueError("monetization evidence kind does not support controlled path")

    @classmethod
    def from_metadata(
        cls, raw_reference: str, metadata: Mapping[str, Any]
    ) -> "MonetizationPathMeasurement":
        value = metadata.get("monetization_path_measurement")
        if not isinstance(value, Mapping):
            raise ValueError("monetization evidence is missing measurement")
        source_reference = value.get("source_reference")
        if source_reference != raw_reference:
            raise ValueError("monetization source reference must match evidence")
        try:
            return cls(
                source_reference,
                MonetizationPath(value.get("path")),
                MonetizationEvidenceKind(value.get("evidence_kind")),
                value.get("validation_rule"),
                MonetizationPath(value.get("result")),
            )
        except ValueError as error:
            raise ValueError("monetization measurement has invalid controlled values") from error

    def as_measurements(self) -> Mapping[str, str]:
        return MappingProxyType({
            "source_reference": self.source_reference,
            "path": self.path.value,
            "evidence_kind": self.evidence_kind.value,
            "validation_rule": self.validation_rule,
            "calculated_path": self.result.value,
        })