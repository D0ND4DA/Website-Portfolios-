"""Entry-filter and stop/target study for the VWMA/WMA trend-riding entries.

Usage:
    python3 trading/strategy_study.py EXPORT_15S.csv [MORE_15S.csv ...] [--five EXPORT_5M.csv]
                                      [--cost 2] [--usd-per-pt 17.5] [--max-hold-min 60]

Inputs are TradingView CSV exports of a 15-second chart with the indicator
(trading/vwma_wma_proximity.pine) and your three MACD indicators (8/22/9, 12/30/12,
72/200/12 with SMA signal lines) applied. Several exports can be passed; overlapping
bars are de-duplicated (later files win), so exporting twice a week builds history.

Exports made with the current indicator contain "5m MACD A/B/C hist" columns. Older
exports don't; for those pass the 5m chart export with --five (its three MACD
histograms are mapped to each 15s bar using the last *completed* 5m bar).

Every trend signal is rebuilt from the exported averages and MACDs with the current
rules, so results don't depend on the indicator version used for the export.
Prices on a Heikin Ashi chart are HA prices: targets/stops touched by HA highs/lows are
slightly optimistic for small targets.
"""
import argparse
import csv

import numpy as np
import pandas as pd

TZ = "America/New_York"


def load(path):
    cols = next(csv.reader(open(path)))
    names, seen = [], {}
    for c in cols:
        seen[c] = seen.get(c, -1) + 1
        names.append(c if seen[c] == 0 else f"{c}_{seen[c]}")
    return pd.read_csv(path, header=0, names=names)


