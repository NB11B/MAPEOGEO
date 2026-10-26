from itertools import permutations
from math import gcd

def cycles(p):
    seen=set(); out=[]
    for i in range(len(p)):
        if i not in seen:
            j=i; k=0
            while j not in seen:
                seen.add(j);j=p[j];k+=1
            out.append(k)
    return tuple(sorted(out))

def classify(n, observed, kind):
    if len(set(i for i,j in observed)) != len(observed) or len(set(j for i,j in observed))!=len(observed):
        return {'status':'refuse','reason':'not_injective'}
    if kind == 'arbitrary': candidates=permutations(range(n))
    elif kind == 'known_coordinates':
        candidates=(tuple((i+k)%n for i in range(n)) for k in range(1,n) if gcd(n,k)==1)
    elif kind == 'latent_coordinates':
        candidates=(p for p in permutations(range(n)) if cycles(p)==(n,))
    else: raise ValueError(kind)
    fitted=[p for p in candidates if all(p[i]==j for i,j in observed)]
    signatures={cycles(p) for p in fitted}
    return {'status':'refuse' if not fitted else ('identified' if len(fitted)==1 else 'ambiguous'),
            'models':len(fitted),'spectra':len(signatures),'spectral_identified':len(signatures)==1 and bool(fitted),
            'cycle_types':sorted(signatures)}

def campaign(n=5):
    observed=[(0,1)]
    result={k:classify(n,observed,k) for k in ('arbitrary','known_coordinates','latent_coordinates')}
    result['empty_latent']=classify(n,[], 'latent_coordinates')
    result['contradictory']=classify(n,[(0,1),(2,1)],'latent_coordinates')
    return result
if __name__=='__main__':
    import json
    print(json.dumps(campaign(),indent=2))
