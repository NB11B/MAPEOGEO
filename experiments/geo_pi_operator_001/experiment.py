"""Exact rational expression audit and pi approximation controls."""
from fractions import Fraction
from math import pi
def closest(limit):
    options=[]
    for q in range(1,limit+1):
        p=round(pi*q)
        for x in (p-1,p,p+1):
            if x>=0:
                r=Fraction(x,q)
                options.append((abs(float(r)-pi),r))
    return min(options,key=lambda x:(x[0],x[1].denominator,x[1].numerator))[1]
def run():
    proposed=Fraction(2*(5+2*3),7)
    return {"proposed":str(proposed),"error":float(proposed)-pi,
      "relative_error_percent":100*(float(proposed)/pi-1),
      "unscaled":str(Fraction(5+2*3,7)),
      "nested":str(Fraction((1+1)+3+2*3,7)),
      "best_denominator_upto_7":str(closest(7)),
      "best_denominator_upto_113":str(closest(113)),
      "alternative_expression":"(3*7+1)/7"}
if __name__=="__main__":
 import json
 print(json.dumps(run(),indent=2))
