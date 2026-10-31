"""
Field-by-field comparison of the administrator's NAV report against the internal model.

The admin data is the reference. Every difference larger than its tolerance is one
row in the break report. All numbers here come from plain pandas arithmetic.
"""

from pathlib import Path

import pandas as pd

KEYS = ["date", "fund_id"]
TOLERANCES = {
    "nav_per_share": 0.0001,   # absolute
    "shares_outstanding": 0,   # exact
    "aum": 0.01,               # absolute
}
BREAK_COLUMNS = ["date", "fund_id", "field", "admin_value", "model_value",
                 "difference", "derived", "issue"]


def _missing_row_breaks(merged: pd.DataFrame) -> list[dict]:
    """One break per (date, fund) that exists on only one side."""
    breaks = []
    for _, row in merged[merged["_merge"] != "both"].iterrows():
        side = "model" if row["_merge"] == "left_only" else "admin"
        breaks.append({
            "date": row["date"], "fund_id": row["fund_id"], "field": "row",
            "admin_value": None, "model_value": None, "difference": None,
            "derived": False, "issue": f"missing in {side}",
        })
    return breaks


def _value_breaks(both: pd.DataFrame, tolerances: dict[str, float]) -> list[dict]:
    """One break per field whose absolute difference exceeds its tolerance."""
    breaks = []
    for field, tol in tolerances.items():
        diff = both[f"{field}_model"] - both[f"{field}_admin"]
        # round() removes float noise so a difference of exactly `tol` is not flagged
        bad = diff.abs().round(10) > tol
        for idx in both.index[bad]:
            breaks.append({
                "date": both.at[idx, "date"], "fund_id": both.at[idx, "fund_id"],
                "field": field,
                "admin_value": both.at[idx, f"{field}_admin"],
                "model_value": both.at[idx, f"{field}_model"],
                "difference": diff.at[idx],
                "derived": False, "issue": "value mismatch",
            })
    return breaks


def _mark_derived(report: pd.DataFrame) -> pd.DataFrame:
    """Flag aum breaks on a row where nav_per_share or shares_outstanding also broke.

    aum is nav_per_share x shares_outstanding, so it differs as a consequence.
    """
    primary = report[report["field"].isin(["nav_per_share", "shares_outstanding"])]
    primary_keys = set(zip(primary["date"], primary["fund_id"]))
    row_has_primary = pd.Series(
        [(d, f) in primary_keys for d, f in zip(report["date"], report["fund_id"])],
        index=report.index,
    )
    report = report.copy()
    report["derived"] = (report["field"] == "aum") & row_has_primary
    return report


def write_break_report(report: pd.DataFrame, path: Path) -> Path:
    """Write the break report as UTF-8 CSV (header only if there are no breaks) and return its path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = report.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out.to_csv(path, index=False, encoding="utf-8")
    return path


def reconcile(admin: pd.DataFrame, model: pd.DataFrame,
              tolerances: dict[str, float] = TOLERANCES) -> pd.DataFrame:
    """Compare model against admin and return one row per break (empty if they tie out)."""
    merged = admin.merge(model, on=KEYS, how="outer",
                         suffixes=("_admin", "_model"), indicator=True)
    both = merged[merged["_merge"] == "both"]

    breaks = _missing_row_breaks(merged) + _value_breaks(both, tolerances)
    report = pd.DataFrame(breaks, columns=BREAK_COLUMNS)
    if report.empty:
        return report
    report = _mark_derived(report)
    return report.sort_values(["date", "fund_id", "field"]).reset_index(drop=True)
