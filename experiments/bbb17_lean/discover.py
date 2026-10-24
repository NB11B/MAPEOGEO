"""BBB17 phase discovery; observations are not formal proofs."""
import argparse, json
from collections import Counter
from pathlib import Path

SPEC=('1RL0RB_1LC1RB_0LK0LD_1RE1LD_0RF0RB_0LG0LG_1LH1LG_0RA0RI_1RJ1RI_1RF1RF_0RA1LK_0LM0LM_0LN1LM_1RO1LN_0RA0RP_0RQ1RP_1RL1RQ')
STATES='ABCDEFGHIJKLMNOPQ'

def rules():
    result={}
    groups=SPEC.split('_')
    assert len(groups)==17
    for s,group in zip(STATES,groups):
        assert len(group)==6
        for b in (0,1):
            w,d,n=group[3*b:3*b+3]
            result[s,b]=(int(w),1 if d=='R' else -1,n)
    return result

TABLE=rules()
def discover(limit=1000000):
    q='A';head=0;tape=set();beeps=[];boundaries=[];visits=Counter()
    for t in range(limit):
        visits[q]+=1
        if q=='O':
            beeps.append(t)
            rank=len(beeps)
            k=0
            while k*(k+1)//2 <rank:k+=1
            if k*(k+1)//2==rank:
                boundaries.append({'rank':k,'step':t,'head':head,'ones':len(tape),
                 'left':min(tape) if tape else None,'right':max(tape) if tape else None})
        w,d,q=TABLE[q,int(head in tape)]
        if w:tape.add(head)
        else:tape.discard(head)
        head+=d
    hypothesis={
      'triangular_checkpoints_head_minus_one':all(b['head']==-1 for b in boundaries),
      'triangular_checkpoints_left_boundary':all(b['left']==-(b['rank']+1) for b in boundaries),
      'triangular_checkpoints_ones_triangular':all(b['ones']==b['rank']*(b['rank']+1)//2 for b in boundaries)}
    return {'steps':limit,'beeps':len(beeps),'last_beep':beeps[-1] if beeps else None,
      'boundaries':boundaries,'hypotheses':hypothesis,'universal_proof':False,
      'state':q,'head':head,'tape_ones':len(tape),'spec':SPEC}
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--steps',type=int,default=1000000)
    parser.add_argument('--out',default='discovery.json')
    a=parser.parse_args()
    x=discover(a.steps)
    Path(a.out).write_text(json.dumps(x,indent=2)+'\n')
    print(json.dumps({'beeps':x['beeps'],'hypotheses':x['hypotheses']},indent=2))
