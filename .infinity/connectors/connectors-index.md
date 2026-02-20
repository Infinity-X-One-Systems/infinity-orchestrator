# Connectors Index

Master index of all external service connectors managed by the Infinity
Orchestrator.  Each connector provides authenticated, governed access to an
external system.

---

## Overview

| Connector | ID | Config File | Auth Method | Status |
|-----------|-----|------------|-------------|--------|
| GitHub REST API | `github-api` | `endpoint-registry.json` | GitHub App | ✅ Active |
| GitHub App Auth | `github-app-auth` | `endpoint-registry.json` | JWT + Installation Token | ✅ Active |
| GitHub Actions API | `github-actions-api` | `endpoint-registry.json` | GitHub App | ✅ Active |
| Orchestrator Memory | `orchestrator-memory` | `endpoint-registry.json` | GitHub App | ✅ Active |
| Org Repo Index | `org-repo-index` | `endpoint-registry.json` | GITHUB_TOKEN | ✅ Active |
| **OpenAI / ChatGPT** | `openai` | `openai-connector.json` | Bearer Token | ✅ Active |
| **GitHub Copilot** | `github-copilot` | `copilot-connector.json` | GitHub App | ✅ Active |
| **Cloudflare** | `cloudflare` | `cloudflare-connector.json` | Bearer Token | ✅ Active |
| **VS Code / Codespaces** | `vscode-codespaces` | `vscode-connector.json` | GitHub App | ✅ Active |

All connectors are registered in `endpoint-registry.json` and governed by
`auth-matrix.md`.

---

## Connector Details

### GitHub API (core)
- **Purpose**: All primary GitHub operations — repo management, workflows,
  issues, PRs, org management.
- **Auth**: GitHub App installation token (preferred) or `GITHUB_TOKEN`.
- **Docs**: `endpoint-registry.md`

### OpenAI / ChatGPT
- **Purpose**: LLM inference for autonomous agents — idea generation, code
  synthesis, scoring, documentation, and embeddings.
- **Auth**: `OPENAI_API_KEY` (secret).
- **Rate limit**: 500 req/min, 800K tokens/min.
- **Guardrails**: Max 100K tokens/run; max $5 cost/run.
- **Docs**: `openai-connector.json`

### GitHub Copilot
- **Purpose**: Copilot Chat completions; `@infinity-orchestrator` Copilot
  Extension for GitHub.com and Copilot Mobile.
- **Auth**: GitHub App token.
- **Mobile access**: Trigger orchestrator workflows from Copilot Chat on iOS/Android via `@infinity-orchestrator`.
- **Docs**: `copilot-connector.json`, `.infinity/runbooks/copilot-mobile.md`

#### Mobile-Specific Endpoints

| Endpoint ID | Surface | `Copilot-Integration-Id` header |
|-------------|---------|--------------------------------|
| `copilot-chat` | VS Code | `vscode-chat` |
| `copilot-mobile-chat` | GitHub Mobile app (iOS/Android) & GitHub.com | `github.com` |
| `copilot-models` | All | _(none needed)_ |
| `copilot-extension-event` | **Inbound webhook** — receives events when any user invokes `@infinity-orchestrator` | `ecdsa-es256` — verify against GitHub public keys |
| `copilot-seats` | Org management | GitHub App token |

#### Invoking from GitHub Mobile App

1. Open the **GitHub Mobile** app (iOS or Android).
2. Tap **Copilot** (chat icon) in the bottom navigation bar.
3. Type `@infinity-orchestrator` followed by an intent:
   - `@infinity-orchestrator run genesis-loop` — trigger autonomous invention
   - `@infinity-orchestrator health` — check system health
   - `@infinity-orchestrator repos` — list org repo index
   - `@infinity-orchestrator memory` — read current ACTIVE_MEMORY.md snapshot
   - `@infinity-orchestrator issue <title>` — create a GitHub issue
4. Copilot routes the message to the extension webhook at `copilot-extension-event`.
5. The orchestrator processes the request and streams a response back.

> 📖 Full setup guide: `.infinity/runbooks/copilot-mobile.md`

### Cloudflare
- **Purpose**: DNS management, Workers deployment, Pages CI/CD, R2 storage,
  KV namespaces, Zero Trust tunnels.
- **Auth**: `CLOUDFLARE_API_TOKEN` (scoped) + `CLOUDFLARE_ACCOUNT_ID`.
- **Guardrails**: Never delete zones or accounts autonomously.
- **Docs**: `cloudflare-connector.json`

### VS Code / GitHub Codespaces
- **Purpose**: Codespace lifecycle management; VS Code Remote Tunnels for
  interactive runner access; devcontainer configuration.
- **Auth**: GitHub App token (Codespaces API) + `VSCODE_TUNNEL_TOKEN` (tunnel).
- **Docs**: `vscode-connector.json`

---

## Required Secrets

| Secret | Used By | Required |
|--------|---------|---------|
| `GITHUB_APP_ID` | GitHub API, Copilot, Codespaces | ✅ |
| `GITHUB_APP_PRIVATE_KEY` | GitHub API, Copilot, Codespaces | ✅ |
| `OPENAI_API_KEY` | OpenAI connector | ✅ for AI features |
| `CLOUDFLARE_API_TOKEN` | Cloudflare connector | ✅ for CF ops |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare connector | ✅ for CF ops |
| `CLOUDFLARE_ZONE_ID` | Cloudflare DNS operations | ⚙️ per-zone ops |
| `VSCODE_TUNNEL_TOKEN` | VS Code tunnel | ⚙️ for tunnel |
| _(no secret needed)_ | Copilot Extension uses ECDSA P-256; verify against `https://api.github.com/meta/public_keys/copilot_api` | ✅ built-in |

---

## Adding a New Connector

1. Create `{service}-connector.json` in this directory.
2. Add an entry to `endpoint-registry.json` with `"governed": true`.
3. Update `auth-matrix.md` with the auth requirements.
4. Update this file's table above.
5. Open a PR with a codeowner review.

---

## Governance

All connectors are subject to:
- **TAP Protocol** (`.infinity/policies/tap-protocol.md`)
- **Authentication rules** (`auth-matrix.md`)
- **Guardrails** (`.infinity/policies/guardrails.md`)

Unregistered connector calls are a TAP violation.
