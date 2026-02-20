# Copilot Mobile + Extension Setup Runbook

> **Org:** Infinity-X-One-Systems
> **Scope:** GitHub Copilot Mobile (iOS/Android) ↔ `infinity-orchestrator`
> **Version:** 1.0.0
> **Connector config:** [`.infinity/connectors/copilot-connector.json`](../connectors/copilot-connector.json)
> **Endpoint registry:** [`.infinity/connectors/endpoint-registry.json`](../connectors/endpoint-registry.json) — `ai_services` category

---

## 1. Purpose

This runbook describes how to configure the `@infinity-orchestrator` **Copilot Extension** so that users can invoke orchestrator operations directly from:

- **GitHub Mobile app** (iOS and Android) — Copilot Chat tab
- **GitHub.com** — Copilot Chat on the web
- **VS Code** — Copilot Chat sidebar

When a user types `@infinity-orchestrator <intent>` in any of these surfaces, GitHub routes the request to the orchestrator's registered webhook endpoint (`copilot-extension-event`), which processes the intent and streams a response back to the user.

---

## 2. Prerequisites

| Item | Required | Notes |
|------|----------|-------|
| GitHub Copilot Business or Enterprise plan | ✅ | Copilot Extensions require Business or Enterprise |
| `infinity-orchestrator` GitHub App installed on org | ✅ | See `config/github-app-manifest.json` |
| Webhook receiver deployed | ✅ | Must be publicly reachable over HTTPS |
| Webhook receiver reachable over HTTPS | ✅ | GitHub sends POST events to this URL; verify ECDSA P-256 signature |
| `GITHUB_APP_ID` + `GITHUB_APP_PRIVATE_KEY` secrets set | ✅ | Used to verify org membership and mint tokens |

---

## 3. Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│  GitHub Mobile / GitHub.com / VS Code                    │
│                                                          │
│   User: "@infinity-orchestrator run genesis-loop"        │
│                       │                                  │
│           Copilot Extensions API                         │
│                       │ POST (ECDSA P-256 / ES256 signed) │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │  copilot-extension-event    │
         │  (webhook receiver)         │
         │  https://orchestrator.      │
         │  infinity-x-one.systems/   │
         │  copilot/events            │
         └──────────────┬──────────────┘
                        │
                        ▼
         ┌─────────────────────────────┐
         │  GitHub Actions             │
         │  workflow_dispatch          │
         │  (or Cloudflare Worker)     │
         └──────────────┬──────────────┘
                        │
                        ▼
         ┌─────────────────────────────┐
         │  infinity-orchestrator      │
         │  (.github/workflows/)       │
         │  Streams response via SSE   │
         └─────────────────────────────┘
```

---

## 4. Step-by-Step Setup

### Step 1 — Register the Copilot Extension on your GitHub App

1. Navigate to **Organization Settings → Developer Settings → GitHub Apps → infinity-orchestrator → Edit**.
2. In the **Copilot** section:
   - Set **App type** to `Agent`
   - Set **Callback URL** to the webhook receiver URL:
     ```
     https://orchestrator.infinity-x-one.systems/copilot/events
     ```
   - Set **Pre-authorization URL** (optional, for OAuth consent): leave blank or set to your app URL
3. Save changes.

> The agent slug is automatically derived from the GitHub App slug: `@infinity-orchestrator`.

### Step 2 — Configure the webhook URL

No shared secret is required.  GitHub Copilot Extensions sign every inbound payload using an **ECDSA P-256 (ES256)** key pair.  The corresponding public keys are published at `https://api.github.com/meta/public_keys/copilot_api` and are automatically rotated by GitHub.

Your webhook receiver must:
1. Read the `X-GitHub-Public-Key-Signature` and `X-GitHub-Public-Key-Identifier` headers.
2. Fetch GitHub's current public keys from the URL above.
3. Locate the key whose `key_identifier` matches the header value.
4. Verify the ECDSA P-256 signature over the raw request body using that public key.
5. Reject the request if verification fails.

