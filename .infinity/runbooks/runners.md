# Self-Hosted Runners — Setup & Management Runbook

This runbook covers registering, configuring, and maintaining self-hosted
GitHub Actions runners for the Infinity Orchestrator system.  Self-hosted
runners unlock capabilities that GitHub-hosted runners cannot provide:
Docker-in-Docker, Cloudflare Workers CLI, persistent caching, and direct
local filesystem access.

---

## Overview

| Runner Type | When to Use |
|-------------|------------|
| GitHub-hosted (`ubuntu-latest`) | Default for all standard workflows |
| Self-hosted (Linux, Docker) | Docker builds, Cloudflare CLI, large artifacts, local sync |
| Self-hosted (Windows / PowerShell) | `deploy-singularity.ps1`, VS Code tunnel |

---

## 1. Prerequisites

Before registering a runner, ensure the host has:

| Tool | Minimum Version | Install |
|------|----------------|---------|
| Git | 2.30+ | `apt install git` |
| Docker | 24.0+ | [docs.docker.com](https://docs.docker.com/engine/install/) |
| GitHub CLI (`gh`) | 2.40+ | [cli.github.com](https://cli.github.com/) |
| jq | 1.6+ | `apt install jq` |
| PowerShell | 7.0+ (optional) | [Microsoft docs](https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-linux) |
| Node.js | 18+ (optional) | For JavaScript tooling |

---

## 2. Runner Registration

### 2.1 Organization-Level Runner (Recommended)

Organization-level runners are available to **all** repositories in
`Infinity-X-One-Systems`, which is required for the orchestrator to dispatch
workflows cross-repo.

```bash
# Step 1: Generate a runner registration token via GitHub API
# (requires organization_self_hosted_runners: write permission)
RUNNER_TOKEN=$(gh api \
  -X POST \
  /orgs/Infinity-X-One-Systems/actions/runners/registration-token \
  --jq '.token')

# Step 2: Download and extract the Actions runner
mkdir -p ~/actions-runner && cd ~/actions-runner
curl -o actions-runner-linux-x64-2.321.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.321.0/actions-runner-linux-x64-2.321.0.tar.gz
tar xzf ./actions-runner-linux-x64-2.321.0.tar.gz

# Step 3: Configure the runner
./config.sh \
  --url https://github.com/Infinity-X-One-Systems \
  --token "${RUNNER_TOKEN}" \
  --name "infinity-runner-$(hostname)" \
  --labels "self-hosted,linux,x64,infinity-orchestrator,docker,cloudflare" \
  --runnergroup "infinity-orchestrator" \
  --work "_work" \
  --replace

# Step 4: Install and start as a systemd service
sudo ./svc.sh install
sudo ./svc.sh start
sudo ./svc.sh status
```

### 2.2 Repository-Level Runner

Use only when the runner is exclusive to `infinity-orchestrator`:

```bash
RUNNER_TOKEN=$(gh api \
  -X POST \
  /repos/Infinity-X-One-Systems/infinity-orchestrator/actions/runners/registration-token \
  --jq '.token')

./config.sh \
  --url https://github.com/Infinity-X-One-Systems/infinity-orchestrator \
  --token "${RUNNER_TOKEN}" \
  --name "infinity-runner-$(hostname)" \
  --labels "self-hosted,linux,x64,infinity-orchestrator,docker"
```

---

## 3. Recommended Runner Labels

Runners should be tagged with the following labels so workflows can target
them precisely:

```
self-hosted        — required for all self-hosted runners
linux              — OS type
x64                — architecture
infinity-orchestrator — indicates this runner is configured for orchestrator ops
docker             — Docker daemon is available
cloudflare         — Cloudflare CLI (wrangler) is installed
```

To use a self-hosted runner in a workflow:

```yaml
jobs:
  my-job:
    runs-on: [self-hosted, linux, x64, infinity-orchestrator]
```

---

## 4. Required Software on the Runner

### Docker
```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Allow runner user to use Docker without sudo
sudo usermod -aG docker runner_user
```

### Cloudflare CLI (wrangler)
```bash
npm install -g wrangler
wrangler --version
```

### GitHub CLI
```bash
type -p curl >/dev/null || sudo apt install curl -y
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
  | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh -y
```

### PowerShell 7 (for deploy-singularity.ps1)
```bash
wget -q "https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb"
sudo dpkg -i packages-microsoft-prod.deb
sudo apt-get update && sudo apt-get install -y powershell
pwsh --version
```

---

## 5. VS Code Remote Tunnel (Optional)

The VS Code tunnel allows interactive access to the runner environment from
any browser or VS Code client:

```bash
# Install VS Code CLI
curl -Lk 'https://code.visualstudio.com/sha/download?build=stable&os=cli-alpine-x64' \
  --output vscode_cli.tar.gz
tar -xf vscode_cli.tar.gz
sudo mv code /usr/local/bin/

# Start the tunnel (runs as a background service)
code tunnel service install \
  --accept-server-license-terms \
  --name infinity-orchestrator

# The tunnel URL will be printed — open it in VS Code or a browser
code tunnel status
```

---

## 6. Runner Health Monitoring

The health monitor workflow (`health-monitor.yml`) checks active runners.
To verify your runner is online:

```bash
# List all runners in the org
gh api /orgs/Infinity-X-One-Systems/actions/runners --jq '.runners[]'

# Check a specific runner
gh api /orgs/Infinity-X-One-Systems/actions/runners \
  --jq '.runners[] | select(.name == "infinity-runner-my-host")'
```

---

## 7. Removing a Runner

```bash
# Graceful removal (from the runner host)
cd ~/actions-runner
sudo ./svc.sh stop
sudo ./svc.sh uninstall
./config.sh remove --token "${RUNNER_TOKEN}"
```

Or via API:
```bash
RUNNER_ID=$(gh api /orgs/Infinity-X-One-Systems/actions/runners \
  --jq '.runners[] | select(.name == "infinity-runner-my-host") | .id')
gh api -X DELETE "/orgs/Infinity-X-One-Systems/actions/runners/${RUNNER_ID}"
```

---

## 8. Security Hardening

- Run the Actions runner as a **dedicated non-root user** (e.g., `runner`).
- Restrict Docker access: add runner user to the `docker` group only.
- Do not expose the runner host's SSH port publicly.
- Rotate the runner registration token after each use.
- Enable ephemeral runners (`--ephemeral`) for untrusted code execution.
- Apply network firewall rules: runner only needs outbound HTTPS to github.com.

---

## 9. Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Runner shows "offline" | Service stopped | `sudo ./svc.sh start` |
| `docker: Permission denied` | Runner user not in docker group | `sudo usermod -aG docker runner_user` |
| `RUNNER_TOKEN expired` | Token is one-time-use | Generate a new token and re-run `config.sh` |
| Workflow picks `ubuntu-latest` not self-hosted | Missing labels | Add correct labels in `config.sh --labels` |
| Disk full on runner | Accumulated artifacts | `docker system prune -a` + clear `_work/` |

---

## Related Files

| File | Purpose |
|------|---------|
| `config/github-app-manifest.json` | App permission reference (includes `organization_self_hosted_runners: write`) |
| `.infinity/connectors/vscode-connector.json` | VS Code tunnel configuration |
| `.github/workflows/health-monitor.yml` | Runner health monitoring |
| `AGENT_ENTRYPOINT.md` | Recommended runner labels for workflows |
