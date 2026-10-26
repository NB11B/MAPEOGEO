"""GEO-BSL-002: positional base vs base-dependent dynamics."""
import math
import unittest
import numpy as np

def digits(n, base):
    if n < 0 or base < 2:
        raise ValueError("invalid integer/base")
    if n == 0:
        return [0]
    output = []
    while n:
        output.append(n % base)
        n //= base
    return output[::-1]

def decode(ds, base):
    if base < 2:
        raise ValueError("invalid base")
    value = 0
    for d in ds:
        if not 0 <= d < base:
            raise ValueError("invalid digit")
        value = base * value + d
    return value

def adjacency(n, path=False):
    a = np.zeros((n, n))
    for i in range(n if not path else n - 1):
        j = (i + 1) % n
        a[i,j] = a[j,i] = 1
    return a

def inverse_spectral_trace(a):
    eig = np.linalg.eigvalsh(np.diag(a.sum(axis=1)) - a)
    return float(np.sum(1 / eig[eig > 1e-9]))

def square_digits(n, base):
    return sum(d*d for d in digits(n, base))

def orbit(n, base, max_steps=1000):
    visited = {}
    sequence = []
    for _ in range(max_steps):
        if n in visited:
            return sequence, sequence[visited[n]:]
        visited[n] = len(sequence)
        sequence.append(n)
        n = square_digits(n, base)
    raise RuntimeError("cycle not reached")

def summary():
    rng = np.random.default_rng(20261025)
    bases = (2,3,7,10,16,36)
    integers = list(range(513)) + [int(x) for x in rng.integers(0,2**31,size=500)]
    encoding = sum(decode(digits(n,b),b)==n for n in integers for b in bases)
    graph = []
    for n in (5,8,16,31,64):
        a = adjacency(n)
        p = rng.permutation(n)
        graph.append({"n":n,
            "cycle_error":abs(inverse_spectral_trace(a)-(n*n-1)/12),
            "path_error":abs(inverse_spectral_trace(adjacency(n,path=True))-(n*n-1)/6),
            "relabel_error":abs(inverse_spectral_trace(a)-inverse_spectral_trace(a[np.ix_(p,p)]))})
    return {"encoding_passed":encoding,"encoding_total":len(integers)*len(bases),
        "graphs":graph,"digit_square_19":{str(b):square_digits(19,b) for b in bases},
        "orbits_19":{str(b):orbit(19,b) for b in (2,7,10)},
        "ifs_contraction":{str(b):1/b for b in (4,7,10)},
        "ifs_similarity_dimension_if_OSC":{str(b):math.log(3)/math.log(b) for b in (4,7,10)}}

class TestBaseInvariance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = summary()
    def test_round_trip(self):
        self.assertEqual(self.r["encoding_passed"],6078)
        self.assertEqual(self.r["encoding_total"],6078)
    def test_cycle_spectrum(self):
        self.assertTrue(all(x["cycle_error"]<1e-8 for x in self.r["graphs"]))
    def test_path_spectrum(self):
        self.assertTrue(all(x["path_error"]<1e-8 for x in self.r["graphs"]))
    def test_relabel(self):
        self.assertTrue(all(x["relabel_error"]<1e-8 for x in self.r["graphs"]))
    def test_base_changes_digit_dynamics(self):
        self.assertEqual(self.r["digit_square_19"]["2"],3)
        self.assertEqual(self.r["digit_square_19"]["7"],29)
        self.assertEqual(self.r["digit_square_19"]["10"],82)
        self.assertEqual(self.r["orbits_19"]["7"][1],[29,17,13,37])
        self.assertEqual(self.r["orbits_19"]["2"][1],[1])
    def test_ifs_parameter(self):
        self.assertNotEqual(self.r["ifs_contraction"]["7"],self.r["ifs_contraction"]["10"])

if __name__=="__main__":
    unittest.main()
