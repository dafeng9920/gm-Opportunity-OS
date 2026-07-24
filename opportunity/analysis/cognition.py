"""Independent, append-only cognition provenance links; never Fact provenance."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from .contracts import AnalysisProposal
from .reference_validator import AnalysisProposalReferenceValidator
from .store import AnalysisProposalStore


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _required(value: str | None, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _ids(values: tuple[str, ...], field_name: str) -> None:
    if not isinstance(values, tuple) or not values or not all(isinstance(value, str) and value.strip() for value in values):
        raise ValueError(f"{field_name} must be a non-empty tuple of IDs")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must be unique")


class ProducedFactLookup(Protocol):
    def get_produced(self, production_id: str): ...


class CognitionLinkStatus(StrEnum):
    PROPOSED = "PROPOSED"
    REVIEWED = "REVIEWED"
    PRODUCED = "PRODUCED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class CognitionProvenanceLink:
    analysis_proposal_id: str
    measurement_artifact_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    runtime_id: str
    runtime_version: str
    status: CognitionLinkStatus
    review_event_id: str | None = None
    produced_fact_id: str | None = None
    producer_event_id: str | None = None
    cognition_link_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=_now)

    def __post_init__(self) -> None:
        for value, name in ((self.cognition_link_id, "cognition_link_id"), (self.analysis_proposal_id, "analysis_proposal_id"), (self.runtime_id, "runtime_id"), (self.runtime_version, "runtime_version"), (self.created_at, "created_at")):
            _required(value, name)
        _ids(self.measurement_artifact_ids, "measurement_artifact_ids")
        _ids(self.evidence_ids, "evidence_ids")
        if not isinstance(self.status, CognitionLinkStatus):
            raise ValueError("cognition link status is invalid")
        for value, name in ((self.review_event_id, "review_event_id"), (self.produced_fact_id, "produced_fact_id"), (self.producer_event_id, "producer_event_id")):
            if value is not None:
                _required(value, name)
        if self.status is CognitionLinkStatus.PRODUCED and self.produced_fact_id is None:
            raise ValueError("PRODUCED cognition link requires produced_fact_id")
        if self.status is not CognitionLinkStatus.PRODUCED and self.produced_fact_id is not None:
            raise ValueError("only PRODUCED cognition links may reference a produced fact")


class CognitionProvenanceLinkStore:
    """Append-only link storage, independent of Fact and Gate persistence."""

    def __init__(self, database: Path | str) -> None:
        self._db = sqlite3.connect(database)
        self._db.row_factory = sqlite3.Row
        self._db.execute("CREATE TABLE IF NOT EXISTS cognition_provenance_links (cognition_link_id TEXT PRIMARY KEY, analysis_proposal_id TEXT NOT NULL, measurement_artifact_ids TEXT NOT NULL, evidence_ids TEXT NOT NULL, runtime_id TEXT NOT NULL, runtime_version TEXT NOT NULL, status TEXT NOT NULL, review_event_id TEXT, produced_fact_id TEXT, producer_event_id TEXT, created_at TEXT NOT NULL)")
        self._db.commit()

    def append(self, link: CognitionProvenanceLink) -> None:
        self._db.execute("INSERT INTO cognition_provenance_links VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (link.cognition_link_id, link.analysis_proposal_id, json.dumps(link.measurement_artifact_ids), json.dumps(link.evidence_ids), link.runtime_id, link.runtime_version, link.status.value, link.review_event_id, link.produced_fact_id, link.producer_event_id, link.created_at))
        self._db.commit()

    def get(self, cognition_link_id: str) -> CognitionProvenanceLink | None:
        row = self._db.execute("SELECT * FROM cognition_provenance_links WHERE cognition_link_id=?", (cognition_link_id,)).fetchone()
        return self._from_row(row) if row is not None else None

    def list_for_proposal(self, proposal_id: str) -> tuple[CognitionProvenanceLink, ...]:
        rows = self._db.execute("SELECT * FROM cognition_provenance_links WHERE analysis_proposal_id=? ORDER BY created_at, cognition_link_id", (proposal_id,)).fetchall()
        return tuple(self._from_row(row) for row in rows)

    @staticmethod
    def _from_row(row: sqlite3.Row) -> CognitionProvenanceLink:
        import json
        return CognitionProvenanceLink(row["analysis_proposal_id"], tuple(json.loads(row["measurement_artifact_ids"])), tuple(json.loads(row["evidence_ids"])), row["runtime_id"], row["runtime_version"], CognitionLinkStatus(row["status"]), row["review_event_id"], row["produced_fact_id"], row["producer_event_id"], row["cognition_link_id"], row["created_at"])


class CognitionProvenanceLinkService:
    """Validates link assertions; it cannot produce, accept, or evaluate Facts."""

    def __init__(self, proposals: AnalysisProposalStore, references: AnalysisProposalReferenceValidator, productions: ProducedFactLookup, links: CognitionProvenanceLinkStore) -> None:
        self._proposals = proposals
        self._references = references
        self._productions = productions
        self._links = links

    def record(self, link: CognitionProvenanceLink) -> CognitionProvenanceLink:
        proposal = self._proposals.get(link.analysis_proposal_id)
        if proposal is None:
            raise KeyError(f"analysis proposal not found: {link.analysis_proposal_id}")
        self._references.validate(proposal)
        self._validate_input_lineage(proposal, link)
        self._validate_runtime_origin(proposal, link)
        self._validate_production_relation(link)
        self._links.append(link)
        return link

    @staticmethod
    def _validate_input_lineage(proposal: AnalysisProposal, link: CognitionProvenanceLink) -> None:
        if not set(link.measurement_artifact_ids).issubset(proposal.measurement_artifact_ids):
            raise ValueError("link measurement artifacts are outside proposal scope")
        if not set(link.evidence_ids).issubset(proposal.evidence_ids):
            raise ValueError("link evidence is outside proposal scope")

    @staticmethod
    def _validate_runtime_origin(proposal: AnalysisProposal, link: CognitionProvenanceLink) -> None:
        if proposal.runtime_identity is not None and proposal.runtime_identity != f"{link.runtime_id}@{link.runtime_version}":
            raise ValueError("link runtime origin does not match proposal runtime identity")

    def _validate_production_relation(self, link: CognitionProvenanceLink) -> None:
        if link.status is not CognitionLinkStatus.PRODUCED:
            return
        produced = self._productions.get_produced(link.produced_fact_id)  # type: ignore[arg-type]
        if produced is None:
            raise KeyError(f"produced fact not found: {link.produced_fact_id}")
        if produced.measurement_artifact_id not in link.measurement_artifact_ids:
            raise ValueError("produced fact measurement is outside link lineage")
        if not set(produced.fact.evidence_ids).issubset(link.evidence_ids):
            raise ValueError("produced fact evidence is outside link lineage")
        if link.producer_event_id is not None and link.producer_event_id != produced.request_id:
            raise ValueError("producer event does not match produced fact")


