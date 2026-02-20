# Infinity Orchestrator

**A fully autonomous, zero-touch GitHub-native orchestration system for managing all repositories in the Infinity-X-One-Systems organization.**

> 🤖 **For AI agents:** Read [`AGENT_ENTRYPOINT.md`](./AGENT_ENTRYPOINT.md) first — it is the canonical bootstrap guide for all autonomous actors interacting with this repository.

## 🚀 Overview

Infinity Orchestrator is a comprehensive automation system that provides:

- 🤖 **Zero Human Intervention**: Fully automated repository management
- 🔄 **Continuous Orchestration**: Automatic discovery, build, test, and deployment
- 🛡️ **Self-Healing**: Automatic detection and recovery from failures
- 🔒 **Security First**: Built-in vulnerability scanning and automated updates
- 📊 **Health Monitoring**: Continuous monitoring and alerting
- 🌐 **GitHub Native**: Uses only GitHub technologies (Actions, Apps, OAuth)
- 🧠 **Persistent Memory**: Auto-rehydrating `ACTIVE_MEMORY.md` snapshot consumed by all agents
- 🔌 **Connector System**: Governed integrations for OpenAI/ChatGPT, GitHub Copilot, Cloudflare, and VS Code/Codespaces
- 📜 **TAP Governance**: Policy > Authority > Truth protocol with 8 immutable guardrails
- 🖥️ **Bidirectional Sync**: Local ↔ Docker ↔ GitHub sync every 30 minutes

## 🎯 Key Features

### Automated Repository Management
- Automatic discovery of new repositories
- Dynamic manifest generation
- Cross-repository dependency management
- Language-agnostic build orchestration

### Multi-Repository Build System
- Parallel and sequential execution
- Dependency-aware build ordering
- Artifact caching and optimization
- Build matrix generation

### Health & Monitoring
- Continuous health checks (every 15 minutes)
- Success rate tracking
- Performance metrics
- Automated alerting

### Self-Healing Capabilities
- Automatic retry on failures
- Dependency conflict resolution
- Configuration auto-repair
- Issue creation for manual intervention needs

### Security & Compliance
- CodeQL security scanning
- Dependabot vulnerability updates
- Secret scanning
- Automated security patches

## 📋 Quick Start

### Prerequisites
- GitHub Organization with repositories
- GitHub App (`infinity-orchestrator`) installed on `Infinity-X-One-Systems`
- Admin access to the organization

### Setup (5 minutes)

1. **Configure GitHub App credentials** (no PATs — TAP P-002)
   ```bash
   # Add these secrets to repository Settings → Secrets and variables → Actions
   GITHUB_APP_ID=<your-app-id>
   GITHUB_APP_PRIVATE_KEY=<contents-of-private-key.pem>
   # Optional AI / Cloudflare connectors
   OPENAI_API_KEY=sk-...
   CLOUDFLARE_API_TOKEN=<scoped-token>
   CLOUDFLARE_ACCOUNT_ID=<account-id>
   ```

2. **Enable GitHub Actions**
   - Go to Settings → Actions → Enable workflows

3. **Trigger Initial Sync**
   ```bash
   gh workflow run repo-sync.yml
   ```

4. **Verify Setup**
   ```bash
   gh run list
   ```

📖 **Detailed setup instructions**: See [SETUP.md](./SETUP.md)
🤖 **Agent bootstrap guide**: See [AGENT_ENTRYPOINT.md](./AGENT_ENTRYPOINT.md)

## 🏗️ Architecture

The orchestrator consists of several integrated components:

```
┌─────────────────────────────────────────────────────────────┐
│                    Infinity Orchestrator                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Repository  │  │    Build &   │  │   Health     │    │
│  │  Discovery   │→ │     Test     │→ │  Monitoring  │    │
│  │   Engine     │  │   Pipeline   │  │    System    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│         ↓                                      ↓           │
│  ┌──────────────┐                    ┌──────────────┐    │
│  │ Orchestration│                    │ Self-Healing │    │
│  │    Engine    │←───────────────────│    System    │    │
│  └──────────────┘                    └──────────────┘    │
│         ↓                                                  │
│  ┌──────────────────────────────────────────────────┐    │
│  │          Security & Compliance Layer              │    │
│  └──────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

📖 **Detailed architecture**: See [ARCHITECTURE.md](./ARCHITECTURE.md)

## 🔄 Core Workflows

### 1. Repository Sync (`repo-sync.yml`)
- **Schedule**: Every 6 hours
- **Purpose**: Discover and catalog all organization repositories
- **Output**: Updated `config/repositories.json`

### 2. Org Repo Index (`org-repo-index.yml`)
- **Schedule**: Every 6 hours + `workflow_dispatch`
- **Purpose**: Generate live `.infinity/ORG_REPO_INDEX.json` and `.infinity/ORG_REPO_INDEX.md`
- **Output**: Machine-readable + human-readable index

### 3. Multi-Repository Build (`multi-repo-build.yml`)
- **Schedule**: Daily at midnight UTC
- **Trigger**: Push to main branch
- **Purpose**: Build and test all repositories

### 4. Genesis Autonomous Loop (`genesis-loop.yml`)
- **Schedule**: Every 6 hours
- **Purpose**: Continuous software improvement — Plan → Code → Validate → Diagnose → Heal → Deploy

### 5. Health Monitor (`health-monitor.yml`)
- **Schedule**: Every 15 minutes
- **Purpose**: Check system health and trigger alerts

### 6. Self-Healing (`self-healing.yml`)
- **Trigger**: On health check failures
- **Purpose**: Automatically recover from common issues

### 7. Security Scanner (`security-scan.yml`)
- **Schedule**: Daily
- **Purpose**: Scan for vulnerabilities and create fix PRs

### 8. Memory Sync & Rehydrate (`memory-sync.yml`, `rehydrate.yml`)
- **Schedule**: Hourly (memory-sync), every 6 hours (rehydrate)
- **Purpose**: Keep `.infinity/ACTIVE_MEMORY.md` fresh for agent sessions

### 9. Local & Docker Bidirectional Sync (`local-docker-sync.yml`)
- **Schedule**: Every 30 minutes
- **Purpose**: Sync `.infinity/` artifacts between GitHub, local filesystem, and Docker Singularity Mesh

## 🛡️ TAP Governance Protocol

All autonomous operations are governed by the **TAP Protocol** (Policy > Authority > Truth):

| Layer | Document | Description |
|-------|---------|-------------|
| Immutable guardrails | [`.infinity/policies/tap-protocol.md`](./.infinity/policies/tap-protocol.md) | 8 rules: no secrets in logs, no PATs, bot attribution, graceful degradation |
| Governance framework | [`.infinity/policies/governance.md`](./.infinity/policies/governance.md) | Role hierarchy, decision matrix, change management |
| Circuit-breakers | [`.infinity/policies/guardrails.md`](./.infinity/policies/guardrails.md) | 15 hard limits, rate limits, destructive-action confirmation |
| Enforcement runbook | [`.infinity/runbooks/governance-enforcement.md`](./.infinity/runbooks/governance-enforcement.md) | TAP gate steps, secret masking, audit logging |

## 🔌 Connector System

Governed integrations for external services:

| Connector | Config | Secrets Required |
|-----------|--------|-----------------|
| OpenAI / ChatGPT | [`.infinity/connectors/openai-connector.json`](./.infinity/connectors/openai-connector.json) | `OPENAI_API_KEY` |
| GitHub Copilot | [`.infinity/connectors/copilot-connector.json`](./.infinity/connectors/copilot-connector.json) | GitHub App token |
| Cloudflare | [`.infinity/connectors/cloudflare-connector.json`](./.infinity/connectors/cloudflare-connector.json) | `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` |
| VS Code / Codespaces | [`.infinity/connectors/vscode-connector.json`](./.infinity/connectors/vscode-connector.json) | GitHub App token, `VSCODE_TUNNEL_TOKEN` |

All endpoints are registered in [`.infinity/connectors/endpoint-registry.json`](./.infinity/connectors/endpoint-registry.json).

## 📁 Repository Structure

```
infinity-orchestrator/
├── AGENT_ENTRYPOINT.md      ← 🤖 Agent bootstrap guide (read first!)
├── README.md                ← This file
├── ARCHITECTURE.md          ← System architecture
├── SETUP.md                 ← Setup guide (updated secrets/permissions)
├── SECURITY.md              ← Security policy
├── CONTRIBUTING.md          ← Contribution guidelines
├── QUICKREF.md              ← Quick reference card
│
├── .infinity/               ← Agent workspace root
│   ├── ACTIVE_MEMORY.md     ← Live state snapshot (auto-rehydrated)
│   ├── ORG_REPO_INDEX.json  ← All org repos (auto-generated)
│   ├── ORG_REPO_INDEX.md    ← Human-readable repo index
│   ├── connectors/          ← External service connectors
│   ├── policies/            ← TAP Protocol, governance, guardrails
│   ├── runbooks/            ← Operational runbooks
│   └── scripts/             ← Bootstrap + sync scripts
│
├── .github/
│   └── workflows/           ← All GitHub Actions workflows (14 total)
│
├── config/
│   ├── orchestrator.yml         ← Master config (connectors, sync, runners)
│   ├── repositories.json        ← Auto-generated repo manifest
│   └── github-app-manifest.json ← GitHub App max-permission manifest
│
├── scripts/                 ← Shell scripts
├── stacks/                  ← Agent implementations (Genesis, Vision, etc.)
└── docker-compose.singularity.yml  ← Singularity Mesh deployment
```

## 🎮 Usage

### Manual Workflow Triggers

```bash
# Discover repositories
gh workflow run repo-sync.yml

