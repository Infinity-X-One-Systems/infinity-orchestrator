# Admin Panel Integration Runbook

> **Org:** Infinity-X-One-Systems
> **Scope:** `admin.vizual-x.com` and `admin.infinityxai.com` operator dashboards
> **Version:** 1.0.0
> **Connector configs:** `.infinity/connectors/vizual-x-connector.json` · `.infinity/connectors/infinityxai-connector.json`

---

## 1. Purpose

This runbook describes how to connect the **Vizual-X** and **InfinityXAI** admin
dashboards to the Infinity Orchestrator so that operators can trigger workflows,
query system status, and create issues directly from the web admin panels without
needing direct GitHub access.

Both panels share the same integration pattern:

```
Admin Panel (browser)
    │
    │  POST repository_dispatch
    ▼
GitHub API (api.github.com)
    │
    │  event_type: vizual_x_command | infinityxai_command
    ▼
universal-dispatch.yml (GitHub Actions)
    │
    │  Routes to appropriate downstream workflow
    ▼
genesis-loop / autonomous-invention / health-monitor / self-healing / …
```

---

## 2. Prerequisites

| Item | Required |
|------|----------|
| GitHub App (`infinity-orchestrator`) installed on org | ✅ |
| `GITHUB_APP_ID` + `GITHUB_APP_PRIVATE_KEY` secrets configured | ✅ |
| GitHub App installation access token (generated per session) | ✅ |
| Admin panel configured with GitHub API base URL | ✅ |

---

## 3. Generating an Installation Access Token

The admin panels must authenticate every API call with a **short-lived GitHub App
installation access token** (valid for 1 hour).  Never use a Personal Access Token
(TAP P-002).

### Step 1 — Mint a JWT from the App private key

```bash
# Install the jose JWT library first
npm install jose
```

```javascript
// Node.js example (also works in Cloudflare Workers with WebCrypto)
// Requires: npm install jose
import { SignJWT, importPKCS8 } from 'jose';

const appId      = process.env.GITHUB_APP_ID;
const privateKey = process.env.GITHUB_APP_PRIVATE_KEY; // PEM format

const key = await importPKCS8(privateKey, 'RS256');
const jwt = await new SignJWT({})
  .setProtectedHeader({ alg: 'RS256' })
  .setIssuedAt()
  .setIssuer(appId)
  .setExpirationTime('10m')
  .sign(key);
```

### Step 2 — Exchange the JWT for an installation token

```bash
# Get the installation ID first (one-time setup)
curl -s \
  -H "Authorization: Bearer $JWT" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/app/installations" | jq '.[0].id'

# Then mint the token
curl -s -X POST \
  -H "Authorization: Bearer $JWT" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/app/installations/$INSTALLATION_ID/access_tokens" \
  | jq -r '.token'
```

Cache the `token` value and refresh it before it expires (< 1 hour TTL).

---

## 4. Dispatching Commands from the Admin Panel

Use the GitHub `repository_dispatch` API to send commands to the orchestrator.
The `universal-dispatch.yml` workflow listens for these event types.

### admin.vizual-x.com

```http
POST https://api.github.com/repos/Infinity-X-One-Systems/infinity-orchestrator/dispatches
Authorization: Bearer <installation_access_token>
Accept: application/vnd.github+json
Content-Type: application/json

{
  "event_type": "vizual_x_command",
  "client_payload": {
    "command": "trigger_invention",
    "source": "admin.vizual-x.com",
    "actor": "john@example.com",
    "params": {
      "goal": "Build a new customer onboarding flow"
    }
  }
}
```

### admin.infinityxai.com

```http
POST https://api.github.com/repos/Infinity-X-One-Systems/infinity-orchestrator/dispatches
Authorization: Bearer <installation_access_token>
Accept: application/vnd.github+json
Content-Type: application/json

{
  "event_type": "infinityxai_command",
  "client_payload": {
    "command": "health_check",
    "source": "admin.infinityxai.com",
    "actor": "admin"
  }
}
```

A `204 No Content` response confirms the event was accepted.

---

## 5. Supported Commands

| Command | Description | Params |
|---------|-------------|--------|
| `run_workflow` | Run any named workflow | `workflow`: filename (e.g. `genesis-loop.yml`) |
| `health_check` | Trigger the health monitor | — |
| `memory_query` | Surface `ACTIVE_MEMORY.md` in the run summary | — |
| `repo_index` | Surface `ORG_REPO_INDEX.md` in the run summary | — |
| `create_issue` | Create a GitHub issue | `title`, `body`, `labels[]` |
| `trigger_invention` | Run the autonomous invention engine | `goal` (optional) |
| `trigger_genesis` | Run the Genesis Loop | — |
| `trigger_healing` | Trigger self-healing | — |
| `rehydrate` | Refresh `ACTIVE_MEMORY.md` | — |

---

## 6. Reading Status from the Admin Panel

The admin panel can poll these endpoints to display current system status:

### ACTIVE_MEMORY.md

```bash
curl -s \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github.raw+json" \
  "https://api.github.com/repos/Infinity-X-One-Systems/infinity-orchestrator/contents/.infinity/ACTIVE_MEMORY.md"
```

### Latest workflow runs

```bash
curl -s \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/Infinity-X-One-Systems/infinity-orchestrator/actions/runs?per_page=10"
```

### Org repository index

```bash
curl -s \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github.raw+json" \
  "https://api.github.com/repos/Infinity-X-One-Systems/infinity-orchestrator/contents/.infinity/ORG_REPO_INDEX.md"
```

---

## 7. Required Secrets (per admin panel)

Configure these in the admin panel's environment settings.  **Never** store them
in client-side JavaScript or commit them to any repository.

| Secret | Purpose |
|--------|---------|
| `GITHUB_APP_ID` | Identifies the infinity-orchestrator GitHub App |
| `GITHUB_APP_PRIVATE_KEY` | Signs JWTs for installation token minting |
| `GITHUB_APP_INSTALLATION_ID` | (Optional) Caches the installation ID to skip the lookup step |

---

## 8. Governance

All commands dispatched via the admin panels are subject to full **TAP Protocol**
enforcement by the `universal-dispatch.yml` workflow:

- **P-001**: No secrets are logged
- **P-003**: Workflow commits use `github-actions[bot]` attribution
- **P-005**: Installation tokens only — no PATs
- **P-006**: Correlation ID logged before execution

See `.infinity/policies/tap-protocol.md` for the full protocol.

---

## 9. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `404` on dispatch endpoint | Wrong repo path | Verify `Infinity-X-One-Systems/infinity-orchestrator` |
| `401` on dispatch | Expired or invalid token | Re-mint the installation access token |
| `422` on dispatch | Invalid `event_type` | Use `vizual_x_command` or `infinityxai_command` |
| Workflow not triggered | `universal-dispatch.yml` not on `main` | Ensure the workflow file is merged to `main` |
| No webhook callback | Webhook URL not configured | Set `VIZUAL_X_WEBHOOK_URL` or `INFINITYXAI_WEBHOOK_URL` secret |

---

*Infinity Orchestrator · Admin Panel Integration v1.0.0 · Infinity-X-One-Systems*
