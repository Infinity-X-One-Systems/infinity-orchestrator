"""
Infinity Memory Subsystem
=========================
Provides vector store, rehydration, and embedding utilities for all agents.

Usage::

    from stacks.memory import VectorStore, rehydrate, embed_text

    # In-process JSON-backed store
    store = VectorStore()
    store.upsert("doc-1", "My content here", metadata={"source": "ACTIVE_MEMORY.md"})
    results = store.query("autonomous agents", top_k=5)

    # Rehydrate context for an agent
    context = rehydrate("generate discovery plan", top_k=10)
"""

from stacks.memory.vector_store import VectorStore
from stacks.memory.rehydration import rehydrate, build_context_prompt

__all__ = ["VectorStore", "rehydrate", "build_context_prompt"]
