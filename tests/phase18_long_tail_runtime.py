"""Runtime evidence: recorded keyword-corpus Evidence reaches the Content Gate."""
from pathlib import Path

from candidates import EvidenceReferenceValidator
from core.schemas import CandidatePacket, EvidenceObject
from evidence import EvidenceLedger
from opportunity.fact_quality import FactQualityBoundary, FactQualityPolicy, FactQualityRegistry, FactQualityStore
from opportunity.facts import FactProducerRegistry, FactProductionBoundary, FactProductionRequest, FactProductionStore, LongTailCountProducer
from opportunity.gates import OpportunityGateEngine


def main() -> None:
    database = Path('.opportunity-os') / 'phase18-long-tail-count.db'
    if database.exists():
        database.unlink()
    raw_reference = 'https://example.test/keyword-corpus/grow-a-garden'
    items = tuple(f'Grow a Garden guide {index}' for index in range(1, 13))
    evidence = EvidenceObject('keyword-corpus', 'keyword-corpus', raw_reference, metadata={
        'long_tail_measurement': {
            'source_reference': raw_reference,
            'topic_scope': 'Grow a Garden',
            'candidate_items': items,
            'count_rule': 'qualified_long_tail_v1',
            'result': len(items),
        },
    })
    ledger = EvidenceLedger(database)
    ledger.append(evidence)
    producer = LongTailCountProducer(ledger)
    request = FactProductionRequest(producer.producer_id, producer.producer_version, 'long_tail_count', '0.1', (evidence.id,))
    producers = FactProducerRegistry()
    producers.register(producer.registration())
    artifact = producer.measure(request)
    produced = FactProductionBoundary(producers, EvidenceReferenceValidator(ledger), FactProductionStore(database)).produce(request, artifact)
    policies = FactQualityRegistry()
    policies.register(FactQualityPolicy(
        'long-tail-count-quality', 'long_tail_count', '0.1',
        ('query_family', 'source', 'method', 'captured_at'),
        ('topic_scope', 'source_reference', 'candidate_items', 'qualified_items', 'count_rule', 'calculated_count'),
        1, ('reproducible-qualified-count',), '0.1',
    ))
    assessment, accepted = FactQualityBoundary(policies, FactQualityStore(database)).assess(produced, artifact)
    if accepted is None:
        raise RuntimeError(f'quality assessment failed: {assessment.assessment_reason}')
    candidate = CandidatePacket('Grow a Garden', 'recorded keyword corpus', (evidence.id,), 'evidence-ledger', 0.5)
    gate = OpportunityGateEngine().evaluate(candidate, 'content_expansion', {'long_tail_count': accepted.fact.value})
    print(f'Phase 18.10 runtime verified: fact={accepted.fact.fact_id}@{accepted.fact.fact_version}, count={accepted.fact.value}, quality={assessment.status}, gate={gate.status}')


if __name__ == '__main__':
    main()