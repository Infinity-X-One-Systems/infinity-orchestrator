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
RUN mkdir -p /logs /tmp/playwright /workspace/infinity-vision/screenshots && \
    chmod -R 777 /logs /tmp/playwright /workspace/infinity-vision/screenshots

# Create stealth configuration script
COPY <<'EOF' /workspace/stealth_config.py
"""
Stealth Configuration for Shadow Browser Operations
Implements anti-detection measures for web automation
"""

import asyncio
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright_stealth import stealth_async

async def create_stealth_browser(playwright, headless=True):
    """Create a browser instance with full stealth capabilities"""
    browser = await playwright.chromium.launch(
        headless=headless,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-gpu',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-infobars',
            '--window-size=1920,1080',
        ]
    )
    return browser

async def create_stealth_context(browser: Browser):
    """Create a stealth browser context with realistic fingerprinting"""
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        locale='en-US',
        timezone_id='America/New_York',
        geolocation={'longitude': -74.0060, 'latitude': 40.7128},
        permissions=['geolocation'],
        color_scheme='light',
        extra_http_headers={
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Upgrade-Insecure-Requests': '1',
        }
    )
    return context

async def apply_stealth_to_page(page: Page):
    """Apply stealth measures to a page"""
    await stealth_async(page)
    
    # Additional anti-detection JavaScript
    await page.add_init_script("""
        // Override the navigator.webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Mock plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        
        // Chrome runtime
        window.chrome = {
            runtime: {}
        };
        
        // Permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    """)
    
    return page

# Export for use in agent_vision.py
__all__ = ['create_stealth_browser', 'create_stealth_context', 'apply_stealth_to_page']
EOF

RUN chmod 644 /workspace/stealth_config.py

# Health check script
COPY <<'EOF' /usr/local/bin/healthcheck.sh
#!/bin/sh
python -c "import sys; from playwright.sync_api import sync_playwright; sys.exit(0)" || exit 1
EOF

RUN chmod +x /usr/local/bin/healthcheck.sh

# Set user for security
RUN useradd -m -u 1000 agent && \
    chown -R agent:agent /workspace /logs /tmp/playwright /ms-playwright
USER agent

# Default command (can be overridden)
CMD ["python", "agent_vision.py"]

# ═══════════════════════════════════════════════════════════════════════════
# END OF DOCKERFILE
# ═══════════════════════════════════════════════════════════════════════════
