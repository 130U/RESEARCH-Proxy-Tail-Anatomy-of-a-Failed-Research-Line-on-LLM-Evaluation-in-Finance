"""Requested four-panel figure, drawn only from saved row-level results."""
from pathlib import Path
import csv,json,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT=Path(__file__).resolve().parent
def read(name):return list(csv.DictReader((ROOT/name).open(encoding='utf-8-sig')))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','pdf.fonttype':42})
fig,axs=plt.subplots(2,2,figsize=(13,9),layout='constrained')
colors={'finqa':'#266b99','tatqa':'#cb6b28','FinQA':'#266b99','TAT-QA':'#cb6b28'}
rows=json.loads((ROOT/'part1_rows_all.json').read_text(encoding='utf-8'))
edges=[0,10,30,100,300,1000,float('inf')];labels=['<10','10–30','30–100','100–300','300–1000','≥1000']
ax=axs[0,0]
for ds in ['finqa','tatqa']:
    obs=[];pred=[]
    for lo,hi in zip(edges,edges[1:]):
        g=[r for r in rows if r['status']=='compatible' and r['dataset']==ds and r['kind']=='percent' and lo<=r['delta']<hi]
        obs.append(np.mean([r['mismatch'] for r in g]) if g else np.nan);pred.append(np.mean([r['mismatch_probability'] for r in g]) if g else np.nan)
    ax.plot(range(6),obs,'o-',color=colors[ds],label=ds.upper()+' observed')
    ax.plot(range(6),pred,'--',color=colors[ds],alpha=.8,label=ds.upper()+' uniform model')
ax.set_xticks(range(6),labels);ax.set_ylim(-.02,1);ax.yaxis.set_major_formatter(PercentFormatter(1))
ax.set(title='A  Printed percentage change ≠ recomputation',xlabel='Δ = |new − base| / (h_new + h_base)',ylabel='Mismatch at printed precision')
ax.text(.97,.96,'Level differences: 0 / 982 observed\n25% predicted by equal-precision model',ha='right',va='top',transform=ax.transAxes,fontsize=9)
ax.legend(loc='upper left',bbox_to_anchor=(0,.99),fontsize=8,frameon=False)
ax=axs[0,1];pos=read('part1_positions.csv');xs=np.arange(12)
selected=[r for r in pos if r['kind']=='percent'];n=sum(int(r['n']) for r in selected if r['bin']=='0')
obs=[sum(int(r['observed_count']) for r in selected if int(r['bin'])==i)/n for i in range(12)]
pred=[sum(float(r['predicted_probability'])*int(r['n']) for r in selected if int(r['bin'])==i)/n for i in range(12)]
ax.bar(xs-.18,obs,.36,color='#266b99',label='Observed printed centers')
ax.bar(xs+.18,pred,.36,color='#a9c6d8',label='Uniform-input + output-rounding model')
ax.set_xticks(xs,['<0','0–.1','.1–.2','.2–.3','.3–.4','.4–.5','.5–.6','.6–.7','.7–.8','.8–.9','.9–1','>1'],rotation=45)
ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set(title='B  Position within the exact output range',xlabel='(printed center − minimum) / (maximum − minimum)',ylabel='Share of compatible percentage rows')
ax.legend(fontsize=8,frameon=False);ax.text(.5,.68,'A printed interval may intersect the range\neven when its center lies outside [0, 1].',transform=ax.transAxes,ha='center',fontsize=9)
ax=axs[1,0];rr=read('part2_growth_plot.csv')
for ds in ['FinQA','TAT-QA']:
    g=[r for r in rr if r['dataset']==ds]
    ax.scatter([float(r['exact_rule_threshold'])*100 for r in g],[float(r['gap'])*100 for r in g],s=65,color=colors[ds],label=ds,zorder=3)
limits=[.0005,300];ax.plot(limits,limits,'--',color='#888',lw=1)
ax.set_xscale('log');ax.set_yscale('log');ax.set_xlim(limits);ax.set_ylim(limits)
ax.set(title='C  Comparing two growth rates: 4 pairs',xlabel='Exact threshold for a fixed order (percentage points)',ylabel='Difference between displayed-center rates (pp)')
ax.text(.30,.87,'Above line: fixed order\nBelow line: input-box flip possible',transform=ax.transAxes,fontsize=9)
unstable=next(r for r in rr if r['unstable']=='True')
ax.annotate('EPS: flips in input box;\nshare-count disclosure resolves it',xy=(float(unstable['exact_rule_threshold'])*100,float(unstable['gap'])*100),xytext=(4,.02),arrowprops={'arrowstyle':'->','color':'#555'},fontsize=8)
ax.legend(loc='lower right',frameon=False,fontsize=9)
ax=axs[1,1];rr=read('part3_growth_precision_plot.csv')
for ds in ['FinQA','TAT-QA']:
    g=sorted([r for r in rr if r['dataset']==ds],key=lambda r:int(r['k']))
    ax.plot([int(r['k']) for r in g],[float(r['observed']) for r in g],'o-',color=colors[ds],label=ds+' observed')
    ax.plot([int(r['k']) for r in g],[float(r['predicted']) for r in g],'--',color=colors[ds],label=ds+' frozen distribution model')
ax.set_xticks(range(1,11));ax.set_ylim(-.02,1.03);ax.yaxis.set_major_formatter(PercentFormatter(1))
ax.set(title='D  Growth questions across datasets',xlabel='Significant digits in the baseline input',ylabel='Not determined within 1% of program center')
ax.legend(fontsize=8,frameon=False)
fig.suptitle('T1g · Rounding consequences and a frozen cross-dataset prediction',fontsize=16,weight='bold')
for ext in ['png','pdf','svg']:fig.savefig(ROOT/f't1g_consequence.{ext}',dpi=180)
print('Saved four-panel PNG, PDF and SVG')
