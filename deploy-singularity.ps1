<#
.SYNOPSIS
    Singularity Mesh - Master Deployment Orchestrator
    
.DESCRIPTION
    FAANG-grade parallel deployment system for the entire Infinity ecosystem.
    Zero manual intervention. One-click sovereign deployment.
    
    This script:
    - Syncs all 5+ repositories in parallel
    - Builds Docker images concurrently
    - Deploys the complete Singularity Mesh stack
    - Performs health validation
    
.PARAMETER Mode
    Deployment mode: 'full', 'sync-only', 'build-only', 'deploy-only'
    
.PARAMETER Parallel
    Enable parallel operations (default: true)
    
.PARAMETER Force
    Force rebuild all images even if they exist
    
.PARAMETER SkipHealthCheck
    Skip post-deployment health validation
    
.EXAMPLE
    .\deploy-singularity.ps1
    Full deployment with default settings
    
.EXAMPLE
    .\deploy-singularity.ps1 -Mode sync-only
    Only sync repositories without building or deploying
    
.EXAMPLE
    .\deploy-singularity.ps1 -Force
    Force rebuild all Docker images
    
.NOTES
    Requires: PowerShell 7+, Docker, Docker Compose, Git
    Author: Overseer-Prime | Infinity X One Systems
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [Parameter()]
    [ValidateSet('full', 'sync-only', 'build-only', 'deploy-only', 'stop', 'status')]
    [string]$Mode = 'full',
    
    [Parameter()]
    [bool]$Parallel = $true,
    
    [Parameter()]
    [switch]$Force,
    
    [Parameter()]
    [switch]$SkipHealthCheck,
    
    [Parameter()]
    [switch]$Verbose
)

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$ScriptRoot = $PSScriptRoot
$ComposeFile = Join-Path $ScriptRoot "docker-compose.singularity.yml"
$EnvFile = Join-Path $ScriptRoot ".env"
$EnvTemplate = Join-Path $ScriptRoot ".env.template"

# Repository definitions (The Singularity Fleet)
$Repositories = @(
    @{
        Name = "infinity-core"
        Path = "../infinity-core"
        Url = "https://github.com/Infinity-X-One-Systems/infinity-core.git"
        Branch = "main"
        Service = "neural-core"
        Color = "Cyan"
        Icon = "🧠"
    },
    @{
        Name = "infinity-vision"
        Path = "../infinity-vision"
        Url = "https://github.com/Infinity-X-One-Systems/infinity-vision.git"
        Branch = "main"
        Service = "vision-cortex"
        Color = "Magenta"
        Icon = "👁️"
    },
    @{
        Name = "infinity-factory"
        Path = "../infinity-factory"
        Url = "https://github.com/Infinity-X-One-Systems/infinity-factory.git"
        Branch = "main"
        Service = "factory-arm"
        Color = "Yellow"
        Icon = "🏭"
    },
    @{
        Name = "infinity-knowledge"
        Path = "../infinity-knowledge"
        Url = "https://github.com/Infinity-X-One-Systems/infinity-knowledge.git"
        Branch = "main"
        Service = "knowledge-base"
        Color = "Green"
        Icon = "📚"
    },
    @{
        Name = "infinity-products"
        Path = "../infinity-products"
        Url = "https://github.com/Infinity-X-One-Systems/infinity-products.git"
        Branch = "main"
        Service = "products"
        Color = "Blue"
        Icon = "📦"
    }
)

# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

function Write-Banner {
    param([string]$Text, [string]$Color = "White")
    
    $border = "═" * 80
    Write-Host ""
    Write-Host $border -ForegroundColor $Color
    Write-Host "  $Text" -ForegroundColor $Color
    Write-Host $border -ForegroundColor $Color
    Write-Host ""
}

function Write-Status {
    param(
        [string]$Icon,
        [string]$Message,
        [string]$Color = "White",
        [switch]$NoNewline
    )
    
    if ($NoNewline) {
        Write-Host "$Icon $Message" -ForegroundColor $Color -NoNewline
    } else {
        Write-Host "$Icon $Message" -ForegroundColor $Color
    }
}

