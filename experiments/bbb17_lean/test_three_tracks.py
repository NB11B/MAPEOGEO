import unittest
from three_tracks import (
    Phase,phase,accelerated,register_step,affine_word,actual_word,
    orbit,run_campaign,classify_word_cycle,verify_envelope_and_drawdown,
    compare_binary_vs_base7,
)
class TestTracks(unittest.TestCase):
    def test_register(self):
        for u in range(0,500):
            if u>0: self.assertEqual(register_step(u)+1,accelerated(u+1))
    def test_geometry(self):
        for u in range(1,30):
            for v in range(30):
                a=Phase(3,u,v); b=phase(a)
                self.assertGreaterEqual(b.u+b.v,u+v)
                self.assertEqual(b.u+b.v,max(u+v,b.u))
                self.assertEqual(b.v,max(u+v,b.u)-b.u)
                if u%2:self.assertEqual(b.u+b.v,u+v)
    def test_envelope_and_drawdown(self):
        for u in range(1,32):
            for v in range(0,16):
                res=verify_envelope_and_drawdown(u,v,24)
                self.assertGreaterEqual(res["final_S"],u+v)
    def test_reset(self):
        for j in range(30):
            for v in range(30):
                s=phase(Phase(j,0,v))
                self.assertEqual((s.j,s.u,s.beeps),(j+1,j+1,j+1))
    def test_affine(self):
        for r in range(8):
            for w in range(1<<r):
                bits=tuple((w>>i)&1 for i in range(r))
                A,B,D=affine_word(bits)
                for n in range(1,128):
                    out=actual_word(n,bits)
                    if out is not None:self.assertEqual(out*D,A*n+B)
    def test_cycle_classification(self):
        for r in range(1,9):
            for w in range(1<<r):
                bits=tuple((w>>i)&1 for i in range(r))
                c=classify_word_cycle(bits)
                self.assertNotEqual(c["status"],"nontrivial_cycle")
    def test_binary_vs_base7(self):
        b7=compare_binary_vs_base7(5)
        self.assertEqual(b7["binary_2r_preserved"],b7["total_nonempty_valid"])
        self.assertEqual(b7["base7_unit_shift_preserved"],0)
        self.assertEqual(b7["base7_lcm_7x2r_preserved"],b7["total_nonempty_valid"])
    def test_orbit_cap(self):
        self.assertEqual(orbit(27,1)["kind"],"limit")
        self.assertEqual(orbit(27,200)["kind"],"reached_one")
    def test_campaign(self):
        r=run_campaign(100,200,5)
        self.assertEqual(r["orbit_results"],{"reached_one":100})
        self.assertFalse(r["universal_claim"])
if __name__=="__main__": unittest.main()
