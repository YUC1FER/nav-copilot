"""
Run the monthly pipeline up to the factsheet.

  ingest -> reconcile -> break report -> STOP if any break exists
                                      -> otherwise: one factsheet per fund

Every break counts as unresolved for now, so a single break stops the run before
any factsheet or draft is produced (drafting is not built yet).

Run:  python src/run_pipeline.py [YYYY-MM]     (default month: 2026-09)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # lets `python src/run_pipeline.py` find the src package

from src.factsheet import TEMPLATE_PATH, render_factsheet
from src.factsheet_figures import compute_figures
from src.ingest import load_admin, load_fund_details, load_model
from src.reconcile import reconcile, write_break_report

DEFAULT_MONTH = "2026-09"
OUTPUT_DIR = ROOT / "output"


def paths_for_month(month: str) -> tuple[Path, Path, Path]:
    """Return (admin CSV, internal model, break report) paths for a month like '2026-09'."""
    sample = ROOT / "data" / "sample"
    return (sample / f"admin_nav_report_{month}.csv",
            sample / f"internal_model_{month}.xlsx",
            ROOT / "logs" / f"break_report_{month}.csv")


def write_factsheets(admin_path: Path, output_dir: Path) -> list[Path]:
    """Write one factsheet per fund, from reconciled admin figures, and return their paths."""
    admin = load_admin(admin_path)
    details = load_fund_details(admin_path)
    written = []
    for fund_id in sorted(admin["fund_id"].unique()):
        figures = compute_figures(admin, fund_id)
        name = f"factsheet_{fund_id}_{figures['as_of']:%Y-%m}.html"
        written.append(render_factsheet(figures, details[fund_id], TEMPLATE_PATH, output_dir / name))
    return written


def run(admin_path: Path, model_path: Path, report_path: Path, output_dir: Path) -> int:
    """Reconcile, write the break report, then factsheets if clean. Return 0 (clean) or 1 (breaks)."""
    admin = load_admin(admin_path)
    model = load_model(model_path)
    breaks = reconcile(admin, model)
    write_break_report(breaks, report_path)

    if not breaks.empty:
        primary = int((~breaks["derived"]).sum())
        print(f"STOP: {len(breaks)} break rows ({primary} primary, {len(breaks) - primary} derived).")
        for _, b in breaks.iterrows():
            tag = " (derived)" if b["derived"] else ""
            print(f"  {b['date']:%Y-%m-%d}  {b['fund_id']}  {b['field']}{tag}: {b['issue']}")
        print(f"Break report: {report_path}")
        return 1

    print("Reconciliation clean: no breaks.")
    for path in write_factsheets(admin_path, output_dir):
        print(f"Factsheet: {path}")
    return 0


def main() -> None:
    """Run the pipeline for the month given on the command line and exit with its code."""
    month = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MONTH
    admin_path, model_path, report_path = paths_for_month(month)
    sys.exit(run(admin_path, model_path, report_path, OUTPUT_DIR))


if __name__ == "__main__":
    main()
