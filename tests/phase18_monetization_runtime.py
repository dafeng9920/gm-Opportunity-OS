"""Runtime evidence: controlled monetization Evidence reaches the Monetization Gate."""
from pathlib import Path

from candidates import EvidenceReferenceValidator
from core.schemas import CandidatePacket, EvidenceObject
from evidence import EvidenceLedger
from opportunity.fact_quality import FactQualityBoundary, FactQualityPolicy, FactQualityRegistry, FactQualityStore
from opportunity.facts import FactProducerRegistry, FactProductionBoundary, FactProductionRequest, FactProductionStore, MonetizationPathProducer
from opportunity.gates import OpportunityGateEngine


def main() -> None:
    database = Path('.opportunity-os') / 'phase18-monetization-path.db'
    if database.exists():
        database.unlink()
    raw_reference = 'https://create.roblox.com/docs/production/monetization'
    evidence = EvidenceObject('create.roblox.com', 'platform-monetization-doc', raw_reference, metadata={
        'monetization_path_measurement': {
            'source_reference': raw_reference,
            'path': 'ADS',
            'evidence_kind': 'PLATFORM_AD_PROGRAM',
            'validation_rule': 'recognized_monetization_path_v1',
            'result': 'ADS',
        },
    })
    ledger = EvidenceLedger(database)
    ledger.append(evidence)
    producer = MonetizationPathProducer(ledger)
    request = FactProductionRequest(producer.producer_id, producer.producer_version, 'monetization_path', '0.1', (evidence.id,))
    producers = FactProducerRegistry()
    producers.register(producer.registration())
    artifact = producer.measure(request)
    produced = FactProductionBoundary(producers, EvidenceReferenceValidator(ledger), FactProductionStore(database)).produce(request, artifact)
    policies = FactQualityRegistry()
    policies.register(FactQualityPolicy(
        'monetization-path-quality', 'monetization_path', '0.1',
        ('path_scope', 'source', 'method', 'captured_at'),
        ('source_reference', 'path', 'evidence_kind', 'validation_rule', 'calculated_path'),
        1, ('controlled-path-evidence',), '0.1',
    ))
    assessment, accepted = FactQualityBoundary(policies, FactQualityStore(database)).assess(produced, artifact)
    if accepted is None:
        raise RuntimeError(f'quality assessment failed: {assessment.assessment_reason}')
    candidate = CandidatePacket('Grow a Garden', 'recorded monetization evidence', (evidence.id,), 'evidence-ledger', 0.5)
    gate = OpportunityGateEngine().evaluate(candidate, 'monetization', {'monetization_path': accepted.fact.value})
    print(f'Phase 18.11 runtime verified: fact={accepted.fact.fact_id}@{accepted.fact.fact_version}, path={accepted.fact.value}, quality={assessment.status}, gate={gate.status}')


if __name__ == '__main__':
    main()