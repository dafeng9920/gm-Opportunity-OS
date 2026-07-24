"""Runtime evidence: Grow a Garden source inventory reaches the data gate."""
from pathlib import Path

from candidates import EvidenceReferenceValidator
from core.schemas import CandidatePacket, EvidenceObject
from evidence import EvidenceLedger
from opportunity.fact_quality import FactQualityBoundary, FactQualityPolicy, FactQualityRegistry, FactQualityStore
from opportunity.facts import FactProducerRegistry, FactProductionBoundary, FactProductionRequest, FactProductionStore, SourceInventoryProducer
from opportunity.gates import OpportunityGateEngine


def main() -> None:
    database = Path('.opportunity-os') / 'phase18-source-inventory.db'
    if database.exists():
        database.unlink()
    ledger = EvidenceLedger(database)
    official = EvidenceObject(
        'roblox.com', 'official-game-entity',
        'https://www.roblox.com/games/126884695634066/Grow-a-Garden',
        metadata={'game_name': 'Grow a Garden', 'phase': '18.7'},
    )
    community = EvidenceObject(
        'growagarden.wiki', 'community-update-log',
        'https://growagarden.wiki/Update_Log/1.07.0',
        metadata={'game_name': 'Grow a Garden', 'phase': '18.7'},
    )
    ledger.append(official)
    ledger.append(community)
    evidence_ids = (official.id, community.id)
    candidate = CandidatePacket('Grow a Garden', 'evidence-backed candidate', evidence_ids, 'evidence-ledger', 0.5)

    producer = SourceInventoryProducer(ledger)
    producers = FactProducerRegistry()
    producers.register(producer.registration())
    request = FactProductionRequest(producer.producer_id, producer.producer_version, 'available_sources', '0.1', evidence_ids)
    artifact = producer.measure(request)
    produced = FactProductionBoundary(producers, EvidenceReferenceValidator(ledger), FactProductionStore(database)).produce(request, artifact)

    policies = FactQualityRegistry()
    policies.register(FactQualityPolicy(
        'available-sources-quality', 'available_sources', '0.1',
        ('source_inventory', 'method', 'captured_at'), ('source_records',), 2,
        ('explicit-classification',), '0.1',
    ))
    assessment, accepted = FactQualityBoundary(policies, FactQualityStore(database)).assess(produced, artifact)
    if accepted is None:
        raise RuntimeError(f'quality assessment failed: {assessment.assessment_reason}')
    gate = OpportunityGateEngine().evaluate(candidate, 'data_availability', {'available_sources': accepted.fact.value})
    print(f'Phase 18.7 runtime verified: fact={accepted.fact.fact_id}@{accepted.fact.fact_version}, quality={assessment.status}, gate={gate.status}')


if __name__ == '__main__':
    main()