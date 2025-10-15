from __future__ import annotations
import math
import pandas as pd

def monthly_repayment_pni(principal: float, annual_rate_pct: float, years: int) -> float:
    r = (annual_rate_pct/100)/12
    n = years*12
    if r == 0:
        return principal/n
    return principal * (r*(1+r)**n)/((1+r)**n - 1)

def assessed_rate_pct(user_rate_pct: float, buffer_pct: float = 3.0) -> float:
    return user_rate_pct + buffer_pct

def lvr_pct(price: float, deposit: float) -> float:
    if price <= 0: return 0.0
    return 100.0 * (1.0 - deposit/price)

def likely_lmi(lvr_percentage: float) -> bool:
    return lvr_percentage > 80.0

def gross_yield_pct(price: float, weekly_rent: float) -> float:
    if price <= 0: return 0.0
    return (weekly_rent*52.0)/price * 100.0

def net_yield_pct(price: float, weekly_rent: float, annual_expenses: float) -> float:
    if price <= 0: return 0.0
    return ((weekly_rent*52.0) - annual_expenses)/price * 100.0

def cash_on_cash_pct(
    annual_net_cashflow_after_debt: float,
    deposit_cash: float,
    stamp_duty: float,
    closing_costs: float,
    lmi_cost: float = 0.0,
) -> float:
    denom = deposit_cash + stamp_duty + closing_costs + lmi_cost
    if denom <= 0: return 0.0
    return (annual_net_cashflow_after_debt/denom) * 100.0

# Simple stamp duty lookup (rough guide). Use exact tables per state in data/stamp_duty_tables.csv
def stamp_duty_estimate(price: float, state: str, occupancy: str, tables_path: str) -> float:
    """Return rough stamp duty from a bracket table CSV with columns:
    state, occupancy, bracket_min, bracket_max, base, rate_pct, marginal_above
    occupancy in {"OO", "INV"}
    """
    df = pd.read_csv(tables_path)
    s = df[(df.state==state.upper()) & (df.occupancy==occupancy.upper())]
    row = s[(s.bracket_min<=price) & (price<=s.bracket_max)].head(1)
    if row.empty:
        # fall back to highest bracket in that state
        row = s.sort_values("bracket_max").tail(1)
    base = float(row.base)
    rate = float(row.rate_pct)/100.0
    marginal_above = float(row.marginal_above)
    return base + rate * max(0.0, price - marginal_above)
