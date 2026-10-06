"""Concrete process adapters for production canonical/coloring/proof tools."""
from __future__ import annotations
import hashlib,json,subprocess,tempfile
from pathlib import Path
from .erdos19_backend_contracts_v12 import CanonicalResult,ColoringResult

def _run(argv,timeout=3600):
    p=subprocess.run(argv,capture_output=True,text=True,timeout=timeout,check=False)
    return p.returncode,p.stdout,p.stderr

class ExternalCanonicalAdapter:
    def __init__(self,command=("dreadnaut",)): self.command=tuple(command)
    def available(self):
        try: return _run([self.command[0],"-help"],10)[0] in (0,1,2)
        except (FileNotFoundError,subprocess.TimeoutExpired): return False
    def canonicalize(self,n,lines):
        # Stable incidence payload is retained even when an external backend is unavailable.
        payload=json.dumps({"n":n,"lines":sorted(sorted(e) for e in lines)},separators=(",",":"))
        if not self.available():
            return CanonicalResult(hashlib.sha256(payload.encode()).hexdigest(),"external-canonical",None,False)
        # Authority remains false until backend-specific canonical output parser/checker is configured.
        return CanonicalResult(hashlib.sha256(payload.encode()).hexdigest(),"dreadnaut",None,False)

class ExternalColoringAdapter:
    def __init__(self,solver=("cadical",),proof_checker=("drat-trim",)):
        self.solver=tuple(solver);self.proof_checker=tuple(proof_checker)
    def available(self):
        try:return _run([self.solver[0],"--version"],10)[0]==0
        except (FileNotFoundError,subprocess.TimeoutExpired):return False
    def verify_drat(self,cnf,proof):
        try:return _run([self.proof_checker[0],str(cnf),str(proof)],3600)[0]==0
        except (FileNotFoundError,subprocess.TimeoutExpired):return False
