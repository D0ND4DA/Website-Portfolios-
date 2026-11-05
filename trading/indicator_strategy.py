#!/usr/bin/env python3
"""
Multi-timeframe MACD / VWMA trading script (15-second trigger, 5-minute filter).

Indicators (from the TradingView layout):
    - Volume, WMA 200 (shown in the snapshot, not used in the entry rules)
    - VWMA 21, VWMA 72
    - MACD 8 / 22 / 9    (close, EMA oscillator, EMA signal)
    - MACD 12 / 30 / 12
    - MACD 72 / 200 / 12
    A MACD is "green" when its histogram (MACD line - signal line) is above 0.

LONG ENTRY - every condition true on a closed 15-second bar:
    15s, MACDs:  all three MACDs are green, AND at least one of them turned
                 green on this bar (its line crossed above its signal line).
    15s, VWMAs:  VWMA21 is below VWMA72.
    15s, price:  price crosses above VWMA72 on this bar, OR price is
                 already above VWMA21.
    5m filter:   on the last *completed* 5-minute bar, at least two of the three
                 MACDs are green, OR the 72/200 MACD is green.
    15m trend:   uptrend per the 21-length WMA on the last *completed*
                 15-minute bar. --trend-mode picks the definition:
                   price (default): 15s close is above the 15m WMA21
                   slope:           15m WMA21 is rising (above its prior bar)
                   both:            price above AND WMA21 rising

EXIT (long): the 72/200 MACD on the 15-second timeframe turns red
    (histogram drops below 0). Exit fills at that bar's close.
    Optional safety nets, off by default: --stop-atr / --target-atr add an
    ATR stop loss / take profit checked intrabar on high/low.

Short rules haven't been defined yet; `--allow-short` turns on the exact
mirror of the long rules as a stand-in.

Data: one feed of fine-grained bars (15s or smaller, or ticks). The script
resamples it to 15s, 5m and 15m itself, so every timeframe comes from the same data.
    --csv PATH   columns: time/datetime/timestamp, open, high, low, close, volume
                 (tick files with price + volume/size also work)
    --demo       synthetic data for testing the script

Warm-up: the 72/200 MACD on 5-minute bars needs ~200 five-minute bars
(~17 hours) of history before the filter is meaningful; the script won't
trade until then.

Research / backtest only. It places no orders. Not financial advice.

Examples:
    python indicator_strategy.py --demo
    python indicator_strategy.py --csv nq_15s.csv --point-value 20
    python indicator_strategy.py --csv nq_ticks.csv --point-value 2 --contracts 3
    python indicator_strategy.py --csv nq_15s.csv --live-signal
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

MACDS = {"fast": (8, 22, 9), "mid": (12, 30, 12), "slow": (72, 200, 12)}


# --------------------------------------------------------------------------- #
# Indicators
# --------------------------------------------------------------------------- #
def ema(s: pd.Series, length: int) -> pd.Series:
    return s.ewm(span=length, adjust=False).mean()


def wma(s: pd.Series, length: int) -> pd.Series:
    w = np.arange(1, length + 1, dtype=float)
    return s.rolling(length).apply(lambda x: np.dot(x, w) / w.sum(), raw=True)


def vwma(close: pd.Series, volume: pd.Series, length: int) -> pd.Series:
    return (close * volume).rolling(length).sum() / volume.rolling(length).sum()


def atr(df: pd.DataFrame, length: int = 14) -> pd.Series:
    pc = df["close"].shift()
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / length, adjust=False).mean()


def add_macds(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for name, (f, s, sig) in MACDS.items():
        line = ema(out["close"], f) - ema(out["close"], s)
        signal = ema(line, sig)
        out[f"macd_{name}"] = line
        out[f"macd_{name}_sig"] = signal
        out[f"macd_{name}_hist"] = line - signal
        out[f"green_{name}"] = out[f"macd_{name}_hist"] > 0
        out[f"turned_green_{name}"] = out[f"green_{name}"] & ~out[f"green_{name}"].shift(fill_value=True)
        out[f"turned_red_{name}"] = ~out[f"green_{name}"] & out[f"green_{name}"].shift(fill_value=False)
    return out


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
def resample(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """OHLCV resample; bars are labelled by their START time (TradingView style)."""
    out = df.resample(rule, label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    )
    return out.dropna(subset=["close"])


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    tcol = next((c for c in ("time", "datetime", "date", "timestamp") if c in df.columns), None)
    if tcol is None:
        raise ValueError("CSV needs a time/datetime/date/timestamp column")
    t = df[tcol]
    df.index = pd.to_datetime(t, unit="s") if np.issubdtype(t.dtype, np.number) else pd.to_datetime(t)
    df = df.sort_index()

    for alias in ("vol", "size", "qty", "quantity"):
        if "volume" not in df.columns and alias in df.columns:
            df["volume"] = df[alias]
    if "close" not in df.columns and "price" in df.columns:  # tick data
        df["open"] = df["high"] = df["low"] = df["close"] = df["price"]
    return df[["open", "high", "low", "close", "volume"]].astype(float)


def demo_data(hours: float = 40, start: float = 28160.0, seed: int = 7) -> pd.DataFrame:
    n = int(hours * 3600 / 15)
    rng = np.random.default_rng(seed)
    drift = np.sin(np.linspace(0, 20, n)) * 0.25
    close = start + np.cumsum(drift + rng.normal(0, 1.6, n))
    open_ = np.r_[start, close[:-1]]
    high = np.maximum(open_, close) + rng.uniform(0, 1.2, n)
    low = np.minimum(open_, close) - rng.uniform(0, 1.2, n)
    vol = rng.integers(5, 150, n).astype(float)
    idx = pd.date_range("2026-11-04 00:00", periods=n, freq="15s")
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": vol}, idx)


# --------------------------------------------------------------------------- #
# Strategy
# --------------------------------------------------------------------------- #
@dataclass
class Config:
    trigger_tf: str = "15s"
    filter_tf: str = "5min"
    trend_tf: str = "15min"
    trend_wma_len: int = 21
    trend_mode: str = "price"  # price | slope | both
    vwma_fast: int = 21
    vwma_slow: int = 72
    wma_len: int = 200
    atr_len: int = 14
    stop_atr: float = 0.0  # 0 = off
    target_atr: float = 0.0  # 0 = off
    point_value: float = 20.0  # NQ $20/pt, MNQ $2/pt
    contracts: int = 1
    commission: float = 2.50  # per contract per side
    slippage_pts: float = 0.25  # per side
    allow_short: bool = False


def build(raw: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Return 15s bars with indicators, the 5m filter merged in, and signals."""
    ltf = add_macds(resample(raw, cfg.trigger_tf))
    ltf["vwma21"] = vwma(ltf["close"], ltf["volume"], cfg.vwma_fast)
    ltf["vwma72"] = vwma(ltf["close"], ltf["volume"], cfg.vwma_slow)
    ltf["wma200"] = wma(ltf["close"], cfg.wma_len)
    ltf["atr"] = atr(ltf, cfg.atr_len)

    # ---- 5-minute filter, using only COMPLETED 5m bars (no lookahead) ----
    htf = add_macds(resample(raw, cfg.filter_tf))
    greens = htf[["green_fast", "green_mid", "green_slow"]].sum(axis=1)
    reds = (~htf[["green_fast", "green_mid", "green_slow"]]).sum(axis=1)
    htf["htf_long_ok"] = (greens >= 2) | htf["green_slow"]
    htf["htf_short_ok"] = (reds >= 2) | ~htf["green_slow"]
    # 5m bar is known once it closes: start + 5m
    htf_ready = htf[["htf_long_ok", "htf_short_ok", "macd_fast_hist", "macd_mid_hist", "macd_slow_hist"]].copy()
    htf_ready.columns = ["htf_long_ok", "htf_short_ok", "htf_fast_hist", "htf_mid_hist", "htf_slow_hist"]
    htf_ready["htf_close_time"] = htf_ready.index + pd.Timedelta(cfg.filter_tf)
    htf_ready = htf_ready.reset_index(drop=True)

    # 15s bar is decided at its close: start + 15s
    ltf["bar_close_time"] = ltf.index + pd.Timedelta(cfg.trigger_tf)
    merged = pd.merge_asof(
        ltf.reset_index().rename(columns={"index": "time"}).sort_values("bar_close_time"),
        htf_ready.sort_values("htf_close_time"),
        left_on="bar_close_time",
        right_on="htf_close_time",
        direction="backward",
    ).set_index(ltf.index.name or "time")
    merged.index.name = "time"
    for col in ("htf_long_ok", "htf_short_ok"):
        merged[col] = merged[col].astype("boolean").fillna(False).astype(bool)

    # ---- 15-minute trend: WMA21 from COMPLETED 15m bars only ----
    tf = resample(raw, cfg.trend_tf)
    trend = pd.DataFrame({"trend_wma": wma(tf["close"], cfg.trend_wma_len)})
    trend["trend_wma_prev"] = trend["trend_wma"].shift()
    trend["trend_close_time"] = trend.index + pd.Timedelta(cfg.trend_tf)
    merged = pd.merge_asof(
        merged.reset_index().sort_values("bar_close_time"),
        trend.dropna().reset_index(drop=True).sort_values("trend_close_time"),
        left_on="bar_close_time",
        right_on="trend_close_time",
        direction="backward",
    ).set_index("time")

    return add_signals(merged, cfg)


