"""Final finite n=13 closure gate: all independent authorities must be present."""
from dataclasses import dataclass
from .erdos19_bucket_uow_v12 import all_closed
from .erdos19_authority_v12 import n13_authority_closed

@dataclass(frozen=True)
class N13Closure:
    closed:bool
    reason:str

def evaluate_n13_closure(bucket_states,authority_deps):
    if not all_closed(bucket_states):return N13Closure(False,"BUCKETS_OPEN")
    if not n13_authority_closed(authority_deps):return N13Closure(False,"AUTHORITY_OPEN")
    return N13Closure(True,"N13_FINITE_CLOSURE")
