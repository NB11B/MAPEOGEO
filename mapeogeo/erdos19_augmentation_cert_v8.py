"""Parent/child augmentation certificates using exact bounded canonical labels."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
from .erdos19_exact_canonical_v8 import exact_canonical_digest


@dataclass(frozen=True)
class AugmentationCertificate:
    parent_digest:str
    child_digest:str
    added_line:tuple[int,...]
    canonical_states:int
    certificate_digest:str


def certify_augmentation(n,parent,added_line,max_states=200000):
    parent=tuple(map(frozenset,parent));added=frozenset(added_line)
    child=parent+(added,)
    pd,ps=exact_canonical_digest(n,parent,max_states=max_states)
    cd,cs=exact_canonical_digest(n,child,max_states=max_states)
    payload=f"{pd}|{cd}|{tuple(sorted(added))}|{ps+cs}"
    digest=hashlib.sha256(payload.encode()).hexdigest()
    return AugmentationCertificate(pd,cd,tuple(sorted(added)),ps+cs,digest)


def replay_augmentation(n,parent,cert,max_states=200000):
    fresh=certify_augmentation(n,parent,cert.added_line,max_states=max_states)
    return fresh==cert
