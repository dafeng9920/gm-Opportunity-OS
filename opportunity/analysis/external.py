"""Captured-fixture external cognition adapter; it has no provider or governance capability."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Protocol
from uuid import uuid4

from .contracts import AnalysisProposal
from .reference_validator import AnalysisProposalReferenceValidator
from .store import AnalysisProposalStore


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _required(value: str | None, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


class CandidateLookup(Protocol):
    def get(self, candidate_id: str): ...


@dataclass(frozen=True, slots=True)
class RawOutputArtifact:
    provider_identity: str
    model_identity: str
    runtime_identity: str
    raw_payload_reference: str
    execution_configuration_reference: str
    model_version: str | None = None
    prompt_reference_id: str | None = None
    raw_output_id: str = field(default_factory=lambda: str(uuid4()))
    captured_at: str = field(default_factory=_now)

    def __post_init__(self) -> None:
        for value, name in ((self.raw_output_id, "raw_output_id"), (self.provider_identity, "provider_identity"), (self.model_identity, "model_identity"), (self.runtime_identity, "runtime_identity"), (self.raw_payload_reference, "raw_payload_reference"), (self.execution_configuration_reference, "execution_configuration_reference"), (self.captured_at, "captured_at")):
            _required(value, name)
        if self.model_version is not None:
            _required(self.model_version, "model_version")
        if self.prompt_reference_id is not None:
            _required(self.prompt_reference_id, "prompt_reference_id")


class ExternalExecutionStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class ExternalExecutionAudit:
    raw_output_id: str
    runtime_identity: str
    status: ExternalExecutionStatus
    proposal_id: str | None = None
    failure_category: str | None = None
    audit_id: str = field(default_factory=lambda: str(uuid4()))
    captured_at: str = field(default_factory=_now)


class RawOutputStore:
    """Append-only captured response storage; no network behavior exists here."""
    def __init__(self, database: Path | str) -> None:
        self._db = sqlite3.connect(database); self._db.row_factory = sqlite3.Row
        self._db.execute("CREATE TABLE IF NOT EXISTS raw_output_artifacts (id TEXT PRIMARY KEY, provider TEXT, model TEXT, runtime TEXT, payload_reference TEXT, configuration_reference TEXT, model_version TEXT, prompt_reference TEXT, captured_at TEXT, payload TEXT)")
        self._db.commit()
    def append(self, artifact: RawOutputArtifact, payload: Any) -> None:
        self._db.execute("INSERT INTO raw_output_artifacts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (artifact.raw_output_id, artifact.provider_identity, artifact.model_identity, artifact.runtime_identity, artifact.raw_payload_reference, artifact.execution_configuration_reference, artifact.model_version, artifact.prompt_reference_id, artifact.captured_at, json.dumps(payload, sort_keys=True)))
        self._db.commit()
    def get(self, raw_output_id: str) -> RawOutputArtifact | None:
        row = self._db.execute("SELECT * FROM raw_output_artifacts WHERE id=?", (raw_output_id,)).fetchone()
        return None if row is None else RawOutputArtifact(row["provider"], row["model"], row["runtime"], row["payload_reference"], row["configuration_reference"], row["model_version"], row["prompt_reference"], row["id"], row["captured_at"])
    def get_payload(self, raw_output_id: str) -> Any | None:
        row = self._db.execute("SELECT payload FROM raw_output_artifacts WHERE id=?", (raw_output_id,)).fetchone()
        return None if row is None else json.loads(row["payload"])


class ExternalExecutionAuditStore:
    def __init__(self, database: Path | str) -> None:
        self._db = sqlite3.connect(database); self._db.row_factory = sqlite3.Row
        self._db.execute("CREATE TABLE IF NOT EXISTS external_execution_audits (id TEXT PRIMARY KEY, raw_output_id TEXT, runtime_identity TEXT, status TEXT, proposal_id TEXT, failure_category TEXT, captured_at TEXT)"); self._db.commit()
    def append(self, audit: ExternalExecutionAudit) -> None:
        self._db.execute("INSERT INTO external_execution_audits VALUES (?, ?, ?, ?, ?, ?, ?)", (audit.audit_id, audit.raw_output_id, audit.runtime_identity, audit.status.value, audit.proposal_id, audit.failure_category, audit.captured_at)); self._db.commit()
    def get(self, audit_id: str) -> ExternalExecutionAudit | None:
        row=self._db.execute("SELECT * FROM external_execution_audits WHERE id=?", (audit_id,)).fetchone()
        return None if row is None else ExternalExecutionAudit(row["raw_output_id"], row["runtime_identity"], ExternalExecutionStatus(row["status"]), row["proposal_id"], row["failure_category"], row["id"], row["captured_at"])


@dataclass(frozen=True, slots=True)
class ExternalAdapterResult:
    raw_output: RawOutputArtifact
    audit: ExternalExecutionAudit
    proposal: AnalysisProposal | None


class CapturedExternalIntelligenceAdapter:
    """Normalizes a captured response into a Proposal or records rejection only."""
    _FIELDS = frozenset(("requested_fact_id", "requested_fact_version", "measurement_artifact_ids", "evidence_ids", "analysis_summary", "assumptions", "uncertainty", "missing_information"))

    def __init__(self, raw_outputs: RawOutputStore, candidates: CandidateLookup, references: AnalysisProposalReferenceValidator, proposals: AnalysisProposalStore, audits: ExternalExecutionAuditStore) -> None:
        self._raw_outputs=raw_outputs; self._candidates=candidates; self._references=references; self._proposals=proposals; self._audits=audits

    def normalize(self, raw_output_id: str, candidate_id: str) -> ExternalAdapterResult:
        raw=self._raw_outputs.get(raw_output_id)
        if raw is None: raise KeyError(f"raw output not found: {raw_output_id}")
        try:
            payload=self._raw_outputs.get_payload(raw_output_id)
            if not isinstance(payload, Mapping) or set(payload) != self._FIELDS:
                raise ValueError("external output does not match closed proposal schema")
            candidate=self._candidates.get(candidate_id)
            if candidate is None: raise KeyError(f"candidate not found: {candidate_id}")
            evidence_ids=tuple(payload["evidence_ids"])
            if not set(evidence_ids).issubset(candidate.evidence_ids): raise ValueError("external output evidence is outside candidate scope")
            proposal=AnalysisProposal(candidate_id, tuple(payload["measurement_artifact_ids"]), evidence_ids, payload["requested_fact_id"], payload["requested_fact_version"], payload["analysis_summary"], tuple(payload["assumptions"]), tuple(payload["uncertainty"]), tuple(payload["missing_information"]), raw.model_identity, raw.model_version or "captured-fixture", raw.runtime_identity, raw.prompt_reference_id)
            self._references.validate(proposal); self._proposals.append(proposal)
            audit=ExternalExecutionAudit(raw.raw_output_id, raw.runtime_identity, ExternalExecutionStatus.SUCCEEDED, proposal.proposal_id)
            self._audits.append(audit); return ExternalAdapterResult(raw, audit, proposal)
        except (KeyError, ValueError, TypeError) as error:
            audit=ExternalExecutionAudit(raw.raw_output_id, raw.runtime_identity, ExternalExecutionStatus.REJECTED, failure_category=type(error).__name__)
            self._audits.append(audit); return ExternalAdapterResult(raw, audit, None)

class ZhipuProviderError(RuntimeError):
    def __init__(self, category: str, *, endpoint: str | None = None, transport_stage: str = "before_request", http_status: int | None = None, timeout_class: str | None = None) -> None:
        super().__init__(category)
        self.category = category
        self.endpoint = endpoint
        self.transport_stage = transport_stage
        self.http_status = http_status
        self.timeout_class = timeout_class

class ZhipuCapturedProvider:
    """Single-provider HTTP client. It only returns captured, untrusted cognition output."""
    endpoint = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    def __init__(self, model: str | None = None, timeout_seconds: float = 20.0, transport=None) -> None:
        import os
        config = self._configuration(Path(".env"))
        if config.get("OPPORTUNITY_OS_PROVIDER", "Zhipu").lower() != "zhipu":
            raise ValueError("Phase 18.29 provider must remain Zhipu")
        self._model = model or config.get("OPPORTUNITY_OS_MODEL") or "glm-5.2"
        self._api_key_environment = config.get("OPPORTUNITY_OS_API_KEY_ENV", "ZHIPU_API_KEY")
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    @staticmethod
    def _configuration(path: Path) -> dict[str, str]:
        config: dict[str, str] = {}
        if not path.exists():
            return config
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            if key in {"OPPORTUNITY_OS_PROVIDER", "OPPORTUNITY_OS_MODEL", "OPPORTUNITY_OS_API_KEY_ENV"}:
                config[key] = value.strip()
        return config
    def invoke(self, request: Mapping[str, Any]) -> tuple[RawOutputArtifact, Any]:
        import os
        import urllib.error
        import urllib.request
        key = os.environ.get(self._api_key_environment)
        if not key:
            raise ZhipuProviderError("configured Zhipu API key environment variable is not available")
        bounded = {key: request[key] for key in ("candidate_id", "measurement_artifact_ids", "evidence_ids", "requested_fact_id", "requested_fact_version")}
        instruction = "Return JSON only with exactly requested_fact_id, requested_fact_version, measurement_artifact_ids, evidence_ids, analysis_summary, assumptions, uncertainty, missing_information. Do not output scores, recommendations, fact values, or decisions."
        body = {"model": self._model, "stream": False, "temperature": 0, "response_format": {"type": "json_object"}, "messages": [{"role": "system", "content": instruction}, {"role": "user", "content": json.dumps(bounded, sort_keys=True)}]}
        try:
            if self._transport is not None:
                response = self._transport(body, key, self._timeout_seconds)
            else:
                wire = json.dumps(body).encode("utf-8")
                http = urllib.request.Request(self.endpoint, data=wire, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(http, timeout=self._timeout_seconds) as result:
                    response = json.loads(result.read().decode("utf-8"))
        except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError) as error:
            raise ZhipuProviderError(type(error).__name__, endpoint=self.endpoint, transport_stage="response_received" if isinstance(error, urllib.error.HTTPError) else "request_sent", http_status=getattr(error, "code", None), timeout_class=type(error).__name__ if isinstance(error, TimeoutError) else None) from error
        try:
            content = response["choices"][0]["message"]["content"]
            payload = json.loads(content) if isinstance(content, str) else content
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
            raise ZhipuProviderError("malformed provider response", endpoint=self.endpoint, transport_stage="response_parsing") from error
        response_id = str(response.get("id", uuid4()))
        artifact = RawOutputArtifact("zhipu", self._model, "zhipu-external-adapter@0.1", f"zhipu-response:{response_id}", "phase-18.29-zhipu-http-v1", self._model, "prompt://phase-18.29/zhipu-closed-schema-v1")
        return artifact, payload



class ZhipuAnthropicCapturedProvider:
    """Zhipu Anthropic-compatible Messages client; no Fact or governance capability."""
    endpoint = "https://open.bigmodel.cn/api/anthropic/v1/messages"
    model = "glm-5.2"

    def __init__(self, timeout_seconds: float = 30.0, transport=None) -> None:
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    def invoke(self, request: Mapping[str, Any]) -> tuple[RawOutputArtifact, Any]:
        import os
        import urllib.error
        import urllib.request
        key = os.environ.get("ZHIPU_API_KEY")
        if not key:
            raise ZhipuProviderError("configured Zhipu API key environment variable is not available")
        bounded = {name: request[name] for name in ("candidate_id", "measurement_artifact_ids", "evidence_ids", "requested_fact_id", "requested_fact_version")}
        body = {"model": self.model, "max_tokens": 512, "stream": False, "system": "Return only JSON with requested_fact_id, requested_fact_version, measurement_artifact_ids, evidence_ids, analysis_summary, assumptions, uncertainty, missing_information. Never return scores, recommendations, fact values, or decisions.", "messages": [{"role": "user", "content": json.dumps(bounded, sort_keys=True)}]}
        try:
            if self._transport is not None:
                response = self._transport(body, key, self._timeout_seconds)
            else:
                wire=json.dumps(body).encode("utf-8")
                http=urllib.request.Request(self.endpoint,data=wire,headers={"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"},method="POST")
                with urllib.request.urlopen(http,timeout=self._timeout_seconds) as result:
                    response=json.loads(result.read().decode("utf-8"))
        except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError) as error:
            raise ZhipuProviderError(type(error).__name__, endpoint=self.endpoint, transport_stage="response_received" if isinstance(error, urllib.error.HTTPError) else "request_sent", http_status=getattr(error, "code", None), timeout_class=type(error).__name__ if isinstance(error, TimeoutError) else None) from error
        try:
            content=response["content"][0]["text"]
            payload=json.loads(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
            raise ZhipuProviderError("malformed provider response", endpoint=self.endpoint, transport_stage="response_parsing") from error
        response_id=str(response.get("id",uuid4()))
        artifact=RawOutputArtifact("zhipu_anthropic",self.model,"zhipu-anthropic-adapter@0.1",f"zhipu-anthropic-response:{response_id}","phase-18.29-zhipu-anthropic-v1",self.model,"prompt://phase-18.29/zhipu-anthropic-closed-schema-v1")
        return artifact,payload

@dataclass(frozen=True, slots=True)
class ProviderFailureAudit:
    provider: str
    endpoint: str
    model: str
    transport_stage: str
    exception_category: str
    http_status: int | None = None
    timeout_class: str | None = None
    failure_audit_id: str = field(default_factory=lambda: str(uuid4()))
    captured_at: str = field(default_factory=_now)


class ProviderFailureAuditStore:
    """Append-only safe provider failure observability; never stores response data or secrets."""
    def __init__(self, database: Path | str) -> None:
        self._db=sqlite3.connect(database)
        self._db.execute("CREATE TABLE IF NOT EXISTS provider_failure_audits (id TEXT PRIMARY KEY, provider TEXT, endpoint TEXT, model TEXT, transport_stage TEXT, exception_category TEXT, http_status INTEGER, timeout_class TEXT, captured_at TEXT)")
        self._db.commit()
    def append(self, audit: ProviderFailureAudit) -> None:
        self._db.execute("INSERT INTO provider_failure_audits VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",(audit.failure_audit_id,audit.provider,audit.endpoint,audit.model,audit.transport_stage,audit.exception_category,audit.http_status,audit.timeout_class,audit.captured_at)); self._db.commit()

