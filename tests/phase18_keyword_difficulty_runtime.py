"""Runtime evidence: recorded SERP Evidence reaches the deterministic Competition Gate."""
from pathlib import Path

from candidates import EvidenceReferenceValidator
from core.schemas import CandidatePacket, EvidenceObject
from evidence import EvidenceLedger
from opportunity.fact_quality import FactQualityBoundary, FactQualityPolicy, FactQualityRegistry, FactQualityStore
from opportunity.facts import FactProducerRegistry, FactProductionBoundary, FactProductionRequest, FactProductionStore, KeywordDifficultyProducer
from opportunity.gates import OpportunityGateEngine


def main() -> None:
    database = Path('.opportunity-os') / 'phase18-keyword-difficulty.db'
    if database.exists():
        database.unlink()
    raw_reference = 'https://www.google.com/search?q=Grow+a+Garden+codes'
    evidence = EvidenceObject('search-snapshot', 'serp-snapshot', raw_reference, metadata={
        'keyword_difficulty_measurement': {
            'source_reference': raw_reference,
            'query': 'Grow a Garden codes',
            'ranked_results': (
                {'position': 1, 'domain': 'result-1.example', 'competition_score': 20},
                {'position': 2, 'domain': 'result-2.example', 'competition_score': 25},
                {'position': 3, 'domain': 'result-3.example', 'competition_score': 30},
            ),
            'calculation_rule': 'mean_result_competition_score_v1',
        },
    })
    ledger = EvidenceLedger(database)
    ledger.append(evidence)
    producer = KeywordDifficultyProducer(ledger)
    request = FactProductionRequest(producer.producer_id, producer.producer_version, 'keyword_difficulty', '0.1', (evidence.id,))
    producers = FactProducerRegistry()
    producers.register(producer.registration())
    artifact = producer.measure(request)
    produced = FactProductionBoundary(producers, EvidenceReferenceValidator(ledger), FactProductionStore(database)).produce(request, artifact)
    policies = FactQualityRegistry()
    policies.register(FactQualityPolicy(
        'keyword-difficulty-quality', 'keyword_difficulty', '0.1',
        ('query', 'source', 'method', 'captured_at'),
        ('source_reference', 'query', 'ranked_results', 'calculation_rule', 'calculated_score'),
        1, ('reproducible-serp-calculation',), '0.1',
    ))
    assessment, accepted = FactQualityBoundary(policies, FactQualityStore(database)).assess(produced, artifact)
    if accepted is None:
        raise RuntimeError(f'quality assessment failed: {assessment.assessment_reason}')
    candidate = CandidatePacket('Grow a Garden', 'recorded SERP signal', (evidence.id,), 'evidence-ledger', 0.5)
    gate = OpportunityGateEngine().evaluate(candidate, 'competition', {'keyword_difficulty': accepted.fact.value})
    print(f'Phase 18.9 runtime verified: fact={accepted.fact.fact_id}@{accepted.fact.fact_version}, score={accepted.fact.value}, quality={assessment.status}, gate={gate.status}')


if __name__ == '__main__':
    main()