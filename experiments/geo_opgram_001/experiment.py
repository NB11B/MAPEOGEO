"""Black-box finite action grammar with held-out word prediction."""
from itertools import product
from collections import deque

def compose(a,b): return tuple(a[b[i]] for i in range(len(a)))
def ident(n): return tuple(range(n))

class Oracle:
    def __init__(self,generators):
        self._generators=generators
        self.n=len(next(iter(generators.values())))
    def step(self,state,op): return self._generators[op][state]
    def walk(self,state,word):
        for a in word:state=self.step(state,a)
        return state

def reconstruct(oracle,names,witnessed_states):
    states=tuple(witnessed_states)
    if len(states)!=oracle.n or set(states)!=set(range(oracle.n)):
        return {'status':'abstain','reason':'unobserved_states'}
    inferred={}
    for a in names:
        p=tuple(oracle.step(s,a) for s in states)
        if sorted(p)!=list(range(oracle.n)):
            return {'status':'abstain','reason':'not_permutation'}
        inferred[a]=p
    return {'status':'qualified','generators':inferred}

def closure(gens):
    n=len(next(iter(gens.values())));E=ident(n)
    seen={E:()};front=deque([E])
    while front:
        p=front.popleft()
        for name,g in gens.items():
            q=compose(g,p)
            if q not in seen:
                seen[q]=seen[p]+(name,)
                front.append(q)
    return seen

def commutes(a,b):return compose(a,b)==compose(b,a)

def word_perm(gens,word):
    n=len(next(iter(gens.values())))
    p=ident(n)
    for a in word:p=compose(gens[a],p)
    return p

def qualify(oracle,names,states,held_out):
    fit=reconstruct(oracle,names,states)
    if fit['status']!='qualified':return fit
    gens=fit['generators'];group=closure(gens)
    errors=[(state,word) for state,word in held_out if word_perm(gens,word)[state]!=oracle.walk(state,word)]
    return {'status':'qualified' if not errors else 'fail',
            'group_size':len(group),
            'noncommuting':any(not commutes(a,b) for a,b in product(gens.values(),repeat=2)),
            'shortest_words':group,'held_out_tests':len(held_out),'errors':errors}

def c4():return Oracle({'r':(1,2,3,0),'s':(0,1,2,3)})
def d4():return Oracle({'r':(1,2,3,0),'f':(0,3,2,1)})
def v4():return Oracle({'a':(1,0,3,2),'b':(2,3,0,1)})

def trial(oracle,names):
    words=[w for length in range(1,6) for w in product(names,repeat=length)]
    heldout=[(s,w) for s in range(oracle.n) for w in words if len(w)>=3]
    r=qualify(oracle,names,range(oracle.n),heldout)
    return {k:v for k,v in r.items() if k!='shortest_words'}

if __name__=='__main__':
    for name,o,ops in [('C4',c4(),('r','s')),('V4',v4(),('a','b')),('D4',d4(),('r','f'))]:
        print(name,trial(o,ops))
