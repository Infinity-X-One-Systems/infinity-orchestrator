# Auth Matrix — Infinity Orchestrator Endpoints

> **Org:** Infinity-X-One-Systems  
> Governs authentication requirements for every registered endpoint category.  
> Cross-reference with [`endpoint-registry.md`](./endpoint-registry.md) for the full endpoint list.

---

## Auth Scheme Definitions

| Scheme ID | Type | Token Lifetime | Secrets Required |
|-----------|------|---------------|-----------------|
| `none` | No auth | — | — |
| `bearer` | HTTP Bearer token | Varies by issuer | `API_TOKEN` or equivalent |
| `github-app-token` | GitHub App installation access token (RS256 JWT → IAT) | 1 hour max | `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY`, `GITHUB_APP_INSTALLATION_ID` (optional) |
| `cloudflare-access` | Cloudflare Access service token | Configurable (default 365 d) | `CF_ACCESS_CLIENT_ID`, `CF_ACCESS_CLIENT_SECRET` |
| `oauth2-google` | Google OAuth 2.0 service account | 1 hour | `GOOGLE_SERVICE_ACCOUNT_KEY` (JSON) or `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` |
| `tls-cert` | Mutual TLS client certificate | Certificate validity period | `DOCKER_CERT_PATH`, `DOCKER_TLS_VERIFY=1` |
| `unix-socket` | Unix domain socket (filesystem permission) | N/A | Docker group membership or `root` |
| `ecdsa-es256` | ECDSA P-256 (ES256) asymmetric signature (GitHub Copilot Extension events) | N/A (per-request) | None — uses GitHub's published public keys |

---

## Per-Category Auth Requirements

### Local

| Endpoint | Scheme | Secret(s) | Masking Required |
|----------|--------|-----------|-----------------|
| `local-health` | `none` | — | No |
| `local-api` | `bearer` | `LOCAL_API_TOKEN` | Yes — mask in logs |

### Cloud

| Endpoint | Scheme | Secret(s) | Masking Required |
|----------|--------|-----------|-----------------|
| `cloud-api-gateway` | `bearer` | `CLOUD_API_TOKEN` | Yes |

### Cloudflare

| Endpoint | Scheme | Secret(s) | Masking Required |
|----------|--------|-----------|-----------------|
| `cf-tunnel-orchestrator` | `cloudflare-access` | `CF_ACCESS_CLIENT_ID`, `CF_ACCESS_CLIENT_SECRET` | Yes — both values |
| `cf-gateway` | `cloudflare-access` | `CF_ACCESS_CLIENT_ID`, `CF_ACCESS_CLIENT_SECRET` | Yes |

> **Note:** Cloudflare Access tokens must **never** appear in query strings; use headers only.

### Docker

| Endpoint | Scheme | Secret(s) | Masking Required |
|----------|--------|-----------|-----------------|
| `docker-socket` | `unix-socket` | _(filesystem permissions)_ | N/A |
| `docker-tcp` | `tls-cert` | `DOCKER_CERT_PATH` (directory of certs) | No — certs are files, not inline secrets |

> **Security note:** Docker socket mounts are documented risks. Prefer read-only socket mounts (`/var/run/docker.sock:ro`) and document alternatives. See `SECURITY.md`.

### GitHub Actions / Dispatch

| Endpoint | Scheme | Secret(s) | Masking Required |
|----------|--------|-----------|-----------------|
| `gh-actions-dispatch` | `github-app-token` | `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY` | Yes — mask JWT + IAT before any log output |
| `gh-repo-dispatch` | `github-app-token` | `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY` | Yes |
| `gh-actions-list-runs` | `github-app-token` | `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY` | Yes |

> **No long-lived PATs.** Always use GitHub App installation access tokens. Tokens expire in ≤ 1 hour and are minted per workflow run. The JWT and IAT must be masked via `::add-mask::` immediately after creation.

### MCP

| Endpoint | Scheme | Secret(s) | Masking Required |
|----------|--------|-----------|-----------------|
| `mcp-server-local` | `bearer` | `MCP_SERVER_TOKEN` | Yes |
| `mcp-server-cloud` | `bearer` | `MCP_SERVER_TOKEN` | Yes |

### REST Gateway

