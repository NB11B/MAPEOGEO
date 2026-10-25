"""Repeated application of the same opaque operator resolves C4/V4 ambiguity."""
import json
from ambiguity import cyclic_four,klein_four,observations,permutation_order
def intervention_signature(ops):
    return tuple(sorted(permutation_order(p) for p in ops))
def run():
    c,v=cyclic_four(),klein_four()
    return {"unlabeled_collision":observations(c)==observations(v),
       "cyclic_orders":intervention_signature(c),
       "klein_orders":intervention_signature(v),
       "distinguishable_with_same_operator_interventions":
          intervention_signature(c)!=intervention_signature(v),
       "cyclic_order_two_count":sum(permutation_order(p)==2 for p in c),
       "klein_order_two_count":sum(permutation_order(p)==2 for p in v)}
if __name__=="__main__":print(json.dumps(run(),indent=2))
