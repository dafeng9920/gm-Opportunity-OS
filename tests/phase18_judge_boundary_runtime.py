"""Runtime evidence: accepted-fact Gate Assessment enters only the static Judge boundary."""
from pathlib import Path

from candidates import CandidateRepository, EvidenceReferenceValidator
from core.schemas import CandidatePacket, EvidenceObject
from evidence import EvidenceLedger
from opportunity.assessments import AssessmentRecordWriter, JudgeAssessmentStore
from opportunity.evaluation.contracts import EvaluationFact, EvaluationFactCategory, FactVerification
from opportunity.fact_quality import AcceptedFact
from opportunity.gate_evaluation import MultiFactGateEvaluator
from opportunity.judge import GateAssessmentJudgeInputAssembler, StaticJudgeAssessmentRuntime


class _AcceptedLookup:
    def __init__(self, items): self._items = tuple(items)
    def list_accepted_for_evidence_ids(self, evidence_ids): return self._items


def _fact(fact_id, category, value, evidence_ids, provenance):
    return EvaluationFact(fact_id, category, value, evidence_ids, 1.0, FactVerification.EVIDENCE_BACKED, '0.1', provenance)


def main() -> None:
    database = Path('.opportunity-os') / 'phase18-judge-boundary.db'
    if database.exists(): database.unlink()
    ledger = EvidenceLedger(database)
    evidence = tuple(EvidenceObject('fixture', 'accepted-fact-scope', f'https://example.test/{index}') for index in range(6))
    for item in evidence: ledger.append(item)
    candidate = CandidatePacket('Grow a Garden', 'assembled accepted facts', tuple(item.id for item in evidence), 'evidence-ledger', 0.5)
    candidates = CandidateRepository(database)
    candidates.create(candidate)
    ids = candidate.evidence_ids
    facts = (
        _fact('available_sources', EvaluationFactCategory.DATA, ('official','community'), ids[:2], {'source_inventory':'fixture','method':'fixture-v1','captured_at':'2026-01-01'}),
        _fact('trend_up', EvaluationFactCategory.DEMAND, True, (ids[2],), {'query':'fixture','region':'US','time_window':'7d','source':'fixture','method':'fixture-v1','captured_at':'2026-01-01'}),
        _fact('keyword_difficulty', EvaluationFactCategory.COMPETITION, 20, (ids[3],), {'query':'fixture','source':'fixture','method':'fixture-v1','captured_at':'2026-01-01'}),
        _fact('long_tail_count', EvaluationFactCategory.CONTENT, 12, (ids[4],), {'query_family':'fixture','source':'fixture','method':'fixture-v1','captured_at':'2026-01-01'}),
        _fact('monetization_path', EvaluationFactCategory.MONETIZATION, 'ADS', (ids[5],), {'path_scope':'ADS','source':'fixture','method':'fixture-v1','captured_at':'2026-01-01'}),
    )
    accepted = tuple(AcceptedFact(f'accepted-{index}', f'produced-{index}', f'quality-{index}', '0.1', fact) for index, fact in enumerate(facts, 1))
    lookup = _AcceptedLookup(accepted)
    gate_record = MultiFactGateEvaluator(lookup).evaluate(candidate)
    judge_input = GateAssessmentJudgeInputAssembler(candidates, EvidenceReferenceValidator(ledger), lookup).assemble(gate_record)
    assessment_store = JudgeAssessmentStore(database)
    assessment_record = StaticJudgeAssessmentRuntime(AssessmentRecordWriter(assessment_store)).assess(judge_input)
    if assessment_store.get(assessment_record.assessment_id) != assessment_record:
        raise RuntimeError('static assessment record did not persist')
    print(f'Phase 18.13 runtime verified: gate={gate_record.overall_status}, assessment_source={assessment_record.source}, runtime={assessment_record.runtime_id}')


if __name__ == '__main__':
    main()