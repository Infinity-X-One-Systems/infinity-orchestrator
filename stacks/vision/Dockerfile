# ═══════════════════════════════════════════════════════════════════════════
# VISION CORTEX - The Eyes (Shadow Browser with Playwright Stealth)
# ═══════════════════════════════════════════════════════════════════════════
# Advanced web automation with stealth capabilities and anti-detection
# ═══════════════════════════════════════════════════════════════════════════

ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim

# Build arguments
ARG VISION_REPO_URL=https://github.com/Infinity-X-One-Systems/infinity-vision.git
ARG VISION_BRANCH=main

# Metadata
LABEL maintainer="Infinity X One Systems"
LABEL description="Vision Cortex - Shadow Browser Agent with Playwright"
LABEL version="1.0.0"

# Environment setup
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0

# Install system dependencies for Playwright and browser automation
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Core utilities
    git \
    curl \
    ca-certificates \
    build-essential \
    # Playwright dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    # Fonts for proper rendering
    fonts-liberation \
    fonts-noto-color-emoji \
    fonts-noto-cjk \
    # Additional utilities
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Create workspace
WORKDIR /workspace

# Clone repository if not mounted (fallback)
RUN if [ ! -d "/workspace/infinity-vision" ]; then \
        git clone --depth 1 --branch ${VISION_BRANCH} ${VISION_REPO_URL} /workspace/infinity-vision; \
    fi

# Set working directory to vision
WORKDIR /workspace/infinity-vision

# Install Python dependencies
RUN pip install --no-cache-dir \
    playwright==1.40.0 \
    playwright-stealth \
    redis \
    chromadb \
    requests \
    python-dotenv \
    pydantic \
    pyyaml \
    loguru \
    asyncio \
    aiohttp \
    beautifulsoup4 \
    lxml \
    pillow \
    fake-useragent

# Install Playwright browsers with full dependencies
RUN playwright install chromium --with-deps && \
    playwright install firefox --with-deps && \
    playwright install webkit --with-deps

# Install stealth plugins and anti-detection measures
RUN pip install --no-cache-dir \
    playwright-recaptcha \
    undetected-playwright

# Create necessary directories
RUN mkdir -p /logs /tmp/playwright /workspace/infinity-vision/screenshots

# Copy stealth configuration
COPY stealth_config.py /workspace/stealth_config.py

# Set proper ownership and permissions
RUN useradd -m -u 1000 agent && \
    chown -R agent:agent /workspace /logs /tmp/playwright /ms-playwright && \
    chmod -R 755 /logs /tmp/playwright /workspace/infinity-vision/screenshots

# Health check script
COPY <<'EOF' /usr/local/bin/healthcheck.sh
#!/bin/sh
python -c "import sys; from playwright.sync_api import sync_playwright; sys.exit(0)" || exit 1
EOF

RUN chmod +x /usr/local/bin/healthcheck.sh

USER agent

# Default command (can be overridden)
CMD ["python", "agent_vision.py"]

# ═══════════════════════════════════════════════════════════════════════════
# END OF DOCKERFILE
# ═══════════════════════════════════════════════════════════════════════════
