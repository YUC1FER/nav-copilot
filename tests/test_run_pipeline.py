"""Tests for src/run_pipeline.py."""

from pathlib import Path

import pandas as pd
import pytest

from src.ingest import MODEL_SHEET
from src.run_pipeline import paths_for_month, run

COLUMNS = ["date", "fund_id", "nav_per_share", "shares_outstanding", "aum"]


def _frame() -> pd.DataFrame:
    """Three synthetic days for one fund (volatility needs at least two daily returns)."""
    return pd.DataFrame({
        "date": ["2026-09-01", "2026-09-02", "2026-09-03"],
        "fund_id": "DEMO-A",
        "nav_per_share": [10.0, 10.1, 10.2],
        "shares_outstanding": 1000,
        "aum": [10000.0, 10100.0, 10200.0],
    })[COLUMNS]


def _write_pair(tmp_path: Path, model: pd.DataFrame) -> tuple[Path, Path]:
    """Write _frame() as the admin CSV (with fund details) and `model` as the model workbook."""
    admin_path = tmp_path / "admin.csv"
    model_path = tmp_path / "model.xlsx"
    _frame().assign(fund_name="Demo A", share_class="Acc USD",
                    isin="XX0000000001", currency="USD").to_csv(admin_path, index=False)
    with pd.ExcelWriter(model_path, engine="openpyxl") as xl:
        model.to_excel(xl, sheet_name=MODEL_SHEET, index=False)
    return admin_path, model_path


def test_september_stops_the_pipeline_and_writes_no_factsheet(tmp_path: Path) -> None:
    admin_path, model_path, _ = paths_for_month("2026-09")
    report_path, out_dir = tmp_path / "report.csv", tmp_path / "output"
    assert run(admin_path, model_path, report_path, out_dir) == 1
    assert len(pd.read_csv(report_path)) == 6
    assert not out_dir.exists()


def test_august_is_clean_and_writes_one_factsheet_per_fund(tmp_path: Path) -> None:
    admin_path, model_path, _ = paths_for_month("2026-08")
    out_dir = tmp_path / "output"
    assert run(admin_path, model_path, tmp_path / "report.csv", out_dir) == 0
    names = sorted(p.name for p in out_dir.iterdir())
    assert names == ["factsheet_DEMO-BTCEQ_2026-08.html", "factsheet_DEMO-MKTN_2026-08.html"]


def test_clean_inputs_pass_and_write_empty_report(tmp_path: Path) -> None:
    admin_path, model_path = _write_pair(tmp_path, _frame())
    report_path, out_dir = tmp_path / "logs" / "report.csv", tmp_path / "output"
    assert run(admin_path, model_path, report_path, out_dir) == 0
    assert pd.read_csv(report_path).empty
    assert (out_dir / "factsheet_DEMO-A_2026-09.html").exists()


def test_single_break_stops_the_pipeline_and_writes_no_factsheet(tmp_path: Path) -> None:
    bad = _frame()
    bad.loc[0, "shares_outstanding"] = 1001
    admin_path, model_path = _write_pair(tmp_path, bad)
    out_dir = tmp_path / "output"
    assert run(admin_path, model_path, tmp_path / "report.csv", out_dir) == 1
    assert not out_dir.exists()


def test_stop_message_lists_each_break(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    admin_path, model_path, _ = paths_for_month("2026-09")
    run(admin_path, model_path, tmp_path / "report.csv", tmp_path / "output")
    out = capsys.readouterr().out
    assert "STOP" in out
    assert "2026-09-15  DEMO-BTCEQ  nav_per_share" in out
