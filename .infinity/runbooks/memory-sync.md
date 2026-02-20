# Memory Sync Runbook

Describes how the automated memory sync mechanism works, what secrets are
required, and how agents should consume memory from this repository.

---

## Overview

The **memory sync** pipeline pulls canonical AI-agent memory files from
[`Infinity-X-One-Systems/infinity-core-memory`][memory-repo] (the single
source of truth) and commits them into this repository
(`Infinity-X-One-Systems/infinity-orchestrator`) under the `.infinity/`
directory tree.

This makes memory artifacts available to every agent and workflow that
operates on the orchestrator repository without needing cross-repository
credentials at runtime.

---

## Required Secrets

Configure the following in
**infinity-orchestrator → Settings → Secrets and variables → Actions**.

| Secret name                   | Required | Description |
|-------------------------------|----------|-------------|
| `GITHUB_APP_ID`               | ✅ Yes    | Numeric ID of the GitHub App used for authentication. Find it at `https://github.com/organizations/Infinity-X-One-Systems/settings/apps/<app-name>`. |
| `GITHUB_APP_PRIVATE_KEY`      | ✅ Yes    | PEM-encoded RSA private key generated for the GitHub App. Paste the full contents of the `.pem` file including the `-----BEGIN RSA PRIVATE KEY-----` header/footer. Literal newlines and `\n`-escaped sequences are both accepted. |
| `GITHUB_APP_INSTALLATION_ID`  | ⚙️ Optional | Pre-known installation ID for the `Infinity-X-One-Systems` org. When omitted, the script discovers it automatically via the GitHub API. Providing it saves one API call and removes the need for the `app` read scope. |

> **GitHub App minimum permissions**
>
> The App must be installed on the `Infinity-X-One-Systems` organisation and
> needs:
>
> * **Repository: Contents** → `Read & Write` on `infinity-orchestrator`
> * **Repository: Contents** → `Read` on `infinity-core-memory`

---

## How the Workflow Works

### File: `.github/workflows/memory-sync.yml`

```
Trigger (schedule / workflow_dispatch / repository_dispatch)
    │
    ▼
actions/checkout  ── clones infinity-orchestrator
    │
    ▼
.infinity/scripts/Sync-MemoryToOrchestrator.ps1
    │
    ├── 1. Validate env vars (GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY)
    ├── 2. Generate short-lived GitHub App JWT (RS256, 10 min TTL)
    ├── 3. Discover installation ID (or use GITHUB_APP_INSTALLATION_ID)
    ├── 4. Mint installation access token  ← masked immediately
    ├── 5. git clone --depth 1 infinity-core-memory (HTTPS + x-access-token)
    ├── 6. Copy artifacts:
    │       .infinity/ACTIVE_MEMORY.md      (mandatory)
    │       .infinity/AGENT_ENTRYPOINT.md   (if present)
    │       .infinity/policies/**           (if present)
    │       .infinity/runbooks/**           (if present)
    │       .infinity/schema/**             (if present)
    ├── 7. Validate ACTIVE_MEMORY.md is present and non-empty → fail if not
    ├── 8. git add / git status  → skip if no changes (idempotent)
    └── 9. git commit + git push  (using http.extraheader, token unset in finally)
```

### Triggers

| Trigger | When |
|---------|------|
| `schedule` (hourly) | Ensures memory is at most 60 minutes stale even if the cross-repo dispatch is not configured. |
| `workflow_dispatch` | Manual run from the Actions UI; optionally accepts a `memory_ref` input to sync from a specific branch or tag. |
| `repository_dispatch` (event: `memory-updated`) | Fired by a companion workflow in `infinity-core-memory` immediately after each push to `main`. See the comment block in `memory-sync.yml` for the companion workflow snippet. |

### Idempotency

The script stages `.infinity/` with `git add`, then runs `git status --porcelain`.
If the output is empty (no changes), no commit is created. Re-running the
workflow is therefore safe and produces no noise in the git history.

### Token Security

* The App private key is read from an environment variable and never written
  to disk.
* The JWT and installation access token are masked with `::add-mask::` before
  being used — GitHub Actions redacts them from all subsequent log lines.
