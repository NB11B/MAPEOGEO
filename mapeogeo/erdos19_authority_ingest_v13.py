"""Digest-bound ingestion of external mathematical authority artifacts."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
from pathlib import Path
from .erdos19_authority_v12 import AuthorityDependency

@dataclass(frozen=True)
class AuthoritySpec:
    id:str
    expected_sha256:str|None=None

def ingest_authority(spec:AuthoritySpec,path):
    p=Path(path)
    if not p.is_file():return AuthorityDependency(spec.id,str(p),False,"")
    d=hashlib.sha256(p.read_bytes()).hexdigest()
    ok=spec.expected_sha256 is None or d==spec.expected_sha256
    return AuthorityDependency(spec.id,str(p),ok,d if ok else "")
