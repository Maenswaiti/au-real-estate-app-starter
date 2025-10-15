import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import pydeck as pdk
import plotly.express as px

from calculators import (
    monthly_repayment_pni,
    assessed_rate_pct,
    lvr_pct,
    likely_lmi,
    gross_yield_pct,
    net_yield_pct,
    cash_on_cash_pct,
    stamp_duty_estimate
)
import data_loader as dl
import scoring as scoring

st.set_page_config(page_title="AU Real Estate Dashboard", layout="wide")

st.title("🏠 Australian Real Estate Insights (Public Data Only)")

st.markdown("""
This app combines publicly available data on Australian housing to explore:
- **Ownership %** per suburb  
- **Socioeconomic advantage (SEIFA)**  
- **Vacancy rates & medians**  
- **Estimated yields, repayments & deposits**
""")

# Sidebar filters
st.sidebar.header("🔍 Filters")
state_choice = st.sidebar.selectbox("State", ["VIC", "NSW", "QLD", "SA", "WA", "TAS", "NT", "ACT"], index=0)
interest_rate = st.sidebar.slider("Mortgage interest rate (%)", 4.5, 10.0, 6.0, 0.1)
loan_term = st.sidebar.selectbox("Loan term (years)", [25, 30])
deposit_pct = st.sidebar.slider("Deposit (%)", 5, 40, 20, 1)

# Load data
geo = dl.load_sa2_geojson()
own = dl.load_ownership_sample()
seifa = dl.load_seifa_sample()
vac = dl.load_vacancy_sample()
med = dl.load_vic_medians_sample()

# Fix data types before merging (safe version)
geo["SA2_CODE21"] = geo["SA2_CODE21"].astype(str)
own["sa2_code21"] = own["sa2_code21"].astype(str)
seifa["sa2_code21"] = seifa["sa2_code21"].astype(str)

# Only cast postcode if column exists
if "postcode" in vac.columns:
    vac["postcode"] = vac["postcode"].astype(str)
if "postcode" in med.columns:
    med["postcode"] = med["postcode"].astype(str)


# Merge datasets
features = (
    geo[["SA2_CODE21", "SA2_NAME21", "geometry"]]
    .merge(own[["sa2_code21", "ownership_pct"]], left_on="SA2_CODE21", right_on="sa2_code21", how="left")
    .merge(seifa[["sa2_code21", "irsad_rank"]], left_on="SA2_CODE21", right_on="sa2_code21", how="left")
)

# Score and calculate sample metrics
features["median_price"] = np.random.randint(400000, 1200000, size=len(features))
features["gross_yield"] = np.random.uniform(3, 6, len(features))
features["net_yield"] = features["gross_yield"] * 0.85
features["score"] = scoring.score_suburb(features)

# === Color scale function ===
def color_from_score(score: float) -> tuple[int, int, int]:
    """
    Convert a numeric score (0–100) to an RGB color gradient.
    Higher = greener, lower = redder.
    """
    if pd.isnull(score):
        s = 0
    else:
        s = max(0, min(100, score))

    r = int(255 * (100 - s) / 100)
    g = int(255 * s / 100)
    b = 60
    return (r, g, b)

# Convert geometry to lat/lon for PyDeck
features = gpd.GeoDataFrame(features, geometry="geometry")
features["lon"] = features["geometry"].centroid.x
features["lat"] = features["geometry"].centroid.y

# Create map dataframe
mapdf = features.copy()
mapdf["color"] = mapdf["score"].apply(color_from_score)

# === Map view ===
st.subheader("🌏 Suburb Investment Heatmap")
view_state = pdk.ViewState(latitude=-37.81, longitude=144.96, zoom=8)

layer = pdk.Layer(
    "ScatterplotLayer",
    data=mapdf,
    get_position=["lon", "lat"],
    get_radius=1000,
    get_fill_color="color",
    pickable=True,
)

st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{SA2_NAME21}\nScore: {score}"}))

# === Table + charts ===
st.subheader("📊 Suburb Comparison")
col1, col2 = st.columns(2)

with col1:
    st.dataframe(
        mapdf[["SA2_NAME21", "ownership_pct", "irsad_rank", "median_price", "gross_yield", "net_yield", "score"]]
        .sort_values("score", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )

with col2:
    st.plotly_chart(
        px.scatter(
            mapdf,
            x="ownership_pct",
            y="gross_yield",
            color="score",
            hover_name="SA2_NAME21",
            title="Ownership vs Gross Yield",
        ),
        use_container_width=True,
    )

# === Mortgage calculator ===
st.subheader("💰 Mortgage Estimator")

price_input = st.number_input("Property price (AUD)", 300000, 2000000, 750000, step=10000)
deposit = price_input * deposit_pct / 100
loan_amount = price_input - deposit
repayment = monthly_repayment_pni(loan_amount, interest_rate, loan_term)

col3, col4, col5 = st.columns(3)
col3.metric("Estimated deposit", f"${deposit:,.0f}")
col4.metric("Loan amount", f"${loan_amount:,.0f}")
col5.metric("Monthly repayment", f"${repayment:,.0f}")

st.markdown("---")
st.caption("Data sources: ABS, SQM Research, RBA (public datasets). This is a demo using sample data for illustration only.")
