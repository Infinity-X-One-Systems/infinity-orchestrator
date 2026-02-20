# TAP Protocol — Governance Policy

> **Org:** Infinity-X-One-Systems  
> **Scope:** All autonomous operations performed by agents, workflows, and scripts  
> operating within the `infinity-orchestrator` system boundary.  
> **Version:** 1.0.0  
> **Enforcement:** Mandatory for all automated actors. See [`../runbooks/governance-enforcement.md`](../runbooks/governance-enforcement.md).

---

## 1. The TAP Triad

The **TAP Protocol** defines a three-layer governance hierarchy for all autonomous decisions:

```
┌─────────────────────────────────────────────────────────────┐
│  T — TRUTH       (What is the verified state of the world?) │
│  A — AUTHORITY   (Who or what is authorised to act?)        │
│  P — POLICY      (What rules constrain the action?)         │
│                                                             │
│  Precedence:  P > A > T                                     │
│  (Policy overrides Authority; Authority overrides Truth.)   │
└─────────────────────────────────────────────────────────────┘
```

**Policy** always takes precedence. No matter what an agent believes to be true (T) or
who granted it a token (A), the configured policies (P) define the hard outer boundary.

---

## 2. Policy Layer (P)

### 2.1 Immutable Guardrails

The following rules **cannot** be overridden by any authority level, including org owners:

| Rule ID | Description |
|---------|-------------|
| `P-001` | No secrets, tokens, or credentials may appear in log output, commit messages, PR bodies, issue comments, or any repository artifact. |
| `P-002` | No long-lived Personal Access Tokens (PATs) may be stored as GitHub Actions secrets. GitHub App tokens must be used instead. |
| `P-003` | Autonomous commits must be attributed to `github-actions[bot]` with the canonical email `41898282+github-actions[bot]@users.noreply.github.com`. |
| `P-004` | No workflow or script may force-push to a protected branch without an explicit human approval step. |
| `P-005` | All cross-repository operations (clone, push, dispatch) must use installation access tokens minted from a registered GitHub App, not user tokens. |
| `P-006` | Endpoint calls must include `X-Infinity-Correlation-ID` and must be logged to the audit trail before execution. |
| `P-007` | Agent bootstrap must not fail catastrophically if `.infinity/ACTIVE_MEMORY.md` is absent; degrade gracefully and attempt GitHub-first memory retrieval. |
| `P-008` | Docker socket access must be read-only unless a write-capable mount is explicitly justified and documented in the PR description. |

### 2.2 Configurable Policies

These policies apply by default but may be overridden with documented justification:

| Rule ID | Default | Override Requires |
|---------|---------|-----------------|
| `P-101` | Workflow schedule maximum frequency: every 15 minutes | Architecture review + TAP decision log entry |
| `P-102` | Memory sync from `infinity-core-memory` runs at most once per hour on schedule | Change to `memory-sync.yml` + TAP decision log entry |
| `P-103` | Org repo index refresh: every 6 hours | Change to `org-repo-index.yml` + TAP decision log entry |
| `P-104` | Secrets rotation reminder: 90 days | Security review |

---

## 3. Authority Layer (A)

### 3.1 Actor Registry

| Actor ID | Type | Permissions | Trust Level |
|----------|------|-------------|-------------|
| `github-actions[bot]` | Automated | Contents write (orchestrator), Contents read (memory repo) | High — scoped to token |
| `infinity-orchestrator-app` | GitHub App | Contents R/W on orchestrator, Contents R on memory repo | High — cryptographically authenticated |
| `org-member` | Human | PR review, manual workflow dispatch | High — requires 2FA |
| `external-collaborator` | Human | PR contribution only | Medium — requires review |
| `anonymous` | Any | Read public content only | Low |

### 3.2 Delegation Rules

- An automated actor may only act within the permissions of its installation access token.
- Tokens must not be stored beyond the workflow run that created them.
- Delegation chains longer than 2 hops require explicit policy review.

---

## 4. Truth Layer (T)

### 4.1 Sources of Truth

| Artifact | Source of Truth | Update Frequency |
|----------|----------------|-----------------|
| Memory state | `infinity-core-memory/.infinity/ACTIVE_MEMORY.md` | On push to `main` + hourly sync |
| Org repo index | `.infinity/ORG_REPO_INDEX.json` | Every 6 hours via `org-repo-index.yml` |
| Endpoint registry | `.infinity/connectors/endpoint-registry.json` | On PR merge (manual) |
| Auth matrix | `.infinity/connectors/auth-matrix.md` | On PR merge (manual) |
| Repository manifest | `config/repositories.json` | Every 6 hours via `repo-sync.yml` |

### 4.2 Stale-State Handling

- If `ACTIVE_MEMORY.md` is older than 2 hours, agents **should** trigger a memory sync before acting.
- If `ORG_REPO_INDEX.json` is older than 24 hours, agents **should** log a warning before using index data.
- Stale state does not authorise skipping policy checks (P > A > T).

---

## 5. Autonomous Operation Guardrails

### 5.1 Pre-Action Checklist

Before any autonomous action, an agent must verify:

- [ ] Action is within the actor's granted permissions (A check)
- [ ] No applicable policy (P-001 through P-008) is violated
- [ ] Correlation ID is generated and attached to the request
- [ ] Token masking is applied to all secrets used in the action
- [ ] Decision is logged (see Section 6)

### 5.2 Prohibited Actions (absolute)

The following are **always prohibited**, regardless of context:

- Writing credentials to any file that will be committed to a repository
- Granting `admin` repository permissions to any automated actor via workflow
- Disabling branch protection rules via automated workflow
- Sending telemetry or data to endpoints outside the registered endpoint registry without explicit policy approval
- Storing user PII in `.infinity/` artifacts

---

## 6. Decision Logging

Every policy-relevant decision made by an autonomous actor **must** be logged.

### 6.1 Log Format

```json
{
  "timestamp": "ISO-8601",
  "actor": "actor-id",
  "action": "short description",
  "policy_rules_checked": ["P-001", "P-005"],
  "decision": "allowed | denied | degraded",
  "correlation_id": "uuid",
  "justification": "free-text"
}
```

### 6.2 Log Destinations

- GitHub Actions step summary (`$GITHUB_STEP_SUMMARY`)
- Workflow run annotations (`::notice::` / `::warning::` / `::error::`)
- Repository audit log (via GitHub App event log where available)

See `.infinity/runbooks/governance-enforcement.md` for enforcement procedures and escalation paths.

---

## 7. Compliance & Review

- This policy is reviewed on every major version bump of the orchestrator.
- Proposed changes require a PR targeting `main` with at least one human reviewer.
- Emergency overrides must be documented in the TAP decision log within 24 hours.

---

*Infinity Orchestrator · TAP Protocol v1.0.0 · Infinity-X-One-Systems*
