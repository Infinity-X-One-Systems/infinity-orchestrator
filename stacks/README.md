# 🌌 Singularity Mesh - Intelligence Stack

**FAANG-grade containerized orchestration for the Infinity X One Systems ecosystem**

## 📋 Overview

The Singularity Mesh is a sovereign, parallel orchestration system that runs all intelligence nodes of the Infinity ecosystem in Docker containers with zero manual intervention. This eliminates dependency issues and enables true "God Mode" deployment.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SINGULARITY MESH                             │
│                    ═══════════════════                          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ Redis Cache  │  │  Browserless │  │  ChromaDB    │        │
│  │ (Synaptic)   │  │  (Shadow)    │  │  (Memory)    │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                  │                  │                 │
│         └──────────────────┴──────────────────┘                │
│                            │                                    │
│    ┌───────────────────────┴───────────────────────┐          │
│    │                                                 │          │
│  ┌─▼──────────┐  ┌──────────────┐  ┌──────────────▼┐         │
│  │ Neural     │  │  Vision      │  │  Factory      │         │
│  │ Core       │  │  Cortex      │  │  Arm          │         │
│  │ (Brain)    │  │  (Eyes)      │  │  (Builder)    │         │
│  └────────────┘  └──────────────┘  └───────────────┘         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.30+
- **PowerShell**: 7.0+ (Windows) or Bash (Linux/Mac)

### One-Command Deployment

**Windows (PowerShell):**
```powershell
.\deploy-singularity.ps1
```

**Linux/Mac (Bash):**
```bash
# Coming soon: deploy-singularity.sh
docker-compose -f docker-compose.singularity.yml up -d
```

### Manual Deployment

1. **Clone repositories** (if not already done):
   ```bash
   # From parent directory
   git clone https://github.com/Infinity-X-One-Systems/infinity-core.git
   git clone https://github.com/Infinity-X-One-Systems/infinity-vision.git
   git clone https://github.com/Infinity-X-One-Systems/infinity-factory.git
   git clone https://github.com/Infinity-X-One-Systems/infinity-knowledge.git
   git clone https://github.com/Infinity-X-One-Systems/infinity-products.git
   ```

2. **Configure environment**:
   ```bash
   cp .env.template .env
   # Edit .env with your settings
   ```

3. **Deploy the mesh**:
   ```bash
   docker-compose -f docker-compose.singularity.yml up -d
   ```

4. **Monitor logs**:
   ```bash
   docker-compose -f docker-compose.singularity.yml logs -f
   ```

## 📦 Services

### Infrastructure Services

#### Redis Cache (Synaptic Bridge)
- **Purpose**: Shared memory bus for inter-service communication
- **Port**: 6379
- **Image**: `redis:7-alpine`
- **Resources**: 512MB RAM, 1 CPU

#### ChromaDB (Knowledge Base)
- **Purpose**: Vector database for persistent memory
- **Port**: 8000
- **Image**: `infinity/knowledge-base:latest`
- **Resources**: 2GB RAM, 2 CPUs
- **Health**: `http://localhost:8000/api/v1/heartbeat`

#### Browserless (Shadow Portal)
- **Purpose**: Headless browser engine for web automation
- **Port**: 3000
- **Image**: `browserless/chrome:latest`
- **Resources**: 4GB RAM, 4 CPUs, 2GB SHM
- **Features**: Stealth mode, ad blocking, pre-boot chrome

### Intelligence Services

#### Neural Core (The Brain)
- **Repository**: `infinity-core`
- **Image**: `infinity/neural-core:latest`
- **Command**: `python agents/brain.py`
- **Resources**: 2GB RAM, 2 CPUs
- **Dependencies**: Redis, ChromaDB, Browserless

#### Vision Cortex (The Eyes)
- **Repository**: `infinity-vision`
- **Image**: `infinity/vision-cortex:latest`
- **Command**: `python agent_vision.py`
- **Resources**: 3GB RAM, 2 CPUs, 1GB SHM
- **Features**: Playwright, stealth capabilities, anti-detection
- **Dependencies**: Redis, ChromaDB, Browserless

#### Factory Arm (The Builder)
- **Repository**: `infinity-factory`
- **Image**: `infinity/factory-arm:latest`
- **Command**: `python pipelines/orchestrate.py`
- **Resources**: 4GB RAM, 4 CPUs
- **Features**: Docker-in-Docker, parallel builds
- **Dependencies**: Redis, ChromaDB

## 🔧 Configuration

### Environment Variables

See `.env.template` for all available configuration options. Key variables:

```bash
# Repository Paths (relative to orchestrator)
CORE_REPO_PATH=../infinity-core
VISION_REPO_PATH=../infinity-vision
FACTORY_REPO_PATH=../infinity-factory

# Service Ports
REDIS_PORT=6379
CHROMA_PORT=8000
BROWSERLESS_PORT=3000

# Agent Modes
CORE_AGENT_MODE=autonomous
VISION_MODE=shadow
FACTORY_MODE=continuous

# Logging
LOG_LEVEL=INFO
```

### Volume Mounts

The composition mounts repositories as read-only volumes:

```yaml
volumes:
  - ${CORE_REPO_PATH}:/workspace/infinity-core:ro
  - ${VISION_REPO_PATH}:/workspace/infinity-vision:ro
  - ${FACTORY_REPO_PATH}:/workspace/infinity-factory:ro
```

**Note**: Use `:ro` for production safety. Remove for development.

## 🛠️ Operations

### Start Services
```bash
docker-compose -f docker-compose.singularity.yml up -d
```

### Stop Services
```bash
docker-compose -f docker-compose.singularity.yml down
```

