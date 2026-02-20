# Endpoint Registry Runbook

Operational guidance for managing the governed endpoint registry that tracks
every API surface used by the Infinity Orchestrator system.

---

## Overview

The endpoint registry lives at:

```
.infinity/connectors/
├── endpoint-registry.json   ← machine-readable registry
├── endpoint-registry.md     ← format documentation
└── auth-matrix.md           ← authentication requirements
```

All API endpoints used by agents, workflows, and scripts **must** be
registered in `endpoint-registry.json` before being called in production.

---

## Adding a New Endpoint

1. **Open a PR** that adds a new entry to `endpoint-registry.json`.

   Minimum required fields:

   ```json
   {
     "id":          "my-new-service",
     "name":        "My New Service",
     "description": "What it does and why we need it.",
     "base_url":    "https://api.example.com",
     "auth_method": "github_app",
     "governed":    true,
     "tags":        ["category"]
   }
   ```

2. **Update `auth-matrix.md`** with the auth requirements for the new
   endpoint.

3. **Update the Registered Endpoints table** in `endpoint-registry.md`.

4. **Get codeowner approval** before merging.

---

## Removing or Deprecating an Endpoint

1. Set `"governed": false` and add a `"deprecated_at"` field with an ISO 8601
   timestamp.
2. Open a tracking issue to remove all callers.
3. Remove the entry in a follow-up PR once all callers have been migrated.

---

## Validating the Registry

Run the following from the repository root to confirm the registry is valid
JSON and contains no ungoverned endpoints:

```bash
# Validate JSON
jq empty .infinity/connectors/endpoint-registry.json && echo "Valid JSON"

# Check all endpoints are governed
UNGOVERNED=$(jq '[.endpoints[] | select(.governed != true) | .id] | length' \
  .infinity/connectors/endpoint-registry.json)
if [ "$UNGOVERNED" -gt 0 ]; then
  echo "ERROR: $UNGOVERNED ungoverned endpoint(s) found"
  jq '[.endpoints[] | select(.governed != true) | .id]' \
    .infinity/connectors/endpoint-registry.json
  exit 1
fi
echo "All endpoints are governed"
```

---

## Governance Policy Summary

* No long-lived PATs in workflows (see [auth-matrix.md](../connectors/auth-matrix.md)).
* All machine-to-machine calls use GitHub App tokens or the Actions built-in
  `GITHUB_TOKEN`.
* Tokens are masked with `::add-mask::` immediately after creation.
* Tokens are never passed as command-line arguments.

---

## Related Files

| File | Purpose |
|------|---------|
| [`../connectors/endpoint-registry.json`](../connectors/endpoint-registry.json) | Registry data |
| [`../connectors/endpoint-registry.md`](../connectors/endpoint-registry.md) | Registry format docs |
| [`../connectors/auth-matrix.md`](../connectors/auth-matrix.md) | Auth requirements |
| [`agent-bootstrap.md`](agent-bootstrap.md) | Agent bootstrap runbook |
| [`memory-sync.md`](memory-sync.md) | Memory sync runbook |
