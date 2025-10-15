import numpy as np
import pandas as pd

def score_suburb(df: pd.DataFrame) -> pd.Series:
    """
    Compute an overall investment score (0–100) for each suburb
    using ownership %, SEIFA rank, and yield.
    """
    # Ensure missing columns don't break it
    ownership = df.get("ownership_pct", pd.Series([50] * len(df)))
    seifa = df.get("irsad_rank", pd.Series([50] * len(df)))
    yield_col = df.get("gross_yield", pd.Series([4] * len(df)))

    # Normalize each component (0–100)
    own_norm = np.clip((ownership - np.nanmin(ownership)) / (np.nanmax(ownership) - np.nanmin(ownership)) * 100, 0, 100)
    seifa_norm = np.clip((seifa - np.nanmin(seifa)) / (np.nanmax(seifa) - np.nanmin(seifa)) * 100, 0, 100)
    yield_norm = np.clip((yield_col - np.nanmin(yield_col)) / (np.nanmax(yield_col) - np.nanmin(yield_col)) * 100, 0, 100)

    # Weighted average
    score = (own_norm * 0.3 + seifa_norm * 0.3 + yield_norm * 0.4)
    return score.round(1)
