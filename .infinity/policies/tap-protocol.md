# TAP Protocol — Policy > Authority > Truth

The **TAP Protocol** is the foundational governance framework that governs
every autonomous action taken by any agent, workflow, or script in the Infinity
Orchestrator system.  It is non-negotiable and cannot be overridden by any
individual agent decision.

---

## The Three Pillars

### T — Truth
> *Ground every decision in verifiable, observable facts.*

- Agents must verify claims before acting on them.
- If a fact cannot be confirmed via the GitHub API, file system, or an
  authoritative connector, the agent must treat it as **unknown** and either
  request clarification or choose the most conservative action.
- Telemetry logs (`logs/telemetry/`) are the source of operational truth.
- `ACTIVE_MEMORY.md` is the source of workspace-context truth.

**In practice:**
- Do not assume a workflow succeeded unless its `conclusion == "success"`.
- Do not assume a file exists unless `Test-Path` or `[ -f ]` confirms it.
- Do not assume a PR is mergeable unless the API `mergeable` field is `true`.

---

### A — Authority
> *Respect the permission hierarchy at all times.*

The authority stack (highest to lowest):

```
1. Human Owner / Org Admin
2. GUARDRAILS  (hard limits in .infinity/policies/guardrails.md)
3. TAP Protocol (this document)
4. Governance Framework (.infinity/policies/governance.md)
5. GitHub App Permissions (config/github-app-manifest.json)
6. Workflow Permissions Block (permissions: in each .yml)
7. Individual Agent Logic
```

No layer may override a layer above it.  An agent that encounters a conflict
must escalate upwards (create a blocking GitHub Issue) rather than proceeding.

**In practice:**
- The `GITHUB_TOKEN` permissions block in each workflow is the **floor**, not
  the ceiling.  Never request more permissions than the workflow declares.
- GitHub App tokens are scoped to the installation; never use a JWT to
  perform actions that require only a `GITHUB_TOKEN`.
- Actions that require `organization_administration: write` (e.g., creating
  or deleting a repository) must log the action and create a tracking issue.

---

### P — Policy
> *Policy rules always supersede individual agent preferences.*

Policy documents in `.infinity/policies/` define rules that no agent may
violate.  When a rule and an agent's goal conflict, the rule wins.

**Core policies in effect:**

| Policy | File | Enforced By |
|--------|------|-------------|
| Hard limits / circuit-breakers | `guardrails.md` | `validator_agent.py` + GUARDRAILS check |
| Governance framework | `governance.md` | Code review + TAP gate |
| Authentication rules | `auth-matrix.md` | All scripts / workflows |
| Endpoint governance | `endpoint-registry.md` | `endpoint-registry.json` |

---

## TAP Validation Gate

Every autonomous invention cycle passes through the TAP Validation Gate
(`stacks/agents/validator_agent.py`) before any mutation is committed.

### Checks Performed

| Check | Description | Failure Action |
|-------|-------------|---------------|
| `README.md content` | File exists and has ≥100 chars | Block + issue |
| `SECURITY.md exists` | Security policy present | Block + issue |
| `ARCHITECTURE.md exists` | Architecture docs present | Block + issue |
| `no secrets committed` | No credential patterns in staged files | Block + issue |
| `workflows present` | At least one workflow in `.github/workflows/` | Block + issue |
| `python syntax` | All `.py` files are parseable by `ast.parse` | Block + issue |
| `guardrails respected` | No hard-limit violations detected | Block + hard-stop |

### Gate Outcome

| Result | Action |
|--------|--------|
| `passed: true` | Proceed to documentation and deployment phases |
| `passed: false` | Create blocking GitHub Issue; halt cycle |

---

## Agent Responsibilities Under TAP

Every agent that operates in this system must:

1. **Rehydrate** context from `ACTIVE_MEMORY.md` before taking any action.
2. **Verify** the target repository and branch before making mutations.
3. **Log** every action to `logs/telemetry/` with a structured JSON record.
4. **Mask** all secrets immediately with `::add-mask::` or
   `Invoke-MaskSecret`.
5. **Check** the endpoint registry before calling any external API.
6. **Escalate** by creating a GitHub Issue (label: `triage:agent-escalation`)
   when encountering any ambiguous or conflicting instruction.
7. **Halt** immediately and create a blocking issue if a GUARDRAILS violation
   is detected.

---

## TAP Violation Escalation Path

```
TAP Violation Detected
        │
        ▼
Create GitHub Issue
  - title: "🚨 TAP Violation: {description}"
  - label: "tap-violation", "priority:critical"
  - body: violation details + trace
        │
        ▼
Halt current workflow phase
  (do NOT proceed to next phase)
        │
        ▼
Notify via repository dispatch
  event_type: "tap_violation"
  payload: { violation_type, run_id, details }
        │
        ▼
Human review required to close issue
  + add label "tap-resolved" before next cycle
```

---

## Related Documents

| Document | Location |
|----------|---------|
| Guardrails | `.infinity/policies/guardrails.md` |
| Governance | `.infinity/policies/governance.md` |
| Auth Matrix | `.infinity/connectors/auth-matrix.md` |
| Validator Agent | `stacks/agents/validator_agent.py` |
| Autonomous Engine | `.github/workflows/autonomous-invention.yml` |
| Agent Entrypoint | `AGENT_ENTRYPOINT.md` |
