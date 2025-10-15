from __future__ import annotations
from pathlib import Path
import pandas as pd
import geopandas as gpd

DATA_DIR = Path(__file__).resolve().parent / "data"
GEOM_DIR = Path(__file__).resolve().parent / "geometry"

def _exists(p: Path) -> bool:
    return p.exists() and p.stat().st_size > 0

# Geometry (SA2)
def load_sa2_geojson() -> gpd.GeoDataFrame:
    full = GEOM_DIR / "sa2_2021_full.geojson"
    if _exists(full):
        return gpd.read_file(full)
    # fallback to small demo
    return gpd.read_file(GEOM_DIR / "sa2_2021_simplified.geojson")

# Ownership (Census G37)
def load_ownership() -> pd.DataFrame:
    full = DATA_DIR / "abs_tenure_home_ownership_sa2.csv"
    if _exists(full):
        return pd.read_csv(full)
    return pd.read_csv(DATA_DIR / "abs_tenure_home_ownership_sa2_sample.csv")

# SEIFA IRSAD
def load_seifa() -> pd.DataFrame:
    full = DATA_DIR / "abs_seifa_irsad_sa2.csv"
    if _exists(full):
        return pd.read_csv(full)
    return pd.read_csv(DATA_DIR / "abs_seifa_irsad_sa2_sample.csv")

# Vacancy (postcode-level public CSV you supply)
def load_vacancy() -> pd.DataFrame:
    full = DATA_DIR / "vacancy_by_postcode.csv"
    if _exists(full):
        return pd.read_csv(full)
    return pd.read_csv(DATA_DIR / "sqm_vacancy_postcode_sample.csv")

# VIC medians (example state)
def load_vic_medians() -> pd.DataFrame:
    full = DATA_DIR / "vic_vpsr_medians.csv"
    if _exists(full):
        return pd.read_csv(full)
    return pd.read_csv(DATA_DIR / "vic_vpsr_medians_sample.csv")

# RBA cash rate
def load_rba_cash_rate() -> pd.DataFrame:
    full = DATA_DIR / "rba_cash_rate_history.csv"
    if _exists(full):
        return pd.read_csv(full)
    # sample already included under same name
    return pd.read_csv(DATA_DIR / "rba_cash_rate_history.csv")

# ABS correspondence for postcode→SA2 (use in your vacancy join)
def load_postcode_sa2_lookup() -> pd.DataFrame | None:
    p = DATA_DIR / "postcode_to_sa2_2021.csv"
    return pd.read_csv(p) if _exists(p) else None