def build(paths, five):
    frames = [load(p) for p in paths]
    d = pd.concat(frames).drop_duplicates("time", keep="last").sort_values("time").reset_index(drop=True)
    if "5m MACD A hist" in d.columns and d["5m MACD A hist"].notna().any() and five is None:
        d["h5a"], d["h5b"], d["h5c"] = d["5m MACD A hist"], d["5m MACD B hist"], d["5m MACD C hist"]
    else:
        if five is None:
            raise SystemExit("These exports have no 5m MACD columns; pass the 5m chart export with --five")
        f5 = load(five).set_index("time")
        key = (d.time // 300) * 300 - 300  # last completed 5m bar (non-repainting)
        for k, src in zip(["h5a", "h5b", "h5c"], ["Histogram", "Histogram_1", "Histogram_2"]):
            d[k] = key.map(f5[src])
    t = pd.to_datetime(d.time, unit="s", utc=True).dt.tz_convert(TZ)
    d["dt"] = t
    m = (t.dt.hour * 60 + t.dt.minute).values
    wd = t.dt.weekday.values
    inmain = ((wd <= 4) & (m >= 120) & (m < 950)) | ((wd == 6) & (m >= 1080)) | ((wd == 0) & (m < 120))
    d["ins"] = inmain & ~((wd <= 4) & (m >= 570) & (m < 580))
    d["mins"] = m
    c, tr, v5 = d.close, d["15m WMA (trend)"], d["5m VWMA"]
    w15, vf, vs = d["15s WMA"], d["15s VWMA fast"], d["15s VWMA slow"]
    h15 = [d["Histogram"], d["Histogram_1"], d["Histogram_2"]]
    h5 = [d.h5a, d.h5b, d.h5c]
    g5 = sum((x > 0).astype(int) for x in h5)
    r5 = sum((x < 0).astype(int) for x in h5)
    d["g5"], d["r5"] = g5, r5
    m5L, m5S = (g5 >= 2) | (h5[2] > 0), (r5 >= 2) | (h5[2] < 0)
    m15L = (h15[0] > 0) & (h15[1] > 0) & (h15[2] > 0)
    m15S = (h15[0] < 0) & (h15[1] < 0) & (h15[2] < 0)
    d["trL"] = (c > tr) & (w15 > v5) & (vf < vs) & m5L & m15L & d.ins
    d["trS"] = (c < tr) & (w15 < v5) & (vf > vs) & m5S & m15S & d.ins
    return d


class Sim:
    def __init__(self, d, cost, max_hold_bars):
        self.c, self.h, self.l = d.close.values, d.high.values, d.low.values
        self.tr, self.tm, self.n = d["15m WMA (trend)"].values, d.time.values, len(d)
        self.cost, self.H = cost, max_hold_bars

    def run(self, startL, startS, kind, S=None, T=None):
        c, h, l, tr, tm, n = self.c, self.h, self.l, self.tr, self.tm, self.n
        out_rows, busy = [], -1
        for i in range(1, n):
            d_ = 1 if startL[i] else -1 if startS[i] else 0
            if d_ == 0 or i <= busy:
                continue
            e, got, res, j = c[i], False, None, i
            for j in range(i + 1, min(i + 1 + self.H, n)):
                if tm[j] - tm[j - 1] > 3600:  # data gap: close at last bar before it
                    j -= 1
                    break
                adv = (e - l[j]) if d_ == 1 else (h[j] - e)
                fav = (h[j] - e) if d_ == 1 else (e - l[j])
                if kind == "full":
                    if adv >= S:
                        res = -S
                    elif fav >= T:
                        res = T
                elif kind == "half":
                    if adv >= S:
                        res = 0.5 * T - 0.5 * S if got else -S
                    else:
                        if not got and fav >= T:
                            got = True
                        if (c[j] - tr[j]) * d_ < 0:
                            r = (c[j] - e) * d_
                            res = 0.5 * T + 0.5 * r if got else r
                if res is not None:
                    break
            if res is None:  # time limit / data gap
                r = (c[j] - e) * d_
                res = 0.5 * T + 0.5 * r if got else r
            out_rows.append((tm[i], d_, res - self.cost))
            busy = j
        return pd.DataFrame(out_rows, columns=["t", "dir", "pts"])


def starts(d, mask=None):
    tL, tS = d.trL.values, d.trS.values
    sL = tL & ~np.r_[False, tL[:-1]]
    sS = tS & ~np.r_[False, tS[:-1]]
    if mask is not None:
        sL, sS = sL & mask[0], sS & mask[1]
    return sL, sS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exports", nargs="+")
    ap.add_argument("--five")
    ap.add_argument("--cost", type=float, default=2.0, help="points per trade (spread + slippage)")
    ap.add_argument("--usd-per-pt", type=float, default=17.5, help="$ per point at your lot size")
    ap.add_argument("--max-hold-min", type=int, default=60)
    a = ap.parse_args()
    d = build(a.exports, a.five)
    # trading week starts Sunday 18:00 NY: shift 6h so Sunday evening counts toward the following week
    d["week"] = (d.dt + pd.Timedelta(hours=6)).dt.strftime("%G-W%V")
    sim = Sim(d, a.cost, a.max_hold_min * 4)
    USD = a.usd_per_pt
    print(f"Data {d.dt.iloc[0]} -> {d.dt.iloc[-1]}, {len(d)} bars, weeks: {sorted(d.week.unique())}")

    # ---- entry quality: forward return after each trend start (no exit rule)
    sL, sS = starts(d)
    idx = np.where(sL | sS)[0]
    c, tm = d.close.values, d.time.values
    rows = []
    for i in idx:
        st = 1 if sL[i] else -1
        j = min(i + a.max_hold_min * 4, len(d) - 1)
        mins = d.mins.iloc[i]
        sess = ("Overnight 18:00-02:00" if (mins >= 1080 or mins < 120) else "London 02:00-09:30" if mins < 570
                else "NY open 09:40-11:30" if mins < 690 else "Midday 11:30-14:00" if mins < 840 else "Afternoon 14:00-15:50")
        rows.append(dict(week=d.week.iloc[i], dir="long" if st == 1 else "short", sess=sess,
                         g5=int(d.g5.iloc[i] if st == 1 else d.r5.iloc[i]),
                         fwd=(c[j] - c[i]) * st - a.cost))
    E = pd.DataFrame(rows)
    print(f"\nTrend starts: {len(E)}.  Net points {a.max_hold_min} min after entry, by filter and week:")
    for col in ["dir", "sess", "g5"]:
        tab = E.pivot_table(index=col, columns="week", values="fwd", aggfunc="mean").round(1)
        tab["n"] = E.groupby(col).size()
        tab["all"] = E.groupby(col).fwd.mean().round(1)
        print(f"\n-- {col}" + (" (5m MACDs agreeing with direction)" if col == "g5" else ""))
        print(tab.to_string())

    # ---- stop/target grid with and without the midday filter
    notMid = ~((d.mins.values >= 690) & (d.mins.values < 840))
    for name, mask in [("No filter", None), ("Skip midday 11:30-14:00", (notMid, notMid))]:
        sL, sS = starts(d, mask)
        res = []
        for kind in ["full", "half"]:
            for S in range(10, 65, 5):
                for T in range(5, 105, 5):
                    r = sim.run(sL, sS, kind, S, T)
                    p = r.pts
                    wk = r.assign(w=(pd.to_datetime(r.t, unit="s", utc=True).dt.tz_convert(TZ) + pd.Timedelta(hours=6)).dt.strftime("%G-W%V")).groupby("w").pts.mean()
                    eq = np.cumsum(p.values * USD)
                    pf = p[p > 0].sum() / -p[p <= 0].sum() if (p <= 0).any() else np.inf
                    res.append(dict(kind=kind, stop=S, target=T, trades=len(p), usd_per_trade=p.mean() * USD,
                                    total_usd=p.sum() * USD, pf=pf, weeks_positive=f"{(wk > 0).sum()}/{len(wk)}",
                                    all_weeks_positive=bool((wk > 0).all()),
                                    max_dd_usd=(eq - np.maximum.accumulate(eq)).min()))
        g = pd.DataFrame(res)
        print(f"\n===== {name}: {sL.sum() + sS.sum()} trend starts; combos profitable {int((g.usd_per_trade > 0).sum())}/{len(g)}, "
              f"profitable in every week {int(g.all_weeks_positive.sum())}")
        top = g[g.all_weeks_positive].sort_values("pf", ascending=False).head(10)
        if len(top):
            print(top.round(2).to_string(index=False))
        out = f"study_grid_{'midday' if mask is not None else 'all'}.csv"
        g.to_csv(out, index=False)
        print(f"(full grid written to {out})")


if __name__ == "__main__":
    main()