| Endpoint | Scheme | Secret(s) | Masking Required |
|----------|--------|-----------|-----------------|
| `rest-gateway-v1` | `bearer` | `GATEWAY_API_TOKEN` | Yes |

### Ingestion Pipeline

| Endpoint | Scheme | Secret(s) | Masking Required |
|----------|--------|-----------|-----------------|
| `ingestion-event-stream` | `bearer` | `INGEST_TOKEN` | Yes |
| `ingestion-batch` | `bearer` | `INGEST_TOKEN` | Yes |

### Google Workspace

| Endpoint | Scheme | Secret(s) | Masking Required |
|----------|--------|-----------|-----------------|
| `gws-gmail` | `oauth2-google` | `GOOGLE_SERVICE_ACCOUNT_KEY` | Yes — mask full JSON key |
| `gws-drive` | `oauth2-google` | `GOOGLE_SERVICE_ACCOUNT_KEY` | Yes |
| `gws-calendar` | `oauth2-google` | `GOOGLE_SERVICE_ACCOUNT_KEY` | Yes |

### AI Services (OpenAI & GitHub Copilot)

| Endpoint | Scheme | Secret(s) | Masking Required | Surface |
|----------|--------|-----------|-----------------|---------|
| `openai-chat` | `bearer` | `OPENAI_API_KEY` | Yes — mask immediately after retrieval | All |
| `openai-embeddings` | `bearer` | `OPENAI_API_KEY` | Yes | All |
| `copilot-chat` | `github-app-token` | `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY` | Yes — mask JWT + IAT | VS Code |
| `copilot-mobile-chat` | `github-app-token` | `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY` | Yes — mask JWT + IAT | Mobile / GitHub.com |
| `copilot-models` | `github-app-token` | `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY` | Yes | All |
| `copilot-extension-event` | `ecdsa-es256` | None — use GitHub public keys from `https://api.github.com/meta/public_keys/copilot_api` | N/A — inbound; verify ECDSA signature | Inbound webhook |
| `copilot-seats` | `github-app-token` | `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY` | Yes | Management |

> **Mobile-specific note:** When the GitHub Mobile app sends a Copilot Chat request, the `Copilot-Integration-Id` header value is `github.com` (not `vscode-chat`). Use the `copilot-mobile-chat` endpoint entry and its header config from `copilot-connector.json`.
>
> **Extension webhook note:** Inbound events from `@infinity-orchestrator` invocations (on any surface, including mobile) arrive at `copilot-extension-event`. Always verify the ECDSA P-256 (ES256) signature using GitHub's published public keys before processing. No shared secret is required. See `.infinity/runbooks/copilot-mobile.md` for the full verification procedure.

---

## Token Masking Protocol

All scripts and workflows **must** call the masking primitive immediately after obtaining any token:

**PowerShell (GitHub Actions runner):**
```powershell
# Use Invoke-MaskSecret wrapper — see .infinity/scripts/Sync-MemoryToOrchestrator.ps1
Invoke-MaskSecret -Secret $accessToken
```

**Bash (GitHub Actions runner):**
```bash
echo "::add-mask::${TOKEN}"
```

Fields that **must never appear unmasked** in logs:
- `Authorization` header value
- `CF-Access-Client-Secret`
- Any value containing `token`, `key`, `secret`, or `password` in its name

---

## Rotation & Expiry Policy

| Scheme | Recommended Rotation | Automated? |
|--------|---------------------|------------|
| `github-app-token` | Per workflow run (auto-expires ≤ 1 h) | ✅ Yes — minted on demand |
| `bearer` (static) | Every 90 days | ❌ Manual — set a calendar reminder |
| `cloudflare-access` | Every 90 days | ❌ Manual |
| `oauth2-google` (service account) | Every 90 days or on personnel change | ❌ Manual |
| `tls-cert` | Before certificate expiry (monitor `notAfter`) | ❌ Manual |
| `ecdsa-es256` (GitHub public key) | GitHub rotates their signing keys periodically — no action needed | ✅ Auto — GitHub publishes current keys at `/meta/public_keys/copilot_api` |

---

## Governance

Violations of this auth matrix are a **TAP Protocol** enforcement point.  
See `.infinity/policies/tap-protocol.md` for the full governance framework and `.infinity/runbooks/governance-enforcement.md` for decision logging procedures.
