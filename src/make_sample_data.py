"""
Generate SYNTHETIC fund data for the NAV Copilot demo.

Nothing here is real Melanion data. Fund names, NAVs and AUM are invented.
For each month the script produces two files that mimic the real monthly workflow:

  data/sample/admin_nav_report_<month>.csv   -> what the fund administrator sends
  data/sample/internal_model_<month>.xlsx    -> the internal Excel model you reconcile against

2026-09 has 3 deliberate mismatches planted in the internal model so the
reconciliation step has something real to catch. 2026-08 is a clean month:
no planted errors, so the pipeline can run through to the factsheet.

Run:  python src/make_sample_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42                     # same seed = same data every run (reproducible demo)
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

MONTHS = [
    # (label, first day, last day, seed, planted errors)
    ("2026-09", "2026-09-01", "2026-09-30", SEED, PLANTED_ERRORS),
    ("2026-08", "2026-08-01", "2026-08-31", SEED + 1, []),
]


def business_days(start: str, end: str) -> pd.DatetimeIndex:
    """Weekdays from start to end inclusive (no holiday calendar)."""
    return pd.bdate_range(start, end)


def simulate_fund(rng: np.random.Generator, fund: tuple, start: str, end: str) -> pd.DataFrame:
    """Simulate one fund's daily NAV, share count and AUM over the given dates."""
    fund_id, name, share_class, isin, start_nav, shares, vol = fund
    days = business_days(start, end)
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


def build_internal_model(admin: pd.DataFrame, planted: list[tuple]) -> pd.DataFrame:
    """The internal model starts as a copy of the admin data, then gets the planted errors."""
    model = admin[["date", "fund_id", "nav_per_share", "shares_outstanding"]].copy()
    for fund_id, date, field, shift in planted:
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


def generate_month(start: str, end: str, seed: int,
                   planted: list[tuple]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build (admin, internal model, monthly stats) for one month, without writing files."""
    rng = np.random.default_rng(seed)
    admin = pd.concat([simulate_fund(rng, f, start, end) for f in FUNDS], ignore_index=True)
    model = build_internal_model(admin, planted)
    stats = monthly_stats(admin)
    return admin, model, stats


def main() -> None:
    """Write the admin CSV and internal model workbook for every month in MONTHS."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for label, start, end, seed, planted in MONTHS:
        admin, model, stats = generate_month(start, end, seed, planted)

        admin_path = OUT_DIR / f"admin_nav_report_{label}.csv"
        model_path = OUT_DIR / f"internal_model_{label}.xlsx"

        admin.to_csv(admin_path, index=False)
        with pd.ExcelWriter(model_path, engine="openpyxl") as xl:
            model.to_excel(xl, sheet_name="daily_nav", index=False)
            stats.to_excel(xl, sheet_name="monthly_stats", index=False)

        print(f"{label}: wrote {admin_path.name} ({len(admin)} rows) and {model_path.name}")
        print(f"{label}: planted {len(planted)} mismatches")


if __name__ == "__main__":
    main()
