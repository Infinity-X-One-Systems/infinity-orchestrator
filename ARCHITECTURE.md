# Infinity Orchestrator Architecture

## Overview

The Infinity Orchestrator is a fully autonomous, zero-touch GitHub-native system designed to manage, compile, test, and deploy all repositories within the `Infinity-X-One-Systems` organization. This system leverages GitHub's native technologies to create a self-sustaining orchestration platform governed by the TAP Protocol (Policy > Authority > Truth).

## Core Principles

1. **Zero Human Intervention**: Low/medium risk changes are automated through GitHub Actions with zero-approval auto-merge
2. **GitHub-Native**: Uses only GitHub technologies (Actions, Apps, OAuth, APIs)
3. **Self-Healing**: Automatic detection and recovery from failures
4. **Scalable**: Handles current and future repositories automatically
5. **Secure**: Built-in security scanning, TAP governance, and quarantine mode
6. **TAP Governed**: Every autonomous action is bound by Policy > Authority > Truth guardrails

## Architecture Components

### 1. Autonomy State Machine (NEW)

The core of zero-approval autonomy — `stacks/core/autonomy_controller.py`:

```
SENSE → THINK → ACT → VERIFY → SHIP → LEARN
```

| Phase | Description |
|-------|-------------|
| **SENSE** | Read org repo index + repositories manifest; collect signals (failing workflows, open issues tagged `bot-task`, security alerts) |
| **THINK** | Score and prioritise signals using `scoring_agent`; upsert into backlog ledger |
| **ACT** | Open PRs for high-priority low/medium-risk items (draft PRs in quarantine mode) |
| **VERIFY** | Check CI status and security scan results for queued PRs |
| **SHIP** | Apply `autonomous-verified` label for auto-merge (skipped in quarantine mode) |
| **LEARN** | Write run summaries to `docs/run-{id}.md` and update `.infinity/` memory |

The state machine is invoked by `.github/workflows/autonomy-controller.yml` on a schedule
(every 6 hours) and on `repository_dispatch: autonomy-trigger`.

**Break-glass toggles** (set as repo variables):

| Variable | Default | Effect |
|----------|---------|--------|
| `INFINITY_AUTONOMY_ENABLED` | `true` | Master kill-switch |
| `INFINITY_AUTOMERGE_ENABLED` | `true` | Enable/disable auto-merge |
| `INFINITY_MAX_PRS_PER_DAY` | `10` | Daily PR circuit-breaker |
| `INFINITY_QUARANTINE_MODE` | `false` | Activates quarantine mode |

See runbooks: `.infinity/runbooks/zero-approval-mode.md` and `.infinity/runbooks/quarantine-mode.md`.

### 2. Backlog Ledger

Machine-readable canonical backlog at `.infinity/ledger/backlog.json`.

Managed by `stacks/agents/backlog_agent.py`. Schema fields per item:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (16-char hex) | Deterministic SHA-1 of `repo:type:title` |
| `repo` | string | `Org/repo` full name |
| `type` | enum | `bug`, `security`, `chore`, `feature` |
| `priority` | int 1–5 | 1 = highest urgency |
| `risk` | enum | `low`, `medium`, `high`, `critical` |
| `status` | enum | `open`, `in_progress`, `done`, `blocked`, `cancelled` |
| `evidence_links` | array | URLs to issues, PRs, alerts |
| `created_at` | ISO-8601 | First upsert timestamp |
| `updated_at` | ISO-8601 | Last upsert timestamp |
| `policy_decision_ref` | string | TAP decision log reference |
| `run_id` | string | GitHub Actions run ID |
| `workflow` | string | Workflow that created/updated the item |
| `commit_sha` | string | Git SHA at time of update |

Updates are atomic (write to `.tmp` then `rename`). Validate with:

```bash
python scripts/validate-ledger.py
```

### 3. Repository Discovery Engine

Automatically discovers and catalogs all repositories in the organization:
- Periodic scanning via GitHub API (`org-repo-index.yml` every 6 hours)
- Index stored in `.infinity/ORG_REPO_INDEX.json` and `.infinity/ORG_REPO_INDEX.md`
- Uses `INFINITY_APP_TOKEN` (P-005) for org-wide listing; falls back to `GITHUB_TOKEN` with warning
- Creates diagnostic issue on discovery failure (no secrets in issue body — P-001)

### 4. Orchestration Engine

Central coordination system that:
- Manages multi-repository builds
- Coordinates cross-repository dependencies
- Schedules and prioritizes workflows
- Handles parallel and sequential execution

### 5. Build & Test Pipeline

Automated compilation and testing:
- Language-agnostic build system
- Parallel test execution
- Artifact management
- Build caching and optimization

### 6. Health Monitoring System

Continuous health checks:
- Repository health metrics
- Build success rates
- Performance monitoring
- Alerting and notifications

### 7. Self-Healing System

Automatic recovery mechanisms:
- Failed build retry logic
- Dependency conflict resolution
- Automated issue creation and tracking
- Rollback capabilities

### 8. Security & Compliance

