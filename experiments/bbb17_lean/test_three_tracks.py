import unittest
from three_tracks import Phase,phase,accelerated,register_step,affine_word,actual_word,orbit,run_campaign
class TestTracks(unittest.TestCase):
    def test_register(self):
        for u in range(0,500):
            if u>0: self.assertEqual(register_step(u)+1,accelerated(u+1))
    def test_geometry(self):
        for u in range(1,30):
            for v in range(30):
                a=Phase(3,u,v); b=phase(a)
                self.assertGreaterEqual(b.u+b.v,u+v)
                if u%2:self.assertEqual(b.u+b.v,u+v)
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
    def test_orbit_cap(self):
        self.assertEqual(orbit(27,1)["kind"],"limit")
        self.assertEqual(orbit(27,200)["kind"],"reached_one")
    def test_campaign(self):
        r=run_campaign(100,200,5)
        self.assertEqual(r["orbit_results"],{"reached_one":100})
        self.assertFalse(r["universal_claim"])
if __name__=="__main__": unittest.main()
