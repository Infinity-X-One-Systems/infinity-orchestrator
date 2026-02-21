# Shadow Headless Browser REST API Specification

> **Service:** `infinity-browserless` / shadow-headless-api  
> **Base URL:** `http://localhost:3000` (local) or `http://browserless:3000` (Docker mesh)  
> **Docker image:** `browserless/chrome:latest`  
> **Version:** 1.0.0  
> **TAP compliance:** P-001 · P-006 · P-008

---

## Overview

The Shadow Headless Browser API provides programmatic control over a stealth
Chromium instance for discovery, scraping, and site-interaction tasks.
It runs inside the `singularity-mesh` Docker network and is accessible to
all agents that need to interact with web pages.

**Security note**: The browserless service is on the `vision-isolated` internal
Docker network. It must never be exposed to the public internet without
Cloudflare Zero Trust protection.

---

## Authentication

All requests require the `BROWSERLESS_API_TOKEN` header when
`ENABLE_DEBUGGER=false` (production mode):

```
Authorization: Bearer {BROWSERLESS_API_TOKEN}
```

Set `BROWSERLESS_API_TOKEN` as a Docker environment variable or GitHub Actions secret.

---

## Endpoints

### `GET /pressure`
**Purpose**: Health and capacity check.  
**Response**:
```json
{
  "date": 1708000000000,
  "isAvailable": true,
  "queued": 0,
  "recentlyRejected": 0,
  "running": 2,
  "maxConcurrent": 10,
  "maxQueued": 50,
  "cpu": 0.12,
  "memory": 0.34
}
```

---

### `POST /content`
**Purpose**: Render a page and return the full HTML content after JavaScript execution.

**Request body**:
```json
{
  "url": "https://example.com",
  "waitFor": 2000,
  "stealth": true,
  "userAgent": "Mozilla/5.0 ...",
  "viewport": { "width": 1280, "height": 800 },
  "gotoOptions": {
    "waitUntil": "networkidle2",
    "timeout": 30000
  }
}
```

**Response**: `text/html` — full rendered page content.

---

### `POST /screenshot`
**Purpose**: Capture a screenshot of a rendered page.

**Request body**:
```json
{
  "url": "https://example.com",
  "options": {
    "type": "png",
    "fullPage": true,
    "encoding": "base64"
  },
  "stealth": true,
  "waitFor": 1000
}
```

**Response**: `image/png` binary or base64-encoded string (per `encoding` option).

---

### `POST /pdf`
**Purpose**: Render a page as a PDF document.

**Request body**:
```json
{
  "url": "https://example.com",
  "options": {
    "format": "A4",
    "printBackground": true,
    "margin": { "top": "1cm", "bottom": "1cm", "left": "1cm", "right": "1cm" }
  }
}
```

**Response**: `application/pdf` binary.

---

### `POST /function`
**Purpose**: Execute arbitrary JavaScript in an incognito browser context.
This is the primary endpoint used by `stacks/agents/sandbox_agent.py`.

**Request body**:
```json
{
  "code": "module.exports = async ({ page, context }) => { await page.goto(context.url); return { title: await page.title() }; }",
  "context": { "url": "https://example.com" },
  "incognito": true,
  "stealth": true
}
```

**Response**:
```json
{
  "data": { "title": "Example Domain" },
  "type": "application/json"
}
```

**Use cases in Infinity agents**:
- `discovery_agent.py` — extract structured data from target pages
- `sandbox_agent.py` — execute sandboxed browser automation tasks
- Persona engine — simulate user journeys for testing

---

### `GET /json`
**Purpose**: List all active Chrome DevTools Protocol sessions (WebSocket targets).

**Response**:
```json
[
  {
    "description": "",
    "id": "abc123",
    "title": "Example Domain",
    "type": "page",
    "url": "https://example.com",
    "webSocketDebuggerUrl": "ws://localhost:3000/devtools/page/abc123"
  }
]
```

---

### WebSocket: `/` (Playwright / Puppeteer connect)
**Purpose**: WebSocket endpoint for Playwright or Puppeteer to connect and control Chrome remotely.

```javascript
// Playwright
const browser = await chromium.connect({
  wsEndpoint: 'ws://localhost:3000',
});
```

```python
# Playwright Python
from playwright.async_api import async_playwright
async with async_playwright() as p:
    browser = await p.chromium.connect_over_cdp("ws://localhost:3000")
```

---

## Integration with Infinity Agents

### Python helper (used in `sandbox_agent.py`)

```python
import json, urllib.request, os

BROWSERLESS_URL = os.environ.get("BROWSERLESS_URL", "http://localhost:3000")

def render_page(url: str) -> str:
    """Render a URL and return the full HTML content."""
    payload = json.dumps({
        "url": url,
        "stealth": True,
        "waitFor": 2000,
        "gotoOptions": {"waitUntil": "networkidle2", "timeout": 30000},
    }).encode()
    req = urllib.request.Request(
        f"{BROWSERLESS_URL}/content",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=35) as resp:
        return resp.read().decode("utf-8", errors="replace")


def execute_function(code: str, context: dict) -> dict:
    """Execute JavaScript in an incognito browser context."""
    payload = json.dumps({
        "code": code,
        "context": context,
        "incognito": True,
        "stealth": True,
    }).encode()
    req = urllib.request.Request(
        f"{BROWSERLESS_URL}/function",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())
```

---

## Stealth Configuration

The browserless service is configured with stealth defaults in
`docker-compose.singularity.yml`:

| Setting | Value | Purpose |
|---------|-------|---------|
| `DEFAULT_STEALTH` | `true` | Applies `puppeteer-extra-plugin-stealth` |
| `DEFAULT_BLOCK_ADS` | `true` | Reduces noise and improves page load speed |
| `FUNCTION_ENABLE_INCOGNITO_MODE` | `true` | Isolates sessions |
| `MAX_CONCURRENT_SESSIONS` | 10 | Limits resource usage |
| `CONNECTION_TIMEOUT` | 600000 ms | 10-minute session timeout |
| `shm_size` | 2gb | Prevents Chrome crashes under memory pressure |

---

## Related Files

| File | Purpose |
|------|---------|
| `docker-compose.singularity.yml` | `browserless` service definition |
| `stacks/agents/sandbox_agent.py` | Python agent using the browser API |
| `.infinity/connectors/endpoint-registry.json` | Registered as `shadow-browser-*` endpoints |
| `stacks/vision/stealth_config.py` | Playwright stealth configuration for vision cortex |

---

*Infinity Orchestrator · Shadow Headless Browser API Spec v1.0.0 · Infinity-X-One-Systems*
