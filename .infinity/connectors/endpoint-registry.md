# Endpoint Registry

Defines and governs all external and internal API endpoints used by the
Infinity Orchestrator and the agents it manages.

---

## Overview

The endpoint registry (`endpoint-registry.json`) is the single source of
truth for every API surface the Infinity system touches.  All new integrations
**must** be registered here before use.  Unregistered endpoints are considered
ungoverned and may not be called from workflows or agent scripts without a
governance review.

---

## Registry Format

Each entry in `endpoint-registry.json` follows this schema:

| Field | Required | Description |
|-------|----------|-------------|
| `id` | ✅ | Machine-readable unique identifier (kebab-case). |
| `name` | ✅ | Human-readable display name. |
| `description` | ✅ | Purpose and usage context. |
| `base_url` | ✅ | Base URL for the endpoint (no trailing slash). |
| `auth_method` | ✅ | Primary authentication method (see [Auth Matrix](auth-matrix.md)). |
| `auth_fallback` | ⚙️ | Fallback method when primary is unavailable. |
| `governed` | ✅ | Must be `true` for all production endpoints. |
| `tags` | ✅ | Categorisation tags for discovery and filtering. |
| `health_check` | ⚙️ | Optional liveness probe configuration. |
| `rate_limit` | ⚙️ | Known rate-limit parameters for throttle management. |

---

## Registered Endpoints

| ID | Name | Auth Method | Governed |
|----|------|-------------|----------|
| `github-api` | GitHub REST API | `github_app` / `github_token` | ✅ |
| `github-app-auth` | GitHub App Authentication | `github_app_jwt` | ✅ |
| `github-actions-api` | GitHub Actions API | `github_app` / `github_token` | ✅ |
| `orchestrator-memory` | Orchestrator Memory (`ACTIVE_MEMORY.md`) | `github_app` / `github_token` | ✅ |
| `org-repo-index` | Organization Repository Index | `github_token` | ✅ |

---

## Adding a New Endpoint

1. Open a PR that adds a new JSON object to the `endpoints` array in
   `endpoint-registry.json`.
2. Set `governed: true`.
3. Document the required `auth_method` in [auth-matrix.md](auth-matrix.md).
4. Update this file's **Registered Endpoints** table.
5. Get approval from a codeowner before merging.

---

## Governance Policy

* **No long-lived PATs.**  All machine-to-machine calls must use GitHub App
  installation tokens (TTL ≤ 10 minutes) or the Actions built-in
  `GITHUB_TOKEN`.
* **Tokens are never stored in environment variables beyond the step that
  mints them.**  They are masked with `::add-mask::` immediately after
  creation.
* **Tokens are never passed as command-line arguments.**  They are written
  to the local git credential helper (`http.extraheader`) scoped to a single
  `try/finally` block and removed immediately afterwards.
* **Rate limits are respected.**  Scripts should honour GitHub API rate limits
  and implement exponential back-off where appropriate.

---

## Related Files

| File | Purpose |
|------|---------|
| [`endpoint-registry.json`](endpoint-registry.json) | Machine-readable registry |
| [`auth-matrix.md`](auth-matrix.md) | Auth method requirements per endpoint |
| [`../runbooks/endpoint-registry.md`](../runbooks/endpoint-registry.md) | Operational runbook |
| [`../runbooks/agent-bootstrap.md`](../runbooks/agent-bootstrap.md) | Agent bootstrap runbook |
