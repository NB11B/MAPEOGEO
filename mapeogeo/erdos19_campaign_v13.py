"""Durable 22-bucket campaign state machine."""
from __future__ import annotations
from dataclasses import dataclass,asdict
import json,hashlib
from pathlib import Path
from .erdos19_bucket_uow_v12 import initial_buckets,update_bucket,all_closed

@dataclass(frozen=True)
class CampaignCheckpoint:
    states:tuple
    manifest:str

def checkpoint(states,path):
    data=[asdict(x) for x in states]
    manifest=hashlib.sha256(json.dumps(data,separators=(",",":"),sort_keys=True).encode()).hexdigest()
    Path(path).write_text(json.dumps({"manifest":manifest,"states":data},indent=2))
    return CampaignCheckpoint(tuple(states),manifest)

def resume(path):
    from .erdos19_bucket_uow_v12 import BucketState
    obj=json.loads(Path(path).read_text())
    states=tuple(BucketState(**x) for x in obj["states"])
    fresh=hashlib.sha256(json.dumps([asdict(x) for x in states],separators=(",",":"),sort_keys=True).encode()).hexdigest()
    if fresh!=obj["manifest"]:raise ValueError("CHECKPOINT_DIGEST_MISMATCH")
    return CampaignCheckpoint(states,fresh)
