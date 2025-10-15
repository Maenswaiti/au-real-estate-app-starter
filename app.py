import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px
from calculators import (
    monthly_repayment_pni, assessed_rate_pct, lvr_pct, likely_lmi,
    gross_yield_pct, net_yield_pct, cash_on_cash_pct, stamp_duty_estimate
)
from scoring import composite_score, DEFAULT_WEIGHTS
import data_loader as dl

st.set_page_config(page_title="AU Real-Estate (Public Data)", layout="wide")

st.title("🇦🇺 Australian Real-Estate — Public Data Explorer (No Login)")
st.caption("Educational tool. Not financial advice. Data from ABS/RBA/state open data. Use your own judgement.")

with st.sidebar:
    st.header("Global Settings")
    mode = st.radio("Mode", ["Home Buyer", "Investor"], index=1)
    interest_rate = st.slider("Interest rate (%)", 1.0, 12.0, 6.5, 0.1)
    deposit_pct = st.slider("Deposit (%)", 5, 40, 20, 1)
    term_years = st.slider("Loan term (years)", 10, 30, 30, 1)

    st.markdown("---")
    st.subheader("Scoring Weights")
    w = DEFAULT_WEIGHTS.copy()
    w["gross_yield"] = st.slider("Weight: Yield", 0.0, 0.5, w["gross_yield"], 0.01)
    w["vacancy_rate"] = st.slider("Weight: Vacancy (lower better)", 0.0, 0.5, w["vacancy_rate"], 0.01)
    w["ownership_pct"] = st.slider("Weight: Ownership %", 0.0, 0.5, w["ownership_pct"], 0.01)
    default_m = 0.20 if mode == "Home Buyer" else 0.10
    w["price_momentum_qoq"] = st.slider("Weight: Price momentum (prefer softer)", 0.0, 0.5, default_m, 0.01)
    w["irsad_rank"] = st.slider("Weight: SEIFA IRSAD", 0.0, 0.5, w["irsad_rank"], 0.01)
    w["distance_cbd_km"] = st.slider("Weight: Distance to CBD", 0.0, 0.5, w["distance_cbd_km"], 0.01)

TAB1, TAB2, TAB3, TAB4 = st.tabs([
    "Where to Buy (Ranking)",
    "Deal Calculator",
    "Maps",
    "Data & Methods",
])

geo = dl.load_sa2_geojson()
own = dl.load_ownership_sample()
seifa = dl.load_seifa_sample()
vac = dl.load_vacancy_sample()
med = dl.load_vic_medians_sample()
rba = dl.load_rba_cash_rate_sample()

features = (
    geo[["SA2_CODE21","SA2_NAME21","geometry"]]
    .merge(own[["sa2_code21","ownership_pct"]], left_on="SA2_CODE21", right_on="sa2_code21", how="left")
    .merge(seifa[["sa2_code21","irsad_rank"]], left_on="SA2_CODE21", right_on="sa2_code21", how="left")
)

features["gross_yield"] = features["ownership_pct"].apply(lambda x: 4.0 + (x or 60)/100.0)
features["vacancy_rate"] = 2.5
features["price_momentum_qoq"] = -1.0
features["distance_cbd_km"] = 10 + np.random.default_rng(42).normal(0, 5, len(features))

with TAB1:
    st.subheader("Suburb ranking (sample SA2 subset)")
    ranked = composite_score(features, weights=w).sort_values("score", ascending=False)
    st.dataframe(ranked[["SA2_NAME21","gross_yield","vacancy_rate","ownership_pct","price_momentum_qoq","irsad_rank","distance_cbd_km","score"]].round(3), use_container_width=True)
    st.markdown("### Suggested picks (top 5)")
    st.write(ranked.head(5)[["SA2_NAME21","score"]])

