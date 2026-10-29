"""
Generate SYNTHETIC fund data for the NAV Copilot demo.

Nothing here is real Melanion data. Fund names, NAVs and AUM are invented.
The script produces two files that mimic the real monthly workflow:

  data/sample/admin_nav_report_2026-09.csv   -> what the fund administrator sends
  data/sample/internal_model_2026-09.xlsx    -> the internal Excel model you reconcile against

It also plants 3 deliberate mismatches in the internal model so the
reconciliation step (Day 2) has something real to catch.

Run:  python src/make_sample_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42                     # same seed = same data every run (reproducible demo)
MONTH_START = "2026-09-01"
MONTH_END = "2026-09-30"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "sample"

FUNDS = [
    # (fund_id, name, share_class, isin_placeholder, start_nav, shares_outstanding, daily_vol)
    ("DEMO-BTCEQ", "Demo Bitcoin Equities UCITS ETF", "Acc USD", "XX0000000001", 18.40, 2_500_000, 0.035),
    ("DEMO-MKTN", "Demo Market Neutral Fund", "I EUR", "XX0000000002", 1_250.00, 18_000, 0.004),
]

# Deliberate errors planted in the internal model: (fund_id, date, field, how much to shift)
PLANTED_ERRORS = [
    ("DEMO-BTCEQ", "2026-09-15", "nav_per_share", +0.05),   # small price break
    ("DEMO-MKTN", "2026-09-22", "nav_per_share", -1.10),     # larger price break
    ("DEMO-BTCEQ", "2026-09-30", "shares_outstanding", +5_000),  # month-end share-count break
]


def business_days() -> pd.DatetimeIndex:
    return pd.bdate_range(MONTH_START, MONTH_END)


def simulate_fund(rng: np.random.Generator, fund) -> pd.DataFrame:
    fund_id, name, share_class, isin, start_nav, shares, vol = fund
    days = business_days()
    returns = rng.normal(loc=0.0005, scale=vol, size=len(days))
    nav = start_nav * np.cumprod(1 + returns)
    # small random subscriptions/redemptions
    share_flows = rng.integers(-0.01 * shares, 0.01 * shares, size=len(days))
    shares_series = shares + np.cumsum(share_flows)
    df = pd.DataFrame({
        "date": days.date,
        "fund_id": fund_id,
        "fund_name": name,
        "share_class": share_class,
        "isin": isin,
        "currency": "USD" if "USD" in share_class else "EUR",
        "nav_per_share": np.round(nav, 4),
        "shares_outstanding": shares_series.astype(int),
    })
    df["aum"] = (df["nav_per_share"] * df["shares_outstanding"]).round(2)
    return df


def build_internal_model(admin: pd.DataFrame) -> pd.DataFrame:
    """The internal model starts as a copy of the admin data, then gets the planted errors."""
    model = admin[["date", "fund_id", "nav_per_share", "shares_outstanding"]].copy()
    for fund_id, date, field, shift in PLANTED_ERRORS:
        mask = (model["fund_id"] == fund_id) & (model["date"].astype(str) == date)
        model.loc[mask, field] = model.loc[mask, field] + shift
    model["aum"] = (model["nav_per_share"] * model["shares_outstanding"]).round(2)
    return model


def monthly_stats(admin: pd.DataFrame) -> pd.DataFrame:
    """Month-level stats the factsheet will need (computed from the admin data)."""
    rows = []
    for fund_id, g in admin.groupby("fund_id"):
        g = g.sort_values("date")
        daily = g["nav_per_share"].pct_change().dropna()
        rows.append({
            "fund_id": fund_id,
            "nav_start": g["nav_per_share"].iloc[0],
            "nav_end": g["nav_per_share"].iloc[-1],
            "mtd_return_pct": round((g["nav_per_share"].iloc[-1] / g["nav_per_share"].iloc[0] - 1) * 100, 2),
            "annualised_vol_pct": round(daily.std() * np.sqrt(252) * 100, 2),
            "aum_end": g["aum"].iloc[-1],
        })
    return pd.DataFrame(rows)


def main() -> None:
    rng = np.random.default_rng(SEED)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    admin = pd.concat([simulate_fund(rng, f) for f in FUNDS], ignore_index=True)
    model = build_internal_model(admin)
    stats = monthly_stats(admin)

    admin_path = OUT_DIR / "admin_nav_report_2026-09.csv"
    model_path = OUT_DIR / "internal_model_2026-09.xlsx"

    admin.to_csv(admin_path, index=False)
    with pd.ExcelWriter(model_path, engine="openpyxl") as xl:
        model.to_excel(xl, sheet_name="daily_nav", index=False)
        stats.to_excel(xl, sheet_name="monthly_stats", index=False)

    print(f"Wrote {admin_path.name}: {len(admin)} rows")
    print(f"Wrote {model_path.name}: sheets daily_nav ({len(model)} rows), monthly_stats ({len(stats)} rows)")
    print(f"Planted {len(PLANTED_ERRORS)} mismatches for Day 2 to catch.")


if __name__ == "__main__":
    main()
