"""Tests for src/run_pipeline.py."""

from pathlib import Path

import pandas as pd
import pytest

from src.ingest import MODEL_SHEET
from src.run_pipeline import ADMIN_PATH, MODEL_PATH, run

COLUMNS = ["date", "fund_id", "nav_per_share", "shares_outstanding", "aum"]


def _frame() -> pd.DataFrame:
    """One synthetic day for one fund."""
    return pd.DataFrame([["2026-09-01", "DEMO-A", 10.0, 1000, 10000.0]], columns=COLUMNS)


def _write_pair(tmp_path: Path, model: pd.DataFrame) -> tuple[Path, Path]:
    """Write _frame() as the admin CSV and `model` as the model workbook."""
    admin_path = tmp_path / "admin.csv"
    model_path = tmp_path / "model.xlsx"
    _frame().to_csv(admin_path, index=False)
    with pd.ExcelWriter(model_path, engine="openpyxl") as xl:
        model.to_excel(xl, sheet_name=MODEL_SHEET, index=False)
    return admin_path, model_path


def test_sample_data_stops_the_pipeline_with_six_rows(tmp_path: Path) -> None:
    report_path = tmp_path / "report.csv"
    assert run(ADMIN_PATH, MODEL_PATH, report_path) == 1
    assert len(pd.read_csv(report_path)) == 6


def test_clean_inputs_pass_and_write_empty_report(tmp_path: Path) -> None:
    admin_path, model_path = _write_pair(tmp_path, _frame())
    report_path = tmp_path / "logs" / "report.csv"
    assert run(admin_path, model_path, report_path) == 0
    assert pd.read_csv(report_path).empty


def test_single_break_stops_the_pipeline(tmp_path: Path) -> None:
    bad = _frame()
    bad.loc[0, "shares_outstanding"] = 1001
    admin_path, model_path = _write_pair(tmp_path, bad)
    assert run(admin_path, model_path, tmp_path / "report.csv") == 1


def test_stop_message_lists_each_break(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    run(ADMIN_PATH, MODEL_PATH, tmp_path / "report.csv")
    out = capsys.readouterr().out
    assert "STOP" in out
    assert "2026-09-15  DEMO-BTCEQ  nav_per_share" in out
