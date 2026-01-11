# Infinity Orchestrator - Quick Reference Guide

## Quick Commands

### Manual Workflow Triggers

```bash
# Repository Discovery
gh workflow run repo-sync.yml

# Multi-Repository Build
gh workflow run multi-repo-build.yml

# Health Check
gh workflow run health-monitor.yml

# Self-Healing
gh workflow run self-healing.yml

# Security Scan
gh workflow run security-scan.yml
```

### Build Specific Repositories

```bash
# Build specific repos
gh workflow run multi-repo-build.yml \
  --field repositories="repo1,repo2,repo3"

# Build without tests
gh workflow run multi-repo-build.yml \
  --field skip_tests=true
```

### View Workflow Status

```bash
# List recent runs
gh run list

# List runs for specific workflow
gh run list --workflow=repo-sync.yml

# View specific run
gh run view <run-id>

# View with logs
gh run view <run-id> --log

# Watch run in progress
gh run watch

# Download logs
gh run download <run-id>
```

### Repository Manifest

```bash
# View manifest
cat config/repositories.json | jq '.'

# Get repository count
jq '.statistics.total_repositories' config/repositories.json

# List all repositories
jq -r '.repositories[].name' config/repositories.json

# List by language
jq -r '.repositories[] | select(.language == "JavaScript") | .name' config/repositories.json

# Check health status
jq -r '.repositories[] | "\(.name): \(.health.status)"' config/repositories.json
```

### Health Monitoring

```bash
# Check current health
./scripts/health-check.sh

# Force health check run
gh workflow run health-monitor.yml

# View health reports
gh run list --workflow=health-monitor.yml
```

### Self-Healing

```bash
# Trigger healing for all repos
gh workflow run self-healing.yml

# Heal specific repository
gh workflow run self-healing.yml \
  --field target_repository="repo-name"
```

## Configuration

### Orchestrator Settings

Edit `config/orchestrator.yml`:

```yaml
# Change discovery interval
discovery:
  scan_interval: "0 */6 * * *"  # Every 6 hours

# Adjust build settings
build:
  max_parallel: 10
  timeout_minutes: 60
  retry_attempts: 3

# Configure monitoring
monitoring:
  health_check_interval: "*/15 * * * *"
  failure_threshold: 3
```

### GitHub Secrets

Required secrets:
- `GH_TOKEN` - GitHub Personal Access Token or GitHub App token
- `GH_ORG` - Organization name (optional, defaults to Infinity-X-One-Systems)

Optional secrets:
- `GH_APP_ID` - GitHub App ID
- `GH_APP_PRIVATE_KEY` - GitHub App private key
- `GH_APP_CLIENT_SECRET` - GitHub App client secret

### Workflow Permissions

Ensure the following permissions are set:
- Actions: Read & Write
- Contents: Read & Write
- Issues: Read & Write
- Pull Requests: Read & Write
- Workflows: Read & Write

## Troubleshooting

### Workflows Not Running

1. Check GitHub Actions are enabled
2. Verify workflow permissions
3. Check secrets are configured
4. Review workflow syntax

```bash
# Validate workflow syntax
gh workflow view repo-sync.yml
```

### Repository Discovery Fails

1. Verify GH_TOKEN has correct permissions
2. Check organization name is correct
3. Ensure GitHub CLI is authenticated

```bash
# Test GitHub CLI
gh auth status

# Test repository access
gh repo list Infinity-X-One-Systems
```

### Build Failures

1. Check repository manifest is current
2. Verify build commands are correct
3. Review build logs

```bash
# View build logs
gh run view --log-failed

# Check manifest
jq '.repositories[] | select(.name == "repo-name")' config/repositories.json
```

### Self-Healing Not Working

1. Ensure health monitor is running
2. Check failure threshold is met
3. Verify permissions allow creating PRs

```bash
# Check recent health runs
gh run list --workflow=health-monitor.yml --limit 5
```

## Workflow Schedule Reference

| Workflow | Schedule | Trigger |
|----------|----------|---------|
| Repository Sync | Every 6 hours | `0 */6 * * *` |
| Multi-Repo Build | Daily at midnight | `0 0 * * *` |
| Health Monitor | Every 15 minutes | `*/15 * * * *` |
| Security Scan | Daily at 2 AM | `0 2 * * *` |
| Self-Healing | On-demand | Via health monitor |

## Common Tasks

### Add New Repository

New repositories are automatically discovered every 6 hours. To force immediate discovery:

```bash
gh workflow run repo-sync.yml
```

### Update Build Command

1. Edit `config/repositories.json`
2. Find your repository
3. Update `build_config.build_command`
4. Commit changes

```bash
jq '.repositories[] | select(.name == "my-repo").build_config.build_command = "new-command"' \
  config/repositories.json > tmp.json
mv tmp.json config/repositories.json
git add config/repositories.json
git commit -m "chore: update build command for my-repo"
git push
```

### Disable Repository from Builds

Edit `config/repositories.json` and set:

```json
{
  "build_config": {
    "enabled": false
  }
}
```

### View Health History

```bash
# Download health reports
gh run list --workflow=health-monitor.yml --json databaseId,conclusion,createdAt

# Get specific report
gh run view <run-id>
gh run download <run-id>
```

## Integration

### With Other Workflows

Use the orchestrator as a trigger:

```yaml
on:
  workflow_run:
    workflows: ["Multi-Repository Build"]
    types:
      - completed
```

### Custom Notifications

Add notification steps to workflows:

```yaml
- name: Notify on failure
  if: failure()
  run: |
    # Send notification
    echo "Build failed!"
```

### Custom Build Steps

Edit repository manifest to add pre/post build steps:

```json
{
  "build_config": {
    "pre_build": ["npm ci", "npm run lint"],
    "build_command": "npm run build",
    "post_build": ["npm run test:coverage"]
  }
}
```

## Maintenance

### Weekly Tasks
- Review health check results
- Check for failed workflows
- Review security alerts

### Monthly Tasks
- Review repository manifest accuracy
- Update documentation
- Audit GitHub App permissions
- Review and merge Dependabot PRs

### Quarterly Tasks
- Security audit
- Performance review
- Update orchestrator configuration
- Review and update workflows

## Performance Tips

1. **Parallel Builds**: Adjust `max_parallel` in config
2. **Cache Usage**: Enable artifact caching
3. **Selective Builds**: Build only changed repos
4. **Timeout Tuning**: Adjust timeout values per repo

## Security Best Practices

1. **Token Rotation**: Rotate GitHub tokens quarterly
2. **Audit Logs**: Review workflow logs regularly
3. **Permissions**: Use least privilege principle
4. **Secrets**: Never commit secrets
5. **Dependencies**: Keep dependencies updated

## Getting Help

1. Check documentation:
   - README.md
   - ARCHITECTURE.md
   - SETUP.md
   - CONTRIBUTING.md

2. Search existing issues

3. Review workflow logs

4. Create a new issue with:
   - Workflow name
   - Run ID
   - Error message
   - Steps to reproduce

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub CLI Manual](https://cli.github.com/manual/)
- [GitHub Apps Documentation](https://docs.github.com/en/apps)
- [Workflow Syntax Reference](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)

---

**Last Updated**: 2026-01-11
