#!/usr/bin/env python3
"""
Fetch full, public datasets for the AU real-estate app (no logins):
- SA2 (2021) boundaries (ABS FeatureServer)
- ABS Census 2021 G37 (home ownership/tenure proxies) by SA2
- SEIFA 2021 IRSAD by SA2
- RBA cash rate history
- VIC VPSR (latest year summary, and suburb-level time series)
- ABS correspondences (postcode <-> SA2) for vacancy mapping (you still need to download a public vacancy CSV separately)

Writes cleaned CSV/GeoJSON files into ./data and ./geometry

Usage:
  python scripts/fetch_full_data.py
"""
import os, sys, time, csv, io, zipfile, tempfile, math, pathlib, json
from pathlib import Path
import pandas as pd
import geopandas as gpd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
GEOM = ROOT / "geometry"
DATA.mkdir(exist_ok=True)
GEOM.mkdir(exist_ok=True)

HEADERS = {"User-Agent": "AU-RealEstate-App/1.0 (+public-data)"}

def fs_query_to_geojson(url: str, params: dict) -> dict:
    """Query ArcGIS FeatureServer layer and return GeoJSON-like dict."""
    p = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "f": "geojson",
        "outSR": "4326",
    }
    p.update(params or {})
    r = requests.get(url, params=p, headers=HEADERS, timeout=120)
    r.raise_for_status()
    return r.json()

def fs_query_to_df(url: str, params: dict) -> pd.DataFrame:
    """Return attributes as DataFrame (JSON format)."""
    p = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "false",
        "f": "json",
        "outSR": "4326",
    }
    p.update(params or {})
    r = requests.get(url, params=p, headers=HEADERS, timeout=120)
    r.raise_for_status()
    js = r.json()
    if "features" not in js:
        raise RuntimeError(f"No features in response from {url}")
    rows = [f["attributes"] for f in js["features"]]
    return pd.DataFrame(rows)

def save_geojson(obj: dict, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)

def fetch_sa2_boundaries():
    # ABS official FeatureServer for ASGS2021 SA2 (layer 0)
    url = "https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/SA2/FeatureServer/0/query"
    gj = fs_query_to_geojson(url, {"where": "1=1"})
    out = GEOM / "sa2_2021_full.geojson"
    save_geojson(gj, out)
    print(f"Wrote {out}")

def fetch_abs_g37_homeownership():
    # G37 Tenure & landlord type by SA2 (Census 2021) – Digital Atlas FeatureServer
    url = "https://services-ap1.arcgis.com/ypkPEy1AmwPKGNNv/ArcGIS/rest/services/ABS_2021_Census_G37_SA2/FeatureServer/0/query"
    df = fs_query_to_df(url, {})
    # Create a simple ownership % proxy: % owned outright + % owned with mortgage
    # Field names vary; common fields include: OWNED_OUTRIGHT_P, OWNED_WITH_MORTGAGE_P (proportions/percent)
    # We normalise to 0-100 if needed.
    cols = [c for c in df.columns]
    # Try to find percentage fields
    guess_oo = [c for c in cols if "OWNED_OUTRIGHT" in c and c.endswith("_P")]
    guess_mort = [c for c in cols if "OWNED_WITH_MORTGAGE" in c and c.endswith("_P")]
    if guess_oo and guess_mort:
        oo = df[guess_oo[0]].astype(float)
        mw = df[guess_mort[0]].astype(float)
        df["ownership_pct"] = oo + mw
    else:
        # Fallback: if proportions not present, try counts then compute percentage
        guess_oo_c = [c for c in cols if "OWNED_OUTRIGHT" in c and c.endswith("_N")]
        guess_mort_c = [c for c in cols if "OWNED_WITH_MORTGAGE" in c and c.endswith("_N")]
        guess_total = [c for c in cols if c.endswith("_Total")]
        if guess_oo_c and guess_mort_c and guess_total:
            total = df[guess_total[0]].replace({0: float("nan")})
            df["ownership_pct"] = (df[guess_oo_c[0]] + df[guess_mort_c[0]]) / total * 100.0
        else:
            raise RuntimeError("Could not derive ownership_pct from G37 fields.")
    # Keep SA2 code/name and ownership_pct
    # Common fields: SA2_CODE_2021 or SA2_CODE21, SA2_NAME_2021 or SA2_NAME21
    code_col = next((c for c in df.columns if c.upper().startswith("SA2_CODE")), None)
    name_col = next((c for c in df.columns if c.upper().startswith("SA2_NAME")), None)
    keep = df[[code_col, name_col, "ownership_pct"]].rename(columns={code_col:"sa2_code21", name_col:"sa2_name21"})
    out = DATA / "abs_tenure_home_ownership_sa2.csv"
    keep.to_csv(out, index=False)
    print(f"Wrote {out}")

