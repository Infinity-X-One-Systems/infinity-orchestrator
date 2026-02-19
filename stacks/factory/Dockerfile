# ═══════════════════════════════════════════════════════════════════════════
# FACTORY ARM - The Builder
# ═══════════════════════════════════════════════════════════════════════════
# Continuous build and deployment pipelines with Docker-in-Docker capability
# ═══════════════════════════════════════════════════════════════════════════

ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim

# Build arguments
ARG FACTORY_REPO_URL=https://github.com/Infinity-X-One-Systems/infinity-factory.git
ARG FACTORY_BRANCH=main

# Metadata
LABEL maintainer="Infinity X One Systems"
LABEL description="Factory Arm - Continuous Build Pipeline Agent"
LABEL version="1.0.0"

# Environment setup
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies including Docker CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    build-essential \
    gnupg \
    lsb-release \
    software-properties-common \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI (for Docker-in-Docker operations)
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y --no-install-recommends docker-ce-cli && \
    rm -rf /var/lib/apt/lists/*

# Create workspace
WORKDIR /workspace

# Clone repository if not mounted (fallback)
RUN if [ ! -d "/workspace/infinity-factory" ]; then \
        git clone --depth 1 --branch ${FACTORY_BRANCH} ${FACTORY_REPO_URL} /workspace/infinity-factory; \
    fi

# Set working directory to factory
WORKDIR /workspace/infinity-factory

# Install Python dependencies
RUN pip install --no-cache-dir \
    redis \
    chromadb \
    requests \
    python-dotenv \
    pydantic \
    pyyaml \
    loguru \
    asyncio \
    aiohttp \
    docker \
    gitpython \
    jinja2 \
    click \
    rich \
    toml

# Create necessary directories
RUN mkdir -p /logs /artifacts

# Copy pipeline configuration
COPY pipeline_config.py /workspace/pipeline_config.py

# Set proper ownership and permissions
RUN useradd -m -u 1000 agent && \
    chown -R agent:agent /workspace /logs /artifacts && \
    chmod -R 755 /logs /artifacts

# Health check script
COPY <<'EOF' /usr/local/bin/healthcheck.sh
#!/bin/sh
python -c "import sys; sys.exit(0)" || exit 1
EOF

RUN chmod +x /usr/local/bin/healthcheck.sh

# Add agent to docker group (if exists) for Docker socket access
RUN groupadd -f -g 999 docker && usermod -aG docker agent

USER agent

# Default command (can be overridden)
CMD ["python", "pipelines/orchestrate.py"]

# ═══════════════════════════════════════════════════════════════════════════
# END OF DOCKERFILE
# ═══════════════════════════════════════════════════════════════════════════
