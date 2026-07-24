from candidates import EvidenceReferenceValidator
from opportunity.facts import FactProducer, FactProducerRegistry, FactProductionBoundary, FactProductionRequest, FactProductionStore, FactSupport, MeasurementArtifact
from opportunity.fact_quality import FactQualityBoundary, FactQualityPolicy, FactQualityRegistry, FactQualityStore

FACTS=(("trend_up",True),("keyword_difficulty",20),("long_tail_count",12),("available_sources",("official","community")),("monetization_path","ads"))
def provenance(f): return {"trend_up":{"query":"fixture","region":"US","time_window":"7d","source":"fixture","method":"fixture-v1","captured_at":"2026-01-01"},"keyword_difficulty":{"query":"fixture","source":"fixture","method":"fixture-v1","captured_at":"2026-01-01"},"long_tail_count":{"query_family":"fixture","source":"fixture","method":"fixture-v1","captured_at":"2026-01-01"},"available_sources":{"source_inventory":"fixture","method":"fixture-v1","captured_at":"2026-01-01"},"monetization_path":{"path_scope":"site","source":"fixture","method":"fixture-v1","captured_at":"2026-01-01"}}[f]
def produce_all(ledger,database,evidence):
 ps=FactProductionStore(database); pr=FactProducerRegistry(); pr.register(FactProducer('fixture.fact-producer','0.1',tuple(FactSupport(f,'0.1',('fixture-v1',)) for f,_ in FACTS))); pb=FactProductionBoundary(pr,EvidenceReferenceValidator(ledger),ps)
 qs=FactQualityStore(database); qr=FactQualityRegistry(); qb=FactQualityBoundary(qr,qs)
 for i,(f,v) in enumerate(FACTS):
  refs=(evidence[0].id,evidence[1].id) if f=='available_sources' else (evidence[i].id,)
  qr.register(FactQualityPolicy(f'policy.{f}',f,'0.1',tuple(provenance(f)),('fixture',),len(refs),('complete',),'0.1'))
  r=FactProductionRequest('fixture.fact-producer','0.1',f,'0.1',refs); a=MeasurementArtifact(r.request_id,r.producer_id,r.producer_version,f,'0.1',refs,'fixture-v1',{'fixture':True},v,provenance(f)); p=pb.produce(r,a); assessment,accepted=qb.assess(p,a); assert accepted is not None
 return qs