# NAV Copilot: rules for Claude Code

## Context
Monthly fund-reporting pipeline for an AMF-regulated asset manager. Demo build, synthetic data only.
Owner is learning: optimise for code he can read and defend, not for cleverness.

## Hard rules
- Synthetic data only. Never create, request or read real fund data.
- Nothing is ever sent. Email output = Gmail DRAFT only.
- LLMs never compute figures. All numbers come from Python code.
- Any unresolved reconciliation break stops the pipeline before drafting.
- Never commit secrets. Secrets live in .env (gitignored).

## How to work
- Plan before coding. Show the plan, wait for approval.
- Small changes: one file or one function per step.
- Plain Python: pandas, openpyxl, pytest. No new dependencies without asking.
- Every function gets a docstring and type hints.
- Write or update tests in tests/ for any logic change. Run `python -m pytest -q` after each change.
- After each change, explain in 3 bullets what changed and why.

## Environment
Windows 11, PowerShell, venv at .venv. Use `python`, not `python3`.
Write files as UTF-8. Never use `echo >>` redirection.
