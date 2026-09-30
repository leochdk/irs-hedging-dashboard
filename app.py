import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="IRS Hedging Dashboard", layout="wide")

# ================= Données de marché (EUR, en %) =================
# À mettre à jour avec les taux Bloomberg EUSA1..EUSA10 d'une même date
MARKET_DATE = "25/09/2026"
MARKET = {0.25: 2.607, 5: 3.65, 10: 3.71}
TAU = 0.25  # paiements trimestriels

# ================= Moteur de calcul =================
def bootstrap(market, max_T=10):
    pillars = np.array(sorted(market))
    rates = np.array([market[p] for p in pillars]) / 100
    years = np.arange(1, max_T + 1)
    swap = np.interp(years, pillars, rates)
    df = []
    for s in swap:
        df.append((1 - s * sum(df)) / (1 + s))
    return years, -np.log(np.array(df)) / years

YEARS, ZERO = bootstrap(MARKET)

def curve_at(dates, shift=0.0):
    t = np.concatenate(([0.25], YEARS))
    z = np.concatenate(([MARKET[0.25] / 100], ZERO))
    return np.interp(dates, t, z) + shift

def payment_dates(T):
    return np.arange(1, int(T / TAU) + 1) * TAU

def swap_value_payer(N, c, curve, dates):
    df = np.exp(-curve * dates)
    return N * (1 - df[-1]) - N * c * TAU * df.sum()

def par_rate(curve, dates):
    df = np.exp(-curve * dates)
    return (1 - df[-1]) / (TAU * df.sum())

def dv01(N, c, curve, dates):
    return swap_value_payer(N, c, curve + 1e-4, dates) - swap_value_payer(N, c, curve, dates)

def pivot_shift(dates, short_bp, long_bp):
    w = np.clip((dates - 0.25) / (10 - 0.25), 0, 1)
    return (short_bp + (long_bp - short_bp) * w) * 1e-4

# ================= Interface =================
st.title("Couverture de taux : swap payeur de fixe")
st.caption(f"Client corporate endetté à taux variable (Euribor). Courbe EUR au {MARKET_DATE}.")

with st.sidebar:
    st.header("Paramètres du swap")
    N = st.number_input("Notionnel (€)", 1_000_000, 500_000_000, 50_000_000, step=5_000_000)
    T = st.select_slider("Maturité (années)", options=[2, 3, 4, 5, 6, 7, 8, 9, 10], value=5)
    dates = payment_dates(T)
    par = par_rate(curve_at(dates), dates)
    c = st.number_input("Taux fixe du swap (%)", 0.0, 10.0, round(par * 100, 3), step=0.01) / 100
    st.header("Scénario de marché")
    shift_bp = st.slider("Choc parallèle de la courbe (bp)", -100, 100, 0, step=5)

curve = curve_at(dates, shift_bp * 1e-4)
value = swap_value_payer(N, c, curve, dates)
d = dv01(N, c, curve, dates)

col1, col2, col3 = st.columns(3)
col1.metric("Taux par (prix de marché)", f"{par:.3%}")
col2.metric("Valeur du swap pour le client", f"{value:,.0f} €")
col3.metric("DV01", f"{d:,.0f} € / bp")

st.info(f"« Ce swap vous expose à {d:,.0f} € de variation de valeur par point de base de mouvement des taux. "
        f"Combiné à votre prêt, vous payez {c:.2%} + votre marge de crédit, quoi qu'il arrive aux taux. »")

left, right = st.columns(2)

with left:
    st.subheader("Valeur selon un choc parallèle")
    shifts = np.arange(-100, 101, 5)
    vals = [swap_value_payer(N, c, curve_at(dates, s * 1e-4), dates) for s in shifts]
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.plot(shifts, np.array(vals) / 1e6, color="navy", lw=2)
    ax.axhline(0, color="gray", ls="--"); ax.axvline(shift_bp, color="darkorange", ls=":")
    ax.set_xlabel("Choc de la courbe (bp)"); ax.set_ylabel("Valeur (M€)"); ax.grid(alpha=0.3)
    st.pyplot(fig)

with right:
    st.subheader("Quelle maturité choisir ?")
    rows = []
    for Tm in [2, 3, 5, 7, 10]:
        dm = payment_dates(Tm)
        cm = curve_at(dm)
        pm = par_rate(cm, dm)
        rows.append({"Maturité": f"{Tm} ans", "Taux fixe proposé": f"{pm:.3%}",
                     "DV01 (€/bp)": f"{dv01(N, pm, cm, dm):,.0f}"})
    st.table(pd.DataFrame(rows))

st.subheader("Scénarios de déformation de la courbe")
scen = {
    "Hausse parallèle +50 bp": (50, 50), "Baisse parallèle -50 bp": (-50, -50),
    "Pentification (court -25 / long +25)": (-25, 25), "Aplatissement (court +25 / long -25)": (25, -25),
}
base = curve_at(dates)
st.table(pd.DataFrame([{"Scénario": k,
    "Valeur du swap (€)": f"{swap_value_payer(N, c, base + pivot_shift(dates, *v), dates):+,.0f}"}
    for k, v in scen.items()]))
