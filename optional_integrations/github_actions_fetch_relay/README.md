# Optional external research relay (disabled by default)

**Not a method for evading intentionally imposed Copilot firewalls.** Use only if repository/org policy and the owner explicitly permit separate GitHub Actions retrieval. Prefer restarting with newly approved Copilot internet settings and use `atlas doctor --network` first.

The workflow is `.disabled` and **is not installed into `.github/workflows`**. It requires manual review and activation, separately authorized domain allowlisting, the repository Actions variable `ATLAS_RELAY_OWNER_AUTHORIZED=true`, and a public recipient key. For public repositories, the **requested URLs, workflow inputs, repository branch history, statuses and logs can be public**; only body content is encrypted. Avoid confidential URLs and any tokenized links. Workflow availability, artifact billing, and provider restrictions depend on the real account.

Setup (operator actions, do not automate without authorization):

1. Confirm owner and organization policies permit external source retrieval by Actions.
2. In an authorized local environment install `cryptography>=46,<47` and run `python relay.py keygen /secure/local/path/recipient.private.key recipient_public.key`. Never commit the private key. Public key must be committed next to the workflow's fetch files.
3. Populate `allowlist.json` with only specific approved public HTTPS hostnames. Review fetching policies for every host.
4. Review then copy `atlas-fetch.yml.disabled` to `.github/workflows/atlas-fetch.yml` on the default branch. Set repository Actions variable `ATLAS_RELAY_OWNER_AUTHORIZED=true` only after owner approval.
5. Manually dispatch a batch using GitHub's documented workflow-dispatch API/UI; use the `urls_json` input. GitHub requires the workflow on the default branch for standard dispatch handling. **Do not assume a Git push creates a workflow event.** The provider logs and artifacts must be checked.
6. Download encrypted artifact from the correct run, verify the run identity, and decrypt locally with `python relay.py decrypt --input encrypted-results.json --private-key /secure/local/path/recipient.private.key --output projects/PROJECT_ID/relay-data.json`.
7. Import results into the ATLAS evidence register as **operator-observed unverified snapshots**; do not mislabel them as independently verified. PDF bodies remain base64 encoded and need separate authorized text extraction.
8. Decommission workflow/keys and remove unnecessary artifacts after use. Deleting a public branch does not necessarily erase copies of URLs already disclosed.

Protection: HTTPS only, manual exact-domain allowlist, public DNS/IP checking, robots.txt checks, redirect validation, bounded requests/bytes/time, TLS, explicit authorization, public-key encryption, one-day artifact lifetime. No logins, paywalls or CAPTCHA circumvention, and no automatic deployment. JavaScript-rendered pages are **not** supported in this safe implementation. Run a real batch, including the GitHub API trigger, before claiming operational status.

### GitHub API request-submission method

Instead of git-push triggers, an owner-authorized operator may use `trigger.py OWNER REPO --urls-file /secure/approved-urls.json --allowlist allowlist.json --owner-approved` with `GH_TOKEN` set in the **operator environment**, and with the workflow already enabled on the default branch. It uses the official `workflow_dispatch` API and accepts HTTP 204 only as **submission**, not successful fetching. URLs are visible in the workflow input/event. The API path and API token scopes must be reviewed for the active repo. This client and its mock test do not establish live GitHub Actions access; perform an actual authorized batch test before enabling for production use.
