# ═══════════════════════════════════════════════════════════════════════════
# NEURAL CORE - The Brain
# ═══════════════════════════════════════════════════════════════════════════
# Central Intelligence Agent from infinity-core repository
# ═══════════════════════════════════════════════════════════════════════════

ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim

# Build arguments
ARG CORE_REPO_URL=https://github.com/Infinity-X-One-Systems/infinity-core.git
ARG CORE_BRANCH=main

# Metadata
LABEL maintainer="Infinity X One Systems"
LABEL description="Neural Core - The Brain Agent"
LABEL version="1.0.0"

# Environment setup
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create workspace
WORKDIR /workspace

# Clone repository if not mounted (fallback)
RUN if [ ! -d "/workspace/infinity-core" ]; then \
        git clone --depth 1 --branch ${CORE_BRANCH} ${CORE_REPO_URL} /workspace/infinity-core; \
    fi

# Set working directory to core
WORKDIR /workspace/infinity-core

# Install Python dependencies
# Note: This is a baseline. Actual dependencies will be from mounted volume
RUN pip install --no-cache-dir \
    redis \
    chromadb \
    requests \
    python-dotenv \
    pydantic \
    pyyaml \
    loguru \
    asyncio \
    aiohttp

# Create logs directory
RUN mkdir -p /logs && chmod 777 /logs

# Health check script
COPY <<'EOF' /usr/local/bin/healthcheck.sh
#!/bin/sh
python -c "import sys; sys.exit(0)" || exit 1
EOF

RUN chmod +x /usr/local/bin/healthcheck.sh

# Set user for security (optional - may need root for some operations)
RUN useradd -m -u 1000 agent
RUN chown -R agent:agent /workspace /logs
USER agent

# Default command (can be overridden)
CMD ["python", "agents/brain.py"]

# ═══════════════════════════════════════════════════════════════════════════
# END OF DOCKERFILE
# ═══════════════════════════════════════════════════════════════════════════
