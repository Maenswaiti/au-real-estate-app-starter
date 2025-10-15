from __future__ import annotations
import numpy as np
import pandas as pd

FACTORS = [
    "gross_yield",
    "vacancy_rate",
    "ownership_pct",
    "price_momentum_qoq",
    "irsad_rank",
    "distance_cbd_km",
]

DEFAULT_WEIGHTS = {
    "gross_yield": 0.25,
    "vacancy_rate": 0.15,
    "ownership_pct": 0.15,
    "price_momentum_qoq": 0.20,
    "irsad_rank": 0.15,
    "distance_cbd_km": 0.10,
}

DIRECTION = {
    "gross_yield": +1,
    "vacancy_rate": -1,
    "ownership_pct": +1,
    "price_momentum_qoq": -1,
    "irsad_rank": +1,
    "distance_cbd_km": -1,
}

def zscore(s: pd.Series) -> pd.Series:
    mu, sigma = s.mean(), s.std(ddof=0)
    if sigma == 0 or np.isnan(sigma):
        return pd.Series([0]*len(s), index=s.index)
    return (s - mu)/sigma

def composite_score(df: pd.DataFrame, weights: dict = None) -> pd.DataFrame:
    weights = weights or DEFAULT_WEIGHTS
    out = df.copy()
    for f in FACTORS:
        if f not in out.columns:
            out[f] = np.nan
        zs = zscore(out[f].astype(float))
        out[f + "_z"] = DIRECTION[f] * zs
    out["score"] = sum(out[f+"_z"] * weights.get(f, 0) for f in FACTORS)
    return out
