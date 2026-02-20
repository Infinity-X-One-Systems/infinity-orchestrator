# Governance Enforcement Runbook

> **Org:** Infinity-X-One-Systems  
> **Scope:** `infinity-orchestrator` autonomous operations  
> **Version:** 1.0.0  
> **Policy reference:** [`.infinity/policies/tap-protocol.md`](../policies/tap-protocol.md)

---

## 1. Purpose

This runbook describes the concrete enforcement points, decision logging procedures, and escalation paths for the **TAP Protocol** governance framework. It is the operational companion to the policy document.

All autonomous actors (workflows, agents, scripts) **must** follow this runbook when making policy-relevant decisions.

---

## 2. Enforcement Points

### 2.1 Workflow Entry (Pre-Job)

Every workflow that performs a write operation must include the following gate step:

```yaml
- name: TAP Policy Gate
  run: |
    echo "::notice::TAP Gate — actor: github-actions[bot] | action: ${{ github.workflow }} | trigger: ${{ github.event_name }}"
    echo "::notice::Correlation ID: ${{ github.run_id }}-${{ github.run_attempt }}"
```

This step:
- Logs the actor, action, and trigger to the step summary.
- Provides a correlation ID derived from the workflow run ID (no additional secret needed).

### 2.2 Secret Access

Every time a secret is read from environment variables, the script must:

1. Immediately mask the value using `::add-mask::` (Bash) or `Invoke-MaskSecret` (PowerShell).
2. Never pass the value as a process argument (use environment variables or stdin).
3. Never write the value to any file that persists beyond the workflow run.

**Bash pattern:**
```bash
echo "::add-mask::${SECRET_VALUE}"
```

**PowerShell pattern:**
```powershell
Invoke-MaskSecret -Secret $SecretValue
```

### 2.3 Cross-Repository Operations

Before cloning or pushing to any repository other than `infinity-orchestrator`:

1. Verify the operation uses a GitHub App installation access token (not a PAT).
2. Log the target repository and operation type to the step summary.
3. Remove the token from `.git/config` in a `finally` block after the operation.

### 2.4 Commit Attribution

All automated commits must use:
- **Name:** `github-actions[bot]`
- **Email:** `41898282+github-actions[bot]@users.noreply.github.com`

Verify with:
```bash
git config user.name  'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
```

### 2.5 Idempotency Check

Before committing, scripts must check for actual changes using `git status --porcelain`. If no changes exist, skip the commit. This prevents noise in git history and ensures re-runs are safe.

---

## 3. Decision Log Format

Every policy-relevant decision must be logged. Use the following JSON schema:

```json
{
  "timestamp": "2026-01-01T00:00:00Z",
  "actor": "github-actions[bot]",
  "action": "memory-sync: push to infinity-orchestrator",
  "policy_rules_checked": ["P-001", "P-003", "P-005"],
  "decision": "allowed",
  "correlation_id": "12345678-1",
  "justification": "All policy checks passed. Token masked. Attributed to bot account."
}
```

**Decision values:**
- `allowed` — action proceeded normally
- `denied` — action was blocked by policy
- `degraded` — action ran in reduced capacity (e.g., memory fallback used)

### 3.1 Logging in GitHub Actions

Output the log entry to the step summary:
```bash
cat >> "$GITHUB_STEP_SUMMARY" << 'EOF'
### TAP Decision Log
```json
{
  "timestamp": "...",
  "actor": "github-actions[bot]",
  ...
}
```
EOF
```

### 3.2 Logging in PowerShell Scripts

```powershell
$decision = [PSCustomObject]@{
    timestamp        = ([System.DateTime]::UtcNow.ToString('o'))
    actor            = 'github-actions[bot]'
    action           = 'memory-sync'
    policy_rules_checked = @('P-001','P-003','P-005')
    decision         = 'allowed'
    correlation_id   = $env:GITHUB_RUN_ID
    justification    = 'All policy checks passed.'
}
Write-Host ($decision | ConvertTo-Json -Compress)
```

---

## 4. Enforcement Scenarios

### Scenario A: Memory Sync (allowed)

1. Trigger: `memory-sync.yml` fires on schedule.
2. Gate step logs correlation ID.
3. Script validates `GITHUB_APP_ID` and `GITHUB_APP_PRIVATE_KEY` are set.
4. JWT and IAT are masked immediately.
5. Clone uses HTTPS with token in extraheader (never in URL arguments logged).
6. `ACTIVE_MEMORY.md` validated non-empty.
7. Changes committed with bot attribution and pushed.
8. Token unset in `finally` block.
9. Decision log: `allowed`.

### Scenario B: Missing Memory (degraded)

1. `Invoke-InfinityAgentBootstrap.ps1` runs on clean checkout.
2. Local `ACTIVE_MEMORY.md` not found — no failure.
3. Script attempts GitHub-first memory retrieval via App token.
4. If App credentials absent, script emits degraded bootstrap payload with empty memory fields.
5. Decision log: `degraded`, justification: "ACTIVE_MEMORY.md not found locally; GitHub retrieval attempted."

### Scenario C: Policy Violation — Secret in Log (denied)

1. A workflow step attempts to `echo $TOKEN`.
2. GitHub Actions redacts the masked value automatically.
3. If the masking was not applied before the echo, the enforcement gate must catch the violation.
4. Violation is logged to step summary with `decision: denied`.
5. Workflow is failed (`exit 1`).

### Scenario D: Unauthorised Force-Push Attempt (denied)

1. An automated step includes `git push --force`.
2. Branch protection rules on `main` block the push at the GitHub level.
3. The error is caught, logged as `decision: denied`.
4. Human escalation is required (see Section 5).

---

## 5. Escalation Paths

| Violation Severity | First Responder | Escalation |
|-------------------|-----------------|------------|
| Low (warning, no data loss) | On-call engineer reviews step summary | None required if resolved within 24 h |
| Medium (failed workflow, service degraded) | On-call engineer + team lead | Postmortem within 48 h |
| High (secret exposure, unauthorised write) | Security lead + org owner | Immediate rotation of affected secrets; postmortem within 24 h |
| Critical (data exfiltration, supply chain compromise) | Org owner + security lead | Revoke all tokens; contact GitHub Security; postmortem within 4 h |

---

## 6. Audit Trail Retention

- GitHub Actions logs: retained per organisation plan (default 90 days).
- Step summaries: retained with workflow run.
- `.infinity/` artifacts: retained in git history indefinitely unless expunged by security incident response.

---

## 7. Policy Review Triggers

This runbook must be reviewed when:

- A new endpoint category is added to the registry.
- A new GitHub App or OAuth credential is introduced.
- A security incident occurs (see Section 5).
- The orchestrator major version increments.

---

*Infinity Orchestrator · Governance Enforcement Runbook v1.0.0 · Infinity-X-One-Systems*
