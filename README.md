# ATLAS Research OS 5.1

**Ready-to-commit, extracted research operating system for GitHub Copilot and Claude Code.** Do not upload only this ZIP to a GitHub repository: **extract and commit the project files, including hidden `.github/` and `.claude/` directories**. Use a private repository for confidential projects; research data belongs under ignored `projects/`, not in Git history.

ATLAS provides a durable local research lifecycle, evidence/claim records, method preparation, reproducible calculation tools and stage-specific agent skills. It is **not** a guarantee of comprehensive research, verified fact, internet permissions, paid databases, or autonomous live agent orchestration.

## Installation

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .        # uses the local package; no system pip modifications
atlas check
atlas doctor --deployment
atlas init                      # announce readiness and STOP
```

The Python engine also works as `python -m atlas` from repository root without pip installation. For PDF export: `python -m pip install -e '.[pdf]'` (optional). Run `python -m unittest discover -s tests -q` for local regression checks.

## First research

1. After readiness, send the research question. ATLAS creates a project: `atlas new example --question 'Your question' --domain general --mode rigorous`.
2. Ask all relevant clarification questions in **one grouped interview**: `atlas intake-batch example`; explicitly agree on report format, outline and depth. Real approval is required for spending or private-data sharing.
3. Record answers and accept the mandate. The CLI `atlas mandate example --acknowledged` advances automatically if essential items are answered; never invent acknowledgment.
4. Use `atlas next example` and `atlas scaffold example --stage META` as needed. Meta-research decides the appropriate sources, tools and methods.
5. Before web work run `atlas doctor --network --host github.com --host www.census.gov` in a permitted environment. A failed DNS/TLS test is a **network limitation**, not automatically an ATLAS defect. Ask for approved firewall changes and a fresh sandbox where required.
6. During RESEARCH, capture retrievals immediately with `atlas source-add` / `atlas search-log-add`, add material claims with `atlas claim-add`, then independently review evidence.
7. Run `atlas report-audit example outputs/report.md`, `atlas render example outputs/report.md outputs/report.pdf --format pdf`. If verification is incomplete, deliver `atlas limited-report` instead.

`atlas next example` shows the next stage and missing items. See [quickstart](docs/QUICKSTART.md) and [v5.1 release and incident fixes](docs/RELEASE_5_1.md).

## Privacy and recovery

`atlas privacy-check example` inspects Git tracked paths for common sensitive patterns. It cannot remove exposed Git history. Configure a private repository and never commit `projects/`, `.atlas/`, credentials, private keys, or confidential exports. Check `git ls-files` before pushing. Local checkpoints and project backups remain available.

## Internet-access alternative

The optional GitHub Actions fetch relay (`optional_integrations/github_actions_fetch_relay/README.md`) is **not activated**. It is an opt-in, owner-authorized separate retrieval mechanism with encrypted artifacts. It must not be deployed to evade intentionally imposed network restrictions. The provider API trigger, web fetch and decryption need a real authorized end-to-end test before production use.
