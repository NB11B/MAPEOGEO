"""MAPEOGEO compiled-operator / learned-controller sandbox pilot.

Requires Python 3.10+, numpy, torch. This is a research prototype, not
an integration with certified MAPEOGEO/Lean or the existing spectral LM.
"""
from __future__ import annotations
import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

OPS = ('ADD8','XOR8','EQ8','GEO_GP3')
PROMPTS = {'ADD8':['sum','plus','add'], 'XOR8':['exclusive','xor','parity'],
           'EQ8':['same','equal','compare'], 'GEO_GP3':['clifford','geometric','bladeproduct']}
VOCAB = {w:i+1 for i,w in enumerate(sorted({x for a in PROMPTS.values() for x in a}))}

# Exact on {0,1} inputs. Implement Boolean gates as fixed affine/ReLU circuits.
def and_gate(a,b): return F.relu(a+b-1)
def or_gate(a,b): return (a+b)-and_gate(a,b)
def xor_gate(a,b): return a+b-2*and_gate(a,b)

def bits8(x: int) -> torch.Tensor:
    if not 0 <= x < 256: raise ValueError('8-bit operand required')
    return torch.tensor([(x>>i)&1 for i in range(8)],dtype=torch.float64)

def unbits(b: torch.Tensor) -> int:
    return sum(int(round(float(v)))<<i for i,v in enumerate(b))

class CompiledAdd8(nn.Module):
    """No learned parameters: eight ripple-carry exact binary full adders."""
    def forward(self,a: torch.Tensor,b: torch.Tensor) -> torch.Tensor:
        carry=torch.zeros_like(a[0])
        out=[]
        for i in range(8):
            t=xor_gate(a[i],b[i])
            out.append(xor_gate(t,carry))
            carry=or_gate(and_gate(a[i],b[i]),and_gate(t,carry))
        return torch.stack(out)

class CompiledXor8(nn.Module):
    def forward(self,a,b): return xor_gate(a,b)

class CompiledEq8(nn.Module):
    def forward(self,a,b):
        # equality of 8-bit vectors, exact binary output
        mismatches=xor_gate(a,b)
        any_bit=torch.zeros((),dtype=a.dtype,device=a.device)
        for bit in mismatches: any_bit=or_gate(any_bit,bit)
        return 1-any_bit

def gp_sign_blade(a: int,b: int,signature=(1,1,1)) -> tuple[int,int]:
    """Clifford basis product: e_A e_B = sign * e_(A xor B)."""
    n=len(signature)
    if not (0<=a<1<<n and 0<=b<1<<n): raise ValueError('bad blade')
    sign=1
    for i in range(n):
        if (a>>i)&1:
            if (b & ((1<<i)-1)).bit_count()%2: sign=-sign
            if (b>>i)&1: sign*=signature[i]
    return sign,a^b

class CompiledGeoGP3(nn.Module):
    """Fixed Clifford(3,0) basis-product weights; no fitted values."""
    def __init__(self,signature=(1,1,1)):
        super().__init__()
        weights=torch.zeros((8,64),dtype=torch.float64)
        for a in range(8):
            for b in range(8):
                sign,blade=gp_sign_blade(a,b,signature)
                weights[blade,a*8+b]=sign
        self.register_buffer('weights',weights)
    def forward(self,a:int,b:int):
        if not (0<=a<8 and 0<=b<8): raise ValueError('3D blade indices required')
        x=F.one_hot(torch.tensor(a*8+b),64).to(self.weights.dtype)
        return self.weights@x

@dataclass
class Step:
    op: str
    a: int
    b: int

class OperatorMachine:
    def __init__(self):
        self.add=CompiledAdd8(); self.xor=CompiledXor8();self.eq=CompiledEq8()
        self.geo=CompiledGeoGP3()
    def run(self,s: Step) -> dict:
        if s.op=='GEO_GP3':
            v=self.geo(s.a,s.b)
            nz=torch.nonzero(v).flatten().tolist()
            assert len(nz)==1
            return {'blade':nz[0], 'sign':int(v[nz[0]].item())}
        a,b=bits8(s.a),bits8(s.b)
        if s.op=='ADD8': return {'value':unbits(self.add(a,b))}
        if s.op=='XOR8': return {'value':unbits(self.xor(a,b))}
        if s.op=='EQ8': return {'value':int(self.eq(a,b).item())}
        raise ValueError(s.op)

