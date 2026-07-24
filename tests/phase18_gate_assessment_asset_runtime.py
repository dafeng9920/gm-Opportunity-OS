"""Runtime evidence: Accepted Facts become a persisted Gate Assessment Asset before JudgeInput."""
from pathlib import Path

from candidates import CandidateRepository, EvidenceReferenceValidator
from core.schemas import CandidatePacket, EvidenceObject
from evidence import EvidenceLedger
from opportunity.evaluation.contracts import EvaluationFact, EvaluationFactCategory, FactVerification
from opportunity.fact_quality import AcceptedFact
from opportunity.gate_evaluation import GateAssessmentAssetStore, GateAssessmentAssetWriter, GateAssessmentStatus, MultiFactGateEvaluator
from opportunity.judge import GateAssessmentJudgeInputAssembler


class AcceptedLookup:
    def __init__(self, facts): self._facts = tuple(facts)
    def list_accepted_for_evidence_ids(self, evidence_ids): return self._facts


def main() -> None:
    database = Path('.opportunity-os') / 'phase18-gate-assessment-asset.db'
    if database.exists(): database.unlink()
    ledger = EvidenceLedger(database)
    evidence = tuple(EvidenceObject('phase18-runtime', 'fact-evidence', f'https://example.test/{index}') for index in range(6))
    for item in evidence: ledger.append(item)
    candidate = CandidatePacket('Grow a Garden', 'evidence-backed', tuple(item.id for item in evidence), 'phase18-runtime', .5)
    candidates = CandidateRepository(database)
    candidates.create(candidate)
    ids = candidate.evidence_ids

    def fact(name, category, value, evidence_ids, provenance):
        return EvaluationFact(name, category, value, evidence_ids, 1.0, FactVerification.EVIDENCE_BACKED, '0.1', provenance)

    definitions = (
        fact('available_sources', EvaluationFactCategory.DATA, ('official', 'community'), ids[:2], {'source_inventory':'runtime','method':'v1','captured_at':'2026-07-24'}),
        fact('trend_up', EvaluationFactCategory.DEMAND, True, (ids[2],), {'query':'Grow a Garden','region':'US','time_window':'7d','source':'runtime','method':'v1','captured_at':'2026-07-24'}),
        fact('keyword_difficulty', EvaluationFactCategory.COMPETITION, 20, (ids[3],), {'query':'Grow a Garden codes','source':'runtime','method':'v1','captured_at':'2026-07-24'}),
        fact('long_tail_count', EvaluationFactCategory.CONTENT, 12, (ids[4],), {'query_family':'Grow a Garden','source':'runtime','method':'v1','captured_at':'2026-07-24'}),
        fact('monetization_path', EvaluationFactCategory.MONETIZATION, 'ADS', (ids[5],), {'path_scope':'ADS','source':'runtime','method':'v1','captured_at':'2026-07-24'}),
    )
    accepted = tuple(AcceptedFact(f'accepted-{index}', f'produced-{index}', f'quality-{index}', '0.1', item) for index, item in enumerate(definitions, 1))
    lookup = AcceptedLookup(accepted)
    record = MultiFactGateEvaluator(lookup).evaluate(candidate)
    store = GateAssessmentAssetStore(database)
    asset = GateAssessmentAssetWriter(store, candidates, lookup).append(record)
    judge_input = GateAssessmentJudgeInputAssembler(candidates, EvidenceReferenceValidator(ledger), lookup, store).assemble(asset)
    if record.overall_status is not GateAssessmentStatus.PASS or store.get(asset.asset_id) != asset:
        raise RuntimeError('gate assessment asset was not persisted')
    if judge_input.candidate.id != candidate.id:
        raise RuntimeError('judge input did not retain candidate lineage')
    print(f'Phase 18.14.1 runtime verified: gate={asset.assessment_status}, asset={asset.asset_id}, judge_input={judge_input.candidate.id}')


if __name__ == '__main__':
    main()