with TAB2:
    st.subheader("Deal calculator (per property)")
    col1, col2 = st.columns(2)
    with col1:
        price = st.number_input("Purchase price ($)", 150000.0, 3000000.0, 800000.0, 1000.0)
        weekly_rent = st.number_input("Weekly rent ($)", 200.0, 2000.0, 700.0, 10.0)
        expenses = st.number_input("Annual expenses ($)", 0.0, 20000.0, 6000.0, 100.0)
        state = st.selectbox("State", ["NSW","VIC","QLD","SA","WA","TAS","NT","ACT"]) 
        occupancy = st.selectbox("Occupancy", ["INV","OO"])  
        closing_costs = st.number_input("Closing costs ($)", 0.0, 20000.0, 3000.0, 100.0)
    with col2:
        deposit_cash = price * (deposit_pct/100)
        lvr = lvr_pct(price, deposit_cash)
        lmi_flag = likely_lmi(lvr)
        stamp_duty = stamp_duty_estimate(price, state, occupancy, "data/stamp_duty_tables.csv")
        repayment = monthly_repayment_pni(price - deposit_cash, interest_rate, term_years)
        assessed_rate = assessed_rate_pct(interest_rate)

        gy = gross_yield_pct(price, weekly_rent)
        ny = net_yield_pct(price, weekly_rent, expenses)

        annual_debt = repayment*12
        annual_net_cashflow = weekly_rent*52 - expenses - annual_debt
        coc = cash_on_cash_pct(annual_net_cashflow, deposit_cash, stamp_duty, closing_costs, lmi_cost=0.0)

        st.metric("LVR %", f"{lvr:.1f}%", help=">80% often implies LMI")
        st.metric("Monthly repayment", f"${repayment:,.0f}")
        st.metric("Assessed rate (APRA +3%)", f"{assessed_rate:.2f}%")
        st.metric("Gross yield", f"{gy:.2f}%")
        st.metric("Net yield", f"{ny:.2f}%")
        st.metric("Cash-on-cash (Yr1)", f"{coc:.1f}%")
        st.write(f"**Stamp duty (est.)**: ${stamp_duty:,.0f}  ")
        if lmi_flag:
            st.warning("LVR above 80% — many lenders charge LMI. This tool does not compute LMI premiums.")

with TAB3:
    st.subheader("SA2 heatmap (demo subset)")
    g = features.dropna(subset=["geometry"]).copy()
    g = g.to_crs(4326)
    g["lon"] = g.geometry.centroid.x
    g["lat"] = g.geometry.centroid.y
    mapdf = composite_score(g, weights=w)
    color = px.colors.sequential.Viridis
    score_min, score_max = float(mapdf["score"].min()), float(mapdf["score"].max())

    def color_from_score(s):
        if score_max == score_min:
            t = 0.5
        else:
            t = (s - score_min)/(score_max - score_min)
        idx = int(t * (len(color)-1))
        return tuple(int(c.strip('rgb() ').split(',')[i]) if isinstance(c, str) else c for i,c in enumerate(color[idx:idx+1][0].strip('rgb()').split(',')))

    mapdf["color"] = mapdf["score"].apply(lambda s: color_from_score(s))

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=mapdf,
        pickable=True,
        get_position='[lon, lat]',
        get_radius=300,
        get_fill_color='color',
    )
    view_state = pdk.ViewState(latitude=-33.8688, longitude=151.2093, zoom=9)

    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={
        "text": "{SA2_NAME21}\nScore: {score}\nYield: {gross_yield}%\nVacancy: {vacancy_rate}%\nOwnership: {ownership_pct}%\nIRSAD: {irsad_rank}"
    }))

with TAB4:
    st.markdown("""
**Sources (public only):**
- ABS Census 2021 — Tenure type (home ownership %) by SA2. CSV snapshot included; replace with the latest ABS/DataPack as you wish.
- ABS/SEIFA 2021 — IRSAD index by SA2.
- Vacancy rates — provide a public CSV (e.g., SQM Research free summaries at postcode level) and map to SA2 by postcode->SA2 lookup.
- State medians — example VIC VPSR CSV included; add NSW/QLD/SAs via their open data portals.
- RBA — cash rate & lending rates CSVs.

**Method:**
- Compute features per SA2: gross_yield, vacancy_rate, ownership_pct, price_momentum_qoq, irsad_rank, distance_cbd_km.
- Standardise with z-scores and combine with user-editable weights.
- Deal calculator uses standard amortisation; shows APRA +3% assessed-rate context.

**Disclaimers:**
- Educational only. Not financial advice. Data may lag (Census 2021, SEIFA 2021).
- Vacancy samples are demos; replace with fresher public CSVs before using.
""")
