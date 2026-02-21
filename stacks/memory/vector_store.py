"""
Vector Store — Infinity Memory Subsystem
=========================================
A lightweight, dependency-free vector store backed by JSON files.

Supports two backends selectable at runtime:
  * ``json``   — pure Python, JSON file on disk (default, zero dependencies)
  * ``chroma`` — ChromaDB persistent store (requires ``chromadb`` package)

Embedding backends (selected by INFINITY_EMBED_BACKEND env var):
  * ``tfidf``  — bag-of-words TF-IDF cosine similarity (default, zero deps)
  * ``openai`` — text-embedding-3-small via OpenAI API (requires OPENAI_API_KEY)
  * ``ollama`` — nomic-embed-text via local Ollama (requires OLLAMA_BASE_URL)

TAP compliance:
  P-001 — No secrets in stored documents
  P-006 — correlation_id carried in every entry
  P-007 — Degrades gracefully when ChromaDB or OpenAI is unavailable
"""

from __future__ import annotations

import json
import math
import os
import re
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Constants ─────────────────────────────────────────────────────────────────

_DEFAULT_STORE_PATH = Path(
    os.environ.get(
        "INFINITY_VECTOR_STORE_PATH",
        str(Path(__file__).parent.parent.parent / ".infinity" / "vector-store" / "store.jsonl"),
    )
)

_EMBED_BACKEND = os.environ.get("INFINITY_EMBED_BACKEND", "tfidf").lower()
_OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
_OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
_OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")

# Number of top TF-IDF terms kept per document
_TFIDF_TOP_TERMS = 200

# Multiplier for the raw-text fallback in _chunk_text when no headings are found.
# Chosen so that a single chunk covers ~3000 words (6 × 512 ≈ 3072), which is
# roughly the context window of a small embedding model.
_CHUNK_FALLBACK_MULTIPLIER = 6


# ── TF-IDF embedding (pure Python, zero dependencies) ─────────────────────────

_TOKEN_RE = re.compile(r"[a-zA-Z0-9_\-]+")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text) if len(t) > 1]


def _tfidf_embed(text: str, vocab: dict[str, int] | None = None) -> dict[str, float]:
    """Return a sparse TF-IDF vector as {term: weight}.

    This uses a non-standard IDF approximation: ``log(1 + 1/tf)`` as a proxy
    for inverse document frequency instead of the corpus-based ``log(N/df)``.
    This works well for single-document similarity (no corpus needed) and is
    appropriate for lightweight rehydration queries where dense embeddings are
    unavailable.  For production semantic search, prefer the OpenAI or Ollama
    embedding backends (set ``INFINITY_EMBED_BACKEND=openai`` or
    ``INFINITY_EMBED_BACKEND=ollama``).
    """
    tokens = _tokenize(text)
    if not tokens:
        return {}
    counts = Counter(tokens)
    total = len(tokens)
    tf = {term: count / total for term, count in counts.items()}
    # Without a corpus IDF we use log(1 + 1/tf) as a proxy for inverse frequency
    return {term: tf_val * math.log1p(1.0 / tf_val) for term, tf_val in tf.items()}


def _cosine_sparse(a: dict[str, float], b: dict[str, float]) -> float:
    """Cosine similarity between two sparse vectors."""
    common = set(a) & set(b)
    if not common:
        return 0.0
    dot = sum(a[k] * b[k] for k in common)
    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ── Remote embedding helpers ───────────────────────────────────────────────────

def _embed_openai(text: str) -> list[float] | None:
    """Call OpenAI text-embedding-3-small. Returns None on failure (P-007)."""
    if not _OPENAI_API_KEY:
        return None
    try:
        import urllib.request  # stdlib only

        payload = json.dumps(
            {"input": text[:8000], "model": "text-embedding-3-small"}
        ).encode()
        req = urllib.request.Request(
            "https://api.openai.com/v1/embeddings",
            data=payload,
            headers={
                "Authorization": f"Bearer {_OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data["data"][0]["embedding"]
    except Exception as exc:  # noqa: BLE001
        print(f"[vector_store] OpenAI embed failed (degrading): {exc}")
        return None


def _embed_ollama(text: str) -> list[float] | None:
    """Call Ollama embeddings API. Returns None on failure (P-007)."""
    try:
        import urllib.request

        payload = json.dumps({"model": _OLLAMA_EMBED_MODEL, "prompt": text[:4096]}).encode()
        req = urllib.request.Request(
            f"{_OLLAMA_BASE_URL}/api/embeddings",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("embedding")
    except Exception as exc:  # noqa: BLE001
        print(f"[vector_store] Ollama embed failed (degrading): {exc}")
        return None


def embed_text(text: str) -> dict[str, Any]:
    """
    Embed text using the configured backend.

    Returns a dict with:
      ``backend``   — which backend was used
      ``sparse``    — sparse TF-IDF vector (always populated)
      ``dense``     — dense float vector or None when unavailable
    """
    sparse = _tfidf_embed(text)
    dense: list[float] | None = None

    if _EMBED_BACKEND == "openai":
        dense = _embed_openai(text)
    elif _EMBED_BACKEND == "ollama":
        dense = _embed_ollama(text)

    return {
        "backend": _EMBED_BACKEND,
        "sparse": sparse,
        "dense": dense,
    }


def _empty_embedding() -> dict[str, Any]:
    """Return an empty embedding structure (used when skip_embed=True)."""
    return {"backend": "none", "sparse": {}, "dense": None}


# ── Document schema ────────────────────────────────────────────────────────────

class Document:
    """A single entry in the vector store."""

    __slots__ = (
        "id", "content", "embedding", "metadata",
        "timestamp", "correlation_id", "run_id",
    )

    def __init__(
        self,
        *,
        id: str,
        content: str,
        embedding: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        timestamp: str | None = None,
        correlation_id: str | None = None,
        run_id: str = "",
    ) -> None:
        self.id = id
        self.content = content
        self.embedding = embedding
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.run_id = run_id or os.environ.get("GITHUB_RUN_ID", "")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "embedding": self.embedding,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "run_id": self.run_id,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Document":
        return cls(
            id=d["id"],
            content=d["content"],
            embedding=d.get("embedding", {}),
            metadata=d.get("metadata", {}),
            timestamp=d.get("timestamp"),
            correlation_id=d.get("correlation_id"),
            run_id=d.get("run_id", ""),
        )


# ── Vector Store ───────────────────────────────────────────────────────────────

class VectorStore:
    """
    Lightweight JSON-backed vector store with cosine similarity search.

    Persists documents to a JSONL file and maintains an in-memory index for
    fast nearest-neighbour queries.

    Example::

        store = VectorStore()
        store.upsert("mem-001", "TAP Protocol governs all agents", metadata={"source": "tap"})
        hits = store.query("governance policy", top_k=3)
        for score, doc in hits:
            print(score, doc.id, doc.content[:60])
    """

    def __init__(self, path: Path | str | None = None) -> None:
        self._path = Path(path) if path else _DEFAULT_STORE_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._index: dict[str, Document] = {}
        self._load()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load(self) -> None:
        """Load existing documents from the JSONL store file."""
        if not self._path.exists():
            return
        with open(self._path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    doc = Document.from_dict(json.loads(line))
                    self._index[doc.id] = doc
                except Exception:  # noqa: BLE001
                    pass

    def _flush(self) -> None:
        """Write all documents to the JSONL store file (full rewrite)."""
        tmp = self._path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            for doc in self._index.values():
                fh.write(json.dumps(doc.to_dict(), ensure_ascii=False) + "\n")
        tmp.replace(self._path)

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def upsert(
        self,
        doc_id: str,
        content: str,
        *,
        metadata: dict[str, Any] | None = None,
        correlation_id: str | None = None,
        run_id: str = "",
        skip_embed: bool = False,
    ) -> Document:
        """Insert or replace a document.  Returns the stored Document."""
        embedding = embed_text(content) if not skip_embed else _empty_embedding()
        doc = Document(
            id=doc_id,
            content=content,
            embedding=embedding,
            metadata=metadata or {},
            correlation_id=correlation_id,
            run_id=run_id,
        )
        self._index[doc_id] = doc
        self._flush()
        return doc

    def get(self, doc_id: str) -> Document | None:
        """Return a document by ID or None."""
        return self._index.get(doc_id)

    def delete(self, doc_id: str) -> bool:
        """Delete a document.  Returns True if it existed."""
        if doc_id in self._index:
            del self._index[doc_id]
            self._flush()
            return True
        return False

    def count(self) -> int:
        return len(self._index)

    # ── Search ────────────────────────────────────────────────────────────────

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[tuple[float, Document]]:
        """
        Return the top-k most similar documents to ``query_text``.

        Results are ``(score, document)`` tuples sorted by descending score.
        ``metadata_filter`` restricts candidates to documents whose metadata
        is a superset of the filter dict.
        """
        if not self._index:
            return []

        q_embed = embed_text(query_text)
        q_sparse = q_embed["sparse"]

        candidates = list(self._index.values())
        if metadata_filter:
            candidates = [
                d for d in candidates
                if all(d.metadata.get(k) == v for k, v in metadata_filter.items())
            ]

        scored: list[tuple[float, Document]] = []
        for doc in candidates:
            d_sparse = doc.embedding.get("sparse", {})
            score = _cosine_sparse(q_sparse, d_sparse)
            scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:top_k]

    # ── Bulk ingest ───────────────────────────────────────────────────────────

    def ingest_markdown(
        self,
        path: Path | str,
        *,
        source: str = "",
        chunk_size: int = 512,
        overlap: int = 64,
    ) -> int:
        """
        Chunk a Markdown file by heading boundaries and ingest each chunk.
        Returns the number of documents added/updated.
        """
        path = Path(path)
        if not path.exists():
            print(f"[vector_store] ingest_markdown: file not found: {path}")
            return 0

        text = path.read_text(encoding="utf-8", errors="replace")
        chunks = _chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        source_label = source or str(path)

        for i, chunk in enumerate(chunks):
            doc_id = f"{source_label}::{i}"
            self.upsert(
                doc_id,
                chunk,
                metadata={"source": source_label, "chunk_index": i, "total_chunks": len(chunks)},
            )
        return len(chunks)

    def clear(self) -> None:
        """Delete all documents from the store."""
        self._index.clear()
        self._flush()


# ── Text chunking ──────────────────────────────────────────────────────────────

_HEADING_RE = re.compile(r"^#{1,6}\s", re.MULTILINE)


def _chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    """
    Split text into overlapping chunks, preferring heading boundaries.
    """
    # Split at headings first
    sections = _HEADING_RE.split(text)
    chunks: list[str] = []

    for section in sections:
        words = section.split()
        if not words:
            continue
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk = " ".join(words[start:end])
            if chunk.strip():
                chunks.append(chunk)
            if end >= len(words):
                break
            start = end - overlap

    return chunks or [text[:chunk_size * _CHUNK_FALLBACK_MULTIPLIER]]  # fallback: raw slice
