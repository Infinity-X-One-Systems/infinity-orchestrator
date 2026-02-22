# CORE_SYSTEM.md — Infinity Orchestrator Consolidation Guide

> **Repository:** `Infinity-X-One-Systems/infinity-orchestrator`
> **Version:** 1.0.0 · Updated: 2026-02-22
>
> This document is the **single source of truth** for operating the Infinity
> Orchestrator from any surface.  Read this before reading any other
> document in the repository.

---

## 1. What This System Is

The Infinity Orchestrator is a **sovereign autonomous control plane** built
entirely on GitHub's platform.  It requires no dedicated server, no cloud VMs,
and no external CI provider.  Every capability runs as a GitHub Actions workflow,
backed by a GitHub App with maximum permissions across the
`Infinity-X-One-Systems` organisation.

### Core Capabilities

| Capability | Engine | Trigger Interval |
|-----------|--------|-----------------|
| Autonomous code invention | `autonomous-invention.yml` | Every 3 hours |
| Software factory (Genesis Loop) | `genesis-loop.yml` | Every 6 hours |
| DevOps auto-healing | `genesis-devops-team.yml` | Every 2 hours |
| Auto-merge verified PRs | `genesis-auto-merge.yml` | Every hour |
| Health monitoring | `health-monitor.yml` | Every 15 minutes |
| Self-healing | `self-healing.yml` | On demand / triggered |
| Memory rehydration | `rehydrate.yml` | Every 6 hours |
| Org repo discovery | `org-repo-index.yml` | Every 6 hours |
| Security scanning | `security-scan.yml` | Daily |
| Cross-repo builds | `multi-repo-build.yml` | Daily |

---

## 2. Operator Surfaces

The orchestrator can be controlled from **four operator surfaces**.  All surfaces
funnel through the same `universal-dispatch.yml` workflow, which enforces the
TAP Protocol before routing to downstream engines.

```
┌─────────────────────────────────────────────────────────────────────┐
│              OPERATOR SURFACES                                       │
│                                                                     │
│  ChatGPT Custom GPT    Copilot Mobile    admin.vizual-x.com         │
│       │                    │                   │                    │
│       │                    │                   │   admin.infinityxai.com
│       │                    │                   │        │           │
│       ▼                    ▼                   ▼        ▼           │
│  repository_dispatch  repository_dispatch  repository_dispatch      │
│  (orchestrator_command) (copilot_command)  (vizual_x_command /      │
│                                            infinityxai_command)     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │  universal-dispatch.yml        │
              │  (TAP audit + command router)  │
              └───────────────┬────────────────┘
                              │
         ┌────────────────────┼───────────────────┐
         ▼                    ▼                   ▼
  genesis-loop.yml  autonomous-invention.yml  health-monitor.yml
  self-healing.yml  rehydrate.yml             … (any workflow)
```

### 2.1 ChatGPT Custom GPT

**How it works:** Install the OpenAPI Actions spec from
`.infinity/connectors/chatgpt-actions-spec.yaml` in a Custom GPT.  ChatGPT
calls the GitHub `repository_dispatch` API with `event_type: orchestrator_command`.

**Setup steps:**
1. In ChatGPT, go to **Explore GPTs → Create → Configure → Actions**.
2. Click **Import from URL** or paste the spec from
   `.infinity/connectors/chatgpt-actions-spec.yaml`.
3. Under **Authentication**, choose **API Key**, set to **Bearer** and paste
   your GitHub App installation access token (or a scoped PAT for testing only).
4. Save the GPT and test with: `"Trigger a health check on the orchestrator."`

**Example prompts:**

| Prompt | Action |
|--------|--------|
| `"Trigger the Genesis Loop"` | Dispatches `trigger_genesis` command |
| `"What is the current system state?"` | Calls `getActiveMemory` |
| `"Invent a new authentication system"` | Dispatches `trigger_invention` with goal |
| `"List all org repositories"` | Calls `getOrgRepoIndex` |
| `"Check the last 5 workflow runs"` | Calls `listWorkflowRuns` |
| `"Create an issue: Fix the health check timeout"` | Dispatches `create_issue` |

**Reference:** `.infinity/connectors/chatgpt-actions-spec.yaml`

---

### 2.2 GitHub Copilot Mobile (iOS / Android)

**How it works:** The `@infinity-orchestrator` Copilot Extension receives messages
from any Copilot Chat surface (GitHub Mobile app, GitHub.com, VS Code).  Messages
are signed with ECDSA P-256 and forwarded to the extension webhook, which triggers
the `universal-dispatch.yml` workflow.

**How to use:**
1. Open the **GitHub Mobile** app → tap **Copilot** (chat icon).
2. Type `@infinity-orchestrator <intent>`.
3. The extension routes the intent to the appropriate workflow.

**Supported intents:**

| Intent | Example |
|--------|---------|
| `run <workflow>` | `@infinity-orchestrator run genesis-loop` |
| `health` | `@infinity-orchestrator health` |
| `memory` | `@infinity-orchestrator memory` |
| `repos` | `@infinity-orchestrator repos` |
| `issue <title>` | `@infinity-orchestrator issue Fix login bug` |
| `invent <topic>` | `@infinity-orchestrator invent new auth system` |