Automated security management:
- CodeQL security scanning
- Dependency vulnerability scanning
- Secret scanning
- Compliance reporting

## Workflow Orchestration

### Primary Workflows

1. **Autonomy Controller** (`autonomy-controller.yml`) ← NEW
   - Runs the Sense→Think→Act→Verify→Ship→Learn state machine
   - Manages backlog ledger and opens governed PRs
   - Respects break-glass toggles and quarantine mode

2. **Auto-Merge** (`genesis-auto-merge.yml`)
   - Governed auto-merge with policy gate and risk assessment
   - Zero-approval for `low`/`medium` risk PRs with TAP decision records
   - Quarantine and kill-switch support

3. **Repository Sync** (`repo-sync.yml`)
   - Discovers new repositories
   - Updates repository manifest
   - Triggers onboarding for new repos

4. **Org Repo Index** (`org-repo-index.yml`)
   - Refreshes `.infinity/ORG_REPO_INDEX.json` every 6 hours
   - Supports `INFINITY_APP_TOKEN` for org-wide listing
   - Creates diagnostic issues on failure

5. **Genesis Loop** (`genesis-loop.yml`)
   - Plan → Code → Validate → Diagnose → Heal → Deploy phases
   - Invokes genesis Python modules for autonomous coding

6. **Autonomous Invention** (`autonomous-invention.yml`)
   - Discovery → Scoring → Sandbox → Validation → Documentation → Telemetry
   - Multi-agent pipeline for invention signals

7. **Multi-Repo Build** (`multi-repo-build.yml`)
   - Builds all repositories in dependency order

8. **Health Monitor** (`health-monitor.yml`)
   - Checks repository health and workflow success rates

9. **Self-Healing** (`self-healing.yml`)
   - Automatic failure recovery

10. **Security Scanner** (`security-scan.yml`)
    - Daily security scans and vulnerability reporting

## Data Flow

```
GitHub API → ORG_REPO_INDEX.json
                   ↓
         Autonomy Controller (state machine)
         SENSE → THINK → ACT → VERIFY → SHIP → LEARN
                   ↓             ↓              ↓
         Backlog Ledger      PRs Opened     Run Docs
         (.infinity/          (governed,      (docs/)
          ledger/)             PR-only)
                               ↓
                      genesis-auto-merge.yml
                      (policy gate + CI check)
                               ↓
                      Auto-merge (low/medium risk)
                      or Human review (high/critical)
```

## Governance Model

All autonomous operations follow the TAP Protocol (`P-001` through `P-008`, `G-01` through `G-15`):

- **P-001**: No secrets in logs, commits, or PR bodies
- **P-003**: Bot attribution on all commits
- **P-004**: No force-push to protected branches
- **P-005**: GitHub App tokens for cross-repo operations
- **G-02**: No force-push to `main`
- **G-08**: Never auto-merge PRs with failing checks

Every auto-merge requires a TAP decision record (`<!-- TAP-DECISION: ... -->`) in the PR body.

## Configuration

### Repository Manifest (`config/repositories.json`)

Automatically generated and maintained:
```json
{
  "repositories": [
    {
      "name": "repo-name",
      "language": "javascript",
      "build_command": "npm run build",
      "test_command": "npm test",
      "dependencies": []
    }
  ]
}
```

### Orchestrator Configuration (`config/orchestrator.yml`)

System-wide settings:
```yaml
discovery:
  scan_interval: "0 */6 * * *"  # Every 6 hours
  organization: "Infinity-X-One-Systems"

build:
  max_parallel: 10
  timeout_minutes: 60
  retry_attempts: 3

monitoring:
  health_check_interval: "*/15 * * * *"  # Every 15 minutes
  failure_threshold: 3

self_healing:
  auto_retry: true
  auto_update_dependencies: true
  create_issues: true
```

## GitHub App Integration

The orchestrator uses a GitHub App (`infinity-orchestrator-app`) for:
- Repository access across the organization
- Fine-grained permissions
- Webhook event handling
- API rate limit optimization

Required permissions:
- Actions: Read & Write
- Contents: Read & Write
- Issues: Read & Write
- Pull Requests: Read & Write
- Workflows: Read & Write
- Metadata: Read
- Members: Read (for org-wide repo listing)

## Security Model

1. **Secret Management**: All secrets stored in GitHub Secrets (never in code — P-001)
2. **Least Privilege**: Minimal required permissions only
3. **Audit Trail**: TAP decision logs in every workflow step summary
4. **Quarantine Mode**: Automatic circuit-breaker prevents runaway automation
5. **Vulnerability Scanning**: Automated and continuous
6. **Dependency Monitoring**: Automatic updates via Dependabot

## Scalability

The system scales automatically:
- Dynamic workflow matrix generation
- Parallel execution where possible
- Efficient caching strategies
- Resource optimization
- Daily PR circuit-breaker (`INFINITY_MAX_PRS_PER_DAY`)

## Future Enhancements

- Automatic quarantine activation after N consecutive failures
- Multi-cloud deployment support
- Advanced AI-powered failure prediction
- Cost optimization algorithms
- Performance analytics dashboard
- Custom workflow DSL
