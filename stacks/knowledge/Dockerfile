# ═══════════════════════════════════════════════════════════════════════════
# KNOWLEDGE BASE - ChromaDB Vector Store
# ═══════════════════════════════════════════════════════════════════════════
# The Eternal Memory - Persistent vector database for the Singularity Mesh
# ═══════════════════════════════════════════════════════════════════════════

FROM python:3.11-slim

# Build arguments
ARG CHROMA_VERSION=0.4.22

# Metadata
LABEL maintainer="Infinity X One Systems"
LABEL description="ChromaDB Vector Store - Knowledge Base"
LABEL version="1.0.0"

# Environment setup
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install ChromaDB
RUN pip install --no-cache-dir \
    chromadb==${CHROMA_VERSION} \
    chromadb[server] \
    fastapi \
    uvicorn[standard] \
    pydantic

# Create data directory
RUN mkdir -p /chroma/chroma && \
    chmod -R 755 /chroma

# Health check script
COPY <<'EOF' /usr/local/bin/healthcheck.sh
#!/bin/sh
curl -f http://localhost:8000/api/v1/heartbeat || exit 1
EOF

RUN chmod +x /usr/local/bin/healthcheck.sh

# Set working directory
WORKDIR /chroma

# Expose port
EXPOSE 8000

# Set user for security
RUN useradd -m -u 1000 chroma && \
    chown -R chroma:chroma /chroma
USER chroma

# Start ChromaDB server
CMD ["uvicorn", "chromadb.app:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]

# ═══════════════════════════════════════════════════════════════════════════
# END OF DOCKERFILE
# ═══════════════════════════════════════════════════════════════════════════
