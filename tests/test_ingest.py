"""Tests for src/ingest.py. Uses small synthetic files written to a temp folder."""

from pathlib import Path

import pandas as pd
import pytest

from src.ingest import MODEL_SHEET, REQUIRED_COLUMNS, load_admin, load_model


def _rows() -> pd.DataFrame:
    """Two synthetic rows with every required column."""
    return pd.DataFrame({
        "date": ["2026-09-01", "2026-09-02"],
        "fund_id": ["DEMO-A", "DEMO-A"],
        "nav_per_share": [10.5, 10.75],
        "shares_outstanding": [1000, 1010],
        "aum": [10500.0, 10857.5],
    })


def _write_admin(path: Path, df: pd.DataFrame) -> Path:
    """Write df as the admin CSV."""
    df.to_csv(path, index=False)
    return path


def _write_model(path: Path, df: pd.DataFrame) -> Path:
    """Write df as the daily_nav sheet of an Excel file."""
    with pd.ExcelWriter(path, engine="openpyxl") as xl:
        df.to_excel(xl, sheet_name=MODEL_SHEET, index=False)
    return path


def test_load_admin_returns_required_columns_typed(tmp_path: Path) -> None:
    extra = _rows().assign(fund_name="Demo A", isin="XX0000000001")
    df = load_admin(_write_admin(tmp_path / "admin.csv", extra))
    assert list(df.columns) == REQUIRED_COLUMNS
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert df["shares_outstanding"].dtype == int


def test_admin_and_model_load_to_identical_frames(tmp_path: Path) -> None:
    admin = load_admin(_write_admin(tmp_path / "admin.csv", _rows()))
    model = load_model(_write_model(tmp_path / "model.xlsx", _rows()))
    pd.testing.assert_frame_equal(admin, model)


def test_missing_column_raises_and_names_it(tmp_path: Path) -> None:
    broken = _rows().drop(columns=["aum"])
    with pytest.raises(ValueError, match="aum"):
        load_admin(_write_admin(tmp_path / "admin.csv", broken))


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_admin(tmp_path / "nope.csv")


def test_real_sample_files_load() -> None:
    root = Path(__file__).resolve().parent.parent / "data" / "sample"
    admin = load_admin(root / "admin_nav_report_2026-09.csv")
    model = load_model(root / "internal_model_2026-09.xlsx")
    assert len(admin) == len(model) == 44
