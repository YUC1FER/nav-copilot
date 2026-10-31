# NAV Copilot

Monthly fund-reporting pipeline: administrator NAV report → reconciliation against the internal model → factsheet and newsletter drafts → Gmail draft for human approval.

> All data in this repo is synthetic. No real fund data, no real ISINs.

## Why
Month-end reporting is copy-paste across a reconciliation, a factsheet, a newsletter and an email. That is slow and is where errors get in. NAV Copilot automates the mechanical steps and keeps humans on every judgment call and every send.

## Pipeline
```
admin_nav_report.csv ─┐
                      ├─> reconcile ──(breaks?)──> STOP + break report
internal_model.xlsx ──┘        │
                               └─(clean)─> factsheet ─> LLM draft + AMF flags ─> Gmail DRAFT ─> human sends
```

## Status
- [x] Day 1: scope, synthetic data, repo hygiene
- [x] Day 2: ingest + reconcile + tests
- [ ] Day 3: factsheet template
- [ ] Day 4: LLM commentary + compliance flags
- [ ] Day 5: Gmail draft (OAuth, compose scope only)
- [ ] Day 6: demo video

## Run
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/make_sample_data.py
```

## Design rules
See [docs/SCOPE.md](docs/SCOPE.md).
