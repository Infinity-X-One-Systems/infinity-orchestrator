# Infinity Orchestrator Setup Guide

## Prerequisites

- GitHub Organization: Infinity-X-One-Systems
- GitHub App or OAuth token with appropriate permissions
- Repository admin access

## Initial Setup

### Step 1: GitHub App Configuration

1. Create a GitHub App for the organization:
   - Go to Organization Settings → Developer settings → GitHub Apps
   - Click "New GitHub App"
   - Configure the following:
     - **Name**: Infinity Orchestrator
     - **Homepage URL**: https://github.com/Infinity-X-One-Systems/infinity-orchestrator
     - **Webhook**: Active (optional, for real-time events)
     - **Webhook URL**: Your endpoint (if using webhooks)

2. Set required permissions:
   - Actions: Read & Write
   - Contents: Read & Write
   - Issues: Read & Write
   - Pull Requests: Read & Write
   - Workflows: Read & Write
   - Metadata: Read
   - Administration: Read & Write (for repo management)
   - Organization → Members: Read & Write
   - Organization → Self-hosted runners: Read & Write
   - (See `config/github-app-manifest.json` for the full permission manifest)

3. Generate and save:
   - App ID (numeric, shown on the App settings page)
   - Private Key (download as `.pem` file from App settings → Private keys)
   - Installation ID (shown in the URL when you install the App on the org:
     `https://github.com/organizations/Infinity-X-One-Systems/settings/installations/<ID>`)

### Step 2: Repository Secrets Configuration

Add the following secrets in **Settings → Secrets and variables → Actions**:

```bash
# ── GitHub App credentials (REQUIRED — no long-lived PATs per TAP P-002) ──
GITHUB_APP_ID=<numeric-app-id>
GITHUB_APP_PRIVATE_KEY=<contents-of-private-key.pem>
GITHUB_APP_INSTALLATION_ID=<numeric-installation-id>  # optional; if omitted, the bootstrap script auto-discovers it via the GitHub App installations API

# ── Organization ──
GH_ORG=Infinity-X-One-Systems   # optional; defaults to this value

# ── AI connectors (required for autonomous invention engine) ──
OPENAI_API_KEY=sk-...

# ── Cloudflare connectors (required for CF automation) ──
CLOUDFLARE_API_TOKEN=<scoped-cloudflare-api-token>
CLOUDFLARE_ACCOUNT_ID=<cloudflare-account-id>
CLOUDFLARE_ZONE_ID=<primary-zone-id>   # optional; per-zone ops

# ── VS Code / Codespaces (optional — for tunnel access) ──
VSCODE_TUNNEL_TOKEN=<tunnel-token>
```

> **Security note (TAP P-002):** Long-lived Personal Access Tokens (PATs) must
> **not** be stored as Actions secrets.  Use GitHub App installation tokens for
> all automated operations.  `GITHUB_TOKEN` is injected automatically by Actions
> and does not need to be configured.

### Step 3: Enable GitHub Actions

1. Go to repository Settings → Actions → General
2. Enable "Allow all actions and reusable workflows"
3. Set workflow permissions to "Read and write permissions"
4. Check "Allow GitHub Actions to create and approve pull requests"

### Step 4: Configure Dependabot

Dependabot is pre-configured. To enable:
1. Go to repository Settings → Security → Dependabot
2. Enable "Dependabot alerts"
3. Enable "Dependabot security updates"

### Step 5: Enable CodeQL Scanning

CodeQL is pre-configured. To enable:
1. Go to repository Security → Code scanning
2. Click "Set up code scanning"
3. Choose "Advanced setup" if asked
4. The workflow is already present in `.github/workflows/`

## Workflow Configuration

### Repository Discovery

The repository discovery workflow runs automatically:
- **Schedule**: Every 6 hours
- **Manual trigger**: Via workflow_dispatch
- **Purpose**: Discovers new repositories and updates manifest

To manually trigger:
```bash
gh workflow run repo-sync.yml
```

### Multi-Repository Build

Builds all repositories in the organization:
- **Schedule**: Daily at midnight UTC
- **Trigger**: On push to main branch
- **Manual trigger**: Available

To manually trigger:
```bash
gh workflow run multi-repo-build.yml
```

### Health Monitoring

Continuous health checks:
- **Schedule**: Every 15 minutes
- **Purpose**: Monitor repository health and trigger self-healing

### Self-Healing

Automatic recovery:
- **Trigger**: On health monitor failure detection
- **Manual trigger**: Available
- **Purpose**: Automatically fix common issues

## Configuration Files

### Orchestrator Configuration

Edit `config/orchestrator.yml` to customize:
- Discovery intervals
- Build settings
- Monitoring thresholds
- Self-healing behavior

### Repository Manifest

The file `config/repositories.json` is auto-generated. To force regeneration:
```bash
gh workflow run repo-sync.yml
```

## Verification

After setup, verify the system is working:

1. **Check agent entrypoint** (read this first for all agent operations):
   ```bash
   cat AGENT_ENTRYPOINT.md
   ```

2. **Bootstrap agent memory**:
   ```powershell
   ./.infinity/scripts/Invoke-InfinityAgentBootstrap.ps1
   ```

3. **Check workflow runs**:
   ```bash
   gh run list
   ```

4. **View repository manifest**:
   ```bash
   cat config/repositories.json
   ```

5. **Test manual build**:
   ```bash
   gh workflow run repo-sync.yml
   ```

6. **Check logs**:
   ```bash
   gh run view --log
   ```

## Troubleshooting

### Issue: Workflows not running

**Solution**: Check that:
- GitHub Actions are enabled
- Workflow permissions are set correctly
- Required secrets are configured

### Issue: Repository discovery fails

**Solution**: Verify:
- GitHub App/token has correct permissions
- Token has not expired
- Organization name is correct in secrets

### Issue: Build failures

**Solution**: Check:
- Repository manifest is up to date
- Dependencies are correctly specified
- Build commands are valid

### Issue: Self-healing not working

**Solution**: Ensure:
- Health monitor is running
- Self-healing workflow is enabled
- Permissions allow creating issues/PRs

## Advanced Configuration

### Custom Build Commands

Edit `config/repositories.json` to specify custom build commands:
```json
{
  "name": "my-repo",
  "build_command": "make build",
  "test_command": "make test"
}
```

### Webhook Integration

For real-time event handling:
1. Configure webhook URL in GitHub App
2. Update `scripts/webhook-handler.sh`
3. Deploy webhook endpoint

### Monitoring Dashboard

Access workflow runs:
```bash
# List all runs
gh run list --workflow=health-monitor.yml

# View specific run
gh run view <run-id>

# Watch run in real-time
gh run watch <run-id>
```

## Maintenance

### Regular Tasks

- **Monthly**: Review repository manifest accuracy
- **Quarterly**: Audit security settings
- **As needed**: Update orchestrator configuration

### Updates

The system auto-updates via Dependabot. For manual updates:
```bash
# Update workflows
git pull origin main

# Update dependencies (if applicable)
npm update  # or appropriate package manager
```

## Support

For issues or questions:
1. Check existing issues in this repository
2. Review workflow logs for error details
3. Create a new issue with relevant details

## Next Steps

After setup:
1. Monitor the first few workflow runs
2. Verify repository discovery is working
3. Check build success for all repositories
4. Review and adjust configuration as needed
5. Set up notifications (optional)
