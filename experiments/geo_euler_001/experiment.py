"""GEO-EULER-001: prime-generator closure versus Euler products."""
import json, math

def primes_through(n):
    s=bytearray([1])*(n+1);s[0:2]=bytes([0,0])
    for p in range(2,math.isqrt(n)+1):
        if s[p]:
            for k in range(p*p,n+1,p):s[k]=0
    return [p for p in range(2,n+1) if s[p]]

def closure(primes,limit):
    states={1}
    for p in primes:
        new=set()
        for n in states:
            power=1
            while n*power<=limit:
                new.add(n*power);power*=p
        states=new
    return states

def euler_product(primes):
    return math.prod(1/(1-1/p**2) for p in primes)

def run(limit=1000):
    ps=primes_through(limit)
    states=closure(ps,limit)
    full=euler_product(ps)
    ablations=[]
    for q in (2,3,5,7,11):
        removed=closure((p for p in ps if p!=q),limit)
        ratio=euler_product(p for p in ps if p!=q)/full
        ablations.append({"removed_prime":q,"retained_states":len(removed),
            "ratio":ratio,"predicted":1-1/q**2,
            "error":abs(ratio-(1-1/q**2)),
            "state_sum":sum(1/n**2 for n in removed)})
    return {"limit":limit,"prime_count":len(ps),"closure_count":len(states),
        "closure_complete":states==set(range(1,limit+1)),
        "finite_integer_sum":sum(1/n**2 for n in states),
        "finite_prime_product":full,"basel_reference":math.pi**2/6,
        "prime_only_sum":sum(1/p**2 for p in ps),
        "ablations":ablations}
if __name__=="__main__":print(json.dumps(run(),indent=2))
