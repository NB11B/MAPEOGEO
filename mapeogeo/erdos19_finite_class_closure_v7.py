"""Compose exhaustion replay with per-representative coloring co-certificates."""
from __future__ import annotations
from dataclasses import dataclass
from .erdos19_exhaustion_cert_v7 import quotient_by_isomorphism,replay_exhaustion
from .erdos19_quantified_cocert_v6 import certify_instance


@dataclass(frozen=True)
class ClosedFiniteClass:
    raw_count:int
    representative_count:int
    manifest_digest:str
    all_representatives_colored:bool
    raw_coverage_verified:bool
    state:str


def close_finite_class(n,raw_instances):
    raw=tuple(raw_instances)
    reps,_=quotient_by_isomorphism(n,raw)
    replay=replay_exhaustion(n,raw,reps)
    certs=tuple(certify_instance(n,rep) for rep in reps)
    colored=all(c.verified for c in certs)
    state="FINITE_CLASS_CLOSED" if replay.all_raw_covered and colored else "OPEN"
    return ClosedFiniteClass(len(raw),len(reps),replay.manifest_digest,colored,replay.all_raw_covered,state)
