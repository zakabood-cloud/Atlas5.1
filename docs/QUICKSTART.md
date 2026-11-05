# ATLAS 5.1 quickstart

Extract the ZIP; **commit extracted files**, not just an archive. Set up a Python venv (`python3 -m venv .venv`, `source .venv/bin/activate`, `pip install -e .`) or run from repo root with `python -m atlas`.

Initialize with `atlas check`, `atlas doctor --deployment`, and `atlas init` (readiness announcement; **STOP**). The initial check is local; internet access remains unverified until `atlas doctor --network --host APPROVED_HOST`. If it fails under a Copilot sandbox firewall, request authorized allowlist changes and create a new session. Do not silently relay around restrictions.

After inquiry:

- `atlas new example --question '...' --domain general --mode rigorous`
- `atlas intake-batch example` — ask as one grouped questionnaire, explicitly agree deliverables, formats, outline and research depth.
- `atlas answer example KEY 'USER ANSWER'` — record user answers; `atlas mandate example --acknowledged` automatically advances.
- `atlas next example`; `atlas scaffold example --stage ENABLEMENT` — use only on relevant stages; generated drafts are not observations.
- `atlas advance example NEXT_STAGE --dry-run` — inspect requirements, then advance normally.
- During RESEARCH: `atlas source-add example --url https://... --title ... --query ... --text 'observed content' --provisional` for a snippet, or supply `--file` for a stored full source. `atlas claim-add example --text '...' --source-ids S0001 --scope '...' --material` records a claim requiring review. `atlas search-log-add` captures zero-result searches.
- `atlas report-contract example contract.json` after the user agrees to report outline/length; `atlas report-audit example outputs/report.md` and `atlas render example outputs/report.md outputs/report.pdf --format pdf` (ReportLab required for PDFs).
- `atlas limited-report example outputs/report.md --reason '...unverified sources...'` produces a prominently labeled incomplete report instead of pretending completion.

`atlas access-renew example NEED_ID access-tests/receipt.json` stores a fresh observed receipt. Routine offline bookkeeping should not halt because receipts expired; external calls still require valid permission and tests.

For safety run `atlas privacy-check example`, and verify repository visibility. Incomplete or synthetic tests never establish world-class research accuracy. See [release note](RELEASE_5_1.md).
