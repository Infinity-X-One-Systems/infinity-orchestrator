# Infinity Invention Machine — End-to-End Architecture

> **Org:** Infinity-X-One-Systems  
> **Version:** 1.0.0  
> **Governance:** TAP Protocol (Policy > Authority > Truth)  
> **Status:** Foundation / Control-Plane Phase

---

## 1. Overview

The **Infinity Invention Machine** is an autonomous, multi-agent pipeline that takes a raw idea from
discovery all the way through to a packaged, deployable "system-in-a-box" product. It operates
under continuous human oversight gates at every irreversible decision boundary.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     INFINITY INVENTION MACHINE                           │
│                                                                          │
│  [Idea Discovery] → [Spec + Docs] → [Code Gen] → [Validation] →         │
│  [Packaging] → [Governance Gate] → [Finished Systems Repo]              │
│                                                                          │
│  ← human oversight gates at every ↑ irreversible boundary →             │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Pipeline Stages

### 2.1 Idea Discovery — Vision Cortex

**Goal:** Surface high-value invention candidates from diverse signal sources.

**Inputs:**
- Multi-agent async web scraper (shadow asyncio workers)
- GitHub trending repositories and issue signals
- Org-internal idea issues (`[IDEA]` label)
- Human-submitted concepts via GitHub Issues (Idea template)

**Outputs:**
- Structured idea record committed to `.infinity/ideas/` as JSON + Markdown
- Idea issue created / updated on the control-plane board
- Vision score (novelty × feasibility × market signal)

**Agents:**
- `VisionCortexAgent` — scoring and deduplication
- `ScraperAgent` — shadow asyncio HTTP workers (rate-limited, robots-respectful)
- `IdeaTriageAgent` — routing to the spec pipeline or parking lot

**TAP checks:** P-001 (no PII in logs), P-006 (endpoint call audit trail).

---

### 2.2 Spec + Documentation Generation

**Goal:** Convert a raw idea into a machine-readable specification and human-readable design doc.

**Inputs:** Idea record from Stage 1

**Outputs:**
- `spec.json` — structured specification (title, goals, constraints, tech stack, acceptance criteria)
- `design.md` — human-readable design document
- Architecture diagram stub (Mermaid)

**Agents:**
- `SpecAgent` — LLM-backed spec writer with structured output schema
- `DiagramAgent` — Mermaid diagram generator

**Human gate:** Spec review issue opened; pipeline pauses until a human approves or requests changes.

---

### 2.3 Code Generation + Review Gates

**Goal:** Generate initial implementation from the approved spec.

**Inputs:** Approved `spec.json` + `design.md`

**Outputs:**
- Feature branch with generated scaffold code
- Pull request opened against `main` of the target system repo
- Automated review annotations (lint, type-check, security scan)

**Agents:**
- `GenesisAgent` — code scaffolding and file generation
- `ReviewGateAgent` — automated PR annotations and gate checks

**Gates (all must pass before merge):**
1. Linting / style checks
2. Type-checking
3. Security scan (CodeQL / Semgrep)
4. Unit test coverage threshold
5. Human PR approval (CODEOWNERS)

**TAP checks:** P-003 (bot attribution), P-004 (no force-push to protected branch).

---

### 2.4 Universal Validation — Frontend + Backend

**Goal:** Verify the generated system works end-to-end in a clean environment.

**Inputs:** Merged feature code

**Outputs:**
- Test report artifact
- Validation badge in the system repo README
- Validation record in `.infinity/validation-log.json`

**Validation suites:**
- Backend: unit tests, integration tests, contract tests
- Frontend: Playwright E2E tests, accessibility scan (axe-core)
- API: schema validation against OpenAPI spec
- Performance: p95 latency budget check

**Agents:**
- `ValidationOrchestrator` — parallel test runner
- `PlaywrightAgent` — headless browser E2E suite

---

### 2.5 Packaging — System-in-a-Box

**Goal:** Bundle the validated system into a self-contained, runnable artefact.

**Inputs:** Validated, merged code

**Outputs:**
- Docker image tagged `{org}/{system}:{semver}`
- `docker-compose.yml` + `.env.template`
- `QUICKSTART.md` with one-command bootstrap instructions
- GitHub Release with attached artefacts

**Agents:**
- `PackagingAgent` — Dockerfile generator and compose assembler
- `ReleaseAgent` — GitHub Release creator

