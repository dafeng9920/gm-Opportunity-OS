"""Append-only storage for non-authoritative analysis proposals."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .contracts import AnalysisProposal, AnalysisProposalStatus


class AnalysisProposalStore:
    def __init__(self, database: Path | str) -> None:
        self._db = sqlite3.connect(database)
        self._db.row_factory = sqlite3.Row
        self._db.execute("CREATE TABLE IF NOT EXISTS analysis_proposals (proposal_id TEXT PRIMARY KEY, candidate_id TEXT, measurement_artifact_ids TEXT, evidence_ids TEXT, requested_fact_id TEXT, requested_fact_version TEXT, analysis_summary TEXT, assumptions TEXT, uncertainty TEXT, missing_information TEXT, model_identity TEXT, model_version TEXT, runtime_identity TEXT, prompt_reference_id TEXT, status TEXT, created_at TEXT)")
        self._db.commit()

    def append(self, proposal: AnalysisProposal) -> None:
        self._db.execute("INSERT INTO analysis_proposals VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (proposal.proposal_id, proposal.candidate_id, json.dumps(proposal.measurement_artifact_ids), json.dumps(proposal.evidence_ids), proposal.requested_fact_id, proposal.requested_fact_version, proposal.analysis_summary, json.dumps(proposal.assumptions), json.dumps(proposal.uncertainty), json.dumps(proposal.missing_information), proposal.model_identity, proposal.model_version, proposal.runtime_identity, proposal.prompt_reference_id, proposal.status.value, proposal.created_at))
        self._db.commit()

    def get(self, proposal_id: str) -> AnalysisProposal | None:
        row = self._db.execute("SELECT * FROM analysis_proposals WHERE proposal_id=?", (proposal_id,)).fetchone()
        if row is None:
            return None
        return AnalysisProposal(row["candidate_id"], tuple(json.loads(row["measurement_artifact_ids"])), tuple(json.loads(row["evidence_ids"])), row["requested_fact_id"], row["requested_fact_version"], row["analysis_summary"], tuple(json.loads(row["assumptions"])), tuple(json.loads(row["uncertainty"])), tuple(json.loads(row["missing_information"])), row["model_identity"], row["model_version"], row["runtime_identity"], row["prompt_reference_id"], AnalysisProposalStatus(row["status"]), row["proposal_id"], row["created_at"])