class Controller(nn.Module):
    """Small learned selector; mathematical operations remain frozen."""
    def __init__(self,emb=12,hidden=32):
        super().__init__()
        self.emb=nn.Embedding(len(VOCAB)+1,emb)
        self.net=nn.Sequential(nn.Linear(emb+16,hidden),nn.ReLU(),nn.Linear(hidden,len(OPS)))
    def forward(self,words,arguments): return self.net(torch.cat([self.emb(words),arguments],dim=-1))

def encode(w:str,a:int,b:int):
    # Stable feature space; deliberately no one-hot operation indicator.
    return VOCAB[w],torch.cat([bits8(a),bits8(b)]).float()

def build_examples(seed=20261028):
    rng=random.Random(seed)
    # disjoint arithmetic argument pairs; split by entire (a,b) pairs
    pairs=list({(rng.randrange(256),rng.randrange(256)) for _ in range(1800)})
    rng.shuffle(pairs)
    split=int(.8*len(pairs))
    trainpairs,testpairs=pairs[:split],pairs[split:]
    def materialize(ps):
        arr=[]
        for a,b in ps:
            for ix,op in enumerate(OPS):
                # the same prompt words are used in both sets to test
                # operand generalization, not unseen mathematical vocabulary
                w=rng.choice(PROMPTS[op])
                p,feats=encode(w,a,b)
                arr.append((p,feats,ix,a,b,w))
        rng.shuffle(arr)
        return arr
    return materialize(trainpairs),materialize(testpairs)

def batch(data,device='cpu'):
    return (torch.tensor([x[0] for x in data],device=device),
            torch.stack([x[1] for x in data]).to(device),
            torch.tensor([x[2] for x in data],device=device))