**TAP checks:** P-008 (Docker socket access must be read-only unless justified).

---

### 2.6 Governance — TAP Protocol

All autonomous actions are subject to the **TAP Protocol** (Policy > Authority > Truth):

| Layer | Enforcement Point |
|-------|------------------|
| **Policy** | Immutable guardrails P-001 → P-008; configurable P-101 → P-104 |
| **Authority** | GitHub App installation token; CODEOWNERS for human gates |
| **Truth** | `.infinity/ACTIVE_MEMORY.md`; `ORG_REPO_INDEX.json`; `endpoint-registry.json` |

Every policy-relevant decision is logged to:
1. `$GITHUB_STEP_SUMMARY` (workflow run)
2. Workflow annotations (`::notice::` / `::warning::` / `::error::`)
3. `.infinity/audit-log.jsonl` (append-only)

Full policy text: [`.infinity/policies/tap-protocol.md`](../../.infinity/policies/tap-protocol.md)

---

### 2.7 Human Oversight Gates

The pipeline contains **four mandatory human gates** that cannot be bypassed by any automated actor:

| Gate | Trigger | Action Required |
|------|---------|----------------|
| **G-1 Spec Approval** | Spec generation complete | Human reviews and approves spec issue |
| **G-2 PR Review** | Generated code PR opened | CODEOWNERS approval required to merge |
| **G-3 Release Sign-off** | Packaging complete | Human triggers release workflow |
| **G-4 Org Publish** | Release created | Human approves publishing to finished systems repo |

---

## 3. Control-Plane Overview

The **control plane** consists of:

| Component | Location | Purpose |
|-----------|----------|---------|
| GitHub Project (v2) | Org-level Projects | Single pane of glass for all repos, PRs, ideas, pipeline state |
| Portfolio Audit Workflow | `.github/workflows/portfolio-audit.yml` | Periodic inventory of all org + user repos |
| Org Repo Index | `.infinity/ORG_REPO_INDEX.json` | Machine-readable org repo manifest |
| Idea Registry | `.infinity/ideas/` | Structured idea records |
| Audit Log | `.infinity/audit-log.jsonl` | Append-only governance decision log |
| Memory State | `.infinity/ACTIVE_MEMORY.md` | Current system snapshot for agent rehydration |

See [`github-project-control-plane.md`](./github-project-control-plane.md) for the GitHub Projects v2 board specification.

---

## 4. Repository Topology

```
Infinity-X-One-Systems/
├── infinity-orchestrator      ← this repo; control plane + agent runtime
├── infinity-core-memory       ← shared memory / ACTIVE_MEMORY source of truth
└── [future system repos]      ← one repo per finished "system-in-a-box" product
```

The `infinity-orchestrator` repo is the **only** repo that orchestrates cross-repository operations.
All other repos are orchestrated, never orchestrators themselves (P-005).

---

## 5. Technology Stack

| Layer | Technology |
|-------|-----------|
| Orchestration | GitHub Actions, GitHub Apps, GitHub Projects v2 |
| Agent Runtime | Python 3.12+, asyncio, LangChain / custom agent loop |
| Memory | Vector store (Chroma/FAISS), Markdown flat-files, JSON manifests |
| Code Generation | LLM API (OpenAI / GitHub Copilot), Jinja2 templates |
| Validation | pytest, Playwright, CodeQL, Semgrep |
| Packaging | Docker, docker-compose, GitHub Releases |
| Governance | TAP Protocol, CODEOWNERS, branch protection, required status checks |

---

## 6. Roadmap

| Phase | Milestone | Status |
|-------|-----------|--------|
| 0 — Foundation | Control-plane docs, portfolio audit workflow, governance templates | ✅ In progress |
| 1 — Idea Pipeline | VisionCortexAgent, ScraperAgent, idea registry | 🔲 Planned |
| 2 — Spec Pipeline | SpecAgent, DiagramAgent, spec review gate | 🔲 Planned |
| 3 — Code Gen | GenesisAgent v2, ReviewGateAgent, full PR automation | 🔲 Planned |
| 4 — Validation | Universal validation suite, Playwright E2E | 🔲 Planned |
| 5 — Packaging | PackagingAgent, ReleaseAgent, system-in-a-box delivery | 🔲 Planned |

---

*Infinity Orchestrator · Architecture v1.0.0 · Infinity-X-One-Systems*
