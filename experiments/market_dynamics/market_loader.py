"""Deterministic UTC market-data adapter. No missing-bar interpolation or predictive claims."""
import csv,hashlib,json,math,argparse
from datetime import datetime,timezone
from pathlib import Path

def read_bars(path):
    blob=Path(path).read_bytes()
    out=[]
    for line,row in enumerate(csv.DictReader(blob.decode("utf-8-sig").splitlines()),2):
        try:
            stamp=row.get("datetime") or row.get("timestamp")
            t=datetime.fromisoformat(stamp.replace("Z","+00:00"))
            if t.tzinfo is None: raise ValueError("timezone missing")
            t=t.astimezone(timezone.utc)
            p={k:float(row[k]) for k in ("open","high","low","close")}
            if any(not math.isfinite(v) or v<=0 for v in p.values()): raise ValueError("invalid price")
            if p["high"]<max(p["open"],p["close"],p["low"]) or p["low"]>min(p.values()):
                raise ValueError("inconsistent OHLC")
            out.append((t,p["close"]))
        except (ValueError,KeyError,AttributeError) as exc:
            raise ValueError(f"{path}:{line}: {exc}") from exc
    if not out: raise ValueError("empty")
    if any(out[i][0]<=out[i-1][0] for i in range(1,len(out))):
        raise ValueError("unordered or duplicate timestamps")
    return out,hashlib.sha256(blob).hexdigest()

def states(bars,cadence_seconds,lags=(1,2,4)):
    if cadence_seconds<=0 or not lags or min(lags)<=0: raise ValueError("invalid cadence/lags")
    lags=tuple(sorted(set(lags)))
    out=[]
    for i in range(max(lags),len(bars)):
        t,c=bars[i]
        if any((t-bars[i-l][0]).total_seconds()!=l*cadence_seconds for l in lags):continue
        out.append(dict(timestamp=t.isoformat(),unix=int(t.timestamp()),
          earth_phase=(t.hour*3600+t.minute*60+t.second)/86400,
          state=[math.log(c/bars[i-l][1]) for l in lags]))
    return out

def transitions(s,cadence_seconds):
    return [(s[i-1],s[i]) for i in range(1,len(s))
            if s[i]["unix"]-s[i-1]["unix"]==cadence_seconds]

def invert(a):
    n=len(a);m=[list(row)+[float(i==j) for j in range(n)] for i,row in enumerate(a)]
    for k in range(n):
        pivot=max(range(k,n),key=lambda i:abs(m[i][k]))
        if abs(m[pivot][k])<1e-12:raise ValueError("singular")
        m[k],m[pivot]=m[pivot],m[k]
        v=m[k][k];m[k]=[x/v for x in m[k]]
        for i in range(n):
            if i!=k:
                f=m[i][k];m[i]=[x-f*y for x,y in zip(m[i],m[k])]
    return [row[n:] for row in m]

def operator_fit(pairs,dimension,ridge=1e-8):
    if ridge<=0:raise ValueError("ridge must be positive")
    gram=[[float(i==j)*ridge for j in range(dimension)] for i in range(dimension)]
    rhs=[[0.0]*dimension for _ in range(dimension)]
    for x,y in pairs:
        for i in range(dimension):
            for j in range(dimension):
                gram[i][j]+=x[i]*x[j]
                rhs[i][j]+=y[i]*x[j]
    gi=invert(gram)
    return [[sum(rhs[i][k]*gi[k][j] for k in range(dimension))
             for j in range(dimension)] for i in range(dimension)]

def matvec(a,x):return [sum(z*v for z,v in zip(row,x)) for row in a]
def error(y,p):return sum((a-b)**2 for a,b in zip(y,p))
def commutator(a,b):
    n=len(a)
    return [[sum(a[i][k]*b[k][j]-b[i][k]*a[k][j] for k in range(n))
             for j in range(n)] for i in range(n)]
def generator_parts(a):
    n=len(a)
    return ([[(a[i][j]+a[j][i])/2 for j in range(n)] for i in range(n)],
            [[(a[i][j]-a[j][i])/2 for j in range(n)] for i in range(n)])

def run(manifest):
    path=manifest["path"];cadence=int(manifest["cadence_seconds"])
    lags=tuple(manifest.get("lags",[1,2,4]))
    bars,sha=read_bars(path);ss=states(bars,cadence,lags)
    split=manifest["split_utc"];dt=datetime.fromisoformat(split.replace("Z","+00:00"))
    if dt.tzinfo is None:raise ValueError("split must have timezone")
    cut=int(dt.timestamp())
    pairs=transitions(ss,cadence)
    train=[(a["state"],b["state"]) for a,b in pairs if b["unix"]<cut]
    test=[(a["state"],b["state"]) for a,b in pairs if a["unix"]>=cut]
    if len(train)<len(lags)*2 or len(test)<2:raise ValueError("insufficient contiguous data")
    A=operator_fit(train,len(lags),float(manifest.get("ridge",1e-8)))
    e=sum(error(y,matvec(A,x)) for x,y in test)/len(test)
    base=sum(error(y,x) for x,y in test)/len(test)
    S,W=generator_parts(A)
    return dict(kind="deterministic_measurement_only",source=str(path),source_sha256=sha,
       observation_count=len(bars),state_count=len(ss),train_transitions=len(train),
       test_transitions=len(test),split_utc=split,lags=list(lags),operator=A,
       symmetric_generator=S,skew_generator=W,test_mse=e,identity_mse=base,
       relative_mse=e/base if base else None,
       scope="contiguous observed bars; not evidence of mechanism or probability")

def main():
    p=argparse.ArgumentParser();p.add_argument("--manifest",required=True);p.add_argument("--out",required=True)
    a=p.parse_args();result=run(json.loads(Path(a.manifest).read_text()))
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n")
if __name__=="__main__":main()
