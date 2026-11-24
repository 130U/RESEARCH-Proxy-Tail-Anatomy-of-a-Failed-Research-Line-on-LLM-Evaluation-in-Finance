"""Create the single four-panel T1 research figure from saved results."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parent
s=json.loads((ROOT/"results/summary.json").read_text(encoding="utf8"))
g=json.loads((ROOT/"results/growth_summary.json").read_text(encoding="utf8"))
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,
                    "axes.spines.right":False,"axes.titleweight":"bold","figure.facecolor":"white",
                    "axes.labelcolor":"#334155","text.color":"#0f172a","svg.fonttype":"none"})
fig,axes=plt.subplots(2,2,figsize=(12,8.6))
blue,orange,gray="#176b87","#c76d27","#64748b"

ax=axes[0,0]
splits=["test","dev","train"]
x=np.arange(3)
for j,(rule,color,label) in enumerate([("relative_1pct",blue,"1% relative tolerance"),("display",orange,"Gold displayed precision")]):
    vals=[100*s[k][rule].get("witnessed_outside",0)/s[k]["n_all"] for k in splits]
    bars=ax.bar(x+(j-.5)*.34,vals,.32,color=color,label=label)
    for b,v in zip(bars,vals): ax.text(b.get_x()+b.get_width()/2,v+.7,f"{v:.1f}%",ha="center",fontsize=9)
ax.axhline(5,color=gray,lw=1,ls="--",label="Continue gate: 5%")
ax.set_xticks(x,[f"{k.title()}\nN = {s[k]['n_all']:,}" for k in splits])
ax.set_ylim(0,55)
ax.set_ylabel("Witnessed crossings / ALL questions (%)")
ax.set_title("A  FinQA census: conditional lower counts",loc="left",pad=12)
ax.legend(frameon=False,fontsize=8.5,loc="upper left")

ax=axes[0,1]
groups=["growth","difference","ratio","sum"]
cs=[s["test"]["by_operation"][k] for k in groups]
vals=[100*c.get("witnessed_outside",0)/c["n"] for c in cs]
bars=ax.bar(np.arange(4),vals,color=[orange,blue,blue,blue],width=.62)
for b,c in zip(bars,cs):
    ax.text(b.get_x()+b.get_width()/2,b.get_height()+1,f"{c.get('witnessed_outside',0)}/{c['n']}",ha="center",fontsize=9)
ax.axhline(15,color=gray,lw=1,ls="--")
ax.set_xticks(range(4),["Growth","Difference","Ratio","Sum"])
ax.set_ylim(0,50)
ax.set_ylabel("Witnessed crossings / analyzed group (%)")
ax.set_title("B  Public test: 1% tolerance by operation",loc="left",pad=12)

ax=axes[1,0]
cs=[s["test"]["by_min_sig"][str(k)] for k in range(1,6)]
vals=[100*c.get("witnessed_outside",0)/c["n"] for c in cs]
ax.plot(range(1,6),vals,"o-",color=blue,lw=2,ms=7)
for k,v,c in zip(range(1,6),vals,cs): ax.annotate(f"{c.get('witnessed_outside',0)}/{c['n']}",(k,v),xytext=(0,9),textcoords="offset points",ha="center",fontsize=9)
ax.set_xticks(range(1,6),["1","2","3","4","5+"])
ax.set_ylim(-4,110)
ax.set_xlabel("Fewest displayed significant digits among inputs")
ax.set_ylabel("Witnessed crossings / analyzed bin (%)")
ax.set_title("C  Public test: low precision is sensitive",loc="left",pad=12)

ax=axes[1,1]
factors=[1,10,100,1000]
vals=[100*g["by_factor"][str(f)]["exact_crossing"]/g["by_factor"][str(f)]["n"] for f in factors]
ax.plot(range(4),vals,"o-",color=blue,lw=2,ms=7,label="Exact growth range")
pred=[100*g["by_factor"][str(f)]["first_order_crossing"]/g["by_factor"][str(f)]["n"] for f in factors]
ax.plot(range(4),pred,"x",color=orange,ms=10,mew=2,label="First-order prediction")
for k,v,f in zip(range(4),vals,factors):
    ax.annotate(f"{g['by_factor'][str(f)]['exact_crossing']:,}",(k,v),xytext=(0,9),textcoords="offset points",ha="center",fontsize=9)
ax.set_xticks(range(4),["Current","10× finer","100× finer","1,000× finer"])
ax.set_ylim(-4,53)
ax.set_ylabel("Exact crossings / strict growth subset (%)")
ax.set_title(f"D  Simulated refinement: {g['n_eligible_questions']:,} growth questions",loc="left",pad=12)
ax.legend(frameon=False,loc="upper right",fontsize=9)
ax.set_xlabel("Same centers, narrower input intervals; no new disclosure")
for ax in axes.flat:
    ax.grid(axis="y",alpha=.13)
    ax.set_axisbelow(True)
fig.suptitle("Rounding precision can move gold-program outputs beyond scoring tolerances",fontsize=16,x=.07,ha="left",y=.98)
fig.text(.07,.925,"Conditional input-box audit  |  FinQA public splits  |  2026-11-16",fontsize=11,color=gray)
fig.text(.07,.035,f"Test: {s['test']['n_analyzed']:,}/{s['test']['n_all']:,} questions analyzed; {s['test']['n_all']-s['test']['n_analyzed']} excluded, {s['test']['relative_1pct'].get('unresolved',0)} unresolved at 1%. Counts concern source-box sensitivity, not labeling errors.\n"
         "Source binding, rounding interpretation and independence are assumptions. Panel D is a synthetic counterfactual, not a higher-precision filing.",fontsize=9,color=gray)
fig.subplots_adjust(left=.075,right=.98,bottom=.14,top=.86,wspace=.28,hspace=.49)
for ext in ["png","pdf"]:
    fig.savefig(ROOT/"results"/f"rounding_summary.{ext}",dpi=190,bbox_inches="tight")
print("Saved results/rounding_summary.png and .pdf")
