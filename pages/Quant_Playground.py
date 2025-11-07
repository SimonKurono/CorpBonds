# pages/Quant_Playground.py ─────────────────────────────────────────────────────────
"""Quantitative Analysis Playground Page.

Features:
- Monte Carlo simulations
- Moving averages analysis
- Relative value analysis
- Simple strategy prototyping
"""

from __future__ import annotations

# ── Stdlib
import math
from typing import Dict, Tuple

# ── Third-party
import numpy as np
import pandas as pd
import streamlit as st

# ── Local
import utils.ui as ui


# ╭─────────────────────────── Constants ───────────────────────────╮
DEFAULT_SEED = 42
DEFAULT_DAYS = 750
DEFAULT_MU = 0.08
DEFAULT_SIGMA = 0.20
DEFAULT_S0 = 100.0
MIN_DAYS = 250
MAX_DAYS = 1250
MIN_MC_PATHS = 100
MAX_MC_PATHS = 5000
DEFAULT_MC_PATHS = 500
MIN_MC_HORIZON = 21
MAX_MC_HORIZON = 756
DEFAULT_MC_HORIZON = 252
# ╰─────────────────────────────────────────────────────────────────╯


# ╭──────────────────────── Helpers and caching ──────────────────────╮
@st.cache_data
def make_synth_price(seed: int, n: int = DEFAULT_DAYS, mu: float = DEFAULT_MU, sigma: float = DEFAULT_SIGMA, s0: float = DEFAULT_S0) -> pd.Series:
    """Geometric Brownian Motion synthetic price."""
    rng = np.random.default_rng(seed)
    dt = 1/252
    shocks = rng.normal((mu - 0.5 * sigma**2) * dt, sigma * math.sqrt(dt), size=n)
    log_price = np.log(s0) + np.cumsum(shocks)
    return pd.Series(np.exp(log_price), index=pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n))

@st.cache_data
def make_synth_pair(seed: int, n: int = DEFAULT_DAYS) -> Tuple[pd.Series, pd.Series]:
    """Generate two correlated synthetic assets for relative value analysis."""
    a = make_synth_price(seed, n=n, mu=0.08, sigma=0.22, s0=100)
    b = make_synth_price(seed + 1, n=n, mu=0.06, sigma=0.18, s0=95)
    return a, b


def zscore(series: pd.Series, window: int = 60) -> pd.Series:
    """Calculate z-score of a series using rolling window."""
    return (series - series.rolling(window).mean()) / series.rolling(window).std(ddof=0)


def perf_stats(returns: pd.Series) -> Dict[str, float]:
    """Calculate simple annualized performance statistics."""
    ret = returns.dropna()
    if ret.empty:
        return {"CAGR": 0, "Vol": 0, "Sharpe": 0, "MaxDD": 0}
    cagr = (1 + ret).prod() ** (252 / len(ret)) - 1
    vol = ret.std() * np.sqrt(252)
    sharpe = cagr / vol if vol != 0 else np.nan
    curve = (1 + ret).cumprod()
    peak = curve.cummax()
    dd = (curve / peak - 1).min()
    return {"CAGR": cagr, "Vol": vol, "Sharpe": sharpe, "MaxDD": dd}
# ╰─────────────────────────────────────────────────────────────────╯


# ╭────────────────────────── Render sections ──────────────────────╮
def render_header() -> None:
    """Configure page header and layout."""
    ui.configure_page(page_title="Quant Playground", page_icon="🧮", layout="wide")
    ui.render_sidebar()
    st.caption("Monte Carlo, moving averages, relative value, and simple strategy prototyping.")


def render_settings() -> tuple[int, str, int]:
    """Render global settings controls and return user selections."""
    st.header("Settings")
    c1, c2, c3 = st.columns([0.75, 0.75, 1.5])
    with c1:
        seed = st.number_input("Random seed (for demo)", min_value=1, max_value=1_000_000, value=DEFAULT_SEED, step=1)

    with c2:
        default_bench = st.selectbox("Benchmark (for context)", ["SPY", "LQD", "HYG", "Custom"], index=1)

    with c3:
        n_days = st.slider("Sample length (business days)", MIN_DAYS, MAX_DAYS, DEFAULT_DAYS, step=50)

    st.write("")
    st.caption("💡 TODO: Replace synthetic generators with your API/DB fetches, e.g. GET /prices?ids=...")

    return seed, default_bench, n_days


