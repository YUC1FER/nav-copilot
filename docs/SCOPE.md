# NAV Copilot: scope (v0, demo)

## Problem
Every month, for every fund, someone manually:
1. Takes the administrator's NAV report
2. Reconciles NAV per share, shares outstanding and AUM against the internal Excel model
3. Waits for figures to tie out and for Paris management to sign off
4. Copies the verified figures into the factsheet, newsletter and investor presentation
5. Writes the monthly commentary and sends via DocSend / email

Steps 2, 4 and the first draft of 5 are mechanical. They are slow and error-prone because they are copy-paste.

## What v0 does
| Step | v0 behaviour | Human role |
|---|---|---|
| Ingest | Reads admin CSV + internal model XLSX | none |
| Reconcile | Field-by-field diff with tolerances, writes a break report | Reviews every break |
| Factsheet | Fills a template ONLY from reconciled figures | Approves |
| Draft | LLM drafts commentary + newsletter, flags AMF risk phrases | Edits, approves |
| Distribute | Creates a Gmail **draft** | Clicks send |

## Hard rules
- Nothing is sent automatically. The agent prepares, a human releases.
- If reconciliation has any unresolved break, the pipeline stops before drafting.
- LLMs never compute figures. Code computes, the LLM only writes prose around verified numbers.
- Only synthetic data in this repo.

## Out of scope for v0
Live admin feeds, DocSend API, PPTX investor deck, multi-language output, scheduling.

## Success metric for the demo
Month-end package for 2 funds produced in under 2 minutes, with all 3 planted breaks caught.
