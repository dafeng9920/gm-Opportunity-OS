"""Runtime evidence: recorded Trend Evidence reaches the deterministic Demand Gate."""
from pathlib import Path

from candidates import EvidenceReferenceValidator
from core.schemas import CandidatePacket, EvidenceObject
from evidence import EvidenceLedger
from opportunity.fact_quality import FactQualityBoundary, FactQualityPolicy, FactQualityRegistry, FactQualityStore
from opportunity.facts import FactProducerRegistry, FactProductionBoundary, FactProductionRequest, FactProductionStore, TrendSignalProducer
from opportunity.gates import OpportunityGateEngine


def main() -> None:
    database = Path('.opportunity-os') / 'phase18-trend-signal.db'
    if database.exists():
        database.unlink()
    raw_reference = 'https://trends.google.com/trends/explore?geo=US&q=Grow%20a%20Garden'
    evidence = EvidenceObject('trends.google.com', 'trend-signal', raw_reference, metadata={
        'query': 'Grow a Garden', 'region': 'US',
        'trend_measurement': {
            'source_reference': raw_reference,
            'time_window': ('2026-07-01', '2026-07-08'),
            'observations': (42, 67),
            'comparison_rule': 'latest_gt_earliest',
        },
    })
    ledger = EvidenceLedger(database)
    ledger.append(evidence)
    producer = TrendSignalProducer(ledger)
    request = FactProductionRequest(producer.producer_id, producer.producer_version, 'trend_up', '0.1', (evidence.id,))
    producers = FactProducerRegistry()
    producers.register(producer.registration())
    artifact = producer.measure(request)
    produced = FactProductionBoundary(producers, EvidenceReferenceValidator(ledger), FactProductionStore(database)).produce(request, artifact)
    policies = FactQualityRegistry()
    policies.register(FactQualityPolicy(
        'trend-quality', 'trend_up', '0.1',
        ('query', 'region', 'time_window', 'source', 'method', 'captured_at'),
        ('source_reference', 'time_window', 'observations', 'comparison_rule', 'calculated_direction'),
        1, ('complete-measurement',), '0.1',
    ))
    assessment, accepted = FactQualityBoundary(policies, FactQualityStore(database)).assess(produced, artifact)
    if accepted is None:
        raise RuntimeError(f'quality assessment failed: {assessment.assessment_reason}')
    candidate = CandidatePacket('Grow a Garden', 'recorded trend signal', (evidence.id,), 'evidence-ledger', 0.5)
    gate = OpportunityGateEngine().evaluate(candidate, 'demand', {'trend_up': accepted.fact.value})
    print(f'Phase 18.8 runtime verified: fact={accepted.fact.fact_id}@{accepted.fact.fact_version}, quality={assessment.status}, gate={gate.status}')


if __name__ == '__main__':
    main()