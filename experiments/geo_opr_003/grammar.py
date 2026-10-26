"""Bounded typed-expression search; full local copy: GEO-OPR-003."""
from dataclasses import dataclass
from itertools import product
@dataclass(frozen=True)
class Expr:
    op:str
    args:tuple=()
    def eval(self,x,y):
        if self.op=="x":return x
        if self.op=="y":return y
        if self.op=="one":return 1
        if self.op=="succ":return self.args[0].eval(x,y)+1
        a,b=(e.eval(x,y) for e in self.args)
        if self.op=="add":return a+b
        if self.op=="mul":return a*b
        raise ValueError(self.op)
    def render(self):
        return self.op if not self.args else self.op+"("+",".join(e.render() for e in self.args)+")"
LEAVES=(Expr("x"),Expr("y"),Expr("one"))
def enumerate_exprs(depth=2,cap=3000):
    levels=[list(LEAVES)]
    for _ in range(depth):
        pool=[e for level in levels for e in level]
        nodes=[Expr("succ",(e,)) for e in levels[-1]]
        nodes.extend(Expr(op,(a,b)) for op in ("add","mul") for a,b in product(pool,pool) if a in levels[-1] or b in levels[-1])
        unique={}
        for e in nodes:
            signature=tuple(e.eval(x,y) for x in (1,2,3) for y in (1,2,3))
            unique.setdefault(signature,e)
            if len(unique)>=cap:break
        levels.append(list(unique.values()))
    return [e for level in levels for e in level]
def discover(samples,depth=2):
    candidates=[e for e in enumerate_exprs(depth) if all(e.eval(x,y)==z for x,y,z in samples)]
    return candidates or None
def benchmark():
    train=[(x,y,x*y+x) for x in (1,2,3) for y in (1,2,3)]
    matched=discover(train) or []
    hold=[(x,y,x*y+x) for x in range(4,11) for y in range(4,11)]
    qualified=[e for e in matched if all(e.eval(x,y)==z for x,y,z in hold)]
    return dict(candidate_count=len(matched),holdout_count=len(hold),qualified_count=len(qualified),
                selected=qualified[0].render() if qualified else None,all_holdout_pass=bool(qualified))
if __name__=="__main__":
    import json
    print(json.dumps(benchmark(),indent=2))
