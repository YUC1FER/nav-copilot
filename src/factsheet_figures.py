"""
Month-end figures for the factsheet, computed in plain pandas from the admin data.

This is the only place the factsheet numbers come from. No LLM is involved.
The pipeline calls it only after reconciliation has come back clean.
"""

import numpy as np
import pandas as pd


def compute_figures(admin: pd.DataFrame, fund_id: str) -> dict:
    """Return as-of date, end NAV, MTD return %, annualised volatility % and end AUM for one fund.

    MTD return is measured from the first NAV of the month, the same basis as the
    monthly_stats sheet in the internal model.
    """
    g = admin[admin["fund_id"] == fund_id].sort_values("date")
    if g.empty:
        raise ValueError(f"no rows for fund {fund_id}")
    nav_start = g["nav_per_share"].iloc[0]
    nav_end = g["nav_per_share"].iloc[-1]
    daily = g["nav_per_share"].pct_change().dropna()
    return {
        "fund_id": fund_id,
        "as_of": g["date"].iloc[-1],
        "nav_end": float(nav_end),
        "mtd_return_pct": round((nav_end / nav_start - 1) * 100, 2),
        "annualised_vol_pct": round(daily.std() * np.sqrt(252) * 100, 2),
        "aum_end": float(g["aum"].iloc[-1]),
    }