def render_monte_carlo_tab(seed: int, n_days: int) -> None:
    """Render Monte Carlo simulation tab."""
    st.subheader("Monte Carlo (GBM)")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        mc_paths = st.number_input("Paths", min_value=MIN_MC_PATHS, max_value=MAX_MC_PATHS, value=DEFAULT_MC_PATHS, step=100)
    with c2:
        mc_horizon = st.number_input("Horizon (days)", min_value=MIN_MC_HORIZON, max_value=MAX_MC_HORIZON, value=DEFAULT_MC_HORIZON, step=21)
    with c3:
        mc_mu = st.number_input("μ (annualized drift)", value=DEFAULT_MU, step=0.01, format="%.2f")
    with c4:
        mc_sigma = st.number_input("σ (annualized vol)", value=DEFAULT_SIGMA, step=0.01, format="%.2f")

    base = make_synth_price(seed, n=n_days)
    s0 = float(base.iloc[-1])

    # Simulate GBM paths
    dt = 1 / 252
    rng = np.random.default_rng(seed)
    shocks = rng.normal((mc_mu - 0.5 * mc_sigma**2) * dt, mc_sigma * math.sqrt(dt), size=(mc_horizon, mc_paths))
    log_paths = np.log(s0) + shocks.cumsum(axis=0)
    sim = pd.DataFrame(np.exp(log_paths), index=pd.bdate_range(start=pd.Timestamp.today().normalize(), periods=mc_horizon))

    cL, cR = st.columns([2, 1])
    with cL:
        st.line_chart(sim.iloc[:, : min(mc_paths, 50)], height=300, use_container_width=True)  # plot first 50 for speed
    with cR:
        terminal = sim.iloc[-1]
        st.metric("Median Terminal Price", f"{terminal.median():.2f}")
        st.metric("5–95% Interval", f"{terminal.quantile(0.05):.2f} – {terminal.quantile(0.95):.2f}")
        st.caption("Plot shows a subset of paths. Export full matrix from the Downloads tab.")


def render_ma_rv_tab(seed: int, n_days: int) -> None:
    """Render Moving Average & Relative Value tab."""
    st.subheader("Moving Average & Relative Value")
    a, b = make_synth_pair(seed, n=n_days)

    cA, cB, cWin = st.columns(3)
    with cA:
        ma_fast = st.number_input("MA fast (days)", min_value=5, max_value=120, value=20, step=5)
    with cB:
        ma_slow = st.number_input("MA slow (days)", min_value=20, max_value=300, value=60, step=10)
    with cWin:
        rv_window = st.number_input("RV z-score window", min_value=20, max_value=240, value=60, step=10)

    df = pd.DataFrame({"A": a, "B": b}).dropna()
    df["A_ma_fast"] = df["A"].rolling(ma_fast).mean()
    df["A_ma_slow"] = df["A"].rolling(ma_slow).mean()
    df["spread"] = np.log(df["A"]) - np.log(df["B"])
    df["z"] = zscore(df["spread"], window=rv_window)
    df["roll_corr"] = df["A"].pct_change().rolling(rv_window).corr(df["B"].pct_change())

    g1, g2 = st.columns(2)
    with g1:
        st.line_chart(df[["A", "A_ma_fast", "A_ma_slow"]].dropna(), height=280, use_container_width=True)
        st.caption("Price with fast/slow moving averages")
    with g2:
        st.line_chart(df[["z"]].dropna(), height=280, use_container_width=True)
        st.caption("Spread z-score (log A − log B)")

    st.metric("Rolling correlation (last)", f"{df['roll_corr'].dropna().iloc[-1]:.2f}")

    with st.expander("Simple RV signal (example)"):
        entry = st.slider("Enter when |z| >=", 0.5, 3.0, 2.0, 0.5)
        exit_ = st.slider("Exit when |z| <=", 0.0, 2.0, 0.5, 0.5)
        # Toy signal: long A/short B when z<-entry, opposite when z>entry; flat when |z|<=exit
        sig = pd.Series(0, index=df.index, dtype=float)
        sig[df["z"] >= entry] = -1.0   # short A, long B
        sig[df["z"] <= -entry] = +1.0  # long A, short B
        sig[(df["z"].abs() <= exit_)] = 0.0
        sig = sig.shift(1).fillna(0)   # enter next day
        ret_pair = (np.log(df["A"]).diff() - np.log(df["B"]).diff()).fillna(0)
        strat_ret = sig * ret_pair
        st.line_chart((1 + strat_ret).cumprod(), height=220, use_container_width=True)
        stats = perf_stats(strat_ret)
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("CAGR", f"{stats['CAGR']*100:.2f}%")
        s2.metric("Vol", f"{stats['Vol']*100:.2f}%")
        s3.metric("Sharpe", f"{stats['Sharpe']:.2f}")
        s4.metric("Max DD", f"{stats['MaxDD']*100:.2f}%")


