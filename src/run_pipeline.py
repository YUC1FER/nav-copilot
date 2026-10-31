"""
Run the monthly pipeline up to the reconciliation gate.

  ingest -> reconcile -> break report -> STOP if any break exists

Every break counts as unresolved for now, so a single break stops the run before
any drafting (drafting is not built yet).

Run:  python src/run_pipeline.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # lets `python src/run_pipeline.py` find the src package

from src.ingest import load_admin, load_model
from src.reconcile import reconcile, write_break_report

ADMIN_PATH = ROOT / "data" / "sample" / "admin_nav_report_2026-09.csv"
MODEL_PATH = ROOT / "data" / "sample" / "internal_model_2026-09.xlsx"
REPORT_PATH = ROOT / "logs" / "break_report_2026-09.csv"


def run(admin_path: Path, model_path: Path, report_path: Path) -> int:
    """Reconcile model against admin, write the break report, return the exit code (0 clean, 1 breaks)."""
    admin = load_admin(admin_path)
    model = load_model(model_path)
    breaks = reconcile(admin, model)
    write_break_report(breaks, report_path)

    if breaks.empty:
        print("Reconciliation clean: no breaks.")
        return 0

    primary = int((~breaks["derived"]).sum())
    print(f"STOP: {len(breaks)} break rows ({primary} primary, {len(breaks) - primary} derived).")
    for _, b in breaks.iterrows():
        tag = " (derived)" if b["derived"] else ""
        print(f"  {b['date']:%Y-%m-%d}  {b['fund_id']}  {b['field']}{tag}: {b['issue']}")
    print(f"Break report: {report_path}")
    return 1


def main() -> None:
    """Run the pipeline on the September sample files and exit with its code."""
    sys.exit(run(ADMIN_PATH, MODEL_PATH, REPORT_PATH))


if __name__ == "__main__":
    main()
