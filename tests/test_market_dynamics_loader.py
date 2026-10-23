"""Deterministic contract tests for UTC market geometry adapter."""
import csv,math,tempfile,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from experiments.market_dynamics.market_loader import (
 read_bars,states,transitions,operator_fit,matvec,commutator,generator_parts,run)

class MarketLoaderTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.path=Path(self.tmp.name)/"bars.csv"
 def write(self,n=120,skip=None,naive=False):
  with self.path.open("w",newline="") as f:
   w=csv.writer(f);w.writerow(["datetime","open","high","low","close","volume"]);p=100.
   for i in range(n):
    if i==skip:continue
    t=datetime(2026,3,1,tzinfo=timezone.utc)+timedelta(minutes=15*i)
    p*=math.exp(.0003*math.sin(i*.17)+.0001)
    w.writerow([(t.replace(tzinfo=None) if naive else t).isoformat(),p,p,p,p,1])
 def test_reject_missing_timezone(self):
  self.write(naive=True)
  with self.assertRaisesRegex(ValueError,"timezone missing"):read_bars(self.path)
 def test_no_gap_imputation(self):
  self.write(skip=30);bars,_=read_bars(self.path);ss=states(bars,900)
  self.assertFalse(any(30<=int((datetime.fromisoformat(z["timestamp"])-bars[0][0]).total_seconds()/900)<=33 for z in ss))
  self.assertEqual(len(transitions(ss,900)),len(ss)-2)
 def test_exact_operator(self):
  A=[[.8,.1],[-.2,.9]];x=[1,.2];pairs=[]
  for _ in range(90):
   y=matvec(A,x);pairs.append((x,y));x=y
  B=operator_fit(pairs,2,1e-12)
  self.assertLess(max(abs(A[i][j]-B[i][j]) for i in range(2) for j in range(2)),1e-5)
 def test_commutator_and_generator(self):
  A=[[1,1],[0,1]];B=[[1,0],[1,1]]
  self.assertNotEqual(commutator(A,B),[[0,0],[0,0]])
  S,W=generator_parts(A)
  self.assertEqual([[S[i][j]+W[i][j] for j in range(2)] for i in range(2)],A)
 def test_temporal_split(self):
  self.write()
  r=run(dict(path=str(self.path),cadence_seconds=900,split_utc="2026-03-01T20:00:00Z"))
  self.assertGreater(r["train_transitions"],1);self.assertGreater(r["test_transitions"],1)
  self.assertEqual(r["kind"],"deterministic_measurement_only")
  self.assertEqual(len(r["source_sha256"]),64)

if __name__=="__main__":unittest.main()
