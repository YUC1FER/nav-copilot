"""Tests for src/reconcile.py."""

from pathlib import Path

import pandas as pd

from src.ingest import load_admin, load_model
from src.reconcile import BREAK_COLUMNS, TOLERANCES, reconcile, write_break_report

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample"


def _admin() -> pd.DataFrame:
    """Two synthetic days for one fund."""
    return pd.DataFrame({
        "date": pd.to_datetime(["2026-09-01", "2026-09-02"]),
        "fund_id": ["DEMO-A", "DEMO-A"],
        "nav_per_share": [10.0, 11.0],
        "shares_outstanding": [1000, 1000],
        "aum": [10000.0, 11000.0],
    })


def test_identical_inputs_have_no_breaks() -> None:
    assert reconcile(_admin(), _admin()).empty


def test_nav_difference_is_reported_with_values() -> None:
    model = _admin()
    model.loc[1, "nav_per_share"] = 11.5
    report = reconcile(_admin(), model)
    row = report[report["field"] == "nav_per_share"].iloc[0]
    assert row["admin_value"] == 11.0
    assert row["model_value"] == 11.5
    assert row["difference"] == 0.5
    assert not row["derived"]


def test_aum_break_alongside_nav_break_is_derived() -> None:
    model = _admin()
    model.loc[1, "nav_per_share"] = 11.5
    model.loc[1, "aum"] = 11500.0
    report = reconcile(_admin(), model)
    assert report.set_index("field")["derived"].to_dict() == {
        "aum": True, "nav_per_share": False}


def test_aum_break_alone_is_not_derived() -> None:
    model = _admin()
    model.loc[0, "aum"] = 10500.0
    report = reconcile(_admin(), model)
    assert list(report["field"]) == ["aum"]
    assert not report["derived"].iloc[0]


def test_difference_inside_tolerance_is_ignored() -> None:
    model = _admin()
    model.loc[0, "nav_per_share"] = 10.0 + TOLERANCES["nav_per_share"]
    assert reconcile(_admin(), model).empty


def test_difference_outside_tolerance_is_flagged() -> None:
    model = _admin()
    model.loc[0, "nav_per_share"] = 10.0 + 2 * TOLERANCES["nav_per_share"]
    assert list(reconcile(_admin(), model)["field"]) == ["nav_per_share"]


def test_shares_tolerance_is_exact() -> None:
    model = _admin()
    model.loc[0, "shares_outstanding"] = 1001
    assert list(reconcile(_admin(), model)["field"]) == ["shares_outstanding"]


def test_row_missing_in_model_is_a_break() -> None:
    report = reconcile(_admin(), _admin().iloc[:1])
    assert list(report["issue"]) == ["missing in model"]
    assert report["date"].iloc[0] == pd.Timestamp("2026-09-02")


def test_row_missing_in_admin_is_a_break() -> None:
    report = reconcile(_admin().iloc[:1], _admin())
    assert list(report["issue"]) == ["missing in admin"]


def test_planted_errors_in_sample_data_are_caught() -> None:
    report = reconcile(load_admin(SAMPLE / "admin_nav_report_2026-09.csv"),
                       load_model(SAMPLE / "internal_model_2026-09.xlsx"))
    primary = report[~report["derived"]]
    found = {(d.strftime("%Y-%m-%d"), f, fld)
             for d, f, fld in zip(primary["date"], primary["fund_id"], primary["field"])}
    assert found == {
        ("2026-09-15", "DEMO-BTCEQ", "nav_per_share"),
        ("2026-09-22", "DEMO-MKTN", "nav_per_share"),
        ("2026-09-30", "DEMO-BTCEQ", "shares_outstanding"),
    }
    assert len(report) == 6          # 3 primary + 3 derived aum
    assert report[report["derived"]]["field"].eq("aum").all()


def test_report_csv_has_one_line_per_break_and_iso_dates(tmp_path: Path) -> None:
    model = _admin()
    model.loc[1, "nav_per_share"] = 11.5
    report = reconcile(_admin(), model)
    path = write_break_report(report, tmp_path / "logs" / "break_report.csv")
    back = pd.read_csv(path)
    assert list(back.columns) == BREAK_COLUMNS
    assert len(back) == len(report)
    assert back["date"].iloc[0] == "2026-09-02"


def test_report_csv_is_header_only_when_no_breaks(tmp_path: Path) -> None:
    path = write_break_report(reconcile(_admin(), _admin()), tmp_path / "r.csv")
    back = pd.read_csv(path)
    assert back.empty
    assert list(back.columns) == BREAK_COLUMNS
