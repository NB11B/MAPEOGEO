"""GEO-EULER-004: recurrence grammar search using withheld opaque transitions."""
import json,random,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"geo_euler_003"))
from experiment import world,chain

def split_tables(w,seed=11,holdout=.3):
    rng=random.Random(seed);train={};test={}
    for name,table in w.tables.items():
        tr={};te={}
        for (a,b),v in table.items():
            (tr if b==w.zero or rng.random()>holdout else te)[(a,b)]=v
        train[name]=tr;test[name]=te
    return train,test

def complete(path,zero,successor,kind,rule,addition=None):
    out={}
    for a in path:
        out[(a,zero)]=a if kind=="first" else zero
        for i,b in enumerate(path[:-1]):
            previous=out.get((a,b))
            if kind=="first":
                v=previous
                for _ in range(rule):
                    v=successor.get(v)
                    if v is None:break
            elif rule=="add-left":v=addition.get((previous,a))
            elif rule=="successor":v=successor.get(previous)
            elif rule=="identity":v=previous
            else:raise ValueError(rule)
            if v is not None:out[(a,path[i+1])]=v
    return out

def select(observed,predictions):
    scores=[]
    for key,pred in predictions.items():
        name=key.split("|")[0];obs=observed[name]
        errors=sum(k not in pred or pred[k]!=v for k,v in obs.items())
        scores.append((errors,key,len(obs)))
    exact=[key for error,key,checks in scores if error==0 and checks>=10]
    return (exact[0] if len(exact)==1 else None),scores

def discover(w,train,test):
    try:path=chain(w.successor,w.zero)
    except ValueError:return {"status":"refuse","stage":"successor"}
    if len(path)<8 or path[1]!=w.one:return {"status":"refuse","stage":"anchors"}
    first={f"{name}|shift={shift}":complete(path,w.zero,w.successor,"first",shift)
           for name in train for shift in (0,1,2)}
    chosen,_=select(train,first)
    if chosen is None:return {"status":"refuse","stage":"first"}
    first_name=chosen.split("|")[0];add=first[chosen]
    second={f"{name}|{rule}":complete(path,w.zero,w.successor,"second",rule,add)
            for name in train if name!=first_name for rule in ("add-left","successor","identity")}
    chosen2,_=select(train,second)
    if chosen2 is None:return {"status":"refuse","stage":"second"}
    second_name=chosen2.split("|")[0];mult=second[chosen2]
    errors={name:sum(k not in predicted or predicted[k]!=v for k,v in test[name].items())
            for name,predicted in ((first_name,add),(second_name,mult))}
    if any(errors.values()):return {"status":"refuse","stage":"holdout"}
    composites={v for (a,b),v in mult.items() if a not in (w.zero,w.one) and b not in (w.zero,w.one)}
    primes=[p for p in path[2:] if p not in composites]
    return {"status":"qualified","addition":chosen,"multiplication":chosen2,
            "holdout_checks":{name:len(test[name]) for name in (first_name,second_name)},
            "holdout_errors":errors,"primes":primes,"prime_count":len(primes)}

def run(seed=11):
    w=world(size=31,seed=seed)
    train,test=split_tables(w,seed+100)
    r=discover(w,train,test)
    if r["status"]=="qualified":r["primes_reference"]=[w.decode[p] for p in r.pop("primes")]
    r["training_entries"]={k:len(v) for k,v in train.items()}
    r["withheld_entries"]={k:len(v) for k,v in test.items()}
    return r
if __name__=="__main__":print(json.dumps(run(),indent=2))
