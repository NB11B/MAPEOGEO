"""Global EFL closure state separates finite n=13 from unresolved effective cutoff."""
from dataclasses import dataclass
@dataclass(frozen=True)
class GlobalClosure:
    closed:bool; reason:str
def evaluate_global(n13_closed:bool,effective_cutoff:int|None,intermediate_closed:bool):
    if not n13_closed:return GlobalClosure(False,"N13_OPEN")
    if effective_cutoff is None:return GlobalClosure(False,"EFFECTIVE_CUTOFF_UNKNOWN")
    if effective_cutoff<=14:return GlobalClosure(True,"GLOBAL_CLOSED")
    if not intermediate_closed:return GlobalClosure(False,"INTERMEDIATE_N_OPEN")
    return GlobalClosure(True,"GLOBAL_CLOSED")
