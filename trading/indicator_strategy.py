#!/usr/bin/env python3
"""
Multi-indicator trading script, built from a TradingView chart layout.

Indicators (matching the chart):
    - Volume
    - WMA 200 (close)
    - VWMA 21
    - VWMA 72
    - MACD 8 / 22 / 9   (close, EMA oscillator, EMA signal)   -> "fast"  trigger
    - MACD 12 / 30 / 12 (close, EMA oscillator, EMA signal)   -> "mid"   confirmation
    - MACD 72 / 200 / 12 (close, EMA oscillator, EMA signal)  -> "slow"  regime

Strategy (long and short, one position at a time):
    LONG entry when ALL are true on a closed bar:
        1. Trend:    close > WMA200  and  VWMA21 > VWMA72
        2. Regime:   slow MACD line > 0
        3. Confirm:  mid MACD line > mid MACD signal
        4. Trigger:  fast MACD line crosses ABOVE fast MACD signal
        5. Volume:   volume > its 20-bar average * vol_mult
    SHORT entry is the exact mirror.

    Exit when any of:
        - fast MACD crosses back against the position
        - close crosses VWMA72 against the position
        - ATR stop loss or ATR take profit is hit (checked intrabar on high/low)

Data sources:
    --csv PATH        CSV with columns: time/datetime, open, high, low, close, volume
    --yf SYMBOL       Yahoo Finance via yfinance (pip install yfinance), e.g. NQ=F
    --demo            synthetic random-walk data, for testing the script itself

This is a research / backtest tool. It does not place orders. Nothing here is
financial advice; test thoroughly before risking money.

Examples:
    python indicator_strategy.py --demo
    python indicator_strategy.py --yf NQ=F --interval 1m --period 5d --point-value 20
    python indicator_strategy.py --csv nq_1min.csv --point-value 2 --contracts 3
    python indicator_strategy.py --yf NQ=F --interval 1m --period 5d --live-signal
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field

import numpy as np
import pandas as pd


# --------------------------------------------------------------------------- #
# Indicators
# --------------------------------------------------------------------------- #
def ema(s: pd.Series, length: int) -> pd.Series:
    # TradingView's ta.ema: alpha = 2 / (length + 1), seeded from the first value
    return s.ewm(span=length, adjust=False).mean()


def wma(s: pd.Series, length: int) -> pd.Series:
    weights = np.arange(1, length + 1, dtype=float)
    return s.rolling(length).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)


def vwma(close: pd.Series, volume: pd.Series, length: int) -> pd.Series:
    return (close * volume).rolling(length).sum() / volume.rolling(length).sum()


def macd(close: pd.Series, fast: int, slow: int, signal: int) -> pd.DataFrame:
    line = ema(close, fast) - ema(close, slow)
    sig = ema(line, signal)
    return pd.DataFrame({"macd": line, "signal": sig, "hist": line - sig})


def atr(df: pd.DataFrame, length: int = 14) -> pd.Series:
    prev_close = df["close"].shift()
    tr = pd.concat(
        [df["high"] - df["low"], (df["high"] - prev_close).abs(), (df["low"] - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / length, adjust=False).mean()  # Wilder / RMA


@dataclass
class Config:
    wma_len: int = 200
    vwma_fast: int = 21
    vwma_slow: int = 72
    macd_fast: tuple = (8, 22, 9)
    macd_mid: tuple = (12, 30, 12)
    macd_slow: tuple = (72, 200, 12)
    vol_avg_len: int = 20
    vol_mult: float = 1.0
    atr_len: int = 14
    stop_atr: float = 2.0
    target_atr: float = 3.0
    point_value: float = 20.0  # NQ = $20/pt, MNQ = $2/pt
    contracts: int = 1
    commission: float = 2.50  # per contract, per side
    slippage_pts: float = 0.25  # per side
    allow_short: bool = True


def add_indicators(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    out = df.copy()
    c, v = out["close"], out["volume"]

    out["wma200"] = wma(c, cfg.wma_len)
    out["vwma21"] = vwma(c, v, cfg.vwma_fast)
    out["vwma72"] = vwma(c, v, cfg.vwma_slow)
    out["vol_avg"] = v.rolling(cfg.vol_avg_len).mean()
    out["atr"] = atr(out, cfg.atr_len)

    for name, params in (("fast", cfg.macd_fast), ("mid", cfg.macd_mid), ("slow", cfg.macd_slow)):
        m = macd(c, *params)
        out[f"macd_{name}"] = m["macd"]
        out[f"macd_{name}_sig"] = m["signal"]
        out[f"macd_{name}_hist"] = m["hist"]

    return out


# --------------------------------------------------------------------------- #
# Signals
# --------------------------------------------------------------------------- #
def add_signals(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    out = df.copy()

    fast_diff = out["macd_fast"] - out["macd_fast_sig"]
    cross_up = (fast_diff > 0) & (fast_diff.shift() <= 0)
    cross_dn = (fast_diff < 0) & (fast_diff.shift() >= 0)

    vol_ok = out["volume"] > out["vol_avg"] * cfg.vol_mult

    trend_up = (out["close"] > out["wma200"]) & (out["vwma21"] > out["vwma72"])
    trend_dn = (out["close"] < out["wma200"]) & (out["vwma21"] < out["vwma72"])

    regime_up = out["macd_slow"] > 0
    regime_dn = out["macd_slow"] < 0

    mid_up = out["macd_mid"] > out["macd_mid_sig"]
    mid_dn = out["macd_mid"] < out["macd_mid_sig"]

    out["long_entry"] = trend_up & regime_up & mid_up & cross_up & vol_ok
    out["short_entry"] = trend_dn & regime_dn & mid_dn & cross_dn & vol_ok

    out["long_exit"] = cross_dn | (out["close"] < out["vwma72"])
    out["short_exit"] = cross_up | (out["close"] > out["vwma72"])

    # Don't trade until the slowest indicator (WMA200 / MACD 200) has warmed up
    warm = max(cfg.wma_len, cfg.macd_slow[1]) + cfg.macd_slow[2]
    out.iloc[:warm, out.columns.get_indexer(["long_entry", "short_entry"])] = False
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
    """Signals fire on a bar's close; entries fill at the NEXT bar's open."""
    res = Result()
    pos: Trade | None = None
    pending: str | None = None
    equity, curve = 0.0, []
    cost = cfg.commission * cfg.contracts

    idx = df.index
    o, h, l, c = (df[k].to_numpy() for k in ("open", "high", "low", "close"))
    a = df["atr"].to_numpy()
    le, se = df["long_entry"].to_numpy(), df["short_entry"].to_numpy()
    lx, sx = df["long_exit"].to_numpy(), df["short_exit"].to_numpy()

    def close_pos(i: int, price: float, reason: str) -> None:
        nonlocal pos, equity
        direction = 1 if pos.side == "long" else -1
        fill = price - direction * cfg.slippage_pts
        pts = (fill - pos.entry) * direction
        pos.pnl = pts * cfg.point_value * cfg.contracts - cost  # exit commission
        pos.exit_time, pos.exit, pos.reason = idx[i], fill, reason
        equity += pos.pnl
        res.trades.append(pos)
        pos = None

    for i in range(len(df)):
        # 1) fill pending entry at this bar's open
        if pending and pos is None and not np.isnan(a[i - 1]):
            d = 1 if pending == "long" else -1
            fill = o[i] + d * cfg.slippage_pts
            pos = Trade(
                side=pending,
                entry_time=idx[i],
                entry=fill,
                stop=fill - d * cfg.stop_atr * a[i - 1],
                target=fill + d * cfg.target_atr * a[i - 1],
            )
            equity -= cost  # entry commission
            pos.pnl = -cost
        pending = None

        # 2) intrabar stop / target (stop assumed first if both touched)
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

        # 3) signal-based exit on close
        if pos is not None:
            if (pos.side == "long" and lx[i]) or (pos.side == "short" and sx[i]):
                close_pos(i, c[i], "signal")

        # 4) queue new entry for next bar
        if pos is None:
            if le[i]:
                pending = "long"
            elif se[i] and cfg.allow_short:
                pending = "short"

        # mark-to-market equity
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
        return "No trades. Try more data, a lower --vol-mult, or check the warm-up (needs > ~220 bars)."
    pnl = np.array([x.pnl for x in t])
    wins, losses = pnl[pnl > 0], pnl[pnl <= 0]
    eq = res.equity
    dd = (eq - eq.cummax()).min()
    pf = wins.sum() / abs(losses.sum()) if losses.sum() != 0 else float("inf")
    by_reason = pd.Series([x.reason for x in t]).value_counts().to_dict()
    return "\n".join(
        [
            f"Trades:         {len(t)}  (long {sum(x.side == 'long' for x in t)}, "
            f"short {sum(x.side == 'short' for x in t)})",
            f"Win rate:       {len(wins) / len(t):.1%}",
            f"Net P&L:        ${pnl.sum():,.2f}",
            f"Avg win/loss:   ${wins.mean() if len(wins) else 0:,.2f} / "
            f"${losses.mean() if len(losses) else 0:,.2f}",
            f"Profit factor:  {pf:.2f}",
            f"Max drawdown:   ${dd:,.2f}",
            f"Exit reasons:   {by_reason}",
        ]
    )


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [col.strip().lower() for col in df.columns]
    tcol = next((col for col in ("time", "datetime", "date", "timestamp") if col in df.columns), None)
    if tcol is None:
        raise ValueError("CSV needs a time/datetime/date/timestamp column")
    # TradingView exports use unix seconds; otherwise parse as text
    t = df[tcol]
    df.index = pd.to_datetime(t, unit="s") if np.issubdtype(t.dtype, np.number) else pd.to_datetime(t)
    if "volume" not in df.columns and "vol" in df.columns:
        df["volume"] = df["vol"]
    return df[["open", "high", "low", "close", "volume"]].astype(float)


def load_yf(symbol: str, interval: str, period: str) -> pd.DataFrame:
    try:
        import yfinance as yf
    except ImportError as e:
        raise SystemExit("yfinance not installed: pip install yfinance") from e
    df = yf.download(symbol, interval=interval, period=period, progress=False, auto_adjust=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [col.lower() for col in df.columns]
    return df[["open", "high", "low", "close", "volume"]].dropna().astype(float)


def demo_data(n: int = 3000, start: float = 28160.0, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    drift = np.sin(np.linspace(0, 12, n)) * 0.6  # regime swings so both sides trade
    close = start + np.cumsum(drift + rng.normal(0, 4, n))
    open_ = np.r_[start, close[:-1]]
    high = np.maximum(open_, close) + rng.uniform(0, 3, n)
    low = np.minimum(open_, close) - rng.uniform(0, 3, n)
    volume = rng.integers(50, 600, n).astype(float)
    idx = pd.date_range("2026-11-04 18:00", periods=n, freq="1min")
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume}, idx)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def snapshot(df: pd.DataFrame) -> str:
    r = df.iloc[-1]
    bias = (
        "LONG bias" if r["close"] > r["wma200"] and r["vwma21"] > r["vwma72"]
        else "SHORT bias" if r["close"] < r["wma200"] and r["vwma21"] < r["vwma72"]
        else "NEUTRAL / mixed"
    )
    signal = "BUY" if r["long_entry"] else "SELL" if r["short_entry"] else "no new signal"
    return (
        f"Last bar {df.index[-1]}  close {r['close']:,.2f}  volume {r['volume']:,.0f}\n"
        f"  WMA200 {r['wma200']:,.2f} | VWMA21 {r['vwma21']:,.2f} | VWMA72 {r['vwma72']:,.2f}\n"
        f"  MACD 8/22/9    line {r['macd_fast']:7.2f}  sig {r['macd_fast_sig']:7.2f}  hist {r['macd_fast_hist']:6.2f}\n"
        f"  MACD 12/30/12  line {r['macd_mid']:7.2f}  sig {r['macd_mid_sig']:7.2f}  hist {r['macd_mid_hist']:6.2f}\n"
        f"  MACD 72/200/12 line {r['macd_slow']:7.2f}  sig {r['macd_slow_sig']:7.2f}  hist {r['macd_slow_hist']:6.2f}\n"
        f"  Trend: {bias}   Signal on this bar: {signal}"
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv")
    src.add_argument("--yf", metavar="SYMBOL")
    src.add_argument("--demo", action="store_true")
    p.add_argument("--interval", default="1m")
    p.add_argument("--period", default="5d")
    p.add_argument("--point-value", type=float, default=20.0)
    p.add_argument("--contracts", type=int, default=1)
    p.add_argument("--commission", type=float, default=2.50)
    p.add_argument("--slippage", type=float, default=0.25)
    p.add_argument("--stop-atr", type=float, default=2.0)
    p.add_argument("--target-atr", type=float, default=3.0)
    p.add_argument("--vol-mult", type=float, default=1.0)
    p.add_argument("--long-only", action="store_true")
    p.add_argument("--live-signal", action="store_true", help="only print the latest bar's readings")
    p.add_argument("--trades-csv", help="write the trade list to this file")
    args = p.parse_args()

    cfg = Config(
        point_value=args.point_value,
        contracts=args.contracts,
        commission=args.commission,
        slippage_pts=args.slippage,
        stop_atr=args.stop_atr,
        target_atr=args.target_atr,
        vol_mult=args.vol_mult,
        allow_short=not args.long_only,
    )

    if args.csv:
        raw = load_csv(args.csv)
    elif args.yf:
        raw = load_yf(args.yf, args.interval, args.period)
    else:
        raw = demo_data()

    df = add_signals(add_indicators(raw, cfg), cfg)
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