**Reference:** `.infinity/runbooks/copilot-mobile.md` · `.infinity/connectors/copilot-connector.json`

---

### 2.3 admin.vizual-x.com

**How it works:** The Vizual-X admin dashboard calls the GitHub
`repository_dispatch` API with `event_type: vizual_x_command`.  The
`universal-dispatch.yml` workflow receives the event, logs a TAP audit entry,
and routes to the appropriate engine.

**Integration pattern:**
```http
POST https://api.github.com/repos/Infinity-X-One-Systems/infinity-orchestrator/dispatches
Authorization: Bearer <github_app_installation_token>

{
  "event_type": "vizual_x_command",
  "client_payload": {
    "command": "trigger_invention",
    "source": "admin.vizual-x.com",
    "actor": "operator@vizual-x.com",
    "params": { "goal": "Build a real-time dashboard widget" }
  }
}
```

**Reference:** `.infinity/connectors/vizual-x-connector.json` · `.infinity/runbooks/admin-panels.md`

---

### 2.4 admin.infinityxai.com

**How it works:** Identical to Vizual-X, but uses `event_type: infinityxai_command`.

**Integration pattern:**
```http
POST https://api.github.com/repos/Infinity-X-One-Systems/infinity-orchestrator/dispatches
Authorization: Bearer <github_app_installation_token>

{
  "event_type": "infinityxai_command",
  "client_payload": {
    "command": "health_check",
    "source": "admin.infinityxai.com",
    "actor": "admin"
  }
}
```

**Reference:** `.infinity/connectors/infinityxai-connector.json` · `.infinity/runbooks/admin-panels.md`

---

## 3. Technology Stack

Every component listed here is active and governed by the TAP Protocol.

### AI / LLM Services

| Service | Purpose | Connector |
|---------|---------|-----------|
| OpenAI / ChatGPT | Code gen, scoring, documentation | `openai-connector.json` |
| GitHub Copilot | Chat completions, mobile operator surface | `copilot-connector.json` |
| Groq | Ultra-low-latency cloud LLM (Llama 3.3 70B) | `groq-connector.json` |
| Google Gemini | Multimodal reasoning, long-context | `gemini-connector.json` |
| Ollama | Local LLM (offline, zero cost) | `ollama-connector.json` |
| Open WebUI | Unified local LLM gateway (browser UI + API) | `openwebui-connector.json` |

### Infrastructure

| Service | Purpose | Connector |
|---------|---------|-----------|
| GitHub Actions | All workflow automation | `endpoint-registry.json` |
| GitHub App | Cross-org auth, App token minting | `config/github-app-manifest.json` |
| Cloudflare | DNS, Workers, Pages, Zero Trust tunnels | `cloudflare-connector.json` |
| VS Code / Codespaces | Remote dev, interactive runners | `vscode-connector.json` |
| Docker | Container runtime for agent stacks | `docker-compose.singularity.yml` |

### Operator Panels

| Panel | Connector |
|-------|-----------|
| admin.vizual-x.com | `vizual-x-connector.json` |
| admin.infinityxai.com | `infinityxai-connector.json` |

---

## 4. The Universal Dispatch Workflow

`.github/workflows/universal-dispatch.yml` is the **single inbound entry point**
for all external surfaces.  It:

1. Accepts `workflow_dispatch` (manual / CI) and `repository_dispatch` (API)
2. Normalises the command regardless of source surface
3. Logs a TAP P-006 compliant audit entry before acting
4. Routes to the appropriate downstream workflow

### Command Reference

| Command | Downstream Workflow | Description |
|---------|--------------------|----|
| `run_workflow` | (named) | Run any workflow by filename |
| `health_check` | `health-monitor.yml` | Run health checks |
| `trigger_invention` | `autonomous-invention.yml` | Autonomous invention cycle |
| `trigger_genesis` | `genesis-loop.yml` | Genesis software factory loop |
| `trigger_healing` | `self-healing.yml` | Self-healing cycle |
| `rehydrate` | `rehydrate.yml` | Refresh ACTIVE_MEMORY.md |
| `memory_query` | (inline) | Surfaces ACTIVE_MEMORY.md in run summary |
| `repo_index` | (inline) | Surfaces ORG_REPO_INDEX.md in run summary |
| `create_issue` | (inline, GitHub API) | Create a GitHub issue |

---

## 5. Memory & State

The orchestrator maintains a live state snapshot in `.infinity/ACTIVE_MEMORY.md`.
This file is the single source of truth for all agents.

| File | Purpose | Refresh |
|------|---------|---------|
| `.infinity/ACTIVE_MEMORY.md` | Live system state | Every 6 hours |
| `.infinity/ORG_REPO_INDEX.json` | All org repositories | Every 6 hours |
| `config/repositories.json` | Active repo manifest | Every 6 hours |

Any operator surface can read the current state via:

```bash
curl -s \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github.raw+json" \
  "https://api.github.com/repos/Infinity-X-One-Systems/infinity-orchestrator/contents/.infinity/ACTIVE_MEMORY.md"
```

