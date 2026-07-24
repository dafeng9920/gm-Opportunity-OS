from .contracts import FactQualityPolicy
class FactQualityRegistry:
 def __init__(self): self._items={}
 def register(self, policy):
  key=(policy.fact_id,policy.fact_version,policy.version)
  if key in self._items: raise ValueError('quality policy already registered')
  self._items[key]=policy
 def get(self,fact_id,fact_version,version): return self._items.get((fact_id,fact_version,version))