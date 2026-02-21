# Coder Standards — Infinity Orchestrator

> **Org:** Infinity-X-One-Systems  
> **Scope:** All code produced within or by the `infinity-orchestrator` system.  
> **Version:** 1.0.0  
> **Stack:** Python 3.11+ · GitHub Actions · Docker · Bash

---

## 1. Python Standards

### 1.1 File Structure
```
module/
├── __init__.py      # Public API exports only
├── module.py        # Implementation
└── tests/
    ├── __init__.py
    ├── test_module.py        # Unit tests
    └── test_module_integration.py  # Integration tests
```

### 1.2 Code Style
- **Formatter**: `black` (line length 100).
- **Linter**: `pylint` (minimum score 8.0), `flake8` (max line length 120).
- **Import order**: `isort` — stdlib → third-party → local.
- **Type hints**: required on all public function signatures.
- **Docstrings**: Google-style for all public classes, functions, and modules.

### 1.3 Defensive Patterns
```python
# ✅ Always use set -euo pipefail equivalent in Python
from __future__ import annotations

# ✅ Explicit exception handling with helpful messages
try:
    result = do_thing()
except requests.Timeout as exc:
    raise RuntimeError(f"Timeout calling {url}: {exc}") from exc

# ✅ No bare except
# ❌ except: pass

# ✅ Graceful degradation (P-007) — return empty/default, log warning
def load_memory() -> dict:
    if not path.exists():
        print("[warn] memory absent — degrading gracefully (P-007)")
        return {}
    ...
```

### 1.4 Security Rules
- **Never** hard-code secrets. Read from `os.environ` only.
- **Never** log secret values. Use `::add-mask::` in GitHub Actions.
- Use `hashlib.sha256` (not sha1) for security-sensitive hashing.
- Sanitize all inputs from external APIs before persisting.

### 1.5 Agent Conventions
- All agents inherit from `stacks.agents.base_agent.BaseAgent`.
- Call `self.rehydrate(task)` at the start of every `run()` method.
- Call `self.tap_preflight(action=task)` before any mutation.
- Call `self.log_decision(...)` after every autonomous decision.
- Write `main()` entrypoints with `argparse` for CLI use.

---

## 2. GitHub Actions Standards

### 2.1 Action Versions
- Use `actions/checkout@v6` (current org standard).
- Use `actions/upload-artifact@v4` and `actions/download-artifact@v4`.
- Use `actions/setup-python@v5`.
- Pin third-party actions to a specific SHA for security-sensitive workflows.

### 2.2 Permissions
- Declare the minimum required `permissions` block on every workflow.
- Never use `permissions: write-all`.
- Workflows that push commits need `contents: write`.
- Workflows that trigger other workflows need `actions: write`.

### 2.3 Secrets
- Never print secret values in `run:` blocks.
- Use `continue-on-error: true` on steps that require optional secrets (P-007).
- Document all required secrets in `.env.template` and `connectors-index.md`.

### 2.4 Output Handling
- Use `$GITHUB_OUTPUT` (not deprecated `::set-output`).
- Use `$GITHUB_STEP_SUMMARY` for human-readable job summaries.

### 2.5 Bot Attribution (P-003)
```yaml
- name: Configure git
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
```

---

## 3. Docker Standards

### 3.1 Image Tags
- Pin base images to specific version tags (`python:3.11-slim`, not `python:latest`).
- Use `alpine` variants where possible to reduce image size.
- Add `LABEL` metadata: `maintainer`, `version`, `description`.

### 3.2 Security
- Run containers as non-root where possible (`USER app`).
- Mount Docker socket as read-only unless write access is justified in PR (`P-008`).
- Never bake secrets into images; inject via environment variables at runtime.

### 3.3 Health Checks
Every service must define a `healthcheck` in `docker-compose.singularity.yml`.

---

## 4. Bash Script Standards

```bash
#!/usr/bin/env bash
set -euo pipefail  # required on all scripts

# Color constants
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
```

- All scripts must start with `set -euo pipefail`.
- Use `log_info`, `log_warn`, `log_error` helper functions.
- Scripts must be idempotent (safe to run multiple times).
- Add a `--help` flag or comment block describing usage.

---

## 5. Naming Conventions

| Entity | Convention | Example |
|--------|-----------|---------|
| Python module | `snake_case` | `vector_store.py` |
| Python class | `PascalCase` | `VectorStore` |
| Python constant | `UPPER_SNAKE` | `_DEFAULT_STORE_PATH` |
| GitHub Actions job | `snake_case` | `lint_and_scan` |
| Docker service | `kebab-case` | `knowledge-base` |
| Workflow file | `kebab-case.yml` | `memory-sync.yml` |
| Branch | `type/description` | `autonomous/update-123` |
| Commit message | `type(scope): description` | `feat(memory): add vector store` |

---

## 6. Commit Message Format

```
<type>(<scope>): <short description>

[optional body]
[optional footer: TAP-DECISION, closes #N]
```

Types: `feat` · `fix` · `chore` · `docs` · `refactor` · `test` · `perf` · `ci`

Example:
```
feat(memory): add vector store with TF-IDF and Ollama embedding backends

Implements VectorStore (JSON-backed) and rehydration engine.
Supports tfidf / openai / ollama embedding backends selectable via
INFINITY_EMBED_BACKEND.

TAP-DECISION: policy=tap protocol=110 result=allowed
Closes #42
```

---

*Infinity Orchestrator · Coder Standards v1.0.0 · Infinity-X-One-Systems*