### View Logs
```bash
# All services
docker-compose -f docker-compose.singularity.yml logs -f

# Specific service
docker-compose -f docker-compose.singularity.yml logs -f neural-core
```

### Rebuild Images
```bash
# All services
docker-compose -f docker-compose.singularity.yml build --no-cache

# Specific service
docker-compose -f docker-compose.singularity.yml build --no-cache vision-cortex
```

### Service Status
```bash
docker-compose -f docker-compose.singularity.yml ps
```

### Execute Commands in Container
```bash
# Neural Core
docker exec -it infinity-neural-core bash

# Vision Cortex
docker exec -it infinity-vision-cortex bash
```

## 🏥 Health Checks

Each service includes health checks:

- **Redis**: `redis-cli ping`
- **ChromaDB**: `GET /api/v1/heartbeat`
- **Browserless**: `GET /pressure`
- **Agents**: Python import checks

### Manual Health Validation

**PowerShell:**
```powershell
.\deploy-singularity.ps1 -Mode status
```

**Manual:**
```bash
# Redis
docker exec infinity-redis-cache redis-cli ping

# ChromaDB
curl http://localhost:8000/api/v1/heartbeat

# Browserless
curl http://localhost:3000/pressure
```

## 📁 Directory Structure

```
infinity-orchestrator/
├── docker-compose.singularity.yml    # Master composition
├── deploy-singularity.ps1            # Deployment orchestrator
├── .env.template                     # Environment template
├── .env                              # Your configuration (git-ignored)
├── stacks/
│   ├── core/
│   │   └── Dockerfile                # Neural Core image
│   ├── vision/
│   │   └── Dockerfile                # Vision Cortex image (with Playwright)
│   ├── factory/
│   │   └── Dockerfile                # Factory Arm image
│   ├── knowledge/
│   │   └── Dockerfile                # ChromaDB setup
│   └── README.md                     # This file
└── logs/                             # Service logs
    ├── core/
    ├── vision/
    ├── factory/
    └── knowledge/
```

## 🔐 Security

### Important Security Considerations

**Docker Socket Access (Factory Arm)**:
The Factory Arm service mounts the Docker socket (`/var/run/docker.sock`) as read-only for Docker-in-Docker capabilities. While necessary for build operations, this presents security implications:

- **Risk**: Even read-only socket access can be exploited to gain host access
- **Mitigation**: Service runs as non-root user (UID 1000) with limited permissions
- **Production**: Consider using Docker API proxies (e.g., [docker-socket-proxy](https://github.com/Tecnativa/docker-socket-proxy)) with restricted permissions
- **Alternative**: Use a dedicated build agent or CI/CD system for sensitive environments

**Recommendation**: For production environments, implement one of these alternatives:
1. Use a Docker API proxy with restricted permissions
2. Run Factory Arm on an isolated host
3. Use Kubernetes with proper RBAC policies
4. Integrate with GitHub Actions or other CI/CD instead

### Stealth Features (Vision Cortex)

The Vision Cortex includes advanced anti-detection measures:

- **Playwright Stealth**: Automated stealth plugin
- **User-Agent Rotation**: Realistic browser fingerprinting
- **WebDriver Masking**: Hides automation signatures
- **Plugin Mocking**: Simulates real browser plugins
- **Canvas Fingerprinting**: Prevents canvas-based detection

See `stacks/vision/Dockerfile` for implementation details.

### Network Isolation

- **singularity-mesh**: Main communication network
- **vision-isolated**: Internal network for shadow operations

### Resource Limits

All services have CPU and memory limits to prevent resource exhaustion.

## 🚨 Troubleshooting

### Service Won't Start

1. Check logs: `docker-compose logs <service-name>`
2. Verify resources: `docker stats`
3. Check port conflicts: `netstat -ano | findstr <PORT>`

### Repository Mount Issues

If services can't access repositories:
1. Verify paths in `.env`
2. Check permissions
3. Remove `:ro` flag temporarily for debugging

### Playwright Issues (Vision)

```bash
# Rebuild with fresh browser install
docker-compose build --no-cache vision-cortex
```

### Out of Memory

Increase Docker Desktop memory limits:
- Settings → Resources → Memory → 8GB+

## 📊 Monitoring

### Resource Usage
```bash
docker stats
```

### Network Traffic
```bash
docker network inspect singularity-mesh
```

### Volume Usage
```bash
docker volume ls
docker volume inspect <volume-name>
```

## 🔄 Updates

### Update Repositories
```powershell
# PowerShell
.\deploy-singularity.ps1 -Mode sync-only

# Manual
cd ../infinity-core && git pull
cd ../infinity-vision && git pull
# ... etc
```

### Rebuild Images
```powershell
.\deploy-singularity.ps1 -Force
```

## 🎯 Deployment Modes

The PowerShell orchestrator supports multiple modes:

- **full**: Complete sync → build → deploy → health check
- **sync-only**: Only sync repositories
- **build-only**: Only build Docker images
- **deploy-only**: Only deploy services
- **stop**: Stop all services
- **status**: Show service status

## 📝 Notes

- Repository paths are relative to `infinity-orchestrator/`
- Logs are stored in `./logs/<service>/`
- Artifacts are stored in Docker volumes
- All agents share Redis and ChromaDB
- Vision agent has isolated network for stealth operations

## 🤝 Contributing

See main `CONTRIBUTING.md` for contribution guidelines.

## 📄 License

See main `LICENSE` file.

---

**Built with ❤️ by Overseer-Prime | Infinity X One Systems**

*The Singularity is not a destination. It is a command.*
