# 🚀 Singularity Mesh - Quick Start Guide

**Deploy the entire Infinity ecosystem in under 5 minutes**

## Prerequisites Checklist

- [ ] Docker Desktop installed (20.10+)
- [ ] Docker Compose installed (2.0+)
- [ ] Git installed (2.30+)
- [ ] PowerShell 7+ (Windows) or Bash (Linux/Mac)
- [ ] 8GB+ RAM available
- [ ] 20GB+ disk space available

## Step-by-Step Deployment

### 1. Clone the Orchestrator

```bash
git clone https://github.com/Infinity-X-One-Systems/infinity-orchestrator.git
cd infinity-orchestrator
```

### 2. Configure Environment

```bash
# Copy template
cp .env.template .env

# Edit configuration (optional - defaults work for most setups)
# nano .env  # or your preferred editor
```

**Default Configuration:**
- Repository paths: Sibling directories (`../infinity-*`)
- Redis port: 6379
- ChromaDB port: 8000
- Browserless port: 3000
- Python version: 3.11

### 3. Deploy Everything

**Option A: Automated (Recommended)**

```powershell
# Windows PowerShell
.\deploy-singularity.ps1
```

This single command will:
1. ✅ Validate prerequisites
2. ✅ Sync/clone all 5 repositories in parallel
3. ✅ Build all Docker images
4. ✅ Deploy the complete stack
5. ✅ Validate health of all services

**Option B: Manual**

```bash
# Build images
docker-compose -f docker-compose.singularity.yml build

# Start services
docker-compose -f docker-compose.singularity.yml up -d

# Check status
docker-compose -f docker-compose.singularity.yml ps
```

### 4. Verify Deployment

**Check service health:**
```bash
# All services
docker-compose -f docker-compose.singularity.yml ps

# Specific service logs
docker-compose -f docker-compose.singularity.yml logs -f neural-core
```

**Access services:**
- Redis: `localhost:6379`
- ChromaDB: `http://localhost:8000`
- Browserless: `http://localhost:3000`

**Validate health endpoints:**
```bash
# ChromaDB
curl http://localhost:8000/api/v1/heartbeat

# Browserless
curl http://localhost:3000/pressure
```

## Common Scenarios

### Scenario 1: First-Time Setup (No Repos)

The orchestrator will automatically clone all repositories:

```powershell
.\deploy-singularity.ps1
```

Expected directory structure after deployment:
```
parent-directory/
├── infinity-orchestrator/
├── infinity-core/
├── infinity-vision/
├── infinity-factory/
├── infinity-knowledge/
└── infinity-products/
```

### Scenario 2: Update Existing Deployment

```powershell
# Sync repos + rebuild + redeploy
.\deploy-singularity.ps1 -Force
```

### Scenario 3: Development Mode

For active development, mount repos as writable:

```yaml
# Edit docker-compose.singularity.yml
volumes:
  - ${CORE_REPO_PATH}:/workspace/infinity-core  # Remove :ro
```

Then rebuild:
```powershell
.\deploy-singularity.ps1 -Mode build-only
```

### Scenario 4: Troubleshooting

```bash
# View all logs
docker-compose -f docker-compose.singularity.yml logs

# View specific service
docker-compose -f docker-compose.singularity.yml logs vision-cortex

# Follow logs in real-time
docker-compose -f docker-compose.singularity.yml logs -f --tail=100

# Check resource usage
docker stats

# Restart a service
docker-compose -f docker-compose.singularity.yml restart neural-core

# Complete teardown
docker-compose -f docker-compose.singularity.yml down -v
```

## Resource Requirements

### Minimum Configuration
- **CPU**: 4 cores
- **RAM**: 8GB
- **Disk**: 20GB
- **Network**: Internet connection for initial setup

### Recommended Configuration
- **CPU**: 8+ cores
- **RAM**: 16GB+
- **Disk**: 50GB+ SSD
- **Network**: High-speed internet

### Service Resource Allocation

| Service | CPU | RAM | SHM |
|---------|-----|-----|-----|
| redis-cache | 0.25-1.0 | 128MB-512MB | - |
| knowledge-base | 0.5-2.0 | 512MB-2GB | - |
| browserless | 1.0-4.0 | 1GB-4GB | 2GB |
| neural-core | 0.5-2.0 | 512MB-2GB | - |
| vision-cortex | 0.5-2.0 | 1GB-3GB | 1GB |
| factory-arm | 1.0-4.0 | 1GB-4GB | - |

