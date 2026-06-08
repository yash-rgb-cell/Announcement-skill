#!/usr/bin/env python3
"""Render the four standard Lilly coverage-report charts as PNGs (locked palette)."""
import argparse, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

POSITIVE="#7BA75B"; NEUTRAL="#F2C310"; NEGATIVE="#C0241C"
MAROON="#521204"; PEACH="#F7CCAA"; BROWN="#8A4B3A"; GOLD="#FABF3A"

plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11,
                     "axes.edgecolor":"#BFBFBF","axes.linewidth":0.8})

def _save(fig,path):
    fig.savefig(path,dpi=200,bbox_inches="tight",facecolor="white"); plt.close(fig); return path

def sentiment_chart(rows,path,title="Sentiment Analysis"):
    labels=[r[0] for r in rows]; y=list(range(len(rows)))[::-1]
    pos=[r[1] for r in rows]; neu=[r[2] for r in rows]; neg=[r[3] for r in rows]
    fig,ax=plt.subplots(figsize=(7,0.7*len(rows)+1.6))
    ax.barh(y,pos,color=POSITIVE,label="Positive")
    ax.barh(y,neu,left=pos,color=NEUTRAL,label="Neutral")
    ax.barh(y,neg,left=[p+n for p,n in zip(pos,neu)],color=NEGATIVE,label="Negative")
    for i,yy in enumerate(y):
        cum=0
        for val,col in ((pos[i],POSITIVE),(neu[i],NEUTRAL),(neg[i],NEGATIVE)):
            if val>=4:
                tc="white" if col==NEGATIVE else "black"
                ax.text(cum+val/2,yy,f"{val:.0f}%",ha="center",va="center",
                        fontsize=10,fontweight="bold",color=tc)
            cum+=val
    ax.set_yticks(list(y)); ax.set_yticklabels(labels,fontweight="bold")
    ax.set_xlim(0,100); ax.xaxis.set_major_formatter(PercentFormatter())
    ax.set_xticks(range(0,101,20)); ax.set_axisbelow(True)
    ax.xaxis.grid(True,color="#D9D9D9",linewidth=0.7); ax.set_frame_on(False); ax.tick_params(length=0)
    ax.set_title(title,fontweight="bold",loc="left",fontsize=13,pad=14)
    ax.legend(loc="upper center",bbox_to_anchor=(0.5,-0.18),ncol=3,frameon=False,fontsize=10)
    return _save(fig,path)

def reach_by_coverage_chart(segments,path,title="Type Of Coverage by Reach"):
    colors={"News & Digital Articles":MAROON,"Social Media":PEACH,"Broadcast":"#A86B4E","Podcasts":BROWN,"Podcast":BROWN}
    fig,ax=plt.subplots(figsize=(7,2.6)); left=0
    for label,pct in segments:
        ax.barh(0,pct,left=left,height=0.5,color=colors.get(label,MAROON),label=label)
        if pct>=4:
            tc="#3A0E04" if colors.get(label,MAROON) in (PEACH,"#F7CCAA") else "white"
            ax.text(left+pct/2,0,f"{pct:.0f}%",ha="center",va="center",color=tc,fontweight="bold")
        left+=pct
    ax.set_xlim(0,100); ax.set_ylim(-0.5,0.7); ax.set_yticks([])
    ax.xaxis.set_major_formatter(PercentFormatter()); ax.set_xticks(range(0,101,20))
    ax.set_axisbelow(True); ax.xaxis.grid(True,color="#D9D9D9",linewidth=0.7)
    ax.set_frame_on(False); ax.tick_params(length=0)
    ax.set_title(title,fontweight="bold",loc="left",fontsize=13,pad=22)
    ax.legend(loc="lower center",bbox_to_anchor=(0.5,1.0),ncol=len(segments),frameon=False,fontsize=10)
    return _save(fig,path)

def social_volume_chart(channels,path,title="Social Media Volume Breakdown"):
    names=[c[0] for c in channels]; vals=[c[1] for c in channels]
    fig,ax=plt.subplots(figsize=(7,4)); ax.bar(names,vals,color=MAROON,width=0.6)
    ax.set_ylabel("Mentions"); ax.set_axisbelow(True)
    ax.yaxis.grid(True,color="#D9D9D9",linewidth=0.7)
    for s in ("top","right"): ax.spines[s].set_visible(False)
    ax.set_xticks(range(len(names))); ax.set_xticklabels(names,fontweight="bold")
    ax.set_title(title,fontweight="bold",loc="left",fontsize=13,pad=14)
    return _save(fig,path)

def sov_chart(shares,path,title="Competitor Share of Voice"):
    names=[s[0] for s in shares]; vals=[s[1] for s in shares]
    palette=[MAROON,GOLD,PEACH,BROWN]
    fig,ax=plt.subplots(figsize=(6,4))
    ax.pie(vals,colors=palette[:len(names)],startangle=90,counterclock=False,
           wedgeprops=dict(width=0.45,edgecolor="white"))
    ax.legend(names,loc="center left",bbox_to_anchor=(1.0,0.5),frameon=False)
    ax.set_title(title,fontweight="bold",loc="left",fontsize=13,pad=14)
    return _save(fig,path)

def render_all(metrics,outdir):
    od=outdir.rstrip("/"); out={}
    if metrics.get("sentiment"): out["sentiment"]=sentiment_chart(metrics["sentiment"],f"{od}/sentiment.png")
    if metrics.get("reach_by_coverage"): out["reach"]=reach_by_coverage_chart(metrics["reach_by_coverage"],f"{od}/reach.png")
    if metrics.get("social_volume"): out["social_volume"]=social_volume_chart(metrics["social_volume"],f"{od}/social_volume.png")
    if metrics.get("sov"): out["sov"]=sov_chart(metrics["sov"],f"{od}/sov.png")
    return out

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("metrics_json"); ap.add_argument("--outdir",default=".")
    a=ap.parse_args(); m=json.load(open(a.metrics_json))
    paths=render_all(m,a.outdir); print("Charts written:",", ".join(paths.values()))