def render_strategy_tab(seed: int, n_days: int) -> None:
    """Render Strategy Lab tab."""
    st.subheader("Strategy Lab (Crossover / Mean Reversion)")
    price = make_synth_price(seed + 7, n=n_days, mu=0.07, sigma=0.22, s0=100)

    c1, c2, c3 = st.columns(3)
    with c1:
        mode = st.selectbox("Mode", ["Crossover", "Mean Reversion"], index=0)
    with c2:
        w1 = st.number_input("Window 1", min_value=5, max_value=200, value=20, step=5)
    with c3:
        w2 = st.number_input("Window 2", min_value=10, max_value=300, value=60, step=10)

    dfS = pd.DataFrame({"px": price})
    dfS["ma1"] = dfS["px"].rolling(w1).mean()
    dfS["ma2"] = dfS["px"].rolling(w2).mean()

    # Signal
    if mode == "Crossover":
        sig = (dfS["ma1"] > dfS["ma2"]).astype(float) - (dfS["ma1"] < dfS["ma2"]).astype(float)
    else:
        z_ = zscore(dfS["px"], window=w2)
        sig = (-z_).clip(-1, 1)  # fade to mean

    sig = sig.shift(1).fillna(0)
    ret = np.log(dfS["px"]).diff().fillna(0)
    strat = (sig * ret).fillna(0)

    # Charts
    cL, cR = st.columns([2, 1])
    with cL:
        st.line_chart(dfS[["px", "ma1", "ma2"]].dropna(), height=280, use_container_width=True)
    with cR:
        equity = (1 + strat).cumprod()
        st.line_chart(equity, height=280, use_container_width=True)

    stats = perf_stats(strat)
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("CAGR", f"{stats['CAGR']*100:.2f}%")
    s2.metric("Vol", f"{stats['Vol']*100:.2f}%")
    s3.metric("Sharpe", f"{stats['Sharpe']:.2f}")
    s4.metric("Max DD", f"{stats['MaxDD']*100:.2f}%")

    with st.expander("Trading assumptions"):
        st.write("• No costs/slippage.")
        st.write("• Daily rebalancing.")
        st.write("• Signals applied next bar (1-day lag).")
        st.caption("TODO: add costs, borrow, position caps, risk budgets.")


def render_visuals_tab(seed: int, n_days: int) -> None:
    """Render Visuals / Downloads tab."""
    st.subheader("Data & Exports")
    st.caption("Inspect the generated demo series and export for offline analysis.")

    a, b = make_synth_pair(seed, n=n_days)
    df_all = pd.DataFrame({
        "A": a, "B": b,
        "A_ret": np.log(a).diff(),
        "B_ret": np.log(b).diff(),
    }).dropna()

    st.dataframe(df_all.tail(250), use_container_width=True, height=300)

    csv = df_all.to_csv(index=True).encode("utf-8")
    st.download_button("Download CSV (A/B demo)", data=csv, file_name="quant_playground_AB.csv", mime="text/csv")

    st.markdown("---")
    st.caption("TODO: Replace with actual symbols and DB-backed prices retrieved via your FastAPI (cached with Redis).")
# ╰─────────────────────────────────────────────────────────────────╯


# ╭─────────────────────────── Main ───────────────────────────╮
def main() -> None:
    """Main page entry point."""
    render_header()

    # Get settings from UI
    seed, default_bench, n_days = render_settings()

    # Create tabs
    tab_mc, tab_ma_rv, tab_strat, tab_viz = st.tabs(
        ["🎲 Monte Carlo", "📏 Moving Avg & Relative Value", "🧪 Strategy Lab", "📈 Visuals / Downloads"]
    )

    with tab_mc:
        render_monte_carlo_tab(seed, n_days)

    with tab_ma_rv:
        render_ma_rv_tab(seed, n_days)

    with tab_strat:
        render_strategy_tab(seed, n_days)

    with tab_viz:
        render_visuals_tab(seed, n_days)


if __name__ == "__main__":
    main()