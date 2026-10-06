"""Symmetry-aware exhaustion certificates for bounded linear-space classes."""
from __future__ import annotations
from dataclasses import dataclass
from itertools import permutations
import hashlib,json


def canonical_lines(lines):
    return tuple(sorted((tuple(sorted(e)) for e in lines),key=lambda x:(len(x),x)))


def relabel(lines,perm):
    return canonical_lines(tuple(tuple(perm[v] for v in e) for e in lines))


def canonical_isomorph(n,lines):
    base=canonical_lines(lines)
    return min(relabel(base,p) for p in permutations(range(n)))


def digest_manifest(representatives):
    payload=json.dumps(tuple(representatives),separators=(",",":"))
    return hashlib.sha256(payload.encode()).hexdigest()


@dataclass(frozen=True)
class ExhaustionReplay:
    raw_count:int
    representative_count:int
    manifest_digest:str
    all_raw_covered:bool


def quotient_by_isomorphism(n,raw_instances):
    buckets={}
    for inst in raw_instances:
        canon=canonical_isomorph(n,inst)
        buckets.setdefault(canon,0)
        buckets[canon]+=1
    reps=tuple(sorted(buckets))
    return reps,buckets


def replay_exhaustion(n,raw_instances,representatives):
    reps=set(representatives)
    raw=tuple(raw_instances)
    covered=all(canonical_isomorph(n,x) in reps for x in raw)
    return ExhaustionReplay(len(raw),len(reps),digest_manifest(tuple(sorted(reps))),covered)