# Build all repositories
gh workflow run multi-repo-build.yml

# Run health check
gh workflow run health-monitor.yml

# Trigger self-healing
gh workflow run self-healing.yml

# Run security scan
gh workflow run security-scan.yml
```

### View Workflow Status

```bash
# List recent runs
gh run list

# View specific run
gh run view <run-id>

# Watch run in progress
gh run watch <run-id>
```

### Configuration

Edit `config/orchestrator.yml` to customize:
- Discovery intervals
- Build parallelization
- Health check thresholds
- Self-healing behavior

### Singularity Mesh Deployment

```bash
# One-command full deployment
.\deploy-singularity.ps1

# Sync repositories only
.\deploy-singularity.ps1 -Mode sync-only

# Build Docker images
.\deploy-singularity.ps1 -Mode build-only

# Force rebuild (no cache)
.\deploy-singularity.ps1 -Force

# Stop all services
.\deploy-singularity.ps1 -Mode stop

# Check service status
.\deploy-singularity.ps1 -Mode status

# View logs
docker-compose -f docker-compose.singularity.yml logs -f
```

## 🔧 Customization

### Adding Custom Build Commands

Edit the auto-generated `config/repositories.json`:
```json
{
  "repositories": [
    {
      "name": "my-custom-repo",
      "language": "go",
      "build_command": "go build ./...",
      "test_command": "go test ./..."
    }
  ]
}
```

### Custom Workflows

Add custom workflows to `.github/workflows/` that leverage the orchestrator's reusable workflows.

## 📊 Monitoring

### Health Metrics
- Build success rate
- Average build time
- Failure patterns
- Security alerts

### Alerts
The system automatically creates issues for:
- Repeated build failures
- Security vulnerabilities
- Configuration problems
- System health degradation

## 🔒 Security

- **Secrets Management**: All credentials in GitHub Secrets
- **Least Privilege**: Minimal required permissions
- **Audit Trail**: All actions logged
- **Vulnerability Scanning**: Automated daily scans
- **Dependency Updates**: Automatic via Dependabot

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - See [LICENSE](./LICENSE) for details.

## 🆘 Support

- **Documentation**: Check [ARCHITECTURE.md](./ARCHITECTURE.md) and [SETUP.md](./SETUP.md)
- **Issues**: Create an issue in this repository
- **Logs**: Check workflow run logs for detailed error information

## 🌌 Singularity Mesh (New!)

**FAANG-grade parallel orchestration via Docker Compose**

The Singularity Mesh is a containerized, parallel deployment system for the entire Infinity ecosystem. One command deploys all intelligence nodes:

```powershell
.\deploy-singularity.ps1
```

**Features:**
- 🐳 **Docker-Native**: All agents containerized (zero Python/Pip issues)
- ⚡ **Parallel Execution**: All 5+ repos run simultaneously
- 🕵️ **Shadow Capabilities**: Vision agent with Playwright stealth mode
- 🧠 **Sovereign Architecture**: Redis cache, ChromaDB, Browserless
- 🚀 **One-Click Deploy**: Single PowerShell command for the entire fleet

**Services:**
- `neural-core` - The Brain (infinity-core)
- `vision-cortex` - The Eyes with stealth (infinity-vision + Playwright)
- `factory-arm` - The Builder (infinity-factory)
- `knowledge-base` - The Memory (ChromaDB)
- `redis-cache` - Synaptic bridge
- `browserless` - Shadow portal

📖 **Full documentation**: [stacks/README.md](./stacks/README.md)

## 🗺️ Roadmap

- [x] Core orchestration engine
- [x] Repository discovery
- [x] Multi-repository builds
- [x] Health monitoring
- [x] Self-healing system
- [x] Security scanning
- [x] **Singularity Mesh (Docker parallel orchestration)**
- [x] **TAP Protocol governance (P-001..P-008)**
- [x] **Connector system (OpenAI, Copilot, Cloudflare, VS Code)**
- [x] **Persistent memory + bidirectional sync**
- [x] **GitHub App maximum-permission manifest**
- [x] **Agent entrypoint + org repo index**
- [ ] Performance analytics dashboard
- [ ] Cost optimization
- [ ] Multi-cloud deployment support
- [ ] Custom workflow DSL
- [ ] AI-powered failure prediction

---

**Built with ❤️ for the InfinityXOneSystems organization**
