---
name: atlas-discover
description: Complete inquiry-specific access and MCP preflight after mandate and enablement, before META or research
---

Run after the user ends intake, the mandate is accepted, and Copilot feature choices are recorded. Read the mandate, domain profile, `methods/TOOL_DISCOVERY.md`, `docs/ACCESS.md`, and `docs/INTEGRATIONS.md`. This step is **access planning only**: do not investigate substantive topic findings, collect evidence, or conduct a research pilot.

Map decision-relevant evidence needs to coverage dimensions. Compare the tools actually exposed in this Copilot session with useful topic-specific MCP, built-in, local, and manual alternatives. For MCP candidates, verify the official publisher and endpoint using authorized discovery capabilities; record the exact supporting basis and date. Do not claim exhaustive MCP discovery or treat an offline `access-needs` suggestion as a live server registry. Explain the incremental coverage, permissions, data shared, privacy/retention, costs, alternatives, and quality impact if access is absent.

Write `projects/<id>/access_plan.json` using the contract in `docs/SCHEMAS.md`. Choose only the minimum useful permissions. Present all proposed access decisions in one concise table and obtain a single informed response; preserve per-need authorization records. Ask for separate spending approval where required; `defer` requires the quality impact. Paid `use` needs separate spending approval. Do not automatically install/connect tools, request secrets, configure accounts, or call topic APIs. After approval, perform only an authorized benign read-only test with each used capability and save truthful current receipts using `access-test`. A configuration listing is not a test. A failed optional discovery/test is logged without stopping unrelated tasks. Critical/security access gaps require appropriate authorization. Use bounded retries only for approved, idempotent read-only operations. Notify the user and follow `docs/ACCESS.md`.

Only after all used tools have current observed tests and user choices are recorded may the coordinator advance to META. Missing or unavailable access remains an explicit quality limitation and may require a narrower mandate; never imply that the original scope is fully feasible when it is not.
