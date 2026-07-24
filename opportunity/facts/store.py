"""Append-only persistence for governed Fact production outputs."""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from contextlib import contextmanager
from pathlib import Path

from opportunity.evaluation.contracts import EvaluationFact, EvaluationFactCategory, FactVerification

from .contracts import ProducedGateFact


def _json_value(value):
    """Convert recursively frozen artifact data into JSON-safe values."""
    if isinstance(value, Mapping):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_json_value(item) for item in value]
    return value


class FactProductionStore:
    def __init__(self, database: Path | str) -> None:
        self.database = str(database)
        with self._session() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS produced_gate_facts (
                production_id TEXT PRIMARY KEY, request_id TEXT NOT NULL, producer_id TEXT NOT NULL,
                producer_version TEXT NOT NULL, measurement_artifact_id TEXT NOT NULL,
                fact_id TEXT NOT NULL, fact_version TEXT NOT NULL, category TEXT NOT NULL,
                value TEXT NOT NULL, evidence_ids TEXT NOT NULL, confidence REAL NOT NULL,
                provenance TEXT NOT NULL, created_at TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS measurement_artifacts (artifact_id TEXT PRIMARY KEY, request_id TEXT, producer_id TEXT, producer_version TEXT, fact_id TEXT, fact_version TEXT, evidence_ids TEXT, method TEXT, measurements TEXT, output_value TEXT, provenance TEXT, captured_at TEXT)""")

    @contextmanager
    def _session(self):
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def append_measurement(self, artifact) -> None:
        with self._session() as db:
            db.execute("INSERT INTO measurement_artifacts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (artifact.artifact_id, artifact.request_id, artifact.producer_id, artifact.producer_version, artifact.fact_id, artifact.fact_version, json.dumps(_json_value(artifact.evidence_ids)), artifact.measurement_method, json.dumps(_json_value(artifact.measurements)), json.dumps(_json_value(artifact.output_value)), json.dumps(_json_value(artifact.provenance)), artifact.captured_at))

    def get_measurement(self, artifact_id: str):
        with self._session() as db:
            return db.execute("SELECT * FROM measurement_artifacts WHERE artifact_id = ?", (artifact_id,)).fetchone()
    def append(self, produced: ProducedGateFact) -> None:
        fact = produced.fact
        with self._session() as db:
            db.execute("INSERT INTO produced_gate_facts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                produced.production_id, produced.request_id, produced.producer_id, produced.producer_version,
                produced.measurement_artifact_id, fact.fact_id, fact.fact_version, fact.category.value,
                json.dumps(_json_value(fact.value)), json.dumps(_json_value(fact.evidence_ids)), fact.confidence,
                json.dumps(_json_value(fact.provenance), sort_keys=True), produced.created_at,
            ))

    def list_for_evidence_ids(self, evidence_ids: tuple[str, ...]) -> tuple[EvaluationFact, ...]:
        allowed = set(evidence_ids)
        with self._session() as db:
            rows = db.execute("SELECT * FROM produced_gate_facts ORDER BY created_at, production_id").fetchall()
        facts = []
        for row in rows:
            references = tuple(json.loads(row["evidence_ids"]))
            if set(references).issubset(allowed):
                facts.append(EvaluationFact(
                    row["fact_id"], EvaluationFactCategory(row["category"]), json.loads(row["value"]),
                    references, row["confidence"], FactVerification.EVIDENCE_BACKED,
                    row["fact_version"], json.loads(row["provenance"]),
                ))
        return tuple(facts)