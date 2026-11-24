"""Render the requested single figure; results are computed by analyze.py."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
try:import matplotlib
except ImportError:
    # Optional existing local plotting environment; a normal matplotlib install also works.
    sys.path.insert(0,str(ROOT.parents[2]/'tmp/tail_plot_deps'))
    import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

def main():
    r=json.loads((ROOT/'results.json').read_text(encoding='utf8'))
    if not r['complete']:raise SystemExit('Do not render a final figure from an incomplete run')
    fig,axes=plt.subplots(1,2,figsize=(13,5.3),gridspec_kw={'width_ratios':[1.3,1]})
    fig.patch.set_facecolor('#faf9f6')
    for ax in axes:ax.set_facecolor('#faf9f6');ax.spines[['top','right']].set_visible(False)
    colors=['#b24b35','#365c78'];x=np.arange(3);width=.32
    for j,(group,label) in enumerate([('witness','Rounding witness (n=196)'),('control','Matched stable (n=196)')]):
        vals=[100*r['tracks']['expression'][k]['groups'][group]['accuracy'] for k in ('official','relative_1pct','display')]
        bars=axes[0].bar(x+(j-.5)*width,vals,width,label=label,color=colors[j])
        axes[0].bar_label(bars,labels=[f'{v:.1f}%' for v in vals],padding=4,fontsize=10)
        printed=[100*r['tracks']['printed'][k]['groups'][group]['accuracy'] for k in ('official','relative_1pct','display')]
        axes[0].scatter(x+(j-.5)*width,printed,marker='_',s=220,color='#222222',linewidths=2,zorder=5)
    axes[0].set_xticks(x,['Official\n5 decimals','Relative\n1%','Human answer\ndisplay places'])
    axes[0].set_ylim(0,105);axes[0].set_ylabel('Accuracy (%)');axes[0].set_title('Unit-normalized expression accuracy',loc='left',fontweight='bold')
    handles,labels=axes[0].get_legend_handles_labels()
    handles.append(Line2D([0],[0],marker='_',markersize=14,markeredgewidth=2,color='#222222',linestyle='None'))
    labels.append('Printed final answer')
    fig.legend(handles,labels,frameon=False,loc='upper left',bbox_to_anchor=(.065,.925),ncol=3,fontsize=10)
    causes=[('alternative_source_precision','Alternate source precision','#2b7567'),('reasonable_alternative','Reasonable interpretation','#c49b38'),('reference_error','Reference problem','#796699'),('true_error','Model error','#b24b35'),('human_label_disagreement','Human/execution label mismatch','#a890a0'),('invalid_format','Invalid response','#555555'),('unresolved','Unresolved / mixed issues','#c3c3c3'),('unreviewed','Not reviewed','#222222')]
    bottoms=np.zeros(2);groups=['witness','control']
    for key,label,color in causes:
        vals=np.array([r['tracks']['expression']['official']['groups'][g]['causes'].get(key,0) for g in groups])
        if vals.sum():
            axes[1].bar(groups,vals,bottom=bottoms,label=label,color=color,width=.55)
            for i,v in enumerate(vals):
                if v:axes[1].text(i,bottoms[i]+v/2,str(v),ha='center',va='center',color='#242424' if key in ('reasonable_alternative','unresolved','human_label_disagreement') else 'white',fontsize=10,fontweight='bold')
            bottoms+=vals
    assert list(bottoms)==[r['tracks']['expression']['official']['groups'][g]['errors'] for g in groups], 'unplotted attribution category'
    axes[1].set_xticks([0,1],['Rounding witness','Matched stable']);axes[1].set_ylabel('Rejected expressions (count)')
    axes[1].set_title('Why official scoring rejects them',loc='left',fontweight='bold')
    axes[1].legend(frameon=False,fontsize=8,loc='upper left',bbox_to_anchor=(1.01,1))
    fig.suptitle('T1C · Financial QA scoring and input precision',x=.065,y=.99,ha='left',fontsize=15,fontweight='bold')
    dn=[r['tracks']['expression']['display']['groups'][g]['n'] for g in groups]
    fig.text(.065,.01,f'392 fresh one-question sessions · display-rule n={dn[0]}/{dn[1]} · source attribution reviewed separately from box membership',fontsize=8,color='#555555')
    fig.tight_layout(rect=(0,.035,1,.89))
    fig.savefig(ROOT/'t1c_results.png',dpi=180,bbox_inches='tight',facecolor=fig.get_facecolor())
    fig.savefig(ROOT/'t1c_results.pdf',bbox_inches='tight',facecolor=fig.get_facecolor())

if __name__=='__main__':main()
