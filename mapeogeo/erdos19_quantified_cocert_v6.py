"""Bounded FORALL->EXISTS co-certificate campaign for Erdős #19."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
from .erdos19_frontier13_v5 import exact_edge_coloring,verify_edge_coloring,verify_linear_space


@dataclass(frozen=True)
class ColoringCoCertificate:
    n:int
    instance_digest:str
    colors:tuple[int,...]
    verified:bool


@dataclass(frozen=True)
class QuantifiedCampaign:
    generated:int
    verified:int
    counterexample:tuple[frozenset[int],...]|None
    certificates:tuple[ColoringCoCertificate,...]
    state:str


def canonical_lines(lines):
    return tuple(sorted((tuple(sorted(e)) for e in lines),key=lambda x:(len(x),x)))


def digest_instance(n,lines):
    payload=json.dumps({"n":n,"lines":canonical_lines(lines)},separators=(",",":"),sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def certify_instance(n,lines):
    lines=tuple(map(frozenset,canonical_lines(lines)))
    if not verify_linear_space(n,lines):
        raise ValueError("instance is not a pair-covering linear space")
    colors=exact_edge_coloring(n,lines)
    ok=verify_edge_coloring(n,lines,colors)
    return ColoringCoCertificate(n,digest_instance(n,lines),tuple(colors or ()),ok)


def run_campaign(n,instances):
    certs=[]
    for raw in instances:
        lines=tuple(map(frozenset,canonical_lines(raw)))
        cert=certify_instance(n,lines)
        certs.append(cert)
        if not cert.verified:
            return QuantifiedCampaign(len(certs),len(certs)-1,lines,tuple(certs),"COUNTEREXAMPLE")
    return QuantifiedCampaign(len(certs),len(certs),None,tuple(certs),"BOUNDED_VERIFIED")
