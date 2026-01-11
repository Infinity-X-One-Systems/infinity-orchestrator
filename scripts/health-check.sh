#!/usr/bin/env bash
# Health Check Script
# Checks the health of all repositories and reports status

set -euo pipefail

# Configuration
MANIFEST_FILE="${MANIFEST_FILE:-config/repositories.json}"
ORG_NAME="${GH_ORG:-Infinity-X-One-Systems}"
FAILURE_THRESHOLD="${FAILURE_THRESHOLD:-3}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Check repository health
check_repository_health() {
    local repo_name=$1
    local full_name="$ORG_NAME/$repo_name"
    
    log_info "Checking health: $repo_name"
    
    # Get recent workflow runs
    local runs
    runs=$(gh run list --repo "$full_name" --limit 10 --json status,conclusion 2>/dev/null || echo '[]')
    
    if [ "$runs" = "[]" ]; then
        echo "unknown"
        return
    fi
    
    # Count failures
    local failure_count
    failure_count=$(echo "$runs" | jq '[.[] | select(.conclusion == "failure")] | length')
    
    local total_runs
    total_runs=$(echo "$runs" | jq '. | length')
    
    if [ "$failure_count" -ge "$FAILURE_THRESHOLD" ]; then
        echo "unhealthy"
    elif [ "$failure_count" -gt 0 ]; then
        echo "warning"
    else
        echo "healthy"
    fi
}

# Main execution
main() {
    log_info "Starting health check..."
    
    if [ ! -f "$MANIFEST_FILE" ]; then
        log_error "Repository manifest not found: $MANIFEST_FILE"
        exit 1
    fi
    
    local healthy=0
    local warning=0
    local unhealthy=0
    local unknown=0
    
    # Check each repository
    while IFS= read -r repo_name; do
        local status
        status=$(check_repository_health "$repo_name")
        
        case "$status" in
            healthy)
                echo -e "  ${GREEN}✅${NC} $repo_name"
                ((healthy++))
                ;;
            warning)
                echo -e "  ${YELLOW}⚠️${NC}  $repo_name"
                ((warning++))
                ;;
            unhealthy)
                echo -e "  ${RED}❌${NC} $repo_name"
                ((unhealthy++))
                ;;
            unknown)
                echo -e "  ${NC}❓${NC} $repo_name"
                ((unknown++))
                ;;
        esac
    done < <(jq -r '.repositories[] | select(.archived == false and .disabled == false) | .name' "$MANIFEST_FILE")
    
    # Print summary
    echo ""
    echo "========================================"
    echo "Health Check Summary"
    echo "========================================"
    echo -e "${GREEN}Healthy:${NC} $healthy"
    echo -e "${YELLOW}Warning:${NC} $warning"
    echo -e "${RED}Unhealthy:${NC} $unhealthy"
    echo -e "Unknown: $unknown"
    echo "========================================"
    
    if [ $unhealthy -gt 0 ]; then
        log_error "Health check found unhealthy repositories"
        exit 1
    else
        log_info "Health check passed"
        exit 0
    fi
}

main "$@"
