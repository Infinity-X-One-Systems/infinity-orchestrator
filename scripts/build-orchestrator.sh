#!/usr/bin/env bash
# Build Orchestrator Script
# This script orchestrates the build process across multiple repositories

set -euo pipefail

# Configuration
MANIFEST_FILE="${MANIFEST_FILE:-config/repositories.json}"
PARALLEL_JOBS="${PARALLEL_JOBS:-5}"
BUILD_LOG_DIR="${BUILD_LOG_DIR:-/tmp/build-logs}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_build() {
    echo -e "${BLUE}[BUILD]${NC} $1"
}

# Initialize
initialize() {
    log_info "Initializing build orchestrator..."
    
    if [ ! -f "$MANIFEST_FILE" ]; then
        log_error "Repository manifest not found: $MANIFEST_FILE"
        exit 1
    fi
    
    mkdir -p "$BUILD_LOG_DIR"
    
    log_info "Build orchestrator initialized"
}

# Get repositories to build
get_repositories() {
    jq -r '.repositories[] | select(.archived == false and .disabled == false) | .name' "$MANIFEST_FILE"
}

# Build single repository
build_repository() {
    local repo_name=$1
    local log_file="$BUILD_LOG_DIR/${repo_name}.log"
    
    log_build "Building repository: $repo_name"
    
    # Get repository details
    local repo_data
    repo_data=$(jq --arg name "$repo_name" '.repositories[] | select(.name == $name)' "$MANIFEST_FILE")
    
    local build_cmd
    build_cmd=$(echo "$repo_data" | jq -r '.build_config.build_command')
    
    # Execute build
    {
        echo "=== Build started at $(date) ==="
        echo "Repository: $repo_name"
        echo "Build command: $build_cmd"
        echo ""
        
        if eval "$build_cmd"; then
            echo ""
            echo "✅ Build succeeded"
            echo "=== Build completed at $(date) ==="
        else
            echo ""
            echo "❌ Build failed"
            echo "=== Build failed at $(date) ==="
            exit 1
        fi
    } > "$log_file" 2>&1
    
    if [ $? -eq 0 ]; then
        log_build "✅ $repo_name build succeeded"
        return 0
    else
        log_error "❌ $repo_name build failed (see $log_file)"
        return 1
    fi
}

# Main orchestration
main() {
    log_info "Starting build orchestration..."
    
    initialize
    
    local repos
    repos=$(get_repositories)
    
    local total
    total=$(echo "$repos" | wc -l)
    
    log_info "Found $total repositories to build"
    
    local success_count=0
    local failure_count=0
    
    # Build each repository
    while IFS= read -r repo; do
        if build_repository "$repo"; then
            ((success_count++))
        else
            ((failure_count++))
        fi
    done <<< "$repos"
    
    # Print summary
    echo ""
    echo "========================================"
    echo "Build Orchestration Summary"
    echo "========================================"
    echo "Total repositories: $total"
    echo "Successful builds: $success_count"
    echo "Failed builds: $failure_count"
    echo "========================================"
    
    if [ $failure_count -gt 0 ]; then
        log_error "Build orchestration completed with failures"
        exit 1
    else
        log_info "Build orchestration completed successfully!"
        exit 0
    fi
}

main "$@"
