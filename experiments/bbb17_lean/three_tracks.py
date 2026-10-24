"""BBB17 Collatz research tracks: bounded recurrence, geometry, affine parity words.
Standard-library only. No finite scan is a proof of global Collatz.
"""
from dataclasses import dataclass
from typing import Optional

def accelerated(n: int) -> int:
    if n <= 0: raise ValueError("positive integers only")
    return n // 2 if n % 2 == 0 else (3*n + 1)//2

def register_step(u: int) -> int:
    if u < 0: raise ValueError("natural registers only")
    return u//2 if u % 2 else 3*(u//2)+1

@dataclass(frozen=True)
class Phase:
    j: int
    u: int
    v: int
    beeps: int = 0

def phase(s: Phase) -> Phase:
    j,u,v=s.j,s.u,s.v
    if min(j,u,v)<0: raise ValueError("negative canonical coordinate")
    if u==0: return Phase(j+1,j+1,max(0,v-(j+1)),j+1)
    if u%2: return Phase(j,u//2,v+(u+1)//2)
    k=u//2
    return Phase(j,3*k+1,max(0,v-k-1))

def orbit(start: int, cap: int=10000):
    """Return termination/cycle/limit diagnostics, never a universal result."""
    if start<1: raise ValueError("start must be positive")
    seen={}
    n=start
    for t in range(cap+1):
        if n==1: return {"kind":"reached_one","steps":t}
        if n in seen: return {"kind":"cycle","steps":t,"period":t-seen[n]}
        if t==cap: return {"kind":"limit","steps":t}
        seen[n]=t
        n=accelerated(n)
    raise AssertionError

def affine_word(bits: tuple[int,...]):
    """For accelerated Collatz: n -> (3^a*n + b)/2^r, on valid parity cells."""
    A,B,D=1,0,1
    for b in bits:
        if b not in (0,1): raise ValueError("parity symbols must be 0/1")
        if b: A,B=3*A,3*B+D
        D*=2
    return A,B,D

def actual_word(n: int,bits: tuple[int,...]) -> Optional[int]:
    if n < 1: raise ValueError("positive integers only")
    for b in bits:
        if n%2 != b: return None
        n=accelerated(n)
    return n

def classify_word_cycle(bits: tuple[int,...]) -> dict:
    """Classify cycle admissibility of a parity word using exact Diophantine & cylinder gates."""
    if not bits:
        return {"status": "empty_identity", "candidate": None}
    A, B, D = affine_word(bits)
    if B == 0:
        return {"status": "all_even_zero_fixed", "candidate": 0}
    if A >= D:
        return {"status": "rejected_expanding", "candidate": None}
    gap = D - A
    if B % gap != 0:
        return {"status": "rejected_non_integer", "candidate": None}
    m0 = B // gap
    out = actual_word(m0, bits) if m0 >= 1 else None
    if out != m0:
        return {"status": "rejected_parity_mismatch", "candidate": m0}
    if m0 in (1, 2):
        return {"status": "trivial_one_two_cycle", "candidate": m0}
    return {"status": "nontrivial_cycle", "candidate": m0}

def verify_envelope_and_drawdown(u0: int, v0: int, max_steps: int = 32) -> dict:
    """Verify S_t = max(S_0, u_1, ..., u_t) and v_t = S_t - u_t across positive-register steps."""
    s = Phase(0, u0, v0)
    s0 = u0 + v0
    running_max = s0
    steps = 0
    exhaustions = 0
    while s.u > 0 and steps < max_steps:
        prev_s = s.u + s.v
        s = phase(s)
        steps += 1
        running_max = max(running_max, s.u)
        assert s.u + s.v == running_max, (u0, v0, steps, s, running_max)
        assert s.v == running_max - s.u, (u0, v0, steps, s, running_max)
        if s.u + s.v > prev_s:
            exhaustions += 1
    return {"steps": steps, "final_S": s.u + s.v, "exhaustions": exhaustions}

def compare_binary_vs_base7(max_r: int = 6) -> dict:
    """Test Base-7 shifts (+7 vs +7*2^r) against the certified 2^r binary parity filtration."""
    binary_preserved = 0
    base7_unit_preserved = 0
    base7_lcm_preserved = 0
    total_nonempty_valid = 0
    for r in range(1, max_r + 1):
        D = 1 << r
        for word in range(D):
            bits = tuple((word >> i) & 1 for i in range(r))
            A, _, _ = affine_word(bits)
            for m in range(1, D + 1):
                out = actual_word(m, bits)
                if out is not None:
                    total_nonempty_valid += 1
                    out_bin = actual_word(m + D, bits)
                    if out_bin == out + A:
                        binary_preserved += 1
                    if actual_word(m + 7, bits) is not None:
                        base7_unit_preserved += 1
                    out_lcm = actual_word(m + 7 * D, bits)
                    if out_lcm == out + 7 * A:
                        base7_lcm_preserved += 1
    return {
        "total_nonempty_valid": total_nonempty_valid,
        "binary_2r_preserved": binary_preserved,
        "base7_unit_shift_preserved": base7_unit_preserved,
        "base7_lcm_7x2r_preserved": base7_lcm_preserved,
    }

def parity_word_of(m: int, r: int) -> tuple[int, ...]:
    bits = []
    x = m
    for _ in range(r):
        bits.append(x % 2)
        x = x // 2 if x % 2 == 0 else (3 * x + 1) // 2
    return tuple(bits)

def cylinder_cert(r: int, r0: int) -> bool:
    D = 1 << r
    m0 = r0 + D if r0 <= 1 else r0
    bits = parity_word_of(r0, r)
    A, B, D_w = affine_word(bits)
    return r > 0 and r0 < D and D_w > A and (D_w - A) * m0 > B

def adaptive_residue_tree(max_r: int = 8) -> dict:
    """Build the COLLATZ-C6 adaptive residue refinement tree up to depth max_r."""
    surviving = [0, 1]
    levels = {}
    for r in range(1, max_r + 1):
        half = 1 << (r - 1)
        candidates = sorted(
            [x for s in surviving for x in (s, s + half)] if r > 1 else [0, 1]
        )
        discharged = []
        next_surviving = []
        contracting_exceptions = []
        for r0 in candidates:
            if cylinder_cert(r, r0):
                discharged.append(r0)
            else:
                next_surviving.append(r0)
                A, B, D = affine_word(parity_word_of(r0, r))
                if D > A:
                    contracting_exceptions.append(r0)
        surviving = next_surviving
        levels[r] = {
            "modulus": 1 << r,
            "newly_discharged": discharged,
            "surviving_frontier": surviving,
            "surviving_count": len(surviving),
            "contracting_exceptions": contracting_exceptions,
        }
    return levels

def odd_to_odd_step(n: int) -> tuple[int, int]:
    """For positive odd n, return (T(n) = (3n+1)/2^t, t = v_2(3n+1))."""
    if n <= 0 or n % 2 == 0:
        raise ValueError("positive odd integers only")
    m = 3 * n + 1
    t = 0
    while m % 2 == 0:
        m //= 2
        t += 1
    return m, t

def return_map_word(valuations: tuple[int, ...]) -> tuple[int, ...]:
    """Expand a sequence of 2-adic valuations (t_1, ..., t_r) with t_i >= 1 into its parity word."""
    bits = []
    for t in valuations:
        if t < 1:
            raise ValueError("valuations must be >= 1")
        bits.append(1)
        bits.extend([0] * (t - 1))
    return tuple(bits)

def verify_return_map_composition(max_odd: int = 255, steps: int = 5) -> dict:
    """Verify C7.1: r odd-to-odd return steps match return_map_word and satisfy 2^K * T^r(n) = 3^r * n + B."""
    checked = 0
    for n in range(1, max_odd + 1, 2):
        curr = n
        vals = []
        for _ in range(steps):
            curr, t = odd_to_odd_step(curr)
            vals.append(t)
        w = return_map_word(tuple(vals))
        A, B, D = affine_word(w)
        assert A == 3 ** steps
        assert D == 1 << sum(vals)
        assert actual_word(n, w) == curr
        assert D * curr == A * n + B
        assert 3 * B <= steps * A or sum(vals) > steps  # general cocycle check
        checked += 1
    return {"checked_odd_starts": checked, "steps": steps}

def word_residue_of_bits(bits: tuple[int, ...]) -> int:
    """Compute canonical wordResidue(w) < 2^|w| matching ThreeTracks.lean."""
    R = 0
    D = 1
    for b in reversed(bits):
        if b == 0:
            R = 2 * R
        else:
            if R % 3 == 2:
                q = 0
            elif (R + D) % 3 == 2:
                q = 1
            else:
                q = 2
            R = 2 * ((R + q * D - 2) // 3) + 1
        D *= 2
    return R

def verify_minimal_crossing_pincer(max_r: int = 12) -> dict:
    """Verify C8 on all first-crossing words up to depth max_r:
    1. 3 * B(w) <= a(w) * A(w) (three_mul_wordB_le_wordOnes_mul_wordA)
    2. (D(w) - A(w)) * m_min(w) > B(w) (zero exceptions)
    """
    words = [()]
    checked = 0
    exceptions = 0
    for r in range(1, max_r + 1):
        D = 1 << r
        next_words = []
        for w in words:
            for b in (0, 1):
                w2 = w + (b,)
                a = sum(w2)
                A, B, D_w = affine_word(w2)
                assert 3 * B <= a * A, (w2, a, A, B)
                if A > D:
                    next_words.append(w2)
                else:
                    checked += 1
                    r0 = word_residue_of_bits(w2)
                    m0 = r0 + D if r0 <= 1 else r0
                    if (D - A) * m0 <= B:
                        exceptions += 1
        words = next_words
    return {"max_r": max_r, "first_crossing_words": checked, "exceptions": exceptions}

def verify_discrete_deficit_c9(max_r: int = 12) -> dict:
    """Verify COLLATZ-C9 laws on all first-crossing words up to depth max_r and key exceptions:
    1. Exact discrete deficit identity: (D(w) - A(w)) * m_min(w) - B(w) == D(w) * (m_min(w) - F_w(m_min(w)))
    2. Quantization law: (D(w) - A(w)) * m_min(w) >= B(w) + D(w)
    3. 2-adic parity lock and 3-adic non-divisibility (B(w) % 3 != 0, F_w(m_min(w)) % 3 != 0 for a >= 1)
    4. Separation of C8 coarse pincer vs C9 exact deficit at m_0 in {27, 47, 63}
    """
    words = [()]
    checked = 0
    min_q = None
    for r in range(1, max_r + 1):
        D = 1 << r
        next_words = []
        for w in words:
            for b in (0, 1):
                w2 = w + (b,)
                a = sum(w2)
                A, B, D_w = affine_word(w2)
                if a >= 1:
                    assert B % 3 != 0, (w2, B)
                if A > D:
                    next_words.append(w2)
                else:
                    checked += 1
                    r0 = word_residue_of_bits(w2)
                    m0 = r0 + D if r0 <= 1 else r0
                    ym = (A * m0 + B) // D
                    delta = D - A
                    deficit = delta * m0 - B
                    q = m0 - ym
                    assert deficit == D * q, (w2, m0, ym, deficit, D * q)
                    assert q >= 1 and deficit >= D, (w2, m0, ym, q)
                    assert B % 2 == m0 % 2, (w2, B, m0)
                    if a >= 1:
                        assert ym % 3 != 0, (w2, m0, ym)
                    if min_q is None or q < min_q:
                        min_q = q
        words = next_words
    # Verify C8 pincer separation witnesses {27, 47, 63}
    separation_witnesses = {}
    for m0 in (27, 47, 63):
        curr = m0
        bits = []
        while True:
            b = curr & 1
            bits.append(b)
            curr = (3 * curr + 1) // 2 if b else curr // 2
            r = len(bits)
            a = sum(bits)
            if (1 << r) > (3 ** a):
                break
        A, B, D = affine_word(tuple(bits))
        delta = D - A
        q = m0 - curr
        assert 3 * delta * m0 <= a * A
        assert delta * m0 - B == D * q and q >= 1
        separation_witnesses[m0] = {"r": r, "a": a, "ym": curr, "q": q}
    return {
        "max_r": max_r,
        "checked_words": checked,
        "min_quantized_quotient": min_q,
        "separation_witnesses": separation_witnesses,
    }

def run_campaign(max_start=10000, cap=10000, depth=8):
    kinds={}
    for n in range(1,max_start+1):
        k=orbit(n,cap)["kind"]; kinds[k]=kinds.get(k,0)+1
    words=0; matched=0
    cycle_classes={}
    for r in range(depth+1):
        for word in range(1<<r):
            bits=tuple((word>>i)&1 for i in range(r))
            A,B,D=affine_word(bits)
            if r >= 1:
                cstatus = classify_word_cycle(bits)["status"]
                cycle_classes[cstatus] = cycle_classes.get(cstatus, 0) + 1
            for n in range(1,min(max_start,128)+1):
                out=actual_word(n,bits)
                if out is not None:
                    words+=1
                    assert D*out==A*n+B,(bits,n,A,B,D,out)
                    matched+=1
    # Geometry: S=u+v is unchanged on even-integer phases, nondecreasing on odd-integer phases,
    # and satisfies S' = max(S, u') on all positive-register steps.
    checked=0; growth=0
    for u in range(1,128):
        for v in range(128):
            s=Phase(0,u,v); t=phase(s)
            assert t.beeps==0 and t.j==0
            assert t.u+ t.v >= s.u+s.v
            assert t.u + t.v == max(s.u + s.v, t.u)
            assert t.v == max(s.u + s.v, t.u) - t.u
            if u%2: assert t.u+t.v==s.u+s.v
            if t.u+t.v > s.u+s.v: growth+=1
            checked+=1
    b7 = compare_binary_vs_base7(min(depth, 6))
    c6 = adaptive_residue_tree(min(depth, 8))
    return {"starts":max_start,"orbit_results":kinds,
            "affine_valid_cases":matched,"geometry_cases":checked,
            "strict_S_growth_cases":growth,"cycle_classification":cycle_classes,
            "binary_vs_base7":b7,"c6_frontier_counts":{r: c6[r]["surviving_count"] for r in c6},
            "universal_claim":False}

if __name__=="__main__":
    import argparse,json
    p=argparse.ArgumentParser()
    p.add_argument("--starts",type=int,default=10000)
    p.add_argument("--cap",type=int,default=10000)
    p.add_argument("--depth",type=int,default=8)
    a=p.parse_args()
    print(json.dumps(run_campaign(a.starts,a.cap,a.depth),indent=2))
