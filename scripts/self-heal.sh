#!/usr/bin/env bash
# Self-Healing Script
# Attempts to automatically fix common repository issues

set -euo pipefail

# Configuration
MANIFEST_FILE="${MANIFEST_FILE:-config/repositories.json}"
ORG_NAME="${GH_ORG:-Infinity-X-One-Systems}"
TARGET_REPO="${TARGET_REPO:-}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_heal() {
    echo -e "${BLUE}[HEAL]${NC} $1"
}

# Analyze repository failures
analyze_failures() {
    local repo_name=$1
    local full_name="$ORG_NAME/$repo_name"
    
    log_info "Analyzing failures for: $repo_name"
    
    # Get recent failed runs
    local failed_runs
    failed_runs=$(gh run list --repo "$full_name" --limit 5 --json databaseId,conclusion --jq '[.[] | select(.conclusion == "failure") | .databaseId]' 2>/dev/null || echo '[]')
    
    if [ "$failed_runs" = "[]" ]; then
        log_info "No recent failures found"
        return 1
    fi
    
    log_warn "Found failed runs: $failed_runs"
    return 0
}

# Determine healing strategy
determine_strategy() {
    local repo_name=$1
    
    log_info "Determining healing strategy for: $repo_name"
    
    # Get repository data
    local repo_data
    repo_data=$(jq --arg name "$repo_name" '.repositories[] | select(.name == $name)' "$MANIFEST_FILE")
    
    local language
    language=$(echo "$repo_data" | jq -r '.language')
    
    case "$language" in
        JavaScript|TypeScript)
            echo "npm_clean"
            ;;
        Python)
            echo "pip_update"
            ;;
        Go)
            echo "go_tidy"
            ;;
        Rust)
            echo "cargo_update"
            ;;
        *)
            echo "cache_clear"
            ;;
    esac
}

# Apply healing strategy
apply_healing() {
    local repo_name=$1
    local strategy=$2
    
    log_heal "Applying healing strategy '$strategy' to $repo_name"
    
    # Note: This script identifies strategies but delegates actual implementation
    # to the GitHub Actions self-healing workflow which has the necessary
    # permissions and context to make repository changes.
    
    case "$strategy" in
        npm_clean)
            log_heal "Strategy identified: Remove package-lock.json and node_modules"
            log_info "This will be executed by the self-healing workflow"
            ;;
        pip_update)
            log_heal "Strategy identified: Update Python dependencies"
            log_info "This will be executed by the self-healing workflow"
            ;;
        go_tidy)
            log_heal "Strategy identified: Run go mod tidy"
            log_info "This will be executed by the self-healing workflow"
            ;;
        cargo_update)
            log_heal "Strategy identified: Remove Cargo.lock"
            log_info "This will be executed by the self-healing workflow"
            ;;
        cache_clear)
            log_heal "Strategy identified: Clear workflow cache"
            log_info "This will be executed by the self-healing workflow"
            ;;
        *)
            log_error "Unknown strategy: $strategy"
            return 1
            ;;
    esac
    
    log_info "Healing strategy identified successfully"
    return 0
}

# Trigger workflow rerun
trigger_rerun() {
    local repo_name=$1
    local full_name="$ORG_NAME/$repo_name"
    
    log_info "Triggering workflow rerun for: $repo_name"
    
    # Get most recent failed run
    local failed_run
    failed_run=$(gh run list --repo "$full_name" --limit 1 --json databaseId,conclusion --jq '[.[] | select(.conclusion == "failure") | .databaseId][0]' 2>/dev/null)
    
    if [ -n "$failed_run" ] && [ "$failed_run" != "null" ]; then
        log_info "Rerunning workflow: $failed_run"
        gh run rerun "$failed_run" --repo "$full_name" 2>/dev/null || log_warn "Could not rerun workflow"
    else
        log_warn "No failed run to rerun"
    fi
}

# Main execution
main() {
    log_info "Starting self-healing process..."
    
    if [ ! -f "$MANIFEST_FILE" ]; then
        log_error "Repository manifest not found: $MANIFEST_FILE"
        exit 1
    fi
    
    local repos
    if [ -n "$TARGET_REPO" ]; then
        repos="$TARGET_REPO"
        log_info "Targeting specific repository: $TARGET_REPO"
    else
        # Find repositories with failures
        repos=$(jq -r '.repositories[] | select(.archived == false and .disabled == false) | .name' "$MANIFEST_FILE")
        log_info "Scanning all active repositories"
    fi
    
    local healed=0
    local skipped=0
    
    while IFS= read -r repo_name; do
        if analyze_failures "$repo_name"; then
            local strategy
            strategy=$(determine_strategy "$repo_name")
            
            if apply_healing "$repo_name" "$strategy"; then
                trigger_rerun "$repo_name"
                ((healed++))
            else
                log_error "Failed to heal: $repo_name"
            fi
        else
            ((skipped++))
        fi
    done <<< "$repos"
    
    # Print summary
    echo ""
    echo "========================================"
    echo "Self-Healing Summary"
    echo "========================================"
    echo "Repositories healed: $healed"
    echo "Repositories skipped: $skipped"
    echo "========================================"
    
    log_info "Self-healing process complete"
}

main "$@"
