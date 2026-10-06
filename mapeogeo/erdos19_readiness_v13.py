"""Machine-readable production readiness audit."""
from dataclasses import dataclass
from .erdos19_external_adapters_v13 import ExternalCanonicalAdapter,ExternalColoringAdapter
@dataclass(frozen=True)
class Readiness:
    ready:bool; missing:tuple[str,...]
def audit():
    missing=[]
    if not ExternalCanonicalAdapter().available():missing.append("CANONICAL_BACKEND")
    c=ExternalColoringAdapter()
    if not c.available():missing.append("SAT_BACKEND")
    return Readiness(not missing,tuple(missing))
