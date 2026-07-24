"""A minimal deterministic container that can create non-authoritative proposals only."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Protocol
from uuid import uuid4

from opportunity.evaluation import DEFAULT_GATE_FACT_REGISTRY

from .contracts import AnalysisProposal
from .reference_validator import AnalysisProposalReferenceValidator
from .store import AnalysisProposalStore


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _required(value: str | None, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _references(values: tuple[str, ...], field_name: str) -> None:
    if not isinstance(values, tuple) or not values or not all(isinstance(value, str) and value.strip() for value in values):
        raise ValueError(f"{field_name} must be a non-empty tuple of IDs")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must be unique")


class CandidateLookup(Protocol):
    def get(self, candidate_id: str): ...


class AnalysisExecutionStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    REJECTED_PRE_EXECUTION = "REJECTED_PRE_EXECUTION"
    FAILED_EXECUTION = "FAILED_EXECUTION"


@dataclass(frozen=True, slots=True)
class AnalysisRuntimeIdentity:
    runtime_id: str
    runtime_version: str
    executor_type: str
    configuration_reference: str
    model_identity: str | None = None
    model_version: str | None = None
    prompt_reference_id: str | None = None

    def __post_init__(self) -> None:
        for value, name in ((self.runtime_id, "runtime_id"), (self.runtime_version, "runtime_version"), (self.executor_type, "executor_type"), (self.configuration_reference, "configuration_reference")):
            _required(value, name)
        if self.executor_type != "deterministic":
            raise ValueError("minimal analysis runtime executor_type must be deterministic")
        if (self.model_identity is None) != (self.model_version is None):
            raise ValueError("model identity and version must be supplied together")
        if self.model_identity is not None:
            raise ValueError("minimal analysis runtime does not permit a model identity")
        if self.prompt_reference_id is not None:
            _required(self.prompt_reference_id, "prompt_reference_id")


@dataclass(frozen=True, slots=True)
class AnalysisRuntimeRequest:
    candidate_id: str
    measurement_artifact_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    requested_fact_id: str
    requested_fact_version: str
    context: Mapping[str, str] = field(default_factory=dict)
    idempotency_key: str | None = None

    def __post_init__(self) -> None:
        for value, name in ((self.candidate_id, "candidate_id"), (self.requested_fact_id, "requested_fact_id"), (self.requested_fact_version, "requested_fact_version")):
            _required(value, name)
        _references(self.measurement_artifact_ids, "measurement_artifact_ids")
        _references(self.evidence_ids, "evidence_ids")
        if not isinstance(self.context, Mapping) or len(self.context) > 8:
            raise ValueError("context must be a mapping with at most eight entries")
        if not all(isinstance(key, str) and key.strip() and len(key) <= 64 and isinstance(value, str) and len(value) <= 512 for key, value in self.context.items()):
            raise ValueError("context must contain bounded string metadata")
        object.__setattr__(self, "context", MappingProxyType(dict(self.context)))
        if self.idempotency_key is not None:
            _required(self.idempotency_key, "idempotency_key")

    def fingerprint(self) -> str:
        payload = {"candidate_id": self.candidate_id, "measurement_artifact_ids": self.measurement_artifact_ids, "evidence_ids": self.evidence_ids, "requested_fact_id": self.requested_fact_id, "requested_fact_version": self.requested_fact_version, "context": dict(self.context)}
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class AnalysisExecutionAudit:
    invocation_id: str
    runtime_id: str
    runtime_version: str
    executor_type: str
    configuration_reference: str
    candidate_id: str
    measurement_artifact_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    requested_fact_id: str
    requested_fact_version: str
    request_fingerprint: str
    status: AnalysisExecutionStatus
    executed_at: str = field(default_factory=_now)
    proposal_id: str | None = None
    idempotency_key: str | None = None
    failure_category: str | None = None


class AnalysisExecutionAuditStore:
    """Append-only execution audit; it is not a Fact or governance artifact."""

    def __init__(self, database: Path | str) -> None:
        self._db = sqlite3.connect(database)
        self._db.row_factory = sqlite3.Row
        self._db.execute("CREATE TABLE IF NOT EXISTS analysis_execution_audits (invocation_id TEXT PRIMARY KEY, runtime_id TEXT, runtime_version TEXT, executor_type TEXT, configuration_reference TEXT, candidate_id TEXT, measurement_artifact_ids TEXT, evidence_ids TEXT, requested_fact_id TEXT, requested_fact_version TEXT, request_fingerprint TEXT, status TEXT, executed_at TEXT, proposal_id TEXT, idempotency_key TEXT UNIQUE, failure_category TEXT)")
        self._db.commit()

    def append(self, audit: AnalysisExecutionAudit) -> None:
        self._db.execute("INSERT INTO analysis_execution_audits VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (audit.invocation_id, audit.runtime_id, audit.runtime_version, audit.executor_type, audit.configuration_reference, audit.candidate_id, json.dumps(audit.measurement_artifact_ids), json.dumps(audit.evidence_ids), audit.requested_fact_id, audit.requested_fact_version, audit.request_fingerprint, audit.status.value, audit.executed_at, audit.proposal_id, audit.idempotency_key, audit.failure_category))
        self._db.commit()

    def get_by_idempotency_key(self, key: str) -> AnalysisExecutionAudit | None:
        row = self._db.execute("SELECT * FROM analysis_execution_audits WHERE idempotency_key=?", (key,)).fetchone()
        return self._from_row(row) if row is not None else None

    @staticmethod
    def _from_row(row: sqlite3.Row) -> AnalysisExecutionAudit:
        return AnalysisExecutionAudit(row["invocation_id"], row["runtime_id"], row["runtime_version"], row["executor_type"], row["configuration_reference"], row["candidate_id"], tuple(json.loads(row["measurement_artifact_ids"])), tuple(json.loads(row["evidence_ids"])), row["requested_fact_id"], row["requested_fact_version"], row["request_fingerprint"], AnalysisExecutionStatus(row["status"]), row["executed_at"], row["proposal_id"], row["idempotency_key"], row["failure_category"])


@dataclass(frozen=True, slots=True)
class AnalysisRuntimeResult:
    audit: AnalysisExecutionAudit
    proposal: AnalysisProposal | None
    replayed: bool = False


class DeterministicAnalysisRuntime:
    """Creates a deliberately non-inferential AnalysisProposal from validated references."""

    def __init__(self, identity: AnalysisRuntimeIdentity, candidates: CandidateLookup, references: AnalysisProposalReferenceValidator, proposals: AnalysisProposalStore, audits: AnalysisExecutionAuditStore) -> None:
        self._identity = identity
        self._candidates = candidates
        self._references = references
        self._proposals = proposals
        self._audits = audits

    def execute(self, request: AnalysisRuntimeRequest) -> AnalysisRuntimeResult:
        if request.idempotency_key is not None:
            prior = self._audits.get_by_idempotency_key(request.idempotency_key)
            if prior is not None:
                if prior.request_fingerprint != request.fingerprint():
                    raise ValueError("idempotency key was already used for a different analysis request")
                proposal = self._proposals.get(prior.proposal_id) if prior.proposal_id else None
                return AnalysisRuntimeResult(prior, proposal, True)
        try:
            candidate = self._candidates.get(request.candidate_id)
            if candidate is None:
                raise KeyError(f"candidate not found: {request.candidate_id}")
            if not set(request.evidence_ids).issubset(candidate.evidence_ids):
                raise ValueError("analysis evidence references are outside candidate scope")
            DEFAULT_GATE_FACT_REGISTRY.get(request.requested_fact_id, request.requested_fact_version)
            proposal = AnalysisProposal(request.candidate_id, request.measurement_artifact_ids, request.evidence_ids, request.requested_fact_id, request.requested_fact_version, "insufficient deterministic measurements for transformation", (), ("this deterministic runtime makes no fact-value inference",), ("authorized review and a fact-specific producer are required",), runtime_identity=f"{self._identity.runtime_id}@{self._identity.runtime_version}")
            self._references.validate(proposal)
            self._proposals.append(proposal)
            audit = self._audit(request, AnalysisExecutionStatus.SUCCEEDED, proposal_id=proposal.proposal_id)
            self._audits.append(audit)
            return AnalysisRuntimeResult(audit, proposal)
        except (KeyError, ValueError) as error:
            audit = self._audit(request, AnalysisExecutionStatus.REJECTED_PRE_EXECUTION, failure_category=type(error).__name__)
            self._audits.append(audit)
            return AnalysisRuntimeResult(audit, None)
        except Exception as error:
            audit = self._audit(request, AnalysisExecutionStatus.FAILED_EXECUTION, failure_category=type(error).__name__)
            self._audits.append(audit)
            return AnalysisRuntimeResult(audit, None)

    def _audit(self, request: AnalysisRuntimeRequest, status: AnalysisExecutionStatus, *, proposal_id: str | None = None, failure_category: str | None = None) -> AnalysisExecutionAudit:
        return AnalysisExecutionAudit(str(uuid4()), self._identity.runtime_id, self._identity.runtime_version, self._identity.executor_type, self._identity.configuration_reference, request.candidate_id, request.measurement_artifact_ids, request.evidence_ids, request.requested_fact_id, request.requested_fact_version, request.fingerprint(), status, proposal_id=proposal_id, idempotency_key=request.idempotency_key, failure_category=failure_category)
