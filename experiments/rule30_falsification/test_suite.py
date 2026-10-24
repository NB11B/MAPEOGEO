import unittest
from rule30_suite import rule30, sideways_left, history, packed_history, central_trace, e1, e2, e3, e4

class TestRule30(unittest.TestCase):
    def test_truth_table(self):
        assert [rule30((i>>2)&1,(i>>1)&1,i&1) for i in range(7,-1,-1)] == [0,0,0,1,1,1,1,0]
    def test_sideways_all_inputs(self):
        for a in range(2):
            for b in range(2):
                for c in range(2):
                    self.assertEqual(sideways_left(rule30(a,b,c),b,c),a)
    def test_seed_boundary(self):
        for depth in (1,3,6,9):
            self.assertEqual(e1(depth)['status'],'PASS')
    def test_trace_exact(self):
        for k in range(1,6):
            for x in range(1<<(2*k+1)):
                self.assertEqual(len(central_trace(x,k)),k+1)
    def test_quotient(self):
        for point in e2(6)['series']:
            k=point['k']
            self.assertEqual(point['observational_classes'],2**(k+1))
            self.assertEqual(point['smallest_class'],2**k)
    def test_anf(self):
        self.assertEqual([x['monomials'] for x in e3(4)['series']],[1,4,10,30,122])
    def test_packed(self):
        for k in (1,8,32):
            exact=history(k)
            packed=packed_history(k)
            for t in range(k+1):
                self.assertEqual(exact[t][0],(packed[t]>>(k+1))&1)

if __name__=='__main__': unittest.main(verbosity=2)