def train_controller(epochs=18,seed=20261028):
    torch.manual_seed(seed); np.random.seed(seed)
    train,test=build_examples(seed)
    model=Controller();opt=torch.optim.AdamW(model.parameters(),lr=0.009)
    train_w,train_x,train_y=batch(train)
    test_w,test_x,test_y=batch(test)
    rng=np.random.default_rng(seed)
    for ep in range(epochs):
        model.train()
        for inds in np.array_split(rng.permutation(len(train)),max(1,(len(train)+127)//128)):
            opt.zero_grad()
            loss=F.cross_entropy(model(train_w[inds],train_x[inds]),train_y[inds])
            loss.backward();opt.step()
    model.eval()
    with torch.no_grad():
        pred=model(test_w,test_x).argmax(-1)
        accuracy=float((pred==test_y).float().mean())
        confusion=torch.zeros(4,4,dtype=torch.int32)
        for truth,guess in zip(test_y,pred): confusion[truth,guess]+=1
    return model, {'train_examples':len(train),'test_examples':len(test),
                   'controller_accuracy':accuracy,'confusion':confusion.tolist()},test

def verify_machine():
    m=OperatorMachine()
    counts={'add':0,'xor':0,'eq':0,'geo':0,'associativity':0}
    # Exhaustive vectorized 8-bit input-pair testing (65536 pairs).
    values=torch.arange(65536,dtype=torch.int64)
    a=(values>>8)&255; b=values&255
    aa=torch.stack([((a>>i)&1).to(torch.float64) for i in range(8)])
    bb=torch.stack([((b>>i)&1).to(torch.float64) for i in range(8)])
    weights=(2**torch.arange(8,dtype=torch.int64))[:,None]
    add=((m.add(aa,bb).to(torch.int64)*weights).sum(0))
    xor=((m.xor(aa,bb).to(torch.int64)*weights).sum(0))
    eq=m.eq(aa,bb).to(torch.int64)
    assert torch.equal(add,(a+b)%256)
    assert torch.equal(xor,a^b)
    assert torch.equal(eq,(a==b).to(torch.int64))
    counts['add']=counts['xor']=counts['eq']=65536
    for a in range(8):
        for b in range(8):
            actual=m.run(Step('GEO_GP3',a,b))
            sign,blade=gp_sign_blade(a,b)
            assert actual=={'sign':sign,'blade':blade}
            counts['geo']+=1
            # Independent ground truth: Pauli-matrix representation of Cl(3,0).
            assert actual==reference_answer('GEO_GP3',a,b)
            counts['geo_pauli']=counts.get('geo_pauli',0)+1
    # Independent check on associative basis products.
    for a in range(8):
        for b in range(8):
            for c in range(8):
                s1,x=gp_sign_blade(a,b);s2,y=gp_sign_blade(x,c)
                t1,z=gp_sign_blade(b,c);t2,w=gp_sign_blade(a,z)
                assert (s1*s2,y)==(t1*t2,w)
                counts['associativity']+=1
    return counts

def reference_answer(op: str, a: int, b: int) -> dict:
    """Plain-Python ground truth, independent of the compiled circuits.

    GEO_GP3 is referenced against an explicit Pauli-matrix representation of
    Cl(3,0) (e1=sx, e2=sy, e3=sz), not against gp_sign_blade.
    """
    if op == 'ADD8': return {'value': (a + b) % 256}
    if op == 'XOR8': return {'value': a ^ b}
    if op == 'EQ8': return {'value': int(a == b)}
    if op == 'GEO_GP3':
        mats = _pauli_blades()
        prod = mats[a] @ mats[b]
        for blade, m in enumerate(mats):
            for sign in (1, -1):
                if np.allclose(prod, sign * m): return {'blade': blade, 'sign': sign}
        raise AssertionError('product not a signed basis blade')
    raise ValueError(op)

def _pauli_blades():
    eye = np.eye(2, dtype=complex)
    pauli = [np.array([[0, 1], [1, 0]], complex), np.array([[0, -1j], [1j, 0]]),
             np.array([[1, 0], [0, -1]], complex)]
    out = []
    for mask in range(8):
        m = eye.copy()
        for i in range(3):
            if (mask >> i) & 1: m = m @ pauli[i]
        out.append(m)
    return out

def integration(model,test):
    # NOTE: the original version only executed when opidx==idx and compared the
    # operator against itself, so it was identical to controller accuracy by
    # construction. This version always executes the *predicted* operator and
    # scores it against independent plain-Python ground truth for the *true* op.
    m=OperatorMachine(); model.eval(); good=0;cases=0
    with torch.no_grad():
        for word,feats,idx,a,b,prompt in test:
            opidx=int(model(torch.tensor([word]),feats[None,:]).argmax(-1).item())
            aa,bb=(a%8,b%8) if idx==3 else (a,b)
            pa,pb=(a%8,b%8) if opidx==3 else (a,b)
            actual=m.run(Step(OPS[opidx],pa,pb))
            expected=reference_answer(OPS[idx],aa,bb)
            good+=int(actual==expected)
            cases+=1
    return {'correct_end_to_end':good,'total_end_to_end':cases,'end_to_end_rate':good/cases,
            'note':'end-to-end scored against independent Python/Pauli ground truth'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--epochs',type=int,default=18)
    p.add_argument('--out',default='results.json');args=p.parse_args()
    gates=verify_machine()
    model,metrics,test=train_controller(epochs=args.epochs)
    results={'compiled_operator_tests':gates,'training':metrics,'integration':integration(model,test),
             'scope':'CPU prototype, 8-bit modular logic and Clifford(3,0) basis products; no Lean or Spectral LM integration'}
    Path(args.out).write_text(json.dumps(results,indent=2))
    torch.save({'state_dict':model.state_dict(),'vocabulary':VOCAB,'operators':OPS},str(Path(args.out).with_suffix('.pt')))
    print(json.dumps(results,indent=2))
if __name__=='__main__': main()