def fetch_seifa_irsad_sa2():
    # SEIFA 2021 by SA2 (IRSAD index) – Digital Atlas dataset
    # Many layers exist; we'll use the 'ABS Socio-Economic Indexes for Areas (SEIFA) by 2021 SA2' service if available
    # Example service often named 'SEIFA_2021_SA2'.
    # Try a known layer path; if it fails, instruct user.
    candidates = [
        "https://services-ap1.arcgis.com/ypkPEy1AmwPKGNNv/arcgis/rest/services/SEIFA_2021_SA2/FeatureServer/0/query",
        "https://geo.abs.gov.au/arcgis/rest/services/Hosted/SEIFA_2021_SA2/FeatureServer/0/query",
    ]
    df = None
    for url in candidates:
        try:
            df = fs_query_to_df(url, {})
            if not df.empty:
                break
        except Exception:
            continue
    if df is None or df.empty:
        raise RuntimeError("Could not fetch SEIFA IRSAD by SA2 via FeatureServer. See README for manual CSV link.")

    cols = df.columns
    code_col = next((c for c in cols if c.upper().startswith("SA2_CODE")), None)
    name_col = next((c for c in cols if c.upper().startswith("SA2_NAME")), None)
    # IRSAD score/rank fields commonly contain 'IRSAD' and 'SCORE' or 'RANK'
    irsad_rank = next((c for c in cols if "IRSAD" in c.upper() and "RANK" in c.upper()), None)
    if irsad_rank is None:
        # Sometimes it's 'irsad_decile' or 'irsad_quintile' – use rank-like field
        irsad_rank = next((c for c in cols if "DECILE" in c.upper()), None)
    if irsad_rank is None:
        raise RuntimeError("Could not identify IRSAD rank field.")
    keep = df[[code_col, name_col, irsad_rank]].rename(columns={code_col:"sa2_code21", name_col:"sa2_name21", irsad_rank:"irsad_rank"})
    out = DATA / "abs_seifa_irsad_sa2.csv"
    keep.to_csv(out, index=False)
    print(f"Wrote {out}")

def fetch_rba_cash_rate():
    # RBA cash rate CSV
    # The RBA provides CSV on the Cash Rate page and statistical tables.
    # We'll scrape the CSV from the 'Cash Rate Target' page if present; otherwise ask user to confirm URL.
    url = "https://www.rba.gov.au/statistics/cash-rate/cash-rate.csv"
    r = requests.get(url, headers=HEADERS, timeout=120)
    if r.status_code != 200:
        # Fallback to generic stats table listing
        url = "https://www.rba.gov.au/statistics/tables/cash-rate.csv"
        r = requests.get(url, headers=HEADERS, timeout=120)
    r.raise_for_status()
    out = DATA / "rba_cash_rate_history.csv"
    with open(out, "wb") as f:
        f.write(r.content)
    print(f"Wrote {out}")

def fetch_vic_vpsr():
    # Victorian Property Sales Report latest XLSX (yearly summary)
    # Data directory lists resources with stable links.
    # We'll fetch the 'Year summary' XLSX then normalise to CSV.
    # NOTE: Links may change. Adjust if 404.
    candidates = [
        "https://www.land.vic.gov.au/__data/assets/file/0015/736078/Year-summary-2024.xlsx",
    ]
    xbytes = None
    for u in candidates:
        try:
            r = requests.get(u, headers=HEADERS, timeout=180)
            if r.status_code == 200 and r.content:
                xbytes = r.content
                break
        except Exception:
            pass
    if xbytes is None:
        print("Could not auto-download VPSR Year summary. Please download manually from land.vic.gov.au and save as data/vic_vpsr_year_summary.xlsx")
        return
    xpath = DATA / "vic_vpsr_year_summary.xlsx"
    with open(xpath, "wb") as f:
        f.write(xbytes)
    # Parse to a tidy CSV for medians by suburb (house/unit where available)
    try:
        xl = pd.read_excel(xpath, sheet_name=None)
        # Heuristic: find any sheet with 'house' or 'unit' and has suburb column
        out_rows = []
        for sname, df in xl.items():
            df.columns = [str(c).strip().lower() for c in df.columns]
            if "suburb" in df.columns and "median" in " ".join(df.columns):
                # pick columns
                subs = df.filter(regex="^suburb").iloc[:,0]
                med = df.filter(regex="median").iloc[:,0]
                if not subs.empty and not med.empty:
                    for a,b in zip(subs, med):
                        out_rows.append({"suburb": str(a).strip(), "median_price": b, "sheet": sname})
        if out_rows:
            pd.DataFrame(out_rows).to_csv(DATA / "vic_vpsr_medians.csv", index=False)
            print(f"Wrote {DATA / 'vic_vpsr_medians.csv'}")
        else:
            print("VPSR parsing heuristic found no rows; please tidy manually.")
    except Exception as e:
        print("Excel parse error:", e)

def fetch_postcode_sa2_correspondence():
    # ABS correspondences (CSV). The exact file name can vary; provide a helpful message.
    # We'll attempt a common endpoint pattern from data.gov.au; otherwise instruct manual download.
    urls = [
        # Example resource ID path sometimes used on data.gov.au
        "https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/correspondences",
    ]
    print("Please download the official ABS postcode<->SA2 correspondence CSV for 2021 from the ABS page and save it as data/postcode_to_sa2_2021.csv")
    print("Page:", urls[0])

def main():
    fetch_sa2_boundaries()
    fetch_abs_g37_homeownership()
    try:
        fetch_seifa_irsad_sa2()
    except Exception as e:
        print(\"SEIFA fetch warning:\", e)
    try:
        fetch_rba_cash_rate()
    except Exception as e:
        print(\"RBA fetch warning:\", e)
    fetch_vic_vpsr()
    fetch_postcode_sa2_correspondence()
    print(\"Done. Replace vacancy CSV with a public source when available and join via postcode->SA2.\")

if __name__ == "__main__":
    main()