def add_signals(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    out = df.copy()
    names = list(MACDS)
    c, v21, v72 = out["close"], out["vwma21"], out["vwma72"]

    # ---- 15m trend (WMA21) ----
    w, wp = out["trend_wma"], out["trend_wma_prev"]
    up = {"price": c > w, "slope": w > wp, "both": (c > w) & (w > wp)}[cfg.trend_mode]
    dn = {"price": c < w, "slope": w < wp, "both": (c < w) & (w < wp)}[cfg.trend_mode]
    out["trend_up"], out["trend_dn"] = up.fillna(False), dn.fillna(False)

    # ---- LONG (as specified) ----
    all_green = np.logical_and.reduce([out[f"green_{n}"] for n in names])
    any_turned_green = np.logical_or.reduce([out[f"turned_green_{n}"] for n in names])
    vwma_stack_long = v21 < v72
    cross_above_72 = (c > v72) & (c.shift() <= v72.shift())
    price_long = cross_above_72 | (c > v21)
    out["long_entry"] = all_green & any_turned_green & vwma_stack_long & price_long & out["htf_long_ok"] & out["trend_up"]

    # ---- SHORT (placeholder mirror; only used with --allow-short) ----
    all_red = np.logical_and.reduce([~out[f"green_{n}"] for n in names])
    any_turned_red = np.logical_or.reduce([out[f"turned_red_{n}"] for n in names])
    cross_below_72 = (c < v72) & (c.shift() >= v72.shift())
    price_short = cross_below_72 | (c < v21)
    out["short_entry"] = all_red & any_turned_red & (v21 > v72) & price_short & out["htf_short_ok"] & out["trend_dn"]

    # ---- EXITS: 15s 72/200 MACD turns against the position ----
    out["long_exit"] = ~out["green_slow"]
    out["short_exit"] = out["green_slow"]

    # warm-up: 15s indicators + 200 bars of 5m data for the 72/200 MACD
    warm_until = out.index[0] + pd.Timedelta(cfg.filter_tf) * (MACDS["slow"][1] + MACDS["slow"][2])
    early = out.index < warm_until
    out.loc[early, ["long_entry", "short_entry"]] = False
    return out


# --------------------------------------------------------------------------- #
# Backtest
# --------------------------------------------------------------------------- #
@dataclass
class Trade:
    side: str
    entry_time: pd.Timestamp
    entry: float
    stop: float
    target: float
    exit_time: pd.Timestamp | None = None
    exit: float | None = None
    reason: str = ""
    pnl: float = 0.0


@dataclass
class Result:
    trades: list[Trade] = field(default_factory=list)
    equity: pd.Series | None = None


def backtest(df: pd.DataFrame, cfg: Config) -> Result:
    """Signals fire on a 15s bar's close; entries fill at the next bar's open."""
    res, pos, pending = Result(), None, None
    equity, curve = 0.0, []
    cost = cfg.commission * cfg.contracts
    idx = df.index
    o, h, l, c, a = (df[k].to_numpy() for k in ("open", "high", "low", "close", "atr"))
    le, se = df["long_entry"].to_numpy(), df["short_entry"].to_numpy()
    lx, sx = df["long_exit"].to_numpy(), df["short_exit"].to_numpy()

    def close_pos(i: int, price: float, reason: str) -> None:
        nonlocal pos, equity
        d = 1 if pos.side == "long" else -1
        fill = price - d * cfg.slippage_pts
        pos.pnl = (fill - pos.entry) * d * cfg.point_value * cfg.contracts - 2 * cost
        pos.exit_time, pos.exit, pos.reason = idx[i], fill, reason
        equity += pos.pnl
        res.trades.append(pos)
        pos = None

    for i in range(len(df)):
        if pending and pos is None:
            d = 1 if pending == "long" else -1
            fill = o[i] + d * cfg.slippage_pts
            stop = fill - d * cfg.stop_atr * a[i - 1] if cfg.stop_atr > 0 else d * -np.inf
            target = fill + d * cfg.target_atr * a[i - 1] if cfg.target_atr > 0 else d * np.inf
            pos = Trade(pending, idx[i], fill, stop, target)
        pending = None

        if pos is not None:
            if pos.side == "long":
                if l[i] <= pos.stop:
                    close_pos(i, min(o[i], pos.stop), "stop")
                elif h[i] >= pos.target:
                    close_pos(i, max(o[i], pos.target), "target")
            else:
                if h[i] >= pos.stop:
                    close_pos(i, max(o[i], pos.stop), "stop")
                elif l[i] <= pos.target:
                    close_pos(i, min(o[i], pos.target), "target")

        if pos is not None and ((pos.side == "long" and lx[i]) or (pos.side == "short" and sx[i])):
            close_pos(i, c[i], "signal")

        if pos is None:
            if le[i]:
                pending = "long"
            elif se[i] and cfg.allow_short:
                pending = "short"

        open_pnl = 0.0
        if pos is not None:
            d = 1 if pos.side == "long" else -1
            open_pnl = (c[i] - pos.entry) * d * cfg.point_value * cfg.contracts
        curve.append(equity + open_pnl)

    if pos is not None:
        close_pos(len(df) - 1, c[-1], "end of data")
        curve[-1] = equity

    res.equity = pd.Series(curve, index=idx, name="equity")
    return res


def summarize(res: Result) -> str:
    t = res.trades
    if not t:
        return "No trades. Need ~17h+ of history for the 5m 72/200 MACD to warm up, or the rules never lined up."
    pnl = np.array([x.pnl for x in t])
    wins, losses = pnl[pnl > 0], pnl[pnl <= 0]
    dd = (res.equity - res.equity.cummax()).min()
    pf = wins.sum() / abs(losses.sum()) if losses.sum() else float("inf")
    return "\n".join([
        f"Trades:         {len(t)}  (long {sum(x.side == 'long' for x in t)}, short {sum(x.side == 'short' for x in t)})",
        f"Win rate:       {len(wins) / len(t):.1%}",
        f"Net P&L:        ${pnl.sum():,.2f}",
        f"Avg win/loss:   ${wins.mean() if len(wins) else 0:,.2f} / ${losses.mean() if len(losses) else 0:,.2f}",
        f"Profit factor:  {pf:.2f}",
        f"Max drawdown:   ${dd:,.2f}",
        f"Exit reasons:   {pd.Series([x.reason for x in t]).value_counts().to_dict()}",
    ])


def snapshot(df: pd.DataFrame) -> str:
    r = df.iloc[-1]
    dot = lambda g: "GREEN" if g else "red  "
    lines = [
        f"Last 15s bar {df.index[-1]}  close {r['close']:,.2f}  vol {r['volume']:,.0f}",
        f"  VWMA21 {r['vwma21']:,.2f}  VWMA72 {r['vwma72']:,.2f}  WMA200 {r['wma200']:,.2f}"
        f"  -> 21 {'<' if r['vwma21'] < r['vwma72'] else '>='} 72",
    ]
    for n, (f, s, sig) in MACDS.items():
        lines.append(
            f"  15s MACD {f}/{s}/{sig}: {dot(r[f'green_{n}'])} hist {r[f'macd_{n}_hist']:7.2f}"
            f"{'  <- turned green' if r[f'turned_green_{n}'] else ''}"
        )
    lines.append(
        f"  5m  MACD hist  8/22 {r['htf_fast_hist']:6.2f} | 12/30 {r['htf_mid_hist']:6.2f} | 72/200 {r['htf_slow_hist']:6.2f}"
        f"  -> 5m filter {'PASS' if r['htf_long_ok'] else 'FAIL'} (long)"
    )
    trend = "UP" if r["trend_up"] else "DOWN" if r["trend_dn"] else "neutral"
    lines.append(f"  15m WMA21 {r['trend_wma']:,.2f} (prev {r['trend_wma_prev']:,.2f})  -> trend {trend}")
    lines.append(f"  Signal: {'LONG ENTRY' if r['long_entry'] else 'SHORT ENTRY' if r['short_entry'] else 'none'}")
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv")
    src.add_argument("--demo", action="store_true")
    p.add_argument("--point-value", type=float, default=20.0)
    p.add_argument("--contracts", type=int, default=1)
    p.add_argument("--commission", type=float, default=2.50)
    p.add_argument("--slippage", type=float, default=0.25)
    p.add_argument("--stop-atr", type=float, default=0.0, help="ATR stop multiple, 0 = off")
    p.add_argument("--target-atr", type=float, default=0.0, help="ATR target multiple, 0 = off")
    p.add_argument("--trend-mode", choices=["price", "slope", "both"], default="price",
                   help="how the 15m WMA21 defines uptrend (default: price above it)")
    p.add_argument("--allow-short", action="store_true", help="enable mirrored short rules (placeholder)")
    p.add_argument("--live-signal", action="store_true", help="only print the latest bar's readings")
    p.add_argument("--trades-csv")
    args = p.parse_args()

    cfg = Config(
        point_value=args.point_value, contracts=args.contracts, commission=args.commission,
        slippage_pts=args.slippage, stop_atr=args.stop_atr, target_atr=args.target_atr,
        allow_short=args.allow_short, trend_mode=args.trend_mode,
    )
    raw = load_csv(args.csv) if args.csv else demo_data()
    df = build(raw, cfg)
    print(snapshot(df))
    if args.live_signal:
        return

    res = backtest(df, cfg)
    print("\n=== Backtest ===")
    print(summarize(res))
    if args.trades_csv and res.trades:
        pd.DataFrame([t.__dict__ for t in res.trades]).to_csv(args.trades_csv, index=False)
        print(f"\nTrades written to {args.trades_csv}")


if __name__ == "__main__":
    main()
