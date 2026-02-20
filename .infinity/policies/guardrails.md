# Guardrails — Hard Limits & Circuit-Breakers

Guardrails are **non-negotiable, hard-coded limits** that no agent, workflow,
or orchestrator action may bypass under any circumstances.  They sit at the
top of the Authority stack and cannot be overridden by governance rules, agent
logic, or human operators without changing this document via the policy change
process.

---

## 1. Absolute Prohibitions (NEVER)

The following actions are **always forbidden**, regardless of context:

| # | Prohibited Action | Rationale |
|---|------------------|-----------|
| G-01 | Delete the `main` branch of any repository | Catastrophic data loss |
| G-02 | Force-push to `main` or any protected branch | History rewrite; breaks CI |
| G-03 | Commit secrets, credentials, or private keys to any file | Security breach |
| G-04 | Echo or log an unmasked secret to stdout/stderr | Secret exposure |
| G-05 | Remove `SECURITY.md`, `CONTRIBUTING.md`, or `LICENSE` | Governance integrity |
| G-06 | Bypass the TAP validation gate | Policy violation |
| G-07 | Call an unregistered external API endpoint | Ungoverned data exfiltration |
| G-08 | Auto-merge a PR with failing checks | Quality gate bypass |
| G-09 | Delete a GitHub repository without a human-confirmed issue | Irreversible data loss |
| G-10 | Modify billing settings autonomously | Financial risk |
| G-11 | Revoke or rotate the GitHub App private key autonomously | Irreversible lockout risk |
| G-12 | Delete a Cloudflare zone or account autonomously | Catastrophic DNS/CDN loss |
| G-13 | Disable secret scanning on any repository | Security regression |
| G-14 | Create or modify org-level webhooks pointing to external URLs | Data exfiltration risk |
| G-15 | Grant `admin` permissions to any new member autonomously | Privilege escalation |

---

## 2. Rate / Volume Circuit-Breakers

Automated workflows must halt and create a tracking issue if they would
exceed these thresholds in a single run:

| Resource | Limit | Action on Breach |
|----------|-------|-----------------|
| GitHub API calls (per workflow job) | 4,000 / hour | Pause + exponential back-off |
| PRs opened per cycle | 20 | Halt + create tracking issue |
| Branches created per cycle | 50 | Halt + create tracking issue |
| Files changed in a single auto-commit | 500 | Halt + split into multiple PRs |
| Workflow runs triggered per hour | 30 | Throttle + queue remainder |
| Cloudflare API calls per minute | 200 | Pause + back-off |
| OpenAI tokens per run | 100,000 | Halt + summarise |
| New repositories created per day | 5 | Halt + human confirmation |

---

## 3. Destructive-Action Confirmation Protocol

Any action tagged as **destructive** (delete, purge, truncate, force-push)
must follow this protocol before executing:

```
1. Create a GitHub Issue:
     title:  "⚠️ DESTRUCTIVE ACTION PENDING: {description}"
     labels: ["guardrail:destructive", "human-approval-required"]
     body:   details of the action + rollback plan

2. Wait for the issue to receive label "approved-by-human"
   (polled every 5 minutes, maximum 24-hour wait).

3. If approval is received: execute action + add comment "action-executed".

4. If timeout: close issue as "not executed"; abort.
```

Automated workflows must **never** skip this protocol for destructive actions.

---

## 4. Sensitive-File Protection

The following files in **any** repository under `Infinity-X-One-Systems`
must never be deleted or overwritten by an autonomous commit:

- `SECURITY.md`
- `CONTRIBUTING.md`
- `LICENSE` / `LICENSE.md`
- `.github/CODEOWNERS`
- `.infinity/policies/*.md`
- `config/github-app-manifest.json`

Attempting to stage a deletion of these files must be blocked with a
TAP violation.

---

## 5. Secret Pattern Detection

Before committing any file, the TAP validator scans for these patterns
(used by `stacks/agents/validator_agent.py`; patterns are applied via
Python `re.search` in multiline mode):

```
# Private key headers
PRIVATE_KEY
BEGIN\s+(RSA\s+)?PRIVATE

# Credential assignments (excluding GitHub context expressions like ${{ secrets.X }})
(?i)password\s*[:=]\s*['"]?\S+
(?i)api[_-]?key\s*[:=]\s*['"]?\S+
(?i)token\s*[:=]\s*['"]?\S+

# Provider-specific key formats
AKIA[0-9A-Z]{16}                   # AWS access key ID
sk-[a-zA-Z0-9]{32,}               # OpenAI API key prefix
```

> **Note:** The Cloudflare API token format (40-character alphanumeric string)
> does not have a universally unique prefix and is detected by the pattern
> `(?i)(cloudflare|cf)[_-]?(api[_-]?)?token\s*[:=]\s*['"]?\S{30,}`.
> GitHub's built-in secret scanning provides more comprehensive detection.

If any pattern is detected in staged content, the commit is rejected and a
`secret-scanning` issue is opened.

---

## 6. Workflow Concurrency Limits

| Workflow | Max Concurrent Runs | Overflow Action |
|----------|:------------------:|----------------|
| `autonomous-invention.yml` | 1 | Queue (cancel-in-progress: false) |
| `genesis-loop.yml` | 1 | Queue |
| `genesis-devops-team.yml` | 1 | Queue |
| `health-monitor.yml` | 3 | New run replaces oldest |
| `self-healing.yml` | 5 | Fail-fast disabled |
| `security-scan.yml` | 1 | Queue |
| `local-docker-sync.yml` | 2 | Queue |

---

## 7. Cross-Repository Mutation Limits

When the orchestrator acts on **other** org repositories (cross-repo ops),
additional limits apply:

| Operation | Max Per Cycle | Requires Issue Log |
|-----------|:------------:|:------------------:|
| Open PRs | 10 | ✅ |
| Commit directly to non-main branch | 20 | ✅ |
| Create releases / tags | 5 | ✅ |
| Delete branches | 10 | ✅ |
| Trigger workflow dispatches | 15 | ❌ |

---

## 8. Escalation on Guardrail Breach

If any guardrail is triggered:

1. The running workflow **immediately halts** the current phase.
2. An issue is created:
   - **title**: `🚨 GUARDRAIL BREACH: {guardrail_id} — {description}`
   - **labels**: `guardrail-breach`, `priority:critical`, `human-approval-required`
3. A `repository_dispatch` event is fired: `event_type: guardrail_breach`.
4. No further autonomous actions proceed until the issue is closed with
   label `guardrail-resolved`.

---

## 9. Guardrail Audit Log

Every time a guardrail check is evaluated (pass or fail), a record is
written to `logs/telemetry/guardrails-{date}.json`:

```json
{
  "timestamp": "...",
  "run_id": "...",
  "guardrail_id": "G-01",
  "check": "delete_main_branch",
  "result": "blocked",
  "details": "..."
}
```

---

## Related Documents

| Document | Location |
|----------|---------|
| TAP Protocol | `.infinity/policies/tap-protocol.md` |
| Governance | `.infinity/policies/governance.md` |
| Validator Agent | `stacks/agents/validator_agent.py` |
| Agent Entrypoint | `AGENT_ENTRYPOINT.md` |