---

## 6. Governance (TAP Protocol)

All autonomous actions are governed by the TAP Protocol (`P > A > T`).
See `.infinity/policies/tap-protocol.md` for the full specification.

### Quick Reference — Immutable Guardrails

| Rule | Summary |
|------|---------|
| P-001 | No secrets in logs, commits, or PR bodies |
| P-002 | No Personal Access Tokens — GitHub App tokens only |
| P-003 | Bot commits attributed to `github-actions[bot]` |
| P-004 | No force-push to protected branches without human approval |
| P-005 | Cross-repo ops use App installation tokens only |
| P-006 | Log correlation ID before every endpoint call |
| P-007 | Degrade gracefully if `ACTIVE_MEMORY.md` is absent |
| P-008 | Docker socket mounts read-only by default |

---

## 7. Required Secrets

Configure these under **Settings → Secrets and variables → Actions**:

| Secret | Required For | Priority |
|--------|-------------|---------|
| `GITHUB_APP_ID` | All surfaces | ✅ Critical |
| `GITHUB_APP_PRIVATE_KEY` | All surfaces | ✅ Critical |
| `OPENAI_API_KEY` | AI features | ✅ For LLM |
| `CLOUDFLARE_API_TOKEN` | Cloudflare ops | ✅ For CF |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare ops | ✅ For CF |
| `GROQ_API_KEY` | Groq LLM | ⚙️ Optional |
| `GEMINI_API_KEY` | Google Gemini | ⚙️ Optional |
| `VSCODE_TUNNEL_TOKEN` | VS Code tunnel | ⚙️ Optional |
| `VIZUAL_X_WEBHOOK_URL` | Vizual-X callbacks | ⚙️ Optional |
| `VIZUAL_X_WEBHOOK_SECRET` | Vizual-X callbacks | ⚙️ Optional |
| `INFINITYXAI_WEBHOOK_URL` | InfinityXAI callbacks | ⚙️ Optional |
| `INFINITYXAI_WEBHOOK_SECRET` | InfinityXAI callbacks | ⚙️ Optional |

---

## 8. Quick Start for Each Surface

### ChatGPT
```
1. Open chatgpt.com → Explore GPTs → Create → Configure → Actions
2. Import spec: .infinity/connectors/chatgpt-actions-spec.yaml
3. Set auth: Bearer <GitHub App installation token>
4. Prompt: "Trigger a health check on the Infinity Orchestrator"
```

### Copilot Mobile
```
1. Install GitHub Mobile app
2. Tap Copilot tab
3. Type: @infinity-orchestrator health
```

### admin.vizual-x.com
```
1. Configure panel with GITHUB_APP_ID + GITHUB_APP_PRIVATE_KEY
2. Mint installation token (see .infinity/runbooks/admin-panels.md)
3. POST to /repos/Infinity-X-One-Systems/infinity-orchestrator/dispatches
   with event_type: vizual_x_command
```

### admin.infinityxai.com
```
1. Configure panel with GITHUB_APP_ID + GITHUB_APP_PRIVATE_KEY
2. Mint installation token (see .infinity/runbooks/admin-panels.md)
3. POST to /repos/Infinity-X-One-Systems/infinity-orchestrator/dispatches
   with event_type: infinityxai_command
```

---

## 9. File Map

```
Key files for the consolidated system:

.github/workflows/
  universal-dispatch.yml       ← SINGLE ENTRY POINT for all surfaces

.infinity/connectors/
  endpoint-registry.json       ← Canonical endpoint registry
  connectors-index.md          ← Connector overview
  chatgpt-actions-spec.yaml    ← ChatGPT Custom GPT Actions spec
  openai-connector.json        ← OpenAI / ChatGPT
  copilot-connector.json       ← GitHub Copilot Mobile
  vizual-x-connector.json      ← admin.vizual-x.com
  infinityxai-connector.json   ← admin.infinityxai.com
  cloudflare-connector.json    ← Cloudflare
  groq-connector.json          ← Groq LLM
  gemini-connector.json        ← Google Gemini
  ollama-connector.json        ← Ollama (local LLM)
  openwebui-connector.json     ← Open WebUI gateway

.infinity/runbooks/
  copilot-mobile.md            ← Copilot Mobile + Extension setup
  admin-panels.md              ← admin.vizual-x.com + admin.infinityxai.com
  agent-bootstrap.md           ← Agent bootstrap procedure
  memory-sync.md               ← Memory sync operations

.infinity/policies/
  tap-protocol.md              ← TAP governance (P > A > T)
  governance.md                ← Org-wide governance rules
  guardrails.md                ← Hard limits and circuit-breakers

config/
  orchestrator.yml             ← Master orchestrator configuration
  github-app-manifest.json     ← GitHub App permissions manifest

AGENT_ENTRYPOINT.md            ← First-read for all agents
CORE_SYSTEM.md                 ← THIS FILE — consolidated operator guide
```

---

*Infinity Orchestrator · Core System Guide v1.0.0 · Infinity-X-One-Systems*
