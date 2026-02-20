# 🤖 AGENT ENTRYPOINT — Infinity Orchestrator

**READ THIS FIRST.** This file is the canonical bootstrap guide for every AI
agent, coding assistant (GitHub Copilot, ChatGPT, Claude, etc.), and
autonomous workflow that interacts with this repository.

---

## 1. What This Repository Is

`Infinity-X-One-Systems/infinity-orchestrator` is the **sovereign control
plane** and **GitHub App host** for the entire Infinity X One Systems
ecosystem.  It functions as a:

| Role | Description |
|------|-------------|
| **Code & System Factory** | Generates, validates, and deploys code across all org repos autonomously |
| **GitHub App Host** | Houses the `infinity-orchestrator` GitHub App, which has maximum permissions across the org |
| **Memory Hub** | Stores and serves `ACTIVE_MEMORY.md` — the single source of truth for agent workspace context |
| **Connector Gateway** | Manages authenticated connections to Cloudflare, VS Code/Codespaces, OpenAI, GitHub Copilot |
| **Governance Centre** | Enforces TAP Protocol, guardrails, and all org-wide policies |

---

## 2. Memory Rehydration (ALWAYS DO THIS FIRST)

Before generating any response or executing any task, you **must** read the
current memory snapshot:

### Option A — Local file (fastest)
```
.infinity/ACTIVE_MEMORY.md
```

### Option B — GitHub Contents API (when no local checkout)
```bash
curl -s \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.raw+json" \
  "https://api.github.com/repos/Infinity-X-One-Systems/infinity-orchestrator/contents/.infinity/ACTIVE_MEMORY.md"
```

### Option C — Bootstrap script (recommended for workflows)
```yaml
- name: Bootstrap agent
  shell: pwsh
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: ./.infinity/scripts/Invoke-InfinityAgentBootstrap.ps1
```

> **If ACTIVE_MEMORY.md is missing or stale**, trigger the rehydrate
> workflow: `gh workflow run rehydrate.yml`

---

## 3. Repository File Map

```
infinity-orchestrator/
│
├── AGENT_ENTRYPOINT.md         ← YOU ARE HERE
├── README.md                   ← Human-facing overview
├── ARCHITECTURE.md             ← System architecture
├── SECURITY.md                 ← Security policy
├── CONTRIBUTING.md             ← Contribution guide
├── QUICKREF.md                 ← Quick reference card
│
├── .infinity/                  ← Agent workspace root
│   ├── ACTIVE_MEMORY.md        ← Live state snapshot (read first!)
│   ├── ORG_REPO_INDEX.json     ← All org repos (auto-generated daily)
│   ├── connectors/             ← External service connectors
│   │   ├── endpoint-registry.json     ← All governed endpoints
│   │   ├── endpoint-registry.md       ← Endpoint docs
│   │   ├── auth-matrix.md             ← Auth requirements
│   │   ├── connectors-index.md        ← Connector overview
│   │   ├── openai-connector.json      ← ChatGPT / OpenAI
│   │   ├── copilot-connector.json     ← GitHub Copilot Mobile
│   │   ├── cloudflare-connector.json  ← Cloudflare
│   │   └── vscode-connector.json      ← VS Code / Codespaces
│   ├── policies/               ← Governance policies
│   │   ├── tap-protocol.md     ← TAP Protocol (Policy > Authority > Truth)
│   │   ├── governance.md       ← Governance framework
│   │   └── guardrails.md       ← Circuit-breakers & limits
│   ├── runbooks/               ← Operational runbooks
│   │   ├── agent-bootstrap.md
│   │   ├── endpoint-registry.md
│   │   ├── memory-sync.md
│   │   └── runners.md          ← Self-hosted runner setup
│   └── scripts/                ← Agent/automation scripts
│       ├── Invoke-InfinityAgentBootstrap.ps1
│       └── Sync-MemoryToOrchestrator.ps1
│
├── .github/
│   ├── app-manifest.json       ← GitHub App manifest (max permissions)
│   └── workflows/
│       ├── autonomous-invention.yml   ← 6-phase autonomous engine
│       ├── genesis-loop.yml           ← Genesis autonomous loop
│       ├── genesis-devops-team.yml    ← Auto-heal DevOps team
│       ├── genesis-auto-merge.yml     ← Auto-merge verified PRs
│       ├── health-monitor.yml         ← Every 15-min health check
│       ├── self-healing.yml           ← Auto-recovery
│       ├── memory-sync.yml            ← Hourly memory sync
│       ├── rehydrate.yml              ← ACTIVE_MEMORY refresh
│       ├── org-repo-index.yml         ← Daily org repo index
│       ├── repo-sync.yml              ← Every-6h repo discovery
│       ├── multi-repo-build.yml       ← Daily cross-repo build
│       ├── local-docker-sync.yml      ← Bidirectional local+Docker sync
│       ├── security-scan.yml          ← Daily security scan
│       └── release.yml                ← Tag-triggered releases
│
├── config/
│   ├── orchestrator.yml        ← Master orchestrator config
│   ├── repositories.json       ← Auto-generated repo manifest
│   └── github-app-manifest.json ← App permissions reference
│
├── scripts/                    ← Shell scripts
│   ├── rehydrate.sh
│   ├── discover-repos.sh
│   ├── health-check.sh
│   ├── self-heal.sh
│   └── build-orchestrator.sh
│
├── stacks/                     ← Agent/service implementations
│   ├── agents/                 ← Python autonomous agents
│   ├── genesis/                ← Genesis autonomous factory
│   ├── prompts/                ← System prompts
│   ├── vision/                 ← Playwright stealth agent
│   ├── core/, factory/, knowledge/  ← Docker service stacks
│   └── README.md
│
├── docker/                     ← Docker configurations
│   └── genesis/
├── docker-compose.singularity.yml  ← Singularity Mesh full-stack
│
├── Run_Memory_Script.ps1       ← PowerShell memory rehydration
├── deploy-singularity.ps1      ← One-click Singularity deploy
│
└── docs/                       ← Generated run reports
```