See [Section 5](#5-signature-verification) for implementation code.

### Step 3 — Deploy the webhook receiver

The webhook receiver must be reachable at the URL you set in Step 1.

#### Option A: Cloudflare Worker (recommended)

Deploy a Cloudflare Worker that:
1. Verifies the `X-GitHub-Public-Key-Signature` ECDSA P-256 (ES256) signature using GitHub's published public keys.
2. Parses the intent from the Copilot message payload.
3. Triggers the corresponding GitHub Actions workflow via `workflow_dispatch`.
4. Streams back a response using Server-Sent Events (SSE).

See the signature verification procedure in [Section 5](#5-signature-verification) below.

#### Option B: GitHub Actions workflow (simpler but asynchronous)

1. Expose a `workflow_dispatch` trigger on `autonomous-invention.yml` (or similar).
2. Use a Cloudflare Worker or GitHub App webhook handler to receive the Copilot event and call `gh workflow run`.
3. Respond immediately with an acknowledgement message; the workflow runs asynchronously.

### Step 4 — Install the Extension for org members

1. Navigate to **GitHub.com → Settings → Copilot → Extensions** (for individual accounts)
   or **Org Settings → Copilot → Extensions** (for org-wide enablement).
2. Find `infinity-orchestrator` and click **Install** or **Enable for all members**.
3. Members can now use `@infinity-orchestrator` in Copilot Chat on GitHub.com, VS Code, and the **GitHub Mobile app**.

### Step 5 — Verify from GitHub Mobile

1. Install the **GitHub Mobile** app on iOS or Android.
2. Sign in with your GitHub account.
3. Tap the **Copilot** tab (chat bubble icon).
4. Type:
   ```
   @infinity-orchestrator health
   ```
5. The extension should respond with the current orchestrator health status.

---

## 5. Signature Verification

Every inbound Copilot Extension event is signed with **ECDSA P-256 (ES256)** using GitHub's key pair. **Always verify before processing.** No stored secret is required — fetch GitHub's public keys on demand and cache them briefly.

### JavaScript (Cloudflare Worker / Node.js)

```javascript
const crypto = require('crypto');

async function verifySignature(req, secret) {
  const signature = req.headers['x-github-public-key-signature'];
  const keyId     = req.headers['x-github-public-key-identifier'];
  const body      = await req.text();

  // 1. Fetch GitHub's public keys
  const keysResp = await fetch('https://api.github.com/meta/public_keys/copilot_api');
  const keys = (await keysResp.json()).public_keys;
  const publicKey = keys.find(k => k.key_identifier === keyId)?.key;
  if (!publicKey) throw new Error('Unknown key identifier');

  // 2. Verify ECDSA signature (GitHub uses ES256 for Copilot Extensions)
  const verify = crypto.createVerify('SHA256');
  verify.update(body);
  const valid = verify.verify(publicKey, Buffer.from(signature, 'base64'));
  if (!valid) throw new Error('Invalid signature — reject request');

  return JSON.parse(body);
}
```

### PowerShell (.NET / GitHub Actions runner)

```powershell
# GitHub Copilot Extensions use ECDSA P-256 (ES256) — asymmetric, no shared secret.
# 1. Read headers from the inbound request.
$signature  = $Request.Headers['X-GitHub-Public-Key-Signature']   # base64 DER
$keyId      = $Request.Headers['X-GitHub-Public-Key-Identifier']
$body       = $Request.Body   # raw bytes

# 2. Fetch GitHub's public keys.
$keys = (Invoke-RestMethod 'https://api.github.com/meta/public_keys/copilot_api').public_keys
$pubKeyPem = ($keys | Where-Object { $_.key_identifier -eq $keyId }).key

# 3. Verify the ECDSA P-256 signature.
$ecdsa = [System.Security.Cryptography.ECDsa]::Create()
$ecdsa.ImportFromPem($pubKeyPem)
$sigBytes  = [Convert]::FromBase64String($signature)
$bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)
$valid = $ecdsa.VerifyData($bodyBytes, $sigBytes, [System.Security.Cryptography.HashAlgorithmName]::SHA256, [System.Security.Cryptography.DSASignatureFormat]::Rfc3279DerSequence)
if (-not $valid) { throw 'Invalid ECDSA signature — reject request' }
```

---

## 6. Supported Intents

| Intent Command | Example | Action |
|----------------|---------|--------|
| `run <workflow>` | `@infinity-orchestrator run genesis-loop` | Triggers `workflow_dispatch` on named workflow |
| `health` | `@infinity-orchestrator health` | Runs health check and returns status summary |
| `memory` | `@infinity-orchestrator memory` | Returns current `ACTIVE_MEMORY.md` snapshot |
| `repos` | `@infinity-orchestrator repos` | Returns `ORG_REPO_INDEX.md` summary |
| `issue <title>` | `@infinity-orchestrator issue Fix login bug` | Creates a GitHub issue |
| `invent <topic>` | `@infinity-orchestrator invent new auth system` | Triggers autonomous invention cycle |

---

## 7. Adding New Intents

1. Add the intent to `copilot_extensions.intents` in `copilot-connector.json`.
2. Update the webhook receiver to handle the new intent and dispatch the appropriate workflow.
3. Update the table in [Section 6](#6-supported-intents) above.
4. Re-deploy the webhook receiver.

---

## 8. Secrets Reference

| Secret / Credential | Where to Set | Purpose |
|--------------------|-------------|---------|
| GitHub public keys (auto-fetched) | `https://api.github.com/meta/public_keys/copilot_api` | Verify ECDSA P-256 signatures on inbound extension events — no stored secret needed |
| `GITHUB_APP_ID` | GitHub Actions secret | Mints installation tokens for dispatching workflows |
| `GITHUB_APP_PRIVATE_KEY` | GitHub Actions secret | Signs App JWTs |

---

## 9. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `@infinity-orchestrator` not found in mobile Copilot | Extension not installed for the user/org | Follow Step 4 of this runbook |
| Signature verification failure | Wrong public key or stale key cache | Re-fetch keys from `https://api.github.com/meta/public_keys/copilot_api` |
| Webhook returns 401 / signature invalid | Stale public key cache or key rotation in progress | Re-fetch keys from `https://api.github.com/meta/public_keys/copilot_api` (cache for ≤ 5 min) |
| Workflow not triggered | Webhook receiver can't authenticate GitHub App | Verify `GITHUB_APP_ID` + `GITHUB_APP_PRIVATE_KEY` are set and the App has `actions:write` |
| Mobile shows "Extension unavailable" | Copilot Business/Enterprise plan not active | Verify org Copilot plan in **Org Settings → Copilot** |

---

## 10. Governance

- All extension webhook invocations are subject to **TAP P-001** (no secrets in logs), **P-005** (App tokens only), and **P-006** (correlation ID logging).
- Log `X-GitHub-Delivery` as the correlation ID for all inbound Copilot Extension events.
- Never log raw `Authorization` headers or payload tokens.

See `.infinity/policies/tap-protocol.md` and `.infinity/runbooks/governance-enforcement.md`.
