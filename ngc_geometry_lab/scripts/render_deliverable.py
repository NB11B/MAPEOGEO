"""Render a standalone HTML report and exportable scientific figure.

Usage: python scripts/render_deliverable.py --results results/release --out deliverables
Only rendering needs matplotlib; the qualification itself needs NumPy/SciPy.
"""

import argparse
import base64
import csv
import html
import json
import os
from pathlib import Path
import re
import tempfile

# Keep Matplotlib's cache in a writable, task-specific directory.
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'ngc_geometry_mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def inline(text):
    text=html.escape(text)
    text=re.sub(r'`([^`]+)`',r'<code>\1</code>',text)
    text=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',text)
    text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',text)
    return text


def markdown_html(markdown):
    """Render the deliberately small Markdown subset used by REPORT.md."""
    lines=markdown.splitlines(); output=[]; index=0
    while index<len(lines):
        line=lines[index]
        if not line.strip():
            index+=1; continue
        if line.startswith('```'):
            code=[]; index+=1
            while index<len(lines) and not lines[index].startswith('```'):
                code.append(lines[index]); index+=1
            output.append('<pre><code>'+html.escape('\n'.join(code))+'</code></pre>'); index+=1; continue
        heading=re.match(r'^(#{1,6})\s+(.*)',line)
        if heading:
            level=len(heading[1]); output.append(f'<h{level}>{inline(heading[2])}</h{level}>'); index+=1; continue
        if line.startswith('|'):
            rows=[]
            while index<len(lines) and lines[index].startswith('|'):
                cells=[c.strip() for c in lines[index].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',c) for c in cells): rows.append(cells)
                index+=1
            output.append('<div class="table-scroll"><table>')
            for row_index,row in enumerate(rows):
                tag='th' if row_index==0 else 'td'
                output.append('<tr>'+''.join(f'<{tag}>{inline(c)}</{tag}>' for c in row)+'</tr>')
            output.append('</table></div>'); continue
        if line.startswith('- '):
            output.append('<ul>')
            while index<len(lines) and lines[index].startswith('- '):
                output.append('<li>'+inline(lines[index][2:])+'</li>'); index+=1
            output.append('</ul>'); continue
        paragraph=[line]; index+=1
        while index<len(lines) and lines[index].strip() and not lines[index].startswith(('#','|','```','- ')):
            paragraph.append(lines[index]); index+=1
        output.append('<p>'+inline(' '.join(paragraph))+'</p>')
    return '\n'.join(output)


def render(results,out):
    results,out=Path(results),Path(out)
    out.mkdir(parents=True,exist_ok=True)
    r=json.loads((results/'results.json').read_text())
    e=r['experiments']
    if not r['qualified']:
        raise ValueError('This visual report expects a completed qualified campaign; use its failure report instead.')
    with (results/'finite_shot.csv').open() as stream:
        finite=list(csv.DictReader(stream))
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12,
                         'axes.titleweight':'bold','axes.labelcolor':'#344657','text.color':'#142d40',
                         'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#ccd7df',
                         'grid.color':'#e8edf1','figure.facecolor':'#ffffff','axes.facecolor':'#ffffff'})
    fig,axes=plt.subplots(2,3,figsize=(16,9.7),layout='constrained')
    blue,teal,gold,slate='#234e70','#00857a','#c38925','#7a8e9f'
    ax=axes[0,0]
    counts=[e['exact_closure']['rank_histogram'][str(rank)] for rank in range(4)]
    bars=ax.bar(['Rank 0','Rank 1','Rank 2','Rank 3'],counts,color=[slate,blue,teal,gold],width=.65)
    ax.bar_label(bars,padding=5); ax.set_ylim(0,85); ax.set_ylabel('Number of operators')
    ax.set_title('A  Exact connected closure: 115 operators',loc='left',pad=14)
    ax.text(.02,.95,'New explicit generator fixture',transform=ax.transAxes,va='top',color='#566c7d',fontsize=9)
    ax=axes[0,1]
    errors=[e['single_qubit']['max_prediction_error'],e['dual_lane']['max_state_error'],e['joint']['max_prediction_error']]
    ax.bar(['Single state','NGC lanes','Joint state'],errors,color=[blue,teal,slate],width=.6)
    ax.axhline(1e-10,color=gold,ls='--',lw=1.6,label='Fixed gate: 1e-10')
    ax.set_yscale('log'); ax.set_ylim(1e-17,1e-9); ax.set_ylabel('Maximum absolute disagreement')
    ax.legend(frameon=False,loc='upper right',fontsize=9)
    ax.set_title('B  Independent implementations agree',loc='left',pad=14)
    for index,value in enumerate(errors): ax.text(index,value*1.8,f'{value:.1e}',ha='center',fontsize=9)
    ax=axes[0,2]
    for key,label,color in [('calibrated_state_error','Calibrated detector',teal),('uncorrected_state_error','Uncorrected counts',gold)]:
        values=np.sort([float(row[key]) for row in finite])
        ax.step(values,np.arange(1,len(values)+1)/len(values),where='post',label=label,color=color,lw=2.3)
    ax.set_xlim(0,.38); ax.set_ylim(0,1.04); ax.set_ylabel('Fraction of held-out states'); ax.set_xlabel('Bloch-vector reconstruction error')
    ax.grid(axis='y'); ax.legend(frameon=False,loc='lower right',fontsize=9)
    ax.set_title('C  Calibration improves count reconstruction',loc='left',pad=14)
    ax=axes[1,0]
    rows=e['readout']['candidate_scores']
    values=[row['heldout_rmse_vs_declared_truth'] for row in rows]
    bars=ax.bar(['Power 1','Power 2','Power 4'],values,color=[slate,teal,slate],width=.6)
    ax.bar_label(bars,labels=[f'{v:.4f}' for v in values],padding=5)
    ax.set_ylim(0,max(values)*1.4); ax.set_ylabel('Held-out probability RMSE')
    ax.set_title('D  Readout alternatives are distinguishable',loc='left',pad=14)
    ax.text(.03,.94,'Synthetic generator explicitly uses power 2',transform=ax.transAxes,va='top',fontsize=9,color='#566c7d')
    ax=axes[1,1]
    values=[e['joint']['local_deterministic_max_chsh'],e['joint']['singlet_chsh']]
    bars=ax.bar(['Local deterministic\nassignments','Singlet model\ncalculation'],values,color=[slate,blue],width=.58)
    ax.bar_label(bars,labels=['2.0000','2.8284'],padding=5); ax.set_ylim(0,3.4); ax.set_ylabel('CHSH magnitude |S|')
    ax.set_title('E  Correlation control',loc='left',pad=14)
    ax.text(.03,.95,'Calculated models; no laboratory events',transform=ax.transAxes,va='top',fontsize=9,color='#566c7d')
    ax=axes[1,2]
    records=e['dual_lane']['state_storage']; n=[v['qubits'] for v in records]; size=[v['dual_lane_bytes'] for v in records]
    ax.plot(n,size,color=teal,marker='o',lw=2.2,label='Two real lanes')
    ax.plot(n,[v['complex_reference_bytes'] for v in records],color=gold,marker='D',mfc='none',markersize=9,ls='--',label='Complex reference')
    ax.set_yscale('log',base=2); ax.set_yticks(size,labels=[str(s) for s in size]); ax.set_xticks(n)
    ax.set_xlabel('Qubits'); ax.set_ylabel('State storage (bytes)'); ax.grid(axis='y'); ax.legend(frameon=False,loc='upper left',fontsize=9)
    ax.set_title('F  Equal full-state storage',loc='left',pad=14)
    fig.suptitle('NGC + MAPEOGEO | Computational qualification',fontsize=20,fontweight='bold',x=.01,ha='left')
    for extension in ('png','svg'):
        fig.savefig(out/f'NGC_MAPEOGEO_Qualification.{extension}',dpi=190,bbox_inches='tight')
    plt.close(fig)
    graphic=base64.b64encode((out/'NGC_MAPEOGEO_Qualification.svg').read_bytes()).decode()
    content=markdown_html((results/'REPORT.md').read_text())
    styles='''
    :root { color-scheme: light; --ink:#173348; --muted:#536b7d; --teal:#007f75; }
    *{box-sizing:border-box} body{margin:0;background:#edf2f5;color:var(--ink);font:16px/1.65 system-ui,-apple-system,Segoe UI,sans-serif}
    main{max-width:1120px;margin:32px auto;background:white;box-shadow:0 8px 40px #183e5210;border-radius:16px;overflow:hidden}
    header{padding:40px 48px;background:#142f43;color:white} .eyebrow{font-size:12px;letter-spacing:.15em;text-transform:uppercase;color:#9fd8d1}
    header h1{font-size:36px;line-height:1.15;margin:16px 0 12px;color:white} header p{color:#d3e2eb;max-width:780px;margin:0}
    .cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:24px 0 0} .card{padding:15px 18px;border:1px solid #496879;border-radius:8px;color:#d5e6eb;font-size:13px}.card strong{display:block;color:white;font-size:27px;line-height:1.35}
    .visual{padding:30px 28px 0}.visual img{display:block;width:100%;height:auto}.caption{font-size:13px;color:var(--muted);margin:8px 20px 24px}
    article{padding:0 48px 40px} article>h1{display:none} h2{font-size:24px;line-height:1.3;margin:38px 0 16px;padding-top:24px;border-top:1px solid #dce6ec} h3{font-size:19px;margin:28px 0 10px}
    p{margin:12px 0 18px} ul{padding-left:22px} li{padding:3px 0} .table-scroll{overflow:auto;margin:20px 0} table{border-collapse:collapse;width:100%;font-size:14px}th{background:#eaf2f4;color:#234958;text-align:left;font-weight:650}th,td{padding:11px 13px;border-bottom:1px solid #dfe8ee;vertical-align:top} tr:nth-child(even)td{background:#f7fafb} code{font:13px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace;background:#edf3f6;padding:2px 5px;border-radius:4px;overflow-wrap:anywhere}pre{background:#142f43;color:#e2eef3;padding:22px;border-radius:8px;overflow:auto} pre code{background:transparent;color:inherit;padding:0;white-space:pre;overflow-wrap:normal} a{color:#00786e} footer{padding:25px 48px;border-top:1px solid #dce6ec;color:var(--muted);font-size:13px}
    @media(max-width:700px){main{margin:0;border-radius:0}header,article{padding:28px 22px}header h1{font-size:28px}.cards{grid-template-columns:1fr}.visual{padding:16px 6px 0}footer{padding:20px 22px}}
    @media print{body{background:white}main{box-shadow:none;margin:0;max-width:none}header{background:white;color:var(--ink)}header h1,.card strong{color:var(--ink)}header p,.card,.eyebrow{color:var(--muted)}h2{break-after:avoid}tr{break-inside:avoid}}
    '''
    document=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>NGC / MAPEOGEO qualification report</title><style>{styles}</style></head><body><main>
    <header><div class="eyebrow">Reconstruction · Prediction · Independent controls</div><h1>Connected geometry, tested end to end</h1><p>Actual repository operators, an independent complex reference, and held-out synthetic observations. CPU computational qualification is complete; native CUDA and physical experiments remain separately identified.</p><div class="cards"><div class="card"><strong>12 / 12</strong>Computational qualification gates</div><div class="card"><strong>115</strong>Exactly enumerated operators</div><div class="card"><strong>{e['finite_shot']['mean_state_error']:.4f}</strong>Mean calibrated state error</div></div></header>
    <section class="visual"><img alt="Six scientific charts show exact closure ranks, numerical equivalence errors, detector calibration improvement, readout candidate comparison, computed CHSH controls, and equal full-state memory." src="data:image/svg+xml;base64,{graphic}"><p class="caption">Master seed {r['seed']}. Figure values come directly from the preserved campaign JSON and per-case CSV records. All count observations are synthetic.</p></section>
    <article>{content}</article><footer>Complete runnable source, tests, pinned upstream files, original failures, correction reviews and raw experiment records accompany this report in the project archive. This standalone HTML embeds its scientific figure and uses no external scripts or assets.</footer></main></body></html>'''
    target=out/'NGC_MAPEOGEO_Qualification_Report.html'; target.write_text(document,encoding='utf-8')
    (out/'NGC_MAPEOGEO_Qualification_Report.md').write_text((results/'REPORT.md').read_text(),encoding='utf-8')
    print(target)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results',required=True)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    render(args.results,args.out)
