from __future__ import annotations
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4
from opportunity.evaluation.contracts import EvaluationFact

def now(): return datetime.now(UTC).isoformat()
class QualityStatus(StrEnum): PASS='PASS'; FAIL='FAIL'; UNKNOWN='UNKNOWN'
class FactLifecycleStatus(StrEnum): PRODUCED='PRODUCED'; QUALITY_PENDING='QUALITY_PENDING'; ACCEPTED='ACCEPTED'; REJECTED='REJECTED'; CONSUMED_BY_GATE='CONSUMED_BY_GATE'
@dataclass(frozen=True, slots=True)
class FactQualityPolicy:
    policy_id:str; fact_id:str; fact_version:str; required_provenance:tuple[str,...]; required_measurement_fields:tuple[str,...]; minimum_evidence_count:int; validation_rules:tuple[str,...]; version:str
@dataclass(frozen=True, slots=True)
class FactQualityAssessment:
    assessment_id:str; source_fact_id:str; policy_id:str; policy_version:str; status:QualityStatus; assessment_reason:str; rework_reference:str|None=None; recommended_action:str|None=None; created_at:str=field(default_factory=now)
@dataclass(frozen=True, slots=True)
class AcceptedFact:
    accepted_fact_id:str; source_fact_id:str; quality_assessment_id:str; accepted_version:str; fact:EvaluationFact; accepted_at:str=field(default_factory=now)
@dataclass(frozen=True, slots=True)
class FactLifecycleEvent:
    source_fact_id:str; status:FactLifecycleStatus; reason:str; created_at:str=field(default_factory=now)