"""Bucketized UoW state for the 22 unresolved n=13 line-count buckets."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json

@dataclass(frozen=True)
class BucketState:
    m:int
    generation_manifest:str=""
    exhaustion_certificate:str=""
    coloring_manifest:str=""
    status:str="PENDING"

def initial_buckets():
    return tuple(BucketState(m) for m in range(33,55))

def update_bucket(states,m,**changes):
    out=[]
    for s in states:
        if s.m!=m:out.append(s);continue
        data=s.__dict__.copy();data.update(changes);out.append(BucketState(**data))
    return tuple(out)

def bucket_manifest(states):
    payload=[s.__dict__ for s in sorted(states,key=lambda x:x.m)]
    return hashlib.sha256(json.dumps(payload,separators=(",",":"),sort_keys=True).encode()).hexdigest()

def all_closed(states):
    return len(states)==22 and all(s.status=="CLOSED" and s.generation_manifest and s.exhaustion_certificate and s.coloring_manifest for s in states)
