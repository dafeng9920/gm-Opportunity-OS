"""Runtime evidence: five quality-accepted facts aggregate into a GateAssessmentRecord."""
from pathlib import Path

from candidates import EvidenceReferenceValidator
from core.schemas import CandidatePacket, EvidenceObject
from evidence import EvidenceLedger
from opportunity.fact_quality import FactQualityBoundary, FactQualityPolicy, FactQualityRegistry, FactQualityStore
from opportunity.facts import (
    FactProducerRegistry, FactProductionBoundary, FactProductionRequest,
    FactProductionStore, KeywordDifficultyProducer, LongTailCountProducer,
    MonetizationPathProducer, SourceInventoryProducer, TrendSignalProducer,
)
from opportunity.gate_evaluation import GateAssessmentStatus, MultiFactGateEvaluator


class _ProducedLookup:
    def __init__(self, produced):
        self._produced = produced

    def list_accepted_for_evidence_ids(self, evidence_ids):
        return (self._produced,)


def _policy(fact_id, provenance, measurements):
    return FactQualityPolicy(
        f'{fact_id}-quality', fact_id, '0.1', provenance, measurements,
        2 if fact_id == 'available_sources' else 1, ('complete',), '0.1',
    )


def main() -> None:
    database = Path('.opportunity-os') / 'phase18-gate-evaluation.db'
    if database.exists():
        database.unlink()
    ledger = EvidenceLedger(database)
    official = EvidenceObject('roblox.com', 'official-game-entity', 'https://www.roblox.com/games/126884695634066/Grow-a-Garden')
    community = EvidenceObject('growagarden.wiki', 'community-update-log', 'https://growagarden.wiki/Update_Log/1.07.0')
    trend_ref = 'https://trends.google.com/trends/explore?geo=US&q=Grow%20a%20Garden'
    trend = EvidenceObject('trends.google.com', 'trend-signal', trend_ref, metadata={
        'query': 'Grow a Garden', 'region': 'US',
        'trend_measurement': {'source_reference': trend_ref, 'time_window': ('2026-07-01', '2026-07-08'), 'observations': (42, 67), 'comparison_rule': 'latest_gt_earliest'},
    })
    low_kd_ref = 'https://www.google.com/search?q=Grow+a+Garden+codes'
    low_kd = EvidenceObject('search-snapshot', 'serp-snapshot', low_kd_ref, metadata={
        'keyword_difficulty_measurement': {'source_reference': low_kd_ref, 'query': 'Grow a Garden codes', 'ranked_results': (
            {'position': 1, 'domain': 'one.example', 'competition_score': 20}, {'position': 2, 'domain': 'two.example', 'competition_score': 25}, {'position': 3, 'domain': 'three.example', 'competition_score': 30},
        ), 'calculation_rule': 'mean_result_competition_score_v1'},
    })
    high_kd_ref = 'https://www.google.com/search?q=Grow+a+Garden+wiki'
    high_kd = EvidenceObject('search-snapshot', 'serp-snapshot', high_kd_ref, metadata={
        'keyword_difficulty_measurement': {'source_reference': high_kd_ref, 'query': 'Grow a Garden wiki', 'ranked_results': (
            {'position': 1, 'domain': 'one.example', 'competition_score': 80}, {'position': 2, 'domain': 'two.example', 'competition_score': 90}, {'position': 3, 'domain': 'three.example', 'competition_score': 100},
        ), 'calculation_rule': 'mean_result_competition_score_v1'},
    })
    corpus_ref = 'https://example.test/keyword-corpus/grow-a-garden'
    corpus = EvidenceObject('keyword-corpus', 'keyword-corpus', corpus_ref, metadata={
        'long_tail_measurement': {'source_reference': corpus_ref, 'topic_scope': 'Grow a Garden', 'candidate_items': tuple(f'Grow a Garden guide {index}' for index in range(1, 13)), 'count_rule': 'qualified_long_tail_v1', 'result': 12},
    })
    money_ref = 'https://create.roblox.com/docs/production/monetization'
    monetization = EvidenceObject('create.roblox.com', 'platform-monetization-doc', money_ref, metadata={
        'monetization_path_measurement': {'source_reference': money_ref, 'path': 'ADS', 'evidence_kind': 'PLATFORM_AD_PROGRAM', 'validation_rule': 'recognized_monetization_path_v1', 'result': 'ADS'},
    })
    for item in (official, community, trend, low_kd, high_kd, corpus, monetization):
        ledger.append(item)

    source_producer = SourceInventoryProducer(ledger)
    trend_producer = TrendSignalProducer(ledger)
    kd_producer = KeywordDifficultyProducer(ledger)
    tail_producer = LongTailCountProducer(ledger)
    money_producer = MonetizationPathProducer(ledger)
    producers = FactProducerRegistry()
    for producer in (source_producer, trend_producer, kd_producer, tail_producer, money_producer):
        producers.register(producer.registration())
    production = FactProductionBoundary(producers, EvidenceReferenceValidator(ledger), FactProductionStore(database))
    quality_store = FactQualityStore(database)
    policies = FactQualityRegistry()
    policies.register(_policy('available_sources', ('source_inventory', 'method', 'captured_at'), ('source_records',)))
    policies.register(_policy('trend_up', ('query', 'region', 'time_window', 'source', 'method', 'captured_at'), ('source_reference', 'time_window', 'observations', 'comparison_rule', 'calculated_direction')))
    policies.register(_policy('keyword_difficulty', ('query', 'source', 'method', 'captured_at'), ('source_reference', 'query', 'ranked_results', 'calculation_rule', 'calculated_score')))
    policies.register(_policy('long_tail_count', ('query_family', 'source', 'method', 'captured_at'), ('topic_scope', 'source_reference', 'candidate_items', 'qualified_items', 'count_rule', 'calculated_count')))
    policies.register(_policy('monetization_path', ('path_scope', 'source', 'method', 'captured_at'), ('source_reference', 'path', 'evidence_kind', 'validation_rule', 'calculated_path')))
    quality = FactQualityBoundary(policies, quality_store)

    def produce(producer, evidence_ids):
        request = FactProductionRequest(producer.producer_id, producer.producer_version, producer.fact_id, '0.1', evidence_ids)
        artifact = producer.measure(request)
        produced = production.produce(request, artifact)
        _, accepted = quality.assess(produced, artifact)
        if accepted is None:
            raise RuntimeError(f'quality rejected {producer.fact_id}')
        return produced

    produced_trend = produce(trend_producer, (trend.id,))
    produce(source_producer, (official.id, community.id))
    produce(kd_producer, (low_kd.id,))
    produce(kd_producer, (high_kd.id,))
    produce(tail_producer, (corpus.id,))
    produce(money_producer, (monetization.id,))
    base_ids = (official.id, community.id, trend.id, low_kd.id, corpus.id, monetization.id)
    evaluator = MultiFactGateEvaluator(quality_store)
    full = evaluator.evaluate(CandidatePacket('Grow a Garden', 'assembled', base_ids, 'evidence-ledger', 0.5))
    missing = evaluator.evaluate(CandidatePacket('Grow a Garden Missing Trend', 'assembled', tuple(item for item in base_ids if item != trend.id), 'evidence-ledger', 0.5))
    failed = evaluator.evaluate(CandidatePacket('Grow a Garden High Competition', 'assembled', (official.id, community.id, trend.id, high_kd.id, corpus.id, monetization.id), 'evidence-ledger', 0.5))
    try:
        MultiFactGateEvaluator(_ProducedLookup(produced_trend)).evaluate(CandidatePacket('Injection', 'assembled', (trend.id,), 'evidence-ledger', 0.5))
    except TypeError:
        boundary = 'REJECTED'
    else:
        raise RuntimeError('ProducedFact bypass was accepted')
    if (full.overall_status, missing.overall_status, failed.overall_status) != (GateAssessmentStatus.PASS, GateAssessmentStatus.UNKNOWN, GateAssessmentStatus.FAIL):
        raise RuntimeError('unexpected multi-fact gate statuses')
    print(f'Phase 18.12 runtime verified: full={full.overall_status}, missing={missing.overall_status}, failed={failed.overall_status}, produced_input={boundary}')


if __name__ == '__main__':
    main()