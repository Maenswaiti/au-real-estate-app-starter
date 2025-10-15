from __future__ import annotations
import pandas as pd
import geopandas as gpd
from pathlib import Path

# --- Directory paths ---
DATA_DIR = Path(__file__).resolve().parent / "data"
GEOM_DIR = Path(__file__).resolve().parent / "geometry"

# ============================================================
#  GEOMETRY
# ============================================================

def load_sa2_geojson(local_only: bool = False) -> gpd.GeoDataFrame:
    """
    Load simplified SA2 boundaries for Australia.
    Default: uses local GeoJSON sample to keep app light.
    Replace with full GeoJSON for national coverage if desired.
    """
    geo_path = GEOM_DIR / "sa2_2021_simplified.geojson"
    if not geo_path.exists():
        raise FileNotFoundError(f"Missing GeoJSON: {geo_path}")
    return gpd.read_file(geo_path)


# ============================================================
#  ABS / CENSUS DATA (PUBLIC)
# ============================================================

def load_ownership_sample() -> pd.DataFrame:
    """
    Load home ownership percentage per SA2 (ABS Census 2021 Tenure data).
    """
    path = DATA_DIR / "abs_tenure_home_ownership_sa2_sample.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return pd.read_csv(path)


def load_seifa_sample() -> pd.DataFrame:
    """
    Load SEIFA IRSAD ranking by SA2 (ABS 2021).
    """
    path = DATA_DIR / "abs_seifa_irsad_sa2_sample.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return pd.read_csv(path)


# ============================================================
#  VACANCY RATES (PUBLIC CSV SAMPLE)
# ============================================================

def load_vacancy_sample() -> pd.DataFrame:
    """
    Load vacancy rate per postcode (sample data).
    Replace with updated SQM Research CSV when available.
    """
    path = DATA_DIR / "sqm_vacancy_postcode_sample.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return pd.read_csv(path)


# ============================================================
#  PROPERTY PRICE MEDIANS
# ============================================================

def load_vic_medians_sample() -> pd.DataFrame:
    """
    Load sample VIC property price medians (VPSR open data).
    Add NSW/QLD/SA equivalents for full coverage.
    """
    path = DATA_DIR / "vic_vpsr_medians_sample.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return pd.read_csv(path)


# ============================================================
#  RBA CASH RATE HISTORY
# ============================================================

def load_rba_cash_rate_sample() -> pd.DataFrame:
    """
    Load Reserve Bank of Australia (RBA) historical cash rate series.
    """
    path = DATA_DIR / "rba_cash_rate_history.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return pd.read_csv(path)


# ============================================================
#  OPTIONAL HELPERS (for expansion)
# ============================================================

def summarize_all() -> dict[str, pd.DataFrame]:
    """
    Load all available datasets at once and return as dictionary.
    Useful for debugging or preloading into session state.
    """
    return {
        "ownership": load_ownership_sample(),
        "seifa": load_seifa_sample(),
        "vacancy": load_vacancy_sample(),
        "vic_medians": load_vic_medians_sample(),
        "rba": load_rba_cash_rate_sample(),
    }
