# Genesis — Autonomous Software Factory Integration

This directory contains the **Genesis Autonomous Software Factory** kernel, integrated from [`InfinityXOneSystems/genesis`](https://github.com/InfinityXOneSystems/genesis) into the Infinity Orchestrator.

## What is Genesis?

Genesis is a FAANG-grade, enterprise-level autonomous software factory that achieves recursive self-improvement without human intervention. Once initialized, Genesis continuously:

- 🔍 **Scans** repositories for improvement opportunities
- 🧠 **Plans** tasks based on intelligent analysis
- 💻 **Codes** solutions using specialized AI personas
- ✅ **Validates** changes through automated testing
- 🚀 **Deploys** approved changes automatically
- 🔄 **Repeats** indefinitely, evolving itself

## Directory Structure

```
stacks/genesis/
├── __init__.py
└── core/
    ├── __init__.py
    ├── agent_team.py          # 11 specialized AI agent personas
    ├── orchestrator.py        # Main task orchestration brain
    ├── loop.py                # Phase driver (Plan→Code→Validate→Diagnose→Heal→Deploy)
    ├── repo_scanner.py        # GitHub org repository scanner
    ├── git_manager.py         # Git operations & PR management
    ├── workflow_analyzer.py   # CI/CD failure analysis & intelligence
    ├── auto_diagnostician.py  # Automated issue diagnosis
    ├── auto_healer.py         # Automated self-healing
    ├── auto_validator.py      # Continuous validation & quality gates
    ├── auto_merger.py         # Automated PR merging
    ├── conflict_resolver.py   # Semantic merge conflict resolution
    ├── branch_manager.py      # Branch analysis & management
    └── auto_merge_orchestrator.py  # Full merge orchestration pipeline
```

## Agent Team

| Agent | Role |
|---|---|
| `chief_architect` | System architecture & high-level design |
| `frontend_lead` | React/Next.js UI development |
| `backend_lead` | Python/FastAPI backend services |
| `devsecops_engineer` | CI/CD, Docker, security |
| `qa_engineer` | Testing & quality assurance |
| `workflow_analyzer` | GitHub Actions monitoring |
| `auto_diagnostician` | Automated issue diagnosis |
| `auto_healer` | Automated bug fixing & self-healing |
| `conflict_resolver` | Merge conflict resolution |
| `auto_validator` | Continuous validation & quality gates |
| `auto_merger` | Automated PR management & merging |

## GitHub Actions Workflows

| Workflow | Trigger | Purpose |
|---|---|---|
| `genesis-loop.yml` | Every 6 hours / manual | Full autonomous cycle (Plan→Deploy) |
| `genesis-devops-team.yml` | Every 2 hours / manual | Auto-healing & monitoring |
| `genesis-auto-merge.yml` | PR labeled / check complete | Auto-merge `autonomous-verified` PRs |

## Docker Infrastructure

```
docker/genesis/
├── Dockerfile.genesis-core     # Python autonomous loop engine
└── docker-compose.genesis.yml  # Full stack (Qdrant, Ollama, Redis)
```

Start Genesis services:
```bash
cd docker/genesis
docker-compose -f docker-compose.genesis.yml up -d
# With local LLM:
docker-compose -f docker-compose.genesis.yml --profile llm up -d
```

## Running Manually

```bash
# Install dependencies
pip install -r requirements.genesis.txt

# Full autonomous cycle
python stacks/genesis/core/loop.py full

# Individual phases
python stacks/genesis/core/loop.py plan      # Scan and plan improvements
python stacks/genesis/core/loop.py code      # Execute coding tasks
python stacks/genesis/core/loop.py validate  # Run tests and quality checks
python stacks/genesis/core/loop.py diagnose  # Diagnose workflow failures
python stacks/genesis/core/loop.py heal      # Auto-fix issues
python stacks/genesis/core/loop.py deploy    # Merge and deploy changes
```

## System Manifest

`genesis_manifest.json` tracks the live system state:
- Current epoch and status
- Active agents and their states
- Task queue
- Metrics (tasks completed, PRs merged, etc.)
- System health

## Auto-Merge Flow

PRs labeled `autonomous-verified` are automatically merged when:
1. All CI/CD checks pass ✅
2. No merge conflicts 🔀
3. Code quality standards met 📊
4. Security scans clean 🔒

## Required Secrets

| Secret | Required | Purpose |
|---|---|---|
| `GITHUB_TOKEN` | ✅ | GitHub API access (auto-provided in Actions) |

## Source Repository

Integrated from [`InfinityXOneSystems/genesis`](https://github.com/InfinityXOneSystems/genesis) at commit `c37ad6ce`.
