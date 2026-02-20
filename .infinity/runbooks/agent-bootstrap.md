# Agent Bootstrap Runbook

Describes the Infinity Agent Bootstrap process, how it resolves workspace
context without a hard dependency on a locally present `ACTIVE_MEMORY.md`,
and how downstream agents should consume the bootstrapped context.

---

## Overview

The bootstrap script (`.infinity/scripts/Invoke-InfinityAgentBootstrap.ps1`)
is the **single entry point** for any agent or workflow that needs to consume
the current orchestrator memory state.  It:

1. Checks whether a fresh local `.infinity/ACTIVE_MEMORY.md` is present.
2. Falls back to fetching the file directly from the GitHub Contents API when
   the local copy is absent, empty, or stale (configurable threshold, default
   60 minutes).
3. Exposes the resolved file path via `AGENT_MEMORY_PATH` environment variable
   and the `memory_path` Actions output.

This design means an agent **does not need a prior `actions/checkout` step**
or a freshly synced local copy to start work.

---

## Resolution Order

```
Local .infinity/ACTIVE_MEMORY.md
        │
        ├─► Present and fresh?  ──► Use local copy.
        │
        └─► Missing / empty / stale?
                │
                ├─► GitHub App credentials available?
                │       ├─► Mint installation token
                │       └─► Fetch via GitHub Contents API  ──► Save locally
                │
                ├─► GITHUB_TOKEN available?
                │       └─► Fetch via GitHub Contents API  ──► Save locally
                │
                └─► No credentials?
                        ├─► Stale local copy exists?  ──► Warn and use stale copy
                        └─► Nothing available?         ──► Fatal error
```

---

## Usage

### In a GitHub Actions workflow

```yaml
- name: Bootstrap agent workspace
  id: bootstrap
  shell: pwsh
  env:
    GITHUB_APP_ID:              ${{ secrets.GITHUB_APP_ID }}
    GITHUB_APP_PRIVATE_KEY:     ${{ secrets.GITHUB_APP_PRIVATE_KEY }}
    GITHUB_APP_INSTALLATION_ID: ${{ secrets.GITHUB_APP_INSTALLATION_ID }}
    GITHUB_TOKEN:               ${{ secrets.GITHUB_TOKEN }}
  run: |
    ./.infinity/scripts/Invoke-InfinityAgentBootstrap.ps1

- name: Use resolved memory
  run: |
    echo "Memory path: ${{ steps.bootstrap.outputs.memory_path }}"
    cat "${{ steps.bootstrap.outputs.memory_path }}"
```

### Standalone (local development)

```powershell
# Requires GITHUB_TOKEN or GITHUB_APP_ID + GITHUB_APP_PRIVATE_KEY in the
# environment.  Falls back to the local copy if present and fresh.
./.infinity/scripts/Invoke-InfinityAgentBootstrap.ps1 -MaxAgeMinutes 120
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MaxAgeMinutes` | `60` | Maximum acceptable age (minutes) for the local copy before a re-fetch is triggered. |
| `OrchestratorWorkspace` | `$PWD` | Path to the checked-out repository root. |
| `MemorySourceRef` | `main` | Branch/ref to fetch from when the local copy is stale. |

---

## Outputs

| Name | Description |
|------|-------------|
| `memory_path` (Actions output) | Absolute path to the resolved `ACTIVE_MEMORY.md`. |
| `memory_lines` (Actions output) | Line count of the resolved memory file. |
| `AGENT_MEMORY_PATH` (env var) | Same as `memory_path`; available to all subsequent steps. |

---

## Required Secrets

| Secret | Required | Description |
|--------|----------|-------------|
| `GITHUB_APP_ID` | ⚙️ Preferred | Numeric GitHub App ID. |
| `GITHUB_APP_PRIVATE_KEY` | ⚙️ Preferred | PEM-encoded private key for the App. |
| `GITHUB_APP_INSTALLATION_ID` | ⚙️ Optional | Pre-known installation ID; saves one API call. |
| `GITHUB_TOKEN` | ✅ Fallback | Built-in Actions token; auto-injected. |

When GitHub App credentials are not configured, the script falls back to
`GITHUB_TOKEN` automatically.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `No GitHub credentials available and no local ACTIVE_MEMORY.md found` | No credentials and no local copy | Set `GITHUB_TOKEN` or `GITHUB_APP_ID` + `GITHUB_APP_PRIVATE_KEY`. |
| `No GitHub App installation found for org 'Infinity-X-One-Systems'` | App not installed on the org | Install the GitHub App on `Infinity-X-One-Systems`. |
| `API fetch failed` with a 404 | `ACTIVE_MEMORY.md` does not exist in the repository | Run the memory-sync workflow first. |
| `API fetch failed` with a 401/403 | Insufficient permissions | Ensure the App or token has `contents:read` on `infinity-orchestrator`. |
| Memory file is always stale | `MaxAgeMinutes` set too low, or clock skew | Increase `MaxAgeMinutes` or run the memory-sync workflow. |

---

## Related Files

| File | Purpose |
|------|---------|
| [`../scripts/Invoke-InfinityAgentBootstrap.ps1`](../scripts/Invoke-InfinityAgentBootstrap.ps1) | Bootstrap script |
| [`../connectors/auth-matrix.md`](../connectors/auth-matrix.md) | Auth requirements |
| [`../connectors/endpoint-registry.md`](../connectors/endpoint-registry.md) | Endpoint registry |
| [`memory-sync.md`](memory-sync.md) | Memory sync runbook |
