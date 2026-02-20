# Authentication Matrix

Maps every governed endpoint to its required authentication method and the
secrets or credentials needed to satisfy it.

---

## Principles

1. **GitHub App first.**  Prefer short-lived installation access tokens over
   any other credential.  GitHub App JWTs expire in 10 minutes; installation
   tokens expire in 1 hour.
2. **`GITHUB_TOKEN` as safe fallback.**  The Actions built-in token is
   acceptable for same-repository operations where write access to a single
   repo is sufficient.
3. **No long-lived PATs in workflows.**  Personal Access Tokens must not be
   stored as repository secrets or used in automated workflows.  If a cross-
   repository PAT is unavoidable, it must be scoped to the minimum permissions
   and rotated at least every 90 days.
4. **Secrets are masked on first use.**  Every script that handles a token
   must call `::add-mask::` (Bash) or `Invoke-MaskSecret` (PowerShell) before
   any operation that may echo the token to stdout/stderr.

---

## Auth Method Definitions

| Method ID | Description | TTL | Secrets Required |
|-----------|-------------|-----|-----------------|
| `github_app_jwt` | RS256-signed JWT minted from the GitHub App private key. Used only to authenticate the App itself (e.g., to list installations or mint an installation token). | 10 min | `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY` |
| `github_app` | Short-lived installation access token minted by presenting a `github_app_jwt` to `/app/installations/{id}/access_tokens`. Preferred for all repo operations. | ≤ 60 min | `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY` (+ optionally `GITHUB_APP_INSTALLATION_ID`) |
| `github_token` | Actions built-in `GITHUB_TOKEN`.  Auto-rotated per job; read/write scope is governed by the workflow's `permissions` block. | Job lifetime | None (automatically injected by Actions) |

---

## Endpoint → Auth Requirements

| Endpoint ID | Primary Method | Fallback Method | Minimum Permissions |
|-------------|---------------|-----------------|---------------------|
| `github-api` | `github_app` | `github_token` | `contents:read` (read); `contents:write` (write) |
| `github-app-auth` | `github_app_jwt` | — | `GITHUB_APP_ID` + `GITHUB_APP_PRIVATE_KEY` |
| `github-actions-api` | `github_app` | `github_token` | `actions:read` + `actions:write` |
| `orchestrator-memory` | `github_app` | `github_token` | `contents:read` on `infinity-orchestrator` |
| `org-repo-index` | `github_token` | `github_app` | `contents:write` on `infinity-orchestrator`; `metadata:read` on org |

---

## GitHub App Configuration

The Infinity Orchestrator GitHub App (`app/infinity-orchestrator`) must be
installed on the `Infinity-X-One-Systems` organisation with at minimum:

| Permission | Level | Rationale |
|-----------|-------|-----------|
| Repository → Contents | Read & Write | Commit and push generated artefacts (e.g., `ORG_REPO_INDEX.json`, `ACTIVE_MEMORY.md`). |
| Repository → Actions | Read & Write | Dispatch workflow runs and read run results. |
| Organization → Members | Read | Used by the org-repo-index workflow to enumerate repositories. |

---

## Required Repository Secrets

Configure the following in
**Settings → Secrets and variables → Actions** for the
`infinity-orchestrator` repository.

| Secret | Required | Description |
|--------|----------|-------------|
| `GITHUB_APP_ID` | ✅ | Numeric ID of the GitHub App. |
| `GITHUB_APP_PRIVATE_KEY` | ✅ | PEM-encoded RSA private key for the App. |
| `GITHUB_APP_INSTALLATION_ID` | ⚙️ Optional | Pre-known installation ID; skips discovery API call. |

> `GITHUB_TOKEN` is injected automatically by GitHub Actions and does not
> need to be set as a secret.

---

## Related Files

| File | Purpose |
|------|---------|
| [`endpoint-registry.json`](endpoint-registry.json) | Machine-readable endpoint registry |
| [`endpoint-registry.md`](endpoint-registry.md) | Registry documentation |
| [`../runbooks/agent-bootstrap.md`](../runbooks/agent-bootstrap.md) | Agent bootstrap runbook |
| [`../scripts/Invoke-InfinityAgentBootstrap.ps1`](../scripts/Invoke-InfinityAgentBootstrap.ps1) | Bootstrap script |
| [`../scripts/Sync-MemoryToOrchestrator.ps1`](../scripts/Sync-MemoryToOrchestrator.ps1) | Memory sync script |
