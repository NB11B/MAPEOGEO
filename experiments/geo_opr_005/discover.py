"""Discover quadratic and cubic additive interaction residuals by exact integer fitting."""
from fractions import Fraction
from itertools import product
import json
def solve(A,b):
 n=len(A);m=[list(map(Fraction,row))+[Fraction(v)] for row,v in zip(A,b)]
 for i in range(n):
  pivot=next((k for k in range(i,n) if m[k][i]),None)
  if pivot is None:raise ValueError("rank deficient")
  m[i],m[pivot]=m[pivot],m[i]
  z=m[i][i];m[i]=[v/z for v in m[i]]
  for k in range(n):
   if k!=i:
    z=m[k][i];m[k]=[v-z*w for v,w in zip(m[k],m[i])]
 return [m[i][-1] for i in range(n)]
def features(degree,a,b):
 return [a**(degree-j)*b**j for j in range(1,degree)]
def residual(degree,a,b):
 return (a+b)**degree-a**degree-b**degree
def discover(degree):
 if degree not in (2,3):raise ValueError("unsupported degree")
 samples=list(product(range(1,4),repeat=2))
 rows=[features(degree,*p) for p in samples]
 ys=[residual(degree,*p) for p in samples]
 import itertools
 for ix in itertools.combinations(range(len(rows)),degree-1):
  try:coeff=solve([rows[i] for i in ix],[ys[i] for i in ix])
  except ValueError:continue
  if all(sum(c*x for c,x in zip(coeff,row))==y for row,y in zip(rows,ys)):
   hold=list(product(range(4,21),repeat=2))
   if all(sum(c*x for c,x in zip(coeff,features(degree,*p)))==residual(degree,*p) for p in hold):
    return {"degree":degree,"coefficients":[int(c) for c in coeff],"train":len(samples),"heldout":len(hold)}
 raise ValueError("no qualified polynomial")
def run():return [discover(2),discover(3)]
if __name__=="__main__":print(json.dumps(run(),indent=2))
