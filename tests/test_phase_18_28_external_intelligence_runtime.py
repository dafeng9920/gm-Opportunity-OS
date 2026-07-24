import ast
import unittest
from pathlib import Path

from candidates import CandidateRepository
from core.schemas import CandidatePacket, EvidenceObject
from evidence import EvidenceLedger
from opportunity.analysis import AnalysisProposalReferenceValidator, AnalysisProposalStore, CapturedExternalIntelligenceAdapter, CognitionLinkStatus, CognitionProvenanceLink, CognitionProvenanceLinkService, CognitionProvenanceLinkStore, ExternalExecutionAuditStore, ExternalExecutionStatus, RawOutputArtifact, RawOutputStore
from opportunity.facts import FactProductionStore, MeasurementArtifact
from opportunity.gate_evaluation import MultiFactGateEvaluator


class ExternalIntelligenceRuntimeSpikeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database=Path('.opportunity-os') / f'phase-18.28-{self._testMethodName}.db'; self.database.unlink(missing_ok=True)
        self.ledger=EvidenceLedger(self.database); self.evidence=EvidenceObject('fixture-provider', 'external-fixture-input', 'https://example.test/roblox'); self.ledger.append(self.evidence)
        self.candidate=CandidatePacket('Grow a Garden', 'captured fixture candidate', (self.evidence.id,), 'phase-18.28', .5); self.candidates=CandidateRepository(self.database); self.candidates.create(self.candidate)
        self.measurement=MeasurementArtifact('fixture-request','fixture-producer','0.1','trend_up','0.1',(self.evidence.id,),'fixture-measurement',{'series_points': 1},False,{'source':'fixture'})
        self.measurements=FactProductionStore(self.database); self.measurements.append_measurement(self.measurement)
        self.proposals=AnalysisProposalStore(self.database); self.raws=RawOutputStore(self.database); self.audits=ExternalExecutionAuditStore(self.database)
        self.references=AnalysisProposalReferenceValidator(self.measurements,self.ledger)
        self.adapter=CapturedExternalIntelligenceAdapter(self.raws,self.candidates,self.references,self.proposals,self.audits)
        self.links=CognitionProvenanceLinkStore(self.database); self.link_service=CognitionProvenanceLinkService(self.proposals,self.references,self.measurements,self.links)

    def payload(self, **changes):
        item={'requested_fact_id':'trend_up','requested_fact_version':'0.1','measurement_artifact_ids':[self.measurement.artifact_id],'evidence_ids':[self.evidence.id],'analysis_summary':'Captured model response requests review only.','assumptions':['fixture is structured'],'uncertainty':['no fact value is inferred'],'missing_information':['authorized producer review']}; item.update(changes); return item
    def raw(self, payload):
        artifact=RawOutputArtifact('fixture-external-provider','fixture-model','external-fixture-adapter@0.1','fixture://response/valid','phase-18.28-config-v1','fixture-model-release-1','prompt://phase-18.28/v1'); self.raws.append(artifact,payload); return artifact

    def test_valid_fixture_is_preserved_normalized_and_linked_as_non_authoritative(self):
        raw=self.raw(self.payload()); result=self.adapter.normalize(raw.raw_output_id,self.candidate.id)
        self.assertEqual(self.raws.get_payload(raw.raw_output_id), self.payload())
        self.assertEqual(result.audit.status,ExternalExecutionStatus.SUCCEEDED); self.assertIsNotNone(result.proposal)
        proposal=result.proposal; assert proposal is not None
        self.assertEqual(proposal.status.value,'NON_AUTHORITATIVE'); self.assertEqual(proposal.model_identity,'fixture-model'); self.assertEqual(proposal.model_version,'fixture-model-release-1'); self.assertEqual(proposal.runtime_identity,'external-fixture-adapter@0.1'); self.assertEqual(proposal.prompt_reference_id,'prompt://phase-18.28/v1')
        link=CognitionProvenanceLink(proposal.proposal_id,proposal.measurement_artifact_ids,proposal.evidence_ids,'external-fixture-adapter','0.1',CognitionLinkStatus.PROPOSED)
        self.link_service.record(link); self.assertEqual(self.links.get(link.cognition_link_id),link)

    def test_invalid_text_and_score_fixture_create_raw_output_and_audit_only(self):
        for payload in ('this game is definitely a great opportunity', {'opportunity_score':95}):
            raw=self.raw(payload); result=self.adapter.normalize(raw.raw_output_id,self.candidate.id)
            self.assertEqual(result.audit.status,ExternalExecutionStatus.REJECTED); self.assertIsNone(result.proposal); self.assertIsNone(result.audit.proposal_id); self.assertEqual(self.raws.get_payload(raw.raw_output_id),payload)

    def test_external_adapter_has_no_fact_or_governance_path(self):
        for method in ('produce','create_fact','accept_fact','evaluate_gate','write_judge','write_triad','write_decision'):
            self.assertFalse(hasattr(self.adapter,method))
        tree=ast.parse(Path('opportunity/analysis/external.py').read_text(encoding='utf-8-sig')); imports=[node.module or '' for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
        for forbidden in ('opportunity.facts','opportunity.fact_quality','opportunity.gate_evaluation','opportunity.judge','opportunity.triad_evaluation'):
            self.assertNotIn(forbidden,imports)
        raw=self.raw(self.payload()); proposal=self.adapter.normalize(raw.raw_output_id,self.candidate.id).proposal
        with self.assertRaisesRegex(TypeError,'AcceptedFact lookup'): MultiFactGateEvaluator(proposal)  # type: ignore[arg-type]

    def test_invalid_references_are_rejected_without_proposal(self):
        raw=self.raw(self.payload(evidence_ids=['fabricated-evidence'])); result=self.adapter.normalize(raw.raw_output_id,self.candidate.id)
        self.assertEqual(result.audit.status,ExternalExecutionStatus.REJECTED); self.assertIsNone(result.proposal)

if __name__=='__main__': unittest.main()
