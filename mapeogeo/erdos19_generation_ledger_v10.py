"""Replayable generation ledger for bounded linear-space canonical augmentation."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
from .erdos19_exact_canonical_v8 import exact_canonical_digest
from .erdos19_generator_validation_v9 import candidate_lines,admissible_add,complete_pair_cover


@dataclass(frozen=True)
class AugmentationDecision:
    line:tuple[int,...]
    child_digest:str
    disposition:str  # ACCEPT or DUPLICATE
    representative_digest:str


@dataclass(frozen=True)
class GenerationNode:
    node_digest:str
    terminal:bool
    decisions:tuple[AugmentationDecision,...]
    seal_digest:str


def seal_node(node_digest,terminal,decisions):
    payload=json.dumps({
      "node":node_digest,"terminal":terminal,
      "decisions":[(d.line,d.child_digest,d.disposition,d.representative_digest) for d in decisions],
    },separators=(",",":"),sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def build_node(n,parent,max_states=200000):
    pd,_=exact_canonical_digest(n,parent,max_states=max_states)
    if complete_pair_cover(n,parent):
        seal=seal_node(pd,True,())
        return GenerationNode(pd,True,(),seal),{}
    seen={};decisions=[];children={}
    for line in candidate_lines(n):
        if not admissible_add(parent,line):continue
        child=tuple(parent)+(line,)
        cd,_=exact_canonical_digest(n,child,max_states=max_states)
        if cd in seen:
            decisions.append(AugmentationDecision(tuple(sorted(line)),cd,"DUPLICATE",cd))
        else:
            seen[cd]=child;children[cd]=child
            decisions.append(AugmentationDecision(tuple(sorted(line)),cd,"ACCEPT",cd))
    decisions=tuple(sorted(decisions,key=lambda d:(d.line,d.child_digest,d.disposition)))
    seal=seal_node(pd,False,decisions)
    return GenerationNode(pd,False,decisions,seal),children


def replay_node(n,parent,node,max_states=200000):
    fresh,children=build_node(n,parent,max_states=max_states)
    return fresh==node,children


def build_generation_ledger(n,max_states=200000):
    root=()
    stack=[root];nodes={};parents={};leaves={}
    while stack:
        parent=stack.pop()
        node,children=build_node(n,parent,max_states=max_states)
        if node.node_digest in nodes:continue
        nodes[node.node_digest]=node;parents[node.node_digest]=parent
        if node.terminal:leaves[node.node_digest]=parent
        else:stack.extend(children.values())
    manifest=hashlib.sha256(json.dumps(sorted((d,nodes[d].seal_digest) for d in nodes),separators=(",",":")).encode()).hexdigest()
    return nodes,parents,leaves,manifest


def replay_generation_ledger(n,nodes,parents,manifest,max_states=200000):
    for d,node in nodes.items():
        if d not in parents:return False
        ok,_=replay_node(n,parents[d],node,max_states=max_states)
        if not ok:return False
    fresh=hashlib.sha256(json.dumps(sorted((d,nodes[d].seal_digest) for d in nodes),separators=(",",":")).encode()).hexdigest()
    return fresh==manifest
