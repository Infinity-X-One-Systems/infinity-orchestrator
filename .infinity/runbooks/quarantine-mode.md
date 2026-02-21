# Quarantine Mode — Runbook

> **Scope:** Infinity Orchestrator — `Infinity-X-One-Systems` org  
> **TAP Reference:** P-001, P-003, P-004, G-08  
> **Owner:** Infinity Orchestrator automation  

---

## 1. Overview

Quarantine mode is a **circuit-breaker** that prevents the autonomous system from
auto-merging PRs after repeated failures or when manual investigation is needed.

When quarantine mode is active:
- All PRs opened by the autonomy controller are created as **drafts**
- Auto-merge is **completely disabled** for all PRs
- Quarantine notices are posted as PR comments
- The system continues to **sense**, **think**, and update the backlog ledger
- The system **stops** before the **ship** phase

Quarantine mode does **not**:
- Stop CI checks from running
- Block human-initiated PR merges
- Affect non-autonomous workflows

---

## 2. Activating Quarantine Mode

### Manual activation

```bash
gh variable set INFINITY_QUARANTINE_MODE --body true \
  --repo Infinity-X-One-Systems/infinity-orchestrator
```

### Automatic activation (future)

The autonomy controller will automatically set quarantine mode when it detects
`N` consecutive failures (configurable). Until this is implemented, operators
must activate quarantine mode manually when they observe:

- Consecutive failed workflow runs (3+ in a row)
- Unexpected PRs being opened or merged
- Alerts from the `health-monitor.yml` workflow
- Security scan failures

---

## 3. Behaviour in Quarantine Mode

### Autonomy Controller (`autonomy-controller.yml`)

| Phase | Behaviour |
|-------|-----------|
| SENSE | Runs normally — collects signals |
| THINK | Runs normally — updates backlog ledger |
| ACT | Opens **draft** PRs only (never ready-for-review) |
| VERIFY | Runs normally — checks CI status |
| SHIP | **Skipped** — no auto-merge labels applied |
| LEARN | Runs normally — writes run docs with quarantine notice |

### Auto-Merge Workflow (`genesis-auto-merge.yml`)

The `policy-gate` job detects `INFINITY_QUARANTINE_MODE=true` and:
1. Sets `quarantine_active=true` output
2. Skips the `auto-merge` job
3. Runs the `quarantine-notice` job which posts a PR comment

---

## 4. Investigating During Quarantine

While in quarantine mode, investigate the root cause using the following approach:

### Step 1: Review recent run docs

```bash
ls -la docs/run-*.md | tail -10
cat docs/run-<LATEST_RUN_ID>.md
```

### Step 2: Check the backlog ledger

```bash
cat .infinity/ledger/backlog.json | jq '.items[] | select(.status == "blocked")'
```

### Step 3: Review workflow run logs

```bash
gh run list --workflow autonomy-controller.yml \
  --repo Infinity-X-One-Systems/infinity-orchestrator \
  --limit 10

gh run view <RUN_ID> --log --repo Infinity-X-One-Systems/infinity-orchestrator
```

### Step 4: Check open alerts

```bash
gh issue list \
  --repo Infinity-X-One-Systems/infinity-orchestrator \
  --label "orchestrator:alert" \
  --state open
```

---

## 5. Resolving Quarantine

After identifying and fixing the root cause:

1. Close or resolve the relevant tracking issues
2. Verify that the underlying problem is fixed (e.g., CI is green, permissions are correct)
3. Disable quarantine mode:

```bash
gh variable set INFINITY_QUARANTINE_MODE --body false \
  --repo Infinity-X-One-Systems/infinity-orchestrator
```

4. Manually trigger the autonomy controller to confirm it runs cleanly:

```bash
gh workflow run autonomy-controller.yml \
  --repo Infinity-X-One-Systems/infinity-orchestrator \
  --field phases="sense think"
```

5. If the run is clean, promote any draft PRs that were opened during quarantine:

```bash
# Convert a draft PR to ready for review
gh pr ready <PR_NUMBER> --repo Infinity-X-One-Systems/infinity-orchestrator
```

---

## 6. Quarantine Mode vs. Full Disable

| Mode | Variable | Effect |
|------|----------|--------|
| Normal | (defaults) | Full autonomy, auto-merge enabled |
| Quarantine | `INFINITY_QUARANTINE_MODE=true` | Draft PRs, no auto-merge, sensing/thinking continues |
| No auto-merge | `INFINITY_AUTOMERGE_ENABLED=false` | Ready PRs, no auto-merge |
| Full disable | `INFINITY_AUTONOMY_ENABLED=false` | All phases skipped |

---

## 7. Notification Checklist for Operators

When activating quarantine mode, operators should:

- [ ] Post a note in the team channel explaining why quarantine was activated
- [ ] Open a tracking issue with label `orchestrator:incident` describing the problem
- [ ] Set quarantine mode: `gh variable set INFINITY_QUARANTINE_MODE --body true`
- [ ] Review the backlog ledger for stale/blocked items
- [ ] Monitor the next autonomy controller run (should show `SHIP: skipped`)
- [ ] After resolution: set `INFINITY_QUARANTINE_MODE=false` and verify

---

## 8. TAP Compliance

Quarantine mode is fully TAP-compliant:
- All policy checks still run during quarantine
- No secrets are logged (P-001)
- Bot attribution is maintained on all commits (P-003)
- No direct pushes to `main` occur (P-004)
- Decision logs are written to step summaries (P-006)

---

*Infinity Orchestrator · Quarantine Mode Runbook · TAP Protocol v1.0.0*