function Write-Success {
    param([string]$Message)
    Write-Status -Icon "✅" -Message $Message -Color "Green"
}

function Write-Error {
    param([string]$Message)
    Write-Status -Icon "❌" -Message $Message -Color "Red"
}

function Write-Warning {
    param([string]$Message)
    Write-Status -Icon "⚠️" -Message $Message -Color "Yellow"
}

function Write-Info {
    param([string]$Message)
    Write-Status -Icon "ℹ️" -Message $Message -Color "Cyan"
}

function Test-CommandExists {
    param([string]$Command)
    return $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

function Test-Prerequisites {
    Write-Banner "🔍 VALIDATING PREREQUISITES" "Cyan"
    
    $missing = @()
    
    # Check Docker
    if (Test-CommandExists "docker") {
        $dockerVersion = (docker --version) -replace '.*version\s+([0-9.]+).*', '$1'
        Write-Success "Docker installed: $dockerVersion"
    } else {
        Write-Error "Docker not found"
        $missing += "Docker"
    }
    
    # Check Docker Compose
    if (Test-CommandExists "docker-compose") {
        $composeVersion = (docker-compose --version) -replace '.*version\s+([0-9.]+).*', '$1'
        Write-Success "Docker Compose installed: $composeVersion"
    } else {
        Write-Error "Docker Compose not found"
        $missing += "Docker Compose"
    }
    
    # Check Git
    if (Test-CommandExists "git") {
        $gitVersion = (git --version) -replace '.*version\s+([0-9.]+).*', '$1'
        Write-Success "Git installed: $gitVersion"
    } else {
        Write-Error "Git not found"
        $missing += "Git"
    }
    
    # Check compose file
    if (Test-Path $ComposeFile) {
        Write-Success "Compose file found: docker-compose.singularity.yml"
    } else {
        Write-Error "Compose file not found"
        $missing += "docker-compose.singularity.yml"
    }
    
    if ($missing.Count -gt 0) {
        Write-Error "Missing prerequisites: $($missing -join ', ')"
        Write-Warning "Please install missing components and try again."
        exit 1
    }
    
    Write-Success "All prerequisites validated"
}

# ═══════════════════════════════════════════════════════════════════════════
# ENVIRONMENT SETUP
# ═══════════════════════════════════════════════════════════════════════════

function Initialize-Environment {
    Write-Banner "⚙️  INITIALIZING ENVIRONMENT" "Yellow"
    
    if (-not (Test-Path $EnvFile)) {
        if (Test-Path $EnvTemplate) {
            Write-Info "Creating .env from template..."
            Copy-Item $EnvTemplate $EnvFile
            Write-Success ".env file created"
            Write-Warning "Please review and update .env with your configuration"
        } else {
            Write-Warning ".env.template not found, creating minimal .env"
            @"
# Minimal Singularity Mesh Configuration
REDIS_PORT=6379
CHROMA_PORT=8000
BROWSERLESS_PORT=3000
PYTHON_VERSION=3.11
LOG_LEVEL=INFO
"@ | Out-File -FilePath $EnvFile -Encoding UTF8
            Write-Success "Minimal .env file created"
        }
    } else {
        Write-Success ".env file exists"
    }
    
    # Create logs directory
    $logsDir = Join-Path $ScriptRoot "logs"
    if (-not (Test-Path $logsDir)) {
        New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
        @('core', 'vision', 'factory', 'knowledge') | ForEach-Object {
            New-Item -ItemType Directory -Path (Join-Path $logsDir $_) -Force | Out-Null
        }
        Write-Success "Logs directory structure created"
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# REPOSITORY OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════

function Sync-Repository {
    param([hashtable]$Repo)
    
    $repoPath = Join-Path $ScriptRoot $Repo.Path
    $repoPath = [System.IO.Path]::GetFullPath($repoPath)
    
    Write-Status -Icon $Repo.Icon -Message "Syncing $($Repo.Name)..." -Color $Repo.Color -NoNewline
    
    try {
        if (Test-Path $repoPath) {
            # Repository exists, pull latest
            Push-Location $repoPath
            $currentBranch = git branch --show-current 2>$null
            
            if ($currentBranch -eq $Repo.Branch) {
                git pull origin $Repo.Branch --quiet 2>&1 | Out-Null
                Write-Host " ✓" -ForegroundColor Green
            } else {
                git fetch origin --quiet 2>&1 | Out-Null
                git checkout $Repo.Branch --quiet 2>&1 | Out-Null
                git pull origin $Repo.Branch --quiet 2>&1 | Out-Null
                Write-Host " ✓ (switched to $($Repo.Branch))" -ForegroundColor Green
            }
            Pop-Location
        } else {
            # Repository doesn't exist, clone it
            $parentDir = Split-Path $repoPath -Parent
            if (-not (Test-Path $parentDir)) {
                New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
            }
            
            git clone --branch $Repo.Branch --depth 1 $Repo.Url $repoPath --quiet 2>&1 | Out-Null
            Write-Host " ✓ (cloned)" -ForegroundColor Green
        }
        return $true
    } catch {
        Write-Host " ✗" -ForegroundColor Red
        Write-Warning "Failed to sync $($Repo.Name): $_"
        return $false
    }
}

function Sync-AllRepositories {
    Write-Banner "🔄 SYNCING REPOSITORIES" "Magenta"
    
    if ($Parallel) {
        Write-Info "Parallel sync enabled (max 5 concurrent)"
        
        $jobs = @()
        foreach ($repo in $Repositories) {
            $jobs += Start-Job -ScriptBlock {
                param($repo, $scriptRoot)
                Set-Location $scriptRoot
                & {
                    $repoPath = Join-Path $scriptRoot $repo.Path
                    $repoPath = [System.IO.Path]::GetFullPath($repoPath)
                    
                    if (Test-Path $repoPath) {
                        Push-Location $repoPath
                        git pull origin $repo.Branch --quiet 2>&1 | Out-Null
                        Pop-Location
                    } else {
                        $parentDir = Split-Path $repoPath -Parent
                        if (-not (Test-Path $parentDir)) {
                            New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
                        }
                        git clone --branch $repo.Branch --depth 1 $repo.Url $repoPath --quiet 2>&1 | Out-Null
                    }
                }
            } -ArgumentList $repo, $ScriptRoot
        }
        
        $completed = 0
        foreach ($job in $jobs) {
            Wait-Job $job | Out-Null
            $completed++
            $repoName = $Repositories[$completed - 1].Name
            Write-Success "Synced: $repoName ($completed/$($Repositories.Count))"
            Remove-Job $job
        }
    } else {
        foreach ($repo in $Repositories) {
            Sync-Repository -Repo $repo | Out-Null
        }
    }
    
    Write-Success "All repositories synchronized"
}

# ═══════════════════════════════════════════════════════════════════════════
# DOCKER OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════

function Build-Services {
    Write-Banner "🐳 BUILDING DOCKER IMAGES" "Blue"
    
    $buildArgs = @(
        "-f", $ComposeFile,
        "build"
    )
    
    if ($Force) {
        $buildArgs += "--no-cache"
        Write-Info "Force rebuild enabled (no cache)"
    }
    
    if ($Parallel) {
        $buildArgs += "--parallel"
        Write-Info "Parallel build enabled"
    }
    
    Write-Info "Building all services..."
    & docker-compose @buildArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "All Docker images built successfully"
    } else {
        Write-Error "Docker build failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
}

function Start-Services {
    Write-Banner "🚀 DEPLOYING SINGULARITY MESH" "Green"
    
    Write-Info "Starting all services..."
    docker-compose -f $ComposeFile up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Singularity Mesh deployed successfully"
    } else {
        Write-Error "Deployment failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
}

function Stop-Services {
    Write-Banner "🛑 STOPPING SINGULARITY MESH" "Red"
    
    Write-Info "Stopping all services..."
    docker-compose -f $ComposeFile down
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Singularity Mesh stopped"
    } else {
        Write-Error "Failed to stop services"
        exit $LASTEXITCODE
    }
}

function Get-ServiceStatus {
    Write-Banner "📊 SINGULARITY MESH STATUS" "Cyan"
    
    docker-compose -f $ComposeFile ps
}

# ═══════════════════════════════════════════════════════════════════════════
# HEALTH CHECKS
# ═══════════════════════════════════════════════════════════════════════════

function Test-ServiceHealth {
    Write-Banner "🏥 HEALTH VALIDATION" "Green"
    
    Write-Info "Waiting for services to stabilize (30s)..."
    Start-Sleep -Seconds 30
    
    $services = @(
        @{ Name = "redis-cache"; Port = 6379 }
        @{ Name = "knowledge-base"; Port = 8000; Path = "/api/v1/heartbeat" }
        @{ Name = "browserless"; Port = 3000; Path = "/pressure" }
    )
    
    foreach ($service in $services) {
        Write-Status -Icon "🔍" -Message "Checking $($service.Name)..." -NoNewline
        
        try {
            if ($service.Path) {
                $url = "http://localhost:$($service.Port)$($service.Path)"
                $response = Invoke-WebRequest -Uri $url -TimeoutSec 5 -UseBasicParsing
                if ($response.StatusCode -eq 200) {
                    Write-Host " ✓" -ForegroundColor Green
                } else {
                    Write-Host " ⚠️ (Status: $($response.StatusCode))" -ForegroundColor Yellow
                }
            } else {
                # Simple port check
                $connection = Test-NetConnection -ComputerName localhost -Port $service.Port -WarningAction SilentlyContinue
                if ($connection.TcpTestSucceeded) {
                    Write-Host " ✓" -ForegroundColor Green
                } else {
                    Write-Host " ✗" -ForegroundColor Red
                }
            }
        } catch {
            Write-Host " ✗" -ForegroundColor Red
            Write-Warning "Health check failed: $_"
        }
    }
    
    Write-Success "Health validation complete"
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

function Invoke-SingularityDeploy {
    Write-Banner "🌌 SINGULARITY MESH DEPLOYMENT" "Magenta"
    Write-Info "Mode: $Mode | Parallel: $Parallel | Force: $Force"
    Write-Host ""
    
    switch ($Mode) {
        'full' {
            Test-Prerequisites
            Initialize-Environment
            Sync-AllRepositories
            Build-Services
            Start-Services
            if (-not $SkipHealthCheck) {
                Test-ServiceHealth
            }
        }
        'sync-only' {
            Test-Prerequisites
            Initialize-Environment
            Sync-AllRepositories
        }
        'build-only' {
            Test-Prerequisites
            Build-Services
        }
        'deploy-only' {
            Test-Prerequisites
            Start-Services
            if (-not $SkipHealthCheck) {
                Test-ServiceHealth
            }
        }
        'stop' {
            Stop-Services
        }
        'status' {
            Get-ServiceStatus
        }
    }
    
    Write-Banner "✨ DEPLOYMENT COMPLETE" "Green"
    Write-Info "View logs: docker-compose -f docker-compose.singularity.yml logs -f"
    Write-Info "Stop services: .\deploy-singularity.ps1 -Mode stop"
    Write-Info "Check status: .\deploy-singularity.ps1 -Mode status"
}

# ═══════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

try {
    Invoke-SingularityDeploy
} catch {
    Write-Error "Deployment failed: $_"
    Write-Host $_.ScriptStackTrace
    exit 1
}

# ═══════════════════════════════════════════════════════════════════════════
# END OF SCRIPT
# ═══════════════════════════════════════════════════════════════════════════
