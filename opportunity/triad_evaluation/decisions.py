from dataclasses import dataclass, field
from enum import StrEnum
from uuid import uuid4
class AgreementStatus(StrEnum): CONSENSUS='CONSENSUS'; CONFLICT='CONFLICT'; INCOMPLETE='INCOMPLETE'
class TriadDecisionStatus(StrEnum): READY='READY'; REVIEW_REQUIRED='REVIEW_REQUIRED'; UNKNOWN='UNKNOWN'
@dataclass(frozen=True, slots=True)
class ConflictReference:
 role_a:str; role_b:str; dimension:str; result_a:str; result_b:str; reason_code:str
@dataclass(frozen=True, slots=True)
class TriadDecisionArtifact:
 candidate_id:str; triad_context_id:str; input_asset_id:str; role_assessment_refs:tuple[str,...]; required_role_ids:tuple[str,...]; agreement_status:AgreementStatus; decision_status:TriadDecisionStatus; reason_codes:tuple[str,...]; conflict_refs:tuple[ConflictReference,...]; policy_version:str; schema_version:str; artifact_id:str=field(default_factory=lambda:str(uuid4()))
