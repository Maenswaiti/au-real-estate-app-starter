# AU Real-Estate App — Public Data Only

**No logins. No commercial APIs.** Streamlit app that ranks suburbs and estimates deal metrics using public data (ABS, RBA, state open-data). Ships with small CSV/GeoJSON samples so it runs out-of-the-box.

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Data
- `data/abs_tenure_home_ownership_sa2_sample.csv` — Home-ownership % (Census 2021) by SA2 (sample rows). Replace with full ABS export if desired.
- `data/abs_seifa_irsad_sa2_sample.csv` — SEIFA IRSAD rank by SA2 (sample rows).
- `data/sqm_vacancy_postcode_sample.csv` — Vacancy by postcode (sample). Replace with your latest public CSV from SQM’s site.
- `data/vic_vpsr_medians_sample.csv` — VIC suburb medians/time-series (sample from VPSR). Add more states.
- `geometry/sa2_2021_simplified.geojson` — Simplified SA2 polygons (small sample). Replace with full Australia for national view.

## Stay public-only
- ABS/SEIFA via ABS Data API or Digital Atlas downloads (no key). Cache to CSV.
- Vacancy: SQM free summaries; manually download and place CSV in `data/`.
- Prices: State open-data portals (e.g., VIC VPSR). Download periodically.
- Rates: RBA CSVs. Fetch on-demand or cache.

## Deploy to GitHub + Streamlit Cloud
1. Create a repo on GitHub (e.g. `au-real-estate-app-starter`).
2. On macOS Terminal:
   ```bash
   cd /path/to/au-real-estate-app-starter
   git init
   git add .
   git commit -m "Initial commit: public-data AU real-estate app"
   git branch -M main
   git remote add origin https://github.com/<you>/au-real-estate-app-starter.git
   git push -u origin main
   ```
3. Go to [share.streamlit.io](https://share.streamlit.io) (Streamlit Community Cloud) → New app → Connect your repo → pick `main` and `app.py`.
4. In Advanced settings, set Python version to 3.11+ and make sure `requirements.txt` is present.
5. Deploy.

**Not financial advice. Use at your own risk.**


## Production: load full public datasets (no keys)

1. Run the fetcher (downloads SA2 boundaries, G37 ownership proxy, SEIFA IRSAD, RBA cash rate, VIC VPSR, and instructs you for ABS postcode↔SA2 table):
```bash
python scripts/fetch_full_data.py
```

2. Replace the sample files in `data/` and `geometry/` with the newly downloaded ones:
   - `geometry/sa2_2021_full.geojson`
   - `data/abs_tenure_home_ownership_sa2.csv`
   - `data/abs_seifa_irsad_sa2.csv` (if fetch succeeded; otherwise follow the link printed)
   - `data/rba_cash_rate_history.csv`
   - `data/vic_vpsr_medians.csv`
   - `data/postcode_to_sa2_2021.csv` (download manually via ABS *Correspondences* page)

3. Provide a **public vacancy** CSV (e.g., SQM free summaries) as `data/vacancy_by_postcode.csv` and update `app.py` to join by postcode→SA2 using the ABS correspondence table.

4. (Optional) Add state datasets for NSW/QLD/SA/WA via their open-data portals.

