from __future__ import annotations
from pathlib import Path
import pandas as pd
import geopandas as gpd

DATA_DIR = Path(__file__).resolve().parent / "data"
GEOM_DIR = Path(__file__).resolve().parent / "geometry"

def load_sa2_geojson(local_only: bool = False) -> gpd.GeoDataFrame:
    gp = GEOM_DIR / "sa2_2021_simplified.geojson"
    return gpd.read_file(gp)

def load_ownership_sample() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR/"abs_tenure_home_ownership_sa2_sample.csv")

def load_seifa_sample() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR/"abs_seifa_irsad_sa2_sample.csv")

def load_vacancy_sample() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR/"sqm_vacancy_postcode_sample.csv")

def load_vic_medians_sample() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR/"vic_vpsr_medians_sample.csv")

def load_rba_cash_rate_sample() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR/"rba_cash_rate_history.csv")
