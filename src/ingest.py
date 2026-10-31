"""
Load the two monthly inputs into DataFrames that can be compared directly.

  admin CSV     -> what the fund administrator sends (the reference)
  model XLSX    -> the internal Excel model (the file under test)

Both loaders return the same five columns with the same types, so the
reconciliation step does not have to care where a row came from.
"""

from pathlib import Path

import pandas as pd

MODEL_SHEET = "daily_nav"
REQUIRED_COLUMNS = ["date", "fund_id", "nav_per_share", "shares_outstanding", "aum"]


def _check_columns(df: pd.DataFrame, source: Path) -> None:
    """Raise ValueError naming every required column that is missing from df."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{source.name}: missing required columns {missing}")


def _normalise(df: pd.DataFrame) -> pd.DataFrame:
    """Keep the required columns only, with dates and numbers in a common type."""
    out = df[REQUIRED_COLUMNS].copy()
    out["date"] = pd.to_datetime(out["date"])
    out["nav_per_share"] = out["nav_per_share"].astype(float)
    out["shares_outstanding"] = out["shares_outstanding"].astype(int)
    out["aum"] = out["aum"].astype(float)
    return out


def load_admin(path: Path) -> pd.DataFrame:
    """Read the administrator's CSV and return the required columns, typed."""
    path = Path(path)
    df = pd.read_csv(path)
    _check_columns(df, path)
    return _normalise(df)


def load_model(path: Path) -> pd.DataFrame:
    """Read the daily_nav sheet of the internal model and return the required columns, typed."""
    path = Path(path)
    df = pd.read_excel(path, sheet_name=MODEL_SHEET)
    _check_columns(df, path)
    return _normalise(df)
