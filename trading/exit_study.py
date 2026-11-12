"""Exit study for the VWMA/WMA trend-riding entries.

Usage: python3 trading/exit_study.py <TradingView 15s CSV export with the indicator applied>
Entries = first bar of a LONG/SHORT trend state inside trading hours (NY time).
Prices in a Heikin Ashi export are HA prices; results are in points per trade.
"""
import sys, csv, numpy as np, pandas as pd
path=sys.argv[1]
cols=next(csv.reader(open(path))); new=[];k=0
for c in cols:
    if c in ("MACD","Signal Line","Histogram","Cross"): new.append(f"{c}_{k//4}"); k+=1
    else: new.append(c)
df=pd.read_csv(path,header=0,names=new)
t=pd.to_datetime(df.time,unit='s',utc=True).dt.tz_convert('America/New_York')
m=t.dt.hour*60+t.dt.minute; wd=t.dt.weekday
inmain=((wd<=4)&(m>=120)&(m<950))|((wd==6)&(m>=1080))|((wd==0)&(m<120))
ins=(inmain&~((wd<=4)&(m>=570)&(m<580))).values
ts=df['Trend state (1 long, -1 short)'].values
c=df.close.values; h=df.high.values; l=df.low.values
w15=df['15s WMA'].values; v5=df['5m VWMA'].values; tr=df['15m WMA (trend)'].values
vf=df['15s VWMA fast'].values; vs=df['15s VWMA slow'].values
hA=df['Histogram_0'].values; hB=df['Histogram_1'].values; hC=df['Histogram_2'].values
n=len(df)
# entries: first bar of a trend state, in session
ent=[i for i in range(1,n) if ts[i]!=0 and ts[i]!=ts[i-1] and ins[i]]
print("trend-start entries in session:",len(ent), " long",sum(ts[i]==1 for i in ent)," short",sum(ts[i]==-1 for i in ent))
H=240  # 60 min max hold
def run(rule):
    res=[]
    for i in ent:
        d=ts[i]; e=c[i]; out=None
        for j in range(i+1,min(i+1+H,n)):
            r=rule(i,j,d,e)
            if r is not None: out=r; break
        if out is None: j=min(i+H,n-1); out=(c[j]-e)*d
        res.append(out)
    return np.array(res)
def stats(name,r):
    w=r[r>0]; L=r[r<=0]
    pf = w.sum()/-L.sum() if L.sum()<0 else np.inf
    print(f"{name:44s} n={len(r):3d} avg={r.mean():6.1f} med={np.median(r):6.1f} win={100*(r>0).mean():5.1f}% PF={pf:4.2f} worst={r.min():7.1f}")
# MFE/MAE
mfe=[];mae=[]
for i in ent:
    d=ts[i]; e=c[i]; js=range(i+1,min(i+1+H,n))
    fav=[(h[j]-e) if d==1 else (e-l[j]) for j in js]; adv=[(e-l[j]) if d==1 else (h[j]-e) for j in js]
    mfe.append(max(fav)); mae.append(max(adv))
mfe=np.array(mfe); mae=np.array(mae)
print("MFE pts (60m) pct 25/50/75:", np.percentile(mfe,[25,50,75]).round(1), " MAE pct 25/50/75:", np.percentile(mae,[25,50,75]).round(1))
print()
stats("Hold 60 min (baseline)", run(lambda i,j,d,e: None))
stats("Exit: trend state ends", run(lambda i,j,d,e: (c[j]-e)*d if ts[j]!=d else None))
stats("Exit: close crosses 15s WMA(200)", run(lambda i,j,d,e: (c[j]-e)*d if (c[j]-w15[j])*d<0 else None))
stats("Exit: close crosses 15s VWMA(72)", run(lambda i,j,d,e: (c[j]-e)*d if (c[j]-vs[j])*d<0 else None))
stats("Exit: close crosses 15s VWMA(21)", run(lambda i,j,d,e: (c[j]-e)*d if (c[j]-vf[j])*d<0 else None))
stats("Exit: close crosses 5m VWMA", run(lambda i,j,d,e: (c[j]-e)*d if (c[j]-v5[j])*d<0 else None))
stats("Exit: close crosses 15m WMA", run(lambda i,j,d,e: (c[j]-e)*d if (c[j]-tr[j])*d<0 else None))
stats("Exit: 15s MACD 72/200/12 flips", run(lambda i,j,d,e: (c[j]-e)*d if hC[j]*d<0 else None))
stats("Exit: 15s MACD 12/30/12 flips", run(lambda i,j,d,e: (c[j]-e)*d if hB[j]*d<0 else None))
stats("Exit: 15s MACD 8/22/9 flips", run(lambda i,j,d,e: (c[j]-e)*d if hA[j]*d<0 else None))
stats("Exit: 2 of 3 15s MACDs flip", run(lambda i,j,d,e: (c[j]-e)*d if (int(hA[j]*d<0)+int(hB[j]*d<0)+int(hC[j]*d<0))>=2 else None))
print()
# fixed stop/target grid (stop checked first if both touched in a bar)
def st(S,T):
    def f(i,j,d,e):
        adv=(e-l[j]) if d==1 else (h[j]-e); fav=(h[j]-e) if d==1 else (e-l[j])
        if adv>=S: return -S
        if fav>=T: return T
        return None
    return f
best=[]
for S in [10,15,20,25,30,40,50]:
    for T in [10,15,20,30,40,60,80]:
        r=run(st(S,T)); best.append((r.mean(),S,T,(r>0).mean()))
best.sort(reverse=True)
print("Top fixed stop/target combos (avg pts/trade):")
for a,S,T,wr in best[:6]: print(f"   stop {S:2d} / target {T:2d}: avg {a:5.1f}  win {100*wr:4.1f}%")
print("   ... worst:", [(round(a,1),S,T) for a,S,T,_ in best[-3:]])
# trailing stop
for TS in [10,15,20,30,40]:
    def f(i,j,d,e,TS=TS,state={}):
        key=i
        if j==i+1: state[key]=e
        state[key]= max(state[key],h[j]) if d==1 else min(state[key],l[j])
        stop= state[key]-TS if d==1 else state[key]+TS
        if (d==1 and l[j]<=stop) or (d==-1 and h[j]>=stop): return (stop-e)*d
        return None
    stats(f"Trailing stop {TS} pts", run(f))

print()
def combo(sig,S):
    def f(i,j,d,e):
        adv=(e-l[j]) if d==1 else (h[j]-e)
        if adv>=S: return -S
        return sig(i,j,d,e)
    return f
x15m=lambda i,j,d,e: (c[j]-e)*d if (c[j]-tr[j])*d<0 else None
x5v=lambda i,j,d,e: (c[j]-e)*d if (c[j]-v5[j])*d<0 else None
for S in [30,40,50,60]:
    stats(f"15m WMA cross + hard stop {S}", run(combo(x15m,S)))
for S in [30,40,50,60]:
    stats(f"5m VWMA cross + hard stop {S}", run(combo(x5v,S)))
for T in [20,40,60,120,240]:
    stats(f"Time stop {T//4} min", run(lambda i,j,d,e,T=T: (c[j]-e)*d if j-i>=T else None))
# split by half to check stability for the leading rules
import random
half=len(ent)//2
for nm,rule in [("Hold 60",lambda i,j,d,e: None),("15m WMA + stop 50",combo(x15m,50)),("stop40/tgt80",st(40,80))]:
    r=run(rule); print(f"{nm:20s} first half avg {r[:half].mean():6.1f} | second half avg {r[half:].mean():6.1f}")