---

## 4. GitHub App — Maximum Permissions

The `infinity-orchestrator` GitHub App is configured for **maximum autonomy**
across the entire organization. See `config/github-app-manifest.json` for the
complete manifest.

**Key capabilities:**

| Capability | Permission |
|-----------|-----------|
| Read/write all repo contents | `contents: write` |
| Create/delete repositories | `administration: write` |
| Manage Actions & runners | `actions: write` |
| Create/close/edit issues & PRs | `issues: write`, `pull_requests: write` |
| Manage billing | `organization_plan: read` |
| Manage org members | `members: write` |
| Manage org secrets | `organization_secrets: write` |
| Manage environments | `environments: write` |
| Manage deployments | `deployments: write` |
| Manage webhooks | `organization_hooks: write` |
| Manage packages | `packages: write` |
| Read/write GitHub Pages | `pages: write` |
| Manage Codespaces | `codespaces: write` |
| Read security events | `security_events: read` |

---

## 5. Connector System

This repository manages authenticated connections to external systems:

| Connector | Config File | Purpose |
|-----------|------------|---------|
| **GitHub API** | `endpoint-registry.json` | Core GitHub operations |
| **OpenAI / ChatGPT** | `openai-connector.json` | LLM inference, embeddings |
| **GitHub Copilot** | `copilot-connector.json` | Copilot Chat API, mobile |
| **Cloudflare** | `cloudflare-connector.json` | DNS, Workers, Pages, R2 |
| **VS Code / Codespaces** | `vscode-connector.json` | Remote development, extensions |

All connectors are governed by:
- Authentication: `.infinity/connectors/auth-matrix.md`
- Registry: `.infinity/connectors/endpoint-registry.json`
- Policy: `.infinity/policies/governance.md`

---

## 6. TAP Protocol (Policy > Authority > Truth)

**TAP** governs every autonomous action taken by any agent in this system:

```
T — Truth     : Ground decisions in verifiable facts, not assumptions.
A — Authority : Respect the permission hierarchy (see governance.md).
P — Policy    : Policy rules always override individual agent decisions.
```

Full protocol: `.infinity/policies/tap-protocol.md`

**Validation gate**: Every autonomous invention cycle runs
`stacks/agents/validator_agent.py` before any mutation is committed.
TAP failures create blocking GitHub Issues.

---

## 7. Autonomous Engine Overview

The system operates through two overlapping autonomous loops:

### Genesis Loop (`.github/workflows/genesis-loop.yml`)
Runs every 6 hours — continuous software improvement:
```
Plan → Code → Validate → Diagnose → Heal → Deploy
```

### Autonomous Invention Engine (`.github/workflows/autonomous-invention.yml`)
Runs every 3 hours — idea factory:
```
Discovery → Scoring → Sandbox → TAP Validation → Documentation → Telemetry
```

### Genesis DevOps Team (`.github/workflows/genesis-devops-team.yml`)
Runs every 2 hours — CI/CD health & healing:
```
Analyze → Diagnose → Heal → Validate → Auto-Merge
```

---

## 8. Key Secrets (Required for Full Autonomy)

Configure these in **Settings → Secrets and variables → Actions**:

| Secret | Purpose | Required |
|--------|---------|---------|
| `GITHUB_APP_ID` | Infinity Orchestrator GitHub App ID | ✅ Critical |
| `GITHUB_APP_PRIVATE_KEY` | App RSA private key (PEM) | ✅ Critical |
| `GITHUB_APP_INSTALLATION_ID` | Pre-known installation ID | ⚙️ Optional |
| `OPENAI_API_KEY` | ChatGPT / GPT-4 inference | ✅ For AI features |
| `CLOUDFLARE_API_TOKEN` | Cloudflare automation | ✅ For CF ops |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account scoping | ✅ For CF ops |
| `VSCODE_TUNNEL_TOKEN` | VS Code tunnel authentication | ⚙️ For remote dev |
| `GH_ORG` | Org override (default: `Infinity-X-One-Systems`) | ⚙️ Optional |

> `GITHUB_TOKEN` is auto-injected by Actions and does not need to be set.

---

## 9. Quick Commands

```bash
# Trigger memory rehydration
gh workflow run rehydrate.yml

# Run full autonomous cycle
gh workflow run autonomous-invention.yml

# Run Genesis loop (specific phase)
gh workflow run genesis-loop.yml -f phase=plan

# Refresh org repo index
gh workflow run org-repo-index.yml

# Check system health
gh workflow run health-monitor.yml

# Run security scan
gh workflow run security-scan.yml

# Trigger self-healing
gh workflow run self-healing.yml

# Bidirectional local+Docker sync
gh workflow run local-docker-sync.yml
```

---

## 10. Self-Hosted Runner Configuration

For maximum capability (Cloudflare Workers, Docker builds, local file access),
use a self-hosted runner. See `.infinity/runbooks/runners.md` for full setup.

**Recommended labels for self-hosted runners:**

```
self-hosted, linux, x64, infinity-orchestrator, docker, cloudflare
```

Runners must be registered at the **organization level** so all repos can use
them.

---

## 11. Memory Freshness Guarantee

```
Rehydrate schedule:  every 6 hours (cron: '30 */6 * * *')
Memory sync:         every hour    (cron: '0 * * * *')
Org repo index:      every day     (cron: '0 2 * * *')
```

If `ACTIVE_MEMORY.md` is older than 60 minutes, the bootstrap script will
automatically re-fetch it via the GitHub Contents API.

---

## 12. Governance Hierarchy

```
1. GUARDRAILS    (hard limits — cannot be overridden by any agent)
2. TAP PROTOCOL  (Policy > Authority > Truth)
3. GOVERNANCE    (org-wide rules and permissions)
4. AGENT LOGIC   (individual agent decisions)
```

An agent may NEVER:
- Delete the `main` branch of any repository
- Remove SECURITY.md, CONTRIBUTING.md, or LICENSE
- Expose secrets in commit messages, logs, or PR bodies
- Bypass the TAP validation gate
- Create or delete billing settings without human confirmation

---

## 13. Contact & Escalation

| Condition | Action |
|-----------|--------|
| TAP validation fails | Issue created automatically; do not proceed |
| Health check 3× consecutive fail | Self-healing triggered; alert issue opened |
| Secret scanning alert | Workflow paused; human review required |
| Billing threshold exceeded | Alert created; workflow paused |
| Unknown error | Create issue with label `triage:agent-escalation` |

---

*This file is maintained as part of the Infinity Orchestrator governance
framework.  Last verified: see `ACTIVE_MEMORY.md` for snapshot timestamp.*
