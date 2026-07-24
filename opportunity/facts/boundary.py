"""The only boundary that can turn ledger Evidence into a persisted Gate Fact."""
from __future__ import annotations

from uuid import uuid4

from candidates.evidence_validator import EvidenceReferenceValidator
from opportunity.evaluation.contracts import EvaluationFact, FactVerification

from .contracts import FactProductionRequest, MeasurementArtifact, ProducedGateFact
from .registry import FactProducerRegistry
from .store import FactProductionStore


class FactProductionBoundary:
    def __init__(self, producers: FactProducerRegistry, evidence: EvidenceReferenceValidator, store: FactProductionStore) -> None:
        self._producers = producers
        self._evidence = evidence
        self._store = store

    def produce(self, request: FactProductionRequest, artifact: MeasurementArtifact) -> ProducedGateFact:
        producer = self._producers.get(request.producer_id, request.producer_version)
        if producer is None:
            raise KeyError("fact producer is not registered")
        support = next((item for item in producer.supported_facts if (item.fact_id, item.fact_version) == (request.fact_id, request.fact_version)), None)
        if support is None:
            raise ValueError("fact producer is not authorized for requested fact")
        if artifact.measurement_method not in support.measurement_methods:
            raise ValueError("measurement method is not authorized for requested fact")
        if (artifact.request_id, artifact.producer_id, artifact.producer_version, artifact.fact_id, artifact.fact_version, artifact.evidence_ids) != (
            request.request_id, request.producer_id, request.producer_version, request.fact_id, request.fact_version, request.evidence_ids,
        ):
            raise ValueError("measurement artifact does not match fact production request")
        self._evidence.validate(request.evidence_ids)
        self._store.append_measurement(artifact)
        provenance = {**dict(artifact.provenance), "method": artifact.measurement_method, "captured_at": artifact.captured_at}
        fact = EvaluationFact(
            request.fact_id, _category_for(request.fact_id, request.fact_version), artifact.output_value,
            request.evidence_ids, 1.0, FactVerification.EVIDENCE_BACKED,
            request.fact_version, provenance,
        )
        produced = ProducedGateFact(
            str(uuid4()), request.request_id, request.producer_id, request.producer_version,
            artifact.artifact_id, fact,
        )
        self._store.append(produced)
        return produced


def _category_for(fact_id: str, fact_version: str):
    from opportunity.evaluation import DEFAULT_GATE_FACT_REGISTRY
    return DEFAULT_GATE_FACT_REGISTRY.get(fact_id, fact_version).category