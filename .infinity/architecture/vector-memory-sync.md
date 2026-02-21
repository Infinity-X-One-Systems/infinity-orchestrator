# Vector Memory Sync Architecture

> **System:** Infinity Orchestrator  
> **Component:** Persistent Context & Vector Memory  
> **Version:** 1.0.0  
> **TAP Compliance:** P-001 · P-005 · P-006 · P-007

---

## Overview

The vector memory sync system provides **persistent, queryable context** to all
autonomous agents and workflows. It ensures that every run of the orchestrator
starts from an accurate, up-to-date world model — even across cold starts and
cross-repository triggers.

The system operates in three layers:

```
┌──────────────────────────────────────────────────────────────────────────┐
│  LAYER 1 — SOURCE LAYER                                                  │
│  Raw inputs: GitHub API, workflow logs, telemetry, agent outputs         │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  LAYER 2 — SYNC LAYER                                                    │
│  Normalization, chunking, embedding, deduplication, freshness checks     │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  LAYER 3 — STORE LAYER                                                   │
│  Vector index + ACTIVE_MEMORY.md snapshot + endpoint registry            │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
infinity-core-memory (upstream)
        │
        │  repository_dispatch: memory-updated
        │  (or hourly schedule fallback — P-102)
        │
        ▼
┌─────────────────────────────┐
│  memory-sync.yml            │  GitHub Actions workflow
│  Sync-MemoryToOrchestrator  │  PowerShell script (P-005: App token)
└──────────┬──────────────────┘
           │
           │  Pull .infinity/** from core-memory@main
           │  Write to workspace .infinity/
           │
           ▼
┌─────────────────────────────┐
│  scripts/rehydrate.sh       │  Bash rehydration script
│  (or Run_Memory_Script.ps1) │  Generates ACTIVE_MEMORY.md
└──────────┬──────────────────┘
           │
           ├──▶  .infinity/ACTIVE_MEMORY.md       ← flat-file snapshot
           ├──▶  .infinity/ORG_REPO_INDEX.json    ← org repository index
           └──▶  .infinity/connectors/            ← endpoint registry

           │
           │  (hourly via autonomous-discovery.yml — memory_sync job)
           ▼
┌─────────────────────────────────────────────────┐
│  Vector Store (in-process, run-scoped)           │
│                                                  │
│  1. Chunker                                      │
│     ├─ Split ACTIVE_MEMORY.md into semantic      │
│     │  paragraphs (≤512 tokens each)             │
│     └─ Include: metadata (timestamp, source,     │
│        correlation_id per P-006)                 │
│                                                  │
│  2. Embedder                                     │
│     └─ text-embedding-ada-002 (OpenAI) or        │
│        sentence-transformers (local fallback)    │
│                                                  │
│  3. Index                                        │
│     └─ FAISS flat L2 index (in-memory)           │
│        OR ChromaDB (persistent, Docker volume)   │
│                                                  │
│  4. Query Interface                              │
│     └─ discovery_agent.py, validator_agent.py,  │
│        reporter_agent.py all call:               │
│        vector_store.query(text, top_k=5)         │
└──────────┬──────────────────────────────────────┘
           │
           │  Top-K chunks injected as context
           │  into agent system prompts
           ▼
┌─────────────────────────────┐
│  Agent Layer                │
│  (stacks/agents/*.py)       │
│                             │
│  ├─ discovery_agent.py      │
│  ├─ scoring_agent.py        │
│  ├─ validator_agent.py      │
│  ├─ reporter_agent.py       │
│  ├─ sandbox_agent.py        │
│  └─ backlog_agent.py        │
└─────────────────────────────┘
```

---

## Sync Triggers

| Event | Workflow | Frequency |
|-------|----------|-----------|
| Push to `infinity-core-memory` main | `memory-sync.yml` (via `repository_dispatch`) | On every push |
| Schedule fallback | `memory-sync.yml` | Hourly (P-102) |
| Pre-simulation gate | `autonomous-discovery.yml` → `memory_sync` job | Every discovery run |
| Manual operator request | `memory-sync.yml` → `workflow_dispatch` | On demand |
| Rehydrate workflow | `rehydrate.yml` | On demand / scheduled |

---

## Freshness Contract (P-007)

```
ACTIVE_MEMORY.md age    │ Agent behaviour
────────────────────────┼──────────────────────────────────────────────
< 2 hours               │ ✅ Use as-is
2 – 6 hours             │ ⚠️ Log warning, trigger background sync, proceed
> 6 hours               │ 🚫 Block action, force sync before proceeding
Absent                  │ 🔄 Degrade gracefully — attempt GitHub-first retrieval
```

---

## Vector Store Schema

Each document stored in the vector index carries the following metadata:

```json
{
  "id": "<sha256 of content>",
  "source": "ACTIVE_MEMORY.md | ORG_REPO_INDEX.json | endpoint-registry.json | tap-report.json",
  "section": "<heading or key path>",
  "timestamp": "<ISO-8601>",
  "correlation_id": "<uuid v4>",
  "run_id": "<github_run_id>",
  "embedding_model": "text-embedding-ada-002 | sentence-transformers/all-MiniLM-L6-v2",
  "token_count": 256,
  "content": "<raw text chunk>"
}
```

---

## Persistence Strategy

| Store | Backend | Scope | Mount |
|-------|---------|-------|-------|
| In-process (CI runs) | FAISS flat L2 (RAM) | Single workflow run | None |
| Persistent (Docker) | ChromaDB | Cross-run, local Docker | `docker volume: infinity-vector-db` |
| Snapshot export | JSON lines (`.infinity/vector-snapshots/`) | Git-committed | `.infinity/vector-snapshots/*.jsonl` |

The persistent ChromaDB store is defined in `docker-compose.singularity.yml`
(service: `vector-store`) and is available to local agent development.

---

## Security Notes (TAP)

- **P-001**: No API keys or tokens are embedded in vector documents or metadata.
- **P-005**: Sync from `infinity-core-memory` uses GitHub App installation tokens
  (minted by `Sync-MemoryToOrchestrator.ps1`) — never user PATs.
- **P-006**: Every embedding and query call must include `X-Infinity-Correlation-ID`
  in the HTTP request header (enforced by the agent base class).
- **P-008**: The ChromaDB Docker volume is mounted read-write only within the
  `vector-store` service; all other services mount it read-only.

---

## Related Files

| File | Purpose |
|------|---------|
| `.infinity/ACTIVE_MEMORY.md` | Primary memory snapshot consumed by all agents |
| `.infinity/connectors/endpoint-registry.json` | Canonical endpoint registry for vector queries |
| `scripts/rehydrate.sh` | Bash rehydration → generates ACTIVE_MEMORY.md |
| `Run_Memory_Script.ps1` | PowerShell rehydration (Windows / CI) |
| `.infinity/scripts/Sync-MemoryToOrchestrator.ps1` | Cross-repo memory pull via App token |
| `.github/workflows/memory-sync.yml` | Automated memory sync workflow |
| `.github/workflows/rehydrate.yml` | ACTIVE_MEMORY.md auto-regeneration |
| `.infinity/monitoring/telemetry-dashboard.yml` | Dashboard consuming vector store metrics |
| `stacks/agents/discovery_agent.py` | Agent that queries vector store for context |
| `stacks/agents/validator_agent.py` | TAP validation agent with vector context |
| `docker-compose.singularity.yml` | Defines the persistent ChromaDB vector-store service |

---

*Infinity Orchestrator · Vector Memory Sync Architecture v1.0.0 · Infinity-X-One-Systems*
