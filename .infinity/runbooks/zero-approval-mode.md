# Zero-Approval Autonomy Mode — Runbook

> **Scope:** Infinity Orchestrator — `Infinity-X-One-Systems` org  
> **TAP Reference:** P-001, P-003, P-004, P-005, G-02, G-08  
> **Owner:** Infinity Orchestrator automation  

---

## 1. Overview

Zero-approval autonomy mode allows the Infinity Orchestrator to open and auto-merge
pull requests **without a human reviewer** for changes that meet all of the following
criteria:

| Criterion | Requirement |
|-----------|-------------|
| Risk level | `low` or `medium` only (label `risk:low` or `risk:medium`) |
| CI status | All checks must pass (no failures or cancellations) |
| Merge conflicts | PR must be conflict-free (`mergeable: true`) |
| TAP decision record | PR body must contain `<!-- TAP-DECISION: ... -->` or a `## TAP Decision` section |
| `autonomous-verified` label | Must be present on the PR |
| `INFINITY_AUTOMERGE_ENABLED` | Must not be `false` |
| `INFINITY_QUARANTINE_MODE` | Must not be `true` |

High-risk (`risk:high`) and critical-risk (`risk:critical`) PRs are **never**
auto-merged regardless of any other setting.

---

## 2. Enabling Zero-Approval Mode

Zero-approval mode is **on by default**. No action is required unless it has been
explicitly disabled.

To confirm it is active:

```bash
# Check repository variable (GitHub CLI)
gh variable list --repo Infinity-X-One-Systems/infinity-orchestrator | grep INFINITY
```

Expected output (defaults apply when variables are absent):

```
INFINITY_AUTOMERGE_ENABLED   true
INFINITY_QUARANTINE_MODE     false
```

To explicitly enable:

```bash
gh variable set INFINITY_AUTOMERGE_ENABLED --body true \
  --repo Infinity-X-One-Systems/infinity-orchestrator

gh variable set INFINITY_QUARANTINE_MODE --body false \
  --repo Infinity-X-One-Systems/infinity-orchestrator
```

---

## 3. Configuration Reference

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `INFINITY_AUTONOMY_ENABLED` | repo var | `true` | Master kill-switch for all autonomous operations |
| `INFINITY_AUTOMERGE_ENABLED` | repo var | `true` | Enable/disable auto-merge specifically |
| `INFINITY_MAX_PRS_PER_DAY` | repo var | `10` | Max PRs opened per autonomy controller run |
| `INFINITY_QUARANTINE_MODE` | repo var | `false` | Activates quarantine mode (see quarantine-mode.md) |

Set variables via GitHub CLI:

```bash
gh variable set VARIABLE_NAME --body VALUE \
  --repo Infinity-X-One-Systems/infinity-orchestrator
```

Or via the GitHub UI: **Settings → Secrets and variables → Actions → Variables**.

---

## 4. How Auto-Merge Works

### 4.1 Workflow triggers

The `genesis-auto-merge.yml` workflow is triggered by:

- `pull_request` events: `labeled`, `synchronize`, `reopened`
- `check_suite` events: `completed`

### 4.2 Policy gate (`policy-gate` job)

The policy gate evaluates:
1. Whether `autonomous-verified` label is present
2. The `INFINITY_AUTOMERGE_ENABLED` and `INFINITY_QUARANTINE_MODE` variables
3. The `risk:*` label to determine risk level
4. Whether the PR body contains a TAP decision record

### 4.3 Auto-merge job

Runs only when all policy gate checks pass. It:
1. Re-fetches the PR to verify label is still present
2. Verifies TAP decision record in PR body
3. Checks mergeability (`pr.mergeable === false` blocks merge)
4. Checks all CI check runs for failures
5. Merges via squash with a governance-compliant commit message

### 4.4 TAP Decision Record format

Every autonomously-opened PR must include a TAP decision record in the PR body:

```markdown
## TAP Decision

<!-- TAP-DECISION: {"actor":"github-actions[bot]","risk":"low","policies":["P-001","P-003","P-005","G-08"],"decision":"allowed","correlation_id":"<RUN_ID>-<ATTEMPT>","justification":"Low-risk chore change within scope of autonomous operation."} -->

| Field | Value |
|-------|-------|
| Risk | low |
| Policies checked | P-001, P-003, P-005, G-08 |
| Decision | allowed |
| Correlation ID | `<RUN_ID>-<ATTEMPT>` |
```

Replace `<RUN_ID>` with `$GITHUB_RUN_ID` and `<ATTEMPT>` with `$GITHUB_RUN_ATTEMPT` at generation time.

---

## 5. Allowed Risk Operations

### Low risk (`risk:low`)
- Dependency version bumps (patch-level)
- Documentation updates
- Test additions without logic changes
- Chore commits (CI config, `.gitignore`, etc.)

### Medium risk (`risk:medium`)
- Minor feature additions (new non-breaking functions)
- Dependency version bumps (minor-level)
- Refactoring with test coverage
- Configuration changes that are reversible

### Blocked (requires human review)
- `risk:high` — major changes, breaking API changes, security-sensitive changes
- `risk:critical` — security fixes, permission changes, infrastructure changes
- Any PR without a `risk:*` label

---

## 6. Monitoring & Audit

All auto-merge decisions are logged in the GitHub Actions step summary and
annotated in the workflow run. To review recent auto-merges:

```bash
# List recent auto-merge workflow runs
gh run list --workflow genesis-auto-merge.yml \
  --repo Infinity-X-One-Systems/infinity-orchestrator \
  --limit 20
```

The autonomy controller writes a run summary to `docs/run-{run_id}.md` for
every execution. These files are committed to the repository and form a
permanent audit trail.

---

## 7. Disabling Zero-Approval Mode

To disable auto-merge without activating full quarantine:

```bash
gh variable set INFINITY_AUTOMERGE_ENABLED --body false \
  --repo Infinity-X-One-Systems/infinity-orchestrator
```

To disable all autonomous operations:

```bash
gh variable set INFINITY_AUTONOMY_ENABLED --body false \
  --repo Infinity-X-One-Systems/infinity-orchestrator
```

---

*Infinity Orchestrator · Zero-Approval Mode Runbook · TAP Protocol v1.0.0*
