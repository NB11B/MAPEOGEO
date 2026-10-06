"""Named authority dependencies required to promote finite n=13 closure."""
from dataclasses import dataclass
@dataclass(frozen=True)
class AuthorityDependency:
    id:str; description:str; verified:bool=False; artifact_digest:str=""
REQUIRED_IDS=("EFL_TO_EFL_PRIME_EQUIVALENCE","N13_OUTSIDE_BUCKETS_THEOREM14","DEGREE13_CORE_REDUCTION")
def n13_authority_closed(deps):
    d={x.id:x for x in deps}
    return all(i in d and d[i].verified and d[i].artifact_digest for i in REQUIRED_IDS)