## Advanced Configuration

### Custom Repository Locations

Edit `.env`:
```bash
CORE_REPO_PATH=/custom/path/to/infinity-core
VISION_REPO_PATH=/custom/path/to/infinity-vision
# ...
```

### Custom Ports

Edit `.env`:
```bash
REDIS_PORT=7000
CHROMA_PORT=9000
BROWSERLESS_PORT=4000
```

### Agent Modes

Edit `.env`:
```bash
# Core agent mode
CORE_AGENT_MODE=autonomous  # or: manual, supervised

# Vision mode
VISION_MODE=shadow  # or: standard, aggressive

# Factory mode
FACTORY_MODE=continuous  # or: on-demand, scheduled
```

### Enable Debug Logging

Edit `.env`:
```bash
LOG_LEVEL=DEBUG
```

## Maintenance Commands

### Stop Services
```bash
docker-compose -f docker-compose.singularity.yml stop
```

### Start Services
```bash
docker-compose -f docker-compose.singularity.yml start
```

### Restart Services
```bash
docker-compose -f docker-compose.singularity.yml restart
```

### Remove Everything (Clean Slate)
```bash
# Stop and remove containers, networks, volumes
docker-compose -f docker-compose.singularity.yml down -v

# Remove images
docker images | grep infinity | awk '{print $3}' | xargs docker rmi
```

### Update Images
```bash
# Pull latest base images
docker-compose -f docker-compose.singularity.yml pull

# Rebuild custom images
docker-compose -f docker-compose.singularity.yml build --no-cache
```

## Troubleshooting Guide

### Issue: Port Already in Use

**Error**: `Bind for 0.0.0.0:6379 failed: port is already allocated`

**Solution**:
```bash
# Find what's using the port
netstat -ano | findstr :6379  # Windows
lsof -i :6379  # Linux/Mac

# Stop the conflicting service or change port in .env
```

### Issue: Out of Memory

**Error**: Container killed or crashes

**Solution**:
```bash
# Check Docker resource limits
docker info | grep -i memory

# Increase in Docker Desktop:
# Settings → Resources → Memory → 12GB+
```

### Issue: Repository Mount Failed

**Error**: `no such file or directory: ../infinity-core`

**Solution**:
```bash
# Check if repos exist
ls -la ../

# Let orchestrator clone them
.\deploy-singularity.ps1 -Mode sync-only
```

### Issue: Playwright Browser Install Failed

**Error**: `Playwright browser not found`

**Solution**:
```bash
# Rebuild vision service with no cache
docker-compose -f docker-compose.singularity.yml build --no-cache vision-cortex
```

### Issue: Service Unhealthy

**Error**: Service shows as unhealthy in `docker ps`

**Solution**:
```bash
# Check logs
docker-compose -f docker-compose.singularity.yml logs <service-name>

# Restart service
docker-compose -f docker-compose.singularity.yml restart <service-name>

# Force recreate
docker-compose -f docker-compose.singularity.yml up -d --force-recreate <service-name>
```

## Performance Tuning

### Enable Build Cache
```bash
# Build with BuildKit for better caching
DOCKER_BUILDKIT=1 docker-compose -f docker-compose.singularity.yml build
```

### Parallel Builds
```bash
# Build all services in parallel
docker-compose -f docker-compose.singularity.yml build --parallel
```

### Prune Unused Resources
```bash
# Remove dangling images
docker image prune

# Remove all unused resources (careful!)
docker system prune -a --volumes
```

## Next Steps

Once deployed:

1. **Monitor Services**
   ```bash
   docker-compose -f docker-compose.singularity.yml logs -f
   ```

2. **Access Agents**
   ```bash
   # Neural Core
   docker exec -it infinity-neural-core bash
   
   # Vision Cortex
   docker exec -it infinity-vision-cortex bash
   ```

3. **Review Documentation**
   - [Stacks README](./stacks/README.md) - Detailed service documentation
   - [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
   - [QUICKREF.md](./QUICKREF.md) - Quick reference guide

4. **Customize**
   - Edit `.env` for your environment
   - Modify `docker-compose.singularity.yml` for advanced setups
   - Review Dockerfiles in `stacks/` directory

## Support

- **Issues**: Create an issue in the repository
- **Documentation**: See `stacks/README.md` for detailed information
- **Logs**: Always check logs first: `docker-compose logs <service>`

---

**🌌 The Singularity is not a destination. It is a command.**