* The access token is stored in `.git/config` only for the duration of the
  `git push` call (via `http.https://github.com/.extraheader`) and is unset in
  a `finally` block.
* The temporary `git clone` directory is deleted in a `finally` block
  regardless of whether the script succeeds or fails.

---

## Setting Up the Cross-Repo Push Trigger (Optional)

To get near-real-time sync (instead of relying on the hourly schedule), add
the following workflow to
`infinity-core-memory/.github/workflows/notify-orchestrator.yml`:

```yaml
name: Notify Orchestrator on Memory Update

on:
  push:
    branches: [main]
    paths: ['.infinity/**']

jobs:
  dispatch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/github-script@v7
        with:
          # Personal Access Token with `repo` scope on infinity-orchestrator,
          # stored as a secret in the infinity-core-memory repository.
          github-token: ${{ secrets.ORCHESTRATOR_DISPATCH_PAT }}
          script: |
            await github.rest.repos.createDispatchEvent({
              owner: 'Infinity-X-One-Systems',
              repo:  'infinity-orchestrator',
              event_type: 'memory-updated',
            });
```

> The `ORCHESTRATOR_DISPATCH_PAT` secret must be added to
> **infinity-core-memory → Settings → Secrets and variables → Actions**.
> A fine-grained PAT scoped to `infinity-orchestrator` with
> **Actions: Read & Write** permission is sufficient.

---

## How Agents Should Read Memory

After each successful sync, the memory files live at well-known paths inside
this repository on the `main` branch.

### Primary entry point

```
Infinity-X-One-Systems/infinity-orchestrator
└── .infinity/
    ├── ACTIVE_MEMORY.md      ← Start here — current state, context, and task list
    ├── AGENT_ENTRYPOINT.md   ← Agent bootstrap instructions (if present)
    ├── policies/             ← Governance policies
    ├── runbooks/             ← Operational runbooks (including this file)
    └── schema/               ← Data schemas
```

### Reading ACTIVE_MEMORY.md in a workflow

```yaml
- name: Read active memory
  id: memory
  run: |
    if [ ! -f .infinity/ACTIVE_MEMORY.md ]; then
      echo "::error::ACTIVE_MEMORY.md not found. Run the memory-sync workflow first."
      exit 1
    fi
    echo "Memory file present ($(wc -l < .infinity/ACTIVE_MEMORY.md) lines)"
```

### Reading ACTIVE_MEMORY.md in a script (PowerShell)

```powershell
$memoryPath = Join-Path $PSScriptRoot '../../ACTIVE_MEMORY.md'
if (-not (Test-Path $memoryPath)) {
    throw 'ACTIVE_MEMORY.md not found. Trigger the memory-sync workflow.'
}
$memory = Get-Content -Raw $memoryPath
```

### Reading via the GitHub API (external agent / zero-clone)

```bash
curl -s \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github.raw+json" \
  "https://api.github.com/repos/Infinity-X-One-Systems/infinity-orchestrator/contents/.infinity/ACTIVE_MEMORY.md"
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `GITHUB_APP_ID environment variable is required` | Secret not set or misspelled | Add `GITHUB_APP_ID` secret to the repository |
| `No installation found for organisation 'Infinity-X-One-Systems'` | App not installed on the org | Install the GitHub App on the `Infinity-X-One-Systems` org |
| `git clone failed with exit code 128` | Access token does not have read access to `infinity-core-memory` | Grant the App **Contents: Read** on `infinity-core-memory` |
| `ACTIVE_MEMORY.md not found in the source repository` | `.infinity/ACTIVE_MEMORY.md` has not been created in the memory repo | Create the file in `infinity-core-memory` |
| `ACTIVE_MEMORY.md is empty after sync` | The file exists but contains only whitespace | Add content to `.infinity/ACTIVE_MEMORY.md` in the memory repo |
| Workflow succeeds but file not updated | No changes were detected (idempotent) | Update the source file in `infinity-core-memory` |

---

[memory-repo]: https://github.com/Infinity-X-One-Systems/infinity-core-memory
