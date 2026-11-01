"""Tests for src/factsheet_figures.py."""

from pathlib import Path

import pandas as pd
import pytest

from src.factsheet_figures import compute_figures
from src.ingest import load_admin

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample"


def _admin() -> pd.DataFrame:
    """Three days for one fund, deliberately out of date order."""
    return pd.DataFrame({
        "date": pd.to_datetime(["2026-09-03", "2026-09-01", "2026-09-02"]),
        "fund_id": "DEMO-A",
        "nav_per_share": [11.0, 10.0, 10.5],
        "shares_outstanding": [1000, 1000, 1000],
        "aum": [11000.0, 10000.0, 10500.0],
    })


def test_figures_use_first_and_last_date_of_the_month() -> None:
    f = compute_figures(_admin(), "DEMO-A")
    assert f["as_of"] == pd.Timestamp("2026-09-03")
    assert f["nav_end"] == 11.0
    assert f["mtd_return_pct"] == 10.0          # 11.0 / 10.0 - 1
    assert f["aum_end"] == 11000.0


def test_volatility_is_annualised_std_of_daily_returns() -> None:
    r1, r2 = 10.5 / 10.0 - 1, 11.0 / 10.5 - 1
    expected = round(pd.Series([r1, r2]).std() * 252 ** 0.5 * 100, 2)
    assert compute_figures(_admin(), "DEMO-A")["annualised_vol_pct"] == expected


def test_unknown_fund_raises() -> None:
    with pytest.raises(ValueError, match="DEMO-X"):
        compute_figures(_admin(), "DEMO-X")


def test_august_figures_match_the_model_monthly_stats_sheet() -> None:
    admin = load_admin(SAMPLE / "admin_nav_report_2026-08.csv")
    stats = pd.read_excel(SAMPLE / "internal_model_2026-08.xlsx", sheet_name="monthly_stats")
    for _, row in stats.iterrows():
        f = compute_figures(admin, row["fund_id"])
        assert f["nav_end"] == pytest.approx(row["nav_end"])
        assert f["mtd_return_pct"] == pytest.approx(row["mtd_return_pct"])
        assert f["annualised_vol_pct"] == pytest.approx(row["annualised_vol_pct"])
        assert f["aum_end"] == pytest.approx(row["aum_end"])
