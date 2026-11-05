# ATLAS Research OS v5.1.0 — Incident Remediation Release

## Release purpose

This update is based on **27 real-world Copilot incident issues** (26 workflow failures plus unavailable web retrieval). It is not another agent expansion. The focus is to get useful research started promptly, preserve observed evidence, reduce repeated approvals and make incomplete outcomes honest.

## Implementation status

- **13** issues have bounded locally implemented functionality.
- **14** have partial implementations or remain dependent on real Copilot/GitHub integration tests.
- **0** issues have been independently certified end-to-end on the user's authenticated Copilot cloud account.

See `docs/INCIDENT_27_MATRIX.csv` for every original problem, affected code, and honest remaining caveat. These labels do not imply verified research-quality superiority.

## Main delivered capabilities

- Safe ZIP extraction utility and venv-installable `atlas` command (`pyproject.toml`).
- `atlas doctor --network --host ...` (explicit consent; checks DNS/TLS only), `--deployment`, and `privacy-check`.
- Concise `AGENTS.md` core instructions; detailed research procedures remain in load-on-demand skills.
- `atlas next` / `advance --dry-run`, stage `scaffold`, grouped `intake-batch`, and CLI mandate auto-advance.
- Approval/test preservation for unchanged access needs; fresh access required at new external execution, not at offline task completion.
- `source-add`, `claim-add`, `search-log-add` and provisional `search_result` sources; no unverified source gains independent authority by being logged.
- Bounded `EXPLORATORY` follow-up searches with existing approved tools; mandatory protocol searches still count.
- Explicit `limited-report` output, zero-claim strict-audit failure, `report-contract`, `render` with human-readable footnotes and optional PDF export.
- Git sensitive-file preflight, an optional pre-commit guard and a GitHub CI privacy check.
- Optional, disabled GitHub Actions fetch relay and a GitHub API trigger implementation. It needs user/organization authorization and a real live test before use. URL lists can be public.

## Tests

- Execute `python -m unittest discover -s tests -q` for local regression tests.
- `python scripts/demo.py` exercises the *synthetic* end-to-end state machine.
- `python scripts/incident_smoke_51.py` exercises optional-failure continuation, capture and explicit limited delivery with *synthetic* evidence.
- `python scripts/validate_release.py` performs the existing broader release gate, historical file hashes and synthetic calculations.

Local tests cannot prove that the Copilot environment will load the agents/skills, reach research websites, support real delegation, obtain paid data or deliver excellent research. No live external fetch or Actions relay job was executed for this release.

## Important limitations and next actions

1. **Unzip and commit the extracted files.** Do not leave only ZIP and README at the repository root. Start a *new* Copilot session from the correct repository root. Confirm `.github/agents/`, `.github/skills/`, `AGENTS.md` and `atlas/` are visible and the installed version is 5.1.0.
2. Before research, run `atlas doctor --deployment` and a **user-authorized** `atlas doctor --network --host www.census.gov --host api.crossref.org`. If blocked, request approved GitHub firewall allowlisting and start a fresh environment. Do not automatically activate a relay to evade intentional restrictions.
3. Run a small, low-cost live research acceptance test with 2–3 public sources, one grouped intake, durable source records, report audit, and either complete verified delivery or an explicitly limited report. Capture the actual Copilot tool logs and stage transitions.
4. Only then decide whether further changes are justified. Particularly test cross-session retention, automatic recording of native Copilot retrievals, semantics of evidence review, report completeness and 0 unnecessary global holds for optional failures.
5. Optional GitHub Actions relay is **not installed or live-tested**; actual workflow API dispatch and encrypted retrieval must be tested only if security policy authorizes it.

## Security

Never commit project datasets, `projects/`, `.atlas/`, private relay keys, provider tokens or research notes containing personal financial data to a public branch. `.gitignore` does not untrack prior commits. No local scanner can erase public Git history or guarantee all credentials are detected.

## Recommended initial Copilot instruction

> Read `AGENTS.md` from the *extracted and committed* ATLAS 5.1 repository. Verify installed version, agents/skills, privacy and real network reachability. Initialize and announce readiness, then STOP. After I submit my inquiry, ask all relevant clarification questions together, request deliverables, conduct meta-research, and use the source capture / next / scaffold commands to minimize bookkeeping. Do not bypass verification or claim external access without testing it.
