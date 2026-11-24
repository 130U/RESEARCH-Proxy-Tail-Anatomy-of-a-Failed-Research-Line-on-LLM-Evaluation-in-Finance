"""Build readable tables, the requested waterfall, and a one-page decision."""
import csv
import hashlib
import json
import platform
import os
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
from prepare import HERE

def disposition(r):
    if r['stages']['duplicates']['status']=='certified_inside':return 'duplicate_determined'
    if r['stages']['sums']['status']=='certified_inside':return 'sum_determined'
    return r['final']

def write_csv(path,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    out=HERE/'results';s=json.loads((out/'summary.json').read_text(encoding='utf8'))
    rows=[json.loads(l) for l in (out/'per_question.jsonl').read_text(encoding='utf8').splitlines()]
    reviews={r['id']:r for part in ('a','b') for r in json.loads((HERE/f'review_{part}.json').read_text(encoding='utf8'))}
    c=Counter(disposition(r) for r in rows);n=len(rows);keep=c['retained']
    assert sum(c.values())==196
    s['mutually_exclusive_waterfall_dispositions']=dict(c)
    s['reviewed_equations']=sum(len(r['equations']) for r in reviews.values())
    s['questions_with_equations']=sum(bool(r['equations']) for r in reviews.values())
    s['duplicate_disclosures']=sum(len(r['duplicates']) for r in reviews.values())
    s['questions_with_duplicates']=sum(bool(r['duplicates']) for r in reviews.values())
    s['questions_with_shrunk_input_box']=sum(r['stages']['original']['bounds']!=r['stages']['duplicates']['bounds'] for r in rows)
    s['questions_with_shrunk_output_after_sums']=sum(
        F(r['stages']['sums']['enclosure']['hi'])-F(r['stages']['sums']['enclosure']['lo']) <
        F(r['stages']['duplicates']['enclosure']['hi'])-F(r['stages']['duplicates']['enclosure']['lo']) for r in rows)
    (out/'delivery_summary.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    compact=[]
    for r in rows:
        compact.append({'id':r['id'],'category':r['category'],'sample40':r['sample40'],
            'review_verdict':r['review_verdict'],'final_semantics_first':r['final'],'waterfall_disposition':disposition(r),
            'original_lo':r['stages']['original']['enclosure']['lo'],'original_hi':r['stages']['original']['enclosure']['hi'],
            'after_duplicates_lo':r['stages']['duplicates']['enclosure']['lo'],'after_duplicates_hi':r['stages']['duplicates']['enclosure']['hi'],
            'after_sums_lo':r['stages']['sums']['enclosure']['lo'],'after_sums_hi':r['stages']['sums']['enclosure']['hi'],
            'inside_value':r['inside_witness']['value'] if r['inside_witness'] else '',
            'outside_value':r['stages']['sums'].get('witness_value',''),
            'range_exact':r['stages']['sums']['range_exact'],'review_reason':r['review_reason']})
    write_csv(out/'question_summary.csv',compact)
    write_csv(out/'sample40_review.csv',[{'id':r['id'],'binding_ok':reviews[r['id']]['binding_ok'],
        'quantity_ok':reviews[r['id']]['quantity_ok'],'program_ok':reviews[r['id']]['program_ok'],
        'verdict':r['review_verdict'],'reason':r['review_reason']} for r in rows if r['sample40']])
    inventory=[{'id':r['id'],'bounds':r['stages']['sums']['bounds'],'constraints':r['stages']['sums']['inventory']} for r in rows]
    (out/'constraint_inventory.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in inventory),encoding='utf8')
    # Published waterfall follows numerical stages, then excludes semantic
    # problems; the MSI semantic uncertainty overlaps the duplicate removal.
    dup=c['duplicate_determined'];sums=c['sum_determined'];ref=c['reference_incompatible']
    invalid=c['semantic_invalid'];uncertain=c['semantic_uncertain'];other=n-keep-dup-sums-ref-invalid-uncertain
    assert other==0
    stages=[n,n-dup,n-dup-sums,n-dup-sums-ref,keep]
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties
    font_path=os.environ.get('T1B_FONT_PATH','C:/Windows/Fonts/arial.ttf')
    font=FontProperties(fname=font_path) if Path(font_path).exists() else FontProperties(family='sans-serif')
    plt.rcParams.update({'axes.unicode_minus':False,'pdf.fonttype':42,'svg.fonttype':'none'})
    fig,ax=plt.subplots(figsize=(11.7,6.3),layout='constrained')
    colors=['#254B65','#4A8E84','#4A8E84','#AD7551','#C48662','#254B65']
    heights=[n,dup,sums,ref,invalid+uncertain,keep]
    bottoms=[0,stages[1],stages[2],stages[3],keep,0]
    labels=['Original candidates','Duplicate disclosure\ntightening','Add sum\nconstraints','Reference answer\nincompatible','Semantic review\nexclusions','Final retained']
    for i,(h,b,col) in enumerate(zip(heights,bottoms,colors)):
        if h:ax.bar(i,h,bottom=b,width=.64,color=col,zorder=3)
        else:ax.plot([i-.32,i+.32],[b,b],color=col,lw=3,zorder=3)
        if i in (0,5):text=str(h);y=h+4
        else:text=f'−{h}' if h else '0';y=b+h+4
        ax.text(i,y,text,ha='center',va='bottom',fontsize=14,fontweight='bold',color='#243B4A',fontproperties=font)
    levels=[n,stages[1],stages[2],stages[3],keep]
    for i,level in enumerate(levels):ax.plot([i+.32,i+.68],[level,level],color='#A5ADB3',lw=1)
    ax.axhline(58,color='#966E35',ls='--',lw=1.4,zorder=2)
    ax.text(.65,61,'Retention threshold: 58 / 1,147',fontproperties=font,color='#966E35',fontsize=10)
    ax.set_xticks(range(6),labels,fontproperties=font,fontsize=11)
    ax.set_ylabel('Questions',fontproperties=font,fontsize=11)
    ax.set_ylim(0,220);ax.set_xlim(-.6,5.6)
    ax.set_yticks([0,50,100,150,200]);ax.grid(axis='y',alpha=.15,zorder=0)
    for side in ('top','right'):ax.spines[side].set_visible(False)
    ax.spines['left'].set_color('#CBD1D5');ax.spines['bottom'].set_color('#CBD1D5')
    ax.tick_params(axis='both',length=0)
    fig.suptitle(f'T1B: after tightening and review, {keep} questions still have feasible values both inside and outside the tolerance',fontproperties=font,fontsize=17,color='#203C50')
    ax.set_title(f'{keep}/1,147 = {keep/1147:.2%} of the test set; 1% is the audit tolerance',fontproperties=font,fontsize=11,loc='left',pad=20,color='#53616B')
    fig.supxlabel('Scope: full FinQA question context. Semantic review found 37 questions with clear problems and 20 doubtful ones; 1 of them was already removed at the duplicate-disclosure stage.',fontproperties=font,fontsize=9,color='#53616B')
    for suffix in ('png','pdf','svg'):fig.savefig(out/f'waterfall.{suffix}',dpi=200,facecolor='white')
    svg=out/'waterfall.svg'
    svg.write_bytes(('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf8').splitlines())+'\n').encode('utf8'))
    plt.close(fig)
    one=f'''# T1B one-page summary: the conclusion holds; the fraction falls from 17.09% to {keep/1147:.2%}

**Finally retained: {keep}/1,147 = {keep/1147:.2%}, above the task threshold of 58 questions.** For each retained question we saved two sets of rational inputs that lie strictly inside the rounding intervals and exactly satisfy all confirmed linear constraints: one gives a result inside the gold's 1% tolerance, the other outside. This is an existence result, not the probability that models usually answer wrongly, and not the benchmark's annotation error rate.

Scope fixed in advance: the complete tables and text provided by FinQA; other pages of the original annual reports are not covered. Only T1's 196 test witnesses are covered; the semantic correctness of unreviewed questions is not extrapolated.

|Sequential attribution (mutually exclusive)|Questions|
|---|---:|
|Still has feasible values both inside and outside the tolerance|{keep}|
|Duplicate disclosures move the numeric interval inside the tolerance|{dup}|
|Further sum constraints move the interval inside the tolerance|{sums}|
|After tightening, the whole interval is incompatible with gold|{ref}|
|Of the rest, clear problems with question meaning, binding or quantity type|{invalid}|
|Of the rest, semantics cannot be confirmed; conservatively removed|{uncertain}|
|Total|196|

The only question tightened numerically by duplicate disclosures, MSI/2008/page_69.pdf-2, also has a semantic doubt of its own ("decrease in loss" versus "growth"); the semantic review total is therefore **37 clear problems + 20 doubtful**, and that question must not be deducted a second time. CME/2010/page_69.pdf-2 becomes incompatible with gold only under the additional assumption that the listed components exhaust the total credit facilities; the original "including" is not enough to support this assumption, so it is kept only as a sensitivity analysis and does not enter the main count.

**Sample review:** with fixed seed 20261116, 40 questions were sampled: 27 passed, 8 had clear problems, 5 were doubtful. Clear errors are 20%; counting the doubtful ones as risk too, 32.5%, more than a quarter. The fix was carried out under the conservative convention: check units, years, economic roles, exact vs. rounded values, program coverage and denominator direction; review all 196 questions one by one, remove all 57 non-passing questions, and rerun T1 on the original 1147 questions to confirm that the original cohort of 196 is reproducible. gold was not silently corrected, and we do not claim that the other 951 questions passed semantic review.

**Computation and review:** {s['duplicate_disclosures']} additional disclosures of the same fact, {s['reviewed_equations']} confirmed linear relations; for {s['questions_with_shrunk_input_box']} questions the input box narrowed because of duplicate disclosures, and for {s['questions_with_shrunk_output_after_sums']} questions the output range narrowed further because of sums. {s['exact_final_ranges']}/196 final ranges reach exact extrema; the rest, if any, use proven outer envelopes. 588 stage certificates and {keep} inside/outside witness pairs passed independent replay.

This item-by-item semantic review was performed and cross-checked by AI agents and **is not an independent human sign-off**. The mathematical proofs are conditional on the listed source bindings, rounding model and constraint inventory; we do not claim to exhaust all possible nonlinear semantic constraints in the documents. FinQA can define the displayed numbers themselves as arithmetic inputs, so this result still does not replace T1C's model-scoring experiment.

[Waterfall chart](results/waterfall.png) · [Full report](REPORT.md) · [Per-question summary](results/question_summary.csv) · [40-question review](results/sample40_review.csv) · [Per-question certificates](results/per_question.jsonl)
'''
    (HERE/'ONE_PAGE.md').write_text(one,encoding='utf8')
    import scipy,sympy
    manifest={'python':platform.python_version(),'scipy':scipy.__version__,'sympy':sympy.__version__,'matplotlib':matplotlib.__version__,
        'files_sha256':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob('*.py'))},
        'review_sha256':s['review_sha256']}
    (out/'run_environment.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'waterfall':stages,'dispositions':dict(c),'equations':s['reviewed_equations'],'exact_ranges':s['exact_final_ranges']},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
