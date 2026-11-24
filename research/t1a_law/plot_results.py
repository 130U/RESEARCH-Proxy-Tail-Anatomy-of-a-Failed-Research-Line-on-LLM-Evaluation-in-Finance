"""One exportable figure: delta threshold, digit budget, and tolerance curve."""
from pathlib import Path
import csv
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter, ScalarFormatter
import numpy as np

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"results"


def main():
    rows=[json.loads(s) for s in (OUT/"per_question.jsonl").read_text(encoding="utf-8").splitlines()]
    b=json.loads((OUT/"benford_summary.json").read_text())
    p=json.loads((OUT/"probability_summary.json").read_text())
    curve=list(csv.DictReader((OUT/"tolerance_curve.csv").open()))
    blue="#245a81"; orange="#c76335"; gray="#68747c"
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,
        "axes.spines.right":False,"axes.labelcolor":"#24333e","text.color":"#24333e",
        "axes.titleweight":"bold","savefig.facecolor":"white"})
    fig,ax=plt.subplots(1,3,figsize=(16.5,5.2),gridspec_kw={"width_ratios":[1.15,1,1.1]})
    growth=[r for r in rows if r["growth"] is not None]
    delta=np.array([r["growth"]["delta"]["decimal"] for r in growth])
    status=np.array([r["exact_status"]=="outside" for r in growth])
    edges=np.array([.8,3,10,30,60,100,150,300,1000,1e4,1e5,1e6,1e8])
    for left,right in zip(edges,edges[1:]):
        selected=(delta>=left)&(delta<right)
        if selected.any():
            rate=status[selected].mean();mid=np.sqrt(left*right)
            ax[0].plot([left,right],[rate,rate],color=blue,lw=2)
            ax[0].plot(mid,rate,"o",color=blue,ms=5)
    ax[0].plot([.8,100,100,1e8],[1,1,0,0],"--",color=orange,lw=1.7,label=r"Rule: $\Delta<100$")
    ax[0].axvline(100,color=orange,lw=.7,alpha=.6)
    ax[0].plot([],[],"o-",color=blue,label="Exact, binned")
    ax[0].set(xscale="log",xlim=(.8,1e8),ylim=(-.035,1.06),
              xlabel=r"Unit-aligned $\Delta=|b-a|/(h_a+h_b)$",ylabel="Share outside the 1% band",
              title="A   The 100-unit approximation")
    ax[0].yaxis.set_major_formatter(PercentFormatter(1))
    ax[0].legend(loc="center right",frameon=False,fontsize=9)
    ax[0].text(.04,.08,"1,427 canonical growth questions\n97.97% classification agreement",transform=ax[0].transAxes,fontsize=9)
    budget=b["by_k_a"]
    ks=[r["k_a"] for r in budget]
    ax[1].plot(ks,[r["observed_gold_rate"] for r in budget],"o-",color=blue,label="Observed")
    ax[1].plot(ks,[r["marginal_prediction"] for r in budget],"s--",color=orange,label="Benford + digit budget",ms=4)
    ax[1].set(xlabel=r"Displayed significant digits in base $a$",ylabel="Share outside the 1% band",
              ylim=(-.035,1.06),xticks=ks,title="B   Population precision budget")
    ax[1].yaxis.set_major_formatter(PercentFormatter(1))
    ax[1].legend(loc="upper right",frameon=False,fontsize=9)
    ax[1].text(.04,.11,"Overall: 41.52% predicted\n40.50% observed  |  +1.01 pp",transform=ax[1].transAxes,fontsize=9)
    test=[r for r in curve if r["split"]=="test"]
    ts=[float(r["tau"])*100 for r in test]
    worst=[float(r["outside_fraction_analyzed"]) for r in test]
    prob=[p["groups"]["test"]["by_tolerance"][str(float(r["tau"]))]["analyzed_rate"] for r in test]
    ax[2].plot(ts,worst,"o-",color=blue,label="Worst-case existence")
    ax[2].plot(ts,prob,"s-",color=orange,label="Uniform-error expectation",ms=4)
    ax[2].set(xscale="log",xticks=ts,xlabel="Relative tolerance (%)",ylabel="Share of 731 analyzable test questions",
              ylim=(-.01,.62),title="C   Worst case and probability")
    ax[2].xaxis.set_major_formatter(ScalarFormatter())
    ax[2].yaxis.set_major_formatter(PercentFormatter(1))
    ax[2].legend(loc="upper right",frameon=False,fontsize=9)
    ax[2].axvline(1,color=gray,lw=.7,ls=":")
    ax[2].annotate("26.81%",(1,worst[2]),xytext=(7,5),textcoords="offset points",color=blue,fontsize=9)
    ax[2].annotate("13.49%",(1,prob[2]),xytext=(7,-12),textcoords="offset points",color=orange,fontsize=9)
    for a in ax:
        a.grid(axis="y",alpha=.17)
        a.tick_params(length=3)
    fig.suptitle("Displayed precision constrains growth-rate precision",x=.06,ha="left",fontsize=17,fontweight="bold",y=.99)
    fig.text(.06,.025,"Conditional on T1 input bindings and independent rounding boxes. 1% is an audit tolerance. "
             "Benford adds mantissa and independence assumptions; uniform probabilities are model-based.",fontsize=9,color=gray)
    fig.tight_layout(rect=(.015,.08,.995,.93),w_pad=2.3)
    fig.savefig(OUT/"t1a_law.png",dpi=220)
    fig.savefig(OUT/"t1a_law.pdf")
    plt.close(fig)


if __name__=="__main__":main()
