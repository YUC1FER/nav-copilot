"""Tests for src/factsheet.py."""

from pathlib import Path

import pandas as pd
import pytest

from src.factsheet import TEMPLATE_PATH, format_figures, render_factsheet

FIGURES = {
    "fund_id": "DEMO-A",
    "as_of": pd.Timestamp("2026-08-31"),
    "nav_end": 18.43215,
    "mtd_return_pct": 3.456,
    "annualised_vol_pct": 12.0,
    "aum_end": 46111548.9,
}
DETAILS = {"fund_name": "Demo A & Co", "share_class": "Acc USD",
           "isin": "XX0000000001", "currency": "USD"}


def test_numbers_are_formatted_as_agreed() -> None:
    v = format_figures(FIGURES, DETAILS)
    assert v["nav_end"] == "18.4322"            # 4 decimals
    assert v["mtd_return"] == "+3.46%"          # 2 decimals, signed
    assert v["volatility"] == "12.00%"
    assert v["aum_end"] == "46,111,548.90"      # thousands separators
    assert v["as_of"] == "2026-08-31"


def test_text_is_html_escaped() -> None:
    assert format_figures(FIGURES, DETAILS)["fund_name"] == "Demo A &amp; Co"


def test_render_fills_every_placeholder(tmp_path: Path) -> None:
    out = render_factsheet(FIGURES, DETAILS, TEMPLATE_PATH, tmp_path / "sub" / "f.html")
    page = out.read_text(encoding="utf-8")
    assert "$" not in page
    assert "18.4322" in page and "+3.46%" in page and "46,111,548.90" in page
    assert "SYNTHETIC DEMO DATA" in page


def test_template_with_unknown_placeholder_fails_loudly(tmp_path: Path) -> None:
    template = tmp_path / "t.html"
    template.write_text("<p>$nav_end $not_a_field</p>", encoding="utf-8")
    with pytest.raises(KeyError):
        render_factsheet(FIGURES, DETAILS, template, tmp_path / "f.html")
