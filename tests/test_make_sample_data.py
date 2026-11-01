"""Tests for src/make_sample_data.py."""

from pathlib import Path

import pandas as pd

from src.ingest import load_admin, load_model
from src.make_sample_data import MONTHS, generate_month
from src.reconcile import reconcile

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample"


def _month(label: str) -> tuple:
    """Return the MONTHS entry for a label."""
    return next(m for m in MONTHS if m[0] == label)


def test_august_is_clean_and_reconciles_with_no_breaks() -> None:
    admin = load_admin(SAMPLE / "admin_nav_report_2026-08.csv")
    model = load_model(SAMPLE / "internal_model_2026-08.xlsx")
    assert len(admin) == 42                      # 21 business days x 2 funds
    assert reconcile(admin, model).empty


def test_september_still_has_its_six_break_rows() -> None:
    admin = load_admin(SAMPLE / "admin_nav_report_2026-09.csv")
    model = load_model(SAMPLE / "internal_model_2026-09.xlsx")
    assert len(reconcile(admin, model)) == 6


def test_regenerated_september_matches_committed_admin_csv() -> None:
    _, start, end, seed, planted = _month("2026-09")
    admin, _, _ = generate_month(start, end, seed, planted)
    committed = pd.read_csv(SAMPLE / "admin_nav_report_2026-09.csv")
    pd.testing.assert_frame_equal(admin.astype(str), committed.astype(str))


def test_regenerated_august_matches_committed_admin_csv() -> None:
    _, start, end, seed, planted = _month("2026-08")
    admin, _, _ = generate_month(start, end, seed, planted)
    committed = pd.read_csv(SAMPLE / "admin_nav_report_2026-08.csv")
    pd.testing.assert_frame_equal(admin.astype(str), committed.astype(str))
