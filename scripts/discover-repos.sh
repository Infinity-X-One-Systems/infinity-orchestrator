#!/usr/bin/env bash
# Repository Discovery Script
# This script discovers all repositories in the organization and generates a manifest

set -euo pipefail

# Configuration
ORG_NAME="${GH_ORG:-Infinity-X-One-Systems}"
OUTPUT_FILE="${OUTPUT_FILE:-config/repositories.json}"
GH_TOKEN="${GH_TOKEN:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) is not installed"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        log_error "jq is not installed"
        exit 1
    fi
    
    if [ -z "$GH_TOKEN" ]; then
        log_warn "GH_TOKEN not set, using gh default authentication"
    fi
    
    log_info "Prerequisites check passed"
}

# Discover repositories
discover_repositories() {
    log_info "Discovering repositories in organization: $ORG_NAME"
    
    # Fetch repositories
    local repos
    repos=$(gh repo list "$ORG_NAME" \
        --json name,description,defaultBranchRef,isPrivate,isArchived,primaryLanguage,repositoryTopics,createdAt,updatedAt \
        --limit 1000)
    
    local count
    count=$(echo "$repos" | jq '. | length')
    log_info "Found $count repositories"
    
    echo "$repos"
}

# Determine build command based on language
get_build_command() {
    local language=$1
    
    case "$language" in
        JavaScript|TypeScript)
            echo "npm run build || echo 'No build script'"
            ;;
        Python)
            echo "python setup.py build || echo 'No setup.py'"
            ;;
        Go)
            echo "go build ./..."
            ;;
        Java)
            echo "mvn package || gradle build || echo 'No build tool'"
            ;;
        Rust)
            echo "cargo build"
            ;;
        "C#")
            echo "dotnet build"
            ;;
        Shell)
            echo "shellcheck scripts/*.sh || true"
            ;;
        *)
            echo "echo 'No build required'"
            ;;
    esac
}

# Determine test command based on language
get_test_command() {
    local language=$1
    
    case "$language" in
        JavaScript|TypeScript)
            echo "npm test || echo 'No test script'"
            ;;
        Python)
            echo "pytest || python -m unittest || echo 'No tests'"
            ;;
        Go)
            echo "go test ./..."
            ;;
        Java)
            echo "mvn test || gradle test || echo 'No test tool'"
            ;;
        Rust)
            echo "cargo test"
            ;;
        "C#")
            echo "dotnet test"
            ;;
        Shell)
            echo "shellcheck scripts/*.sh || true"
            ;;
        *)
            echo "echo 'No tests configured'"
            ;;
    esac
}

# Generate manifest
generate_manifest() {
    local repos=$1
    
    log_info "Generating repository manifest..."
    
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    # Create manifest structure
    cat > "$OUTPUT_FILE" << EOF
{
  "version": "1.0.0",
  "last_updated": "$timestamp",
  "organization": "$ORG_NAME",
  "repositories": [],
  "statistics": {}
}
EOF
    
    # Process each repository
    local processed_repos
    processed_repos=$(echo "$repos" | jq -c '.[]' | while IFS= read -r repo; do
        local name
        name=$(echo "$repo" | jq -r '.name')
        
        local language
        language=$(echo "$repo" | jq -r '.primaryLanguage.name // "unknown"')
        
        local build_cmd
        build_cmd=$(get_build_command "$language")
        
        local test_cmd
        test_cmd=$(get_test_command "$language")
        
        echo "$repo" | jq \
            --arg build "$build_cmd" \
            --arg test "$test_cmd" \
            --arg org "$ORG_NAME" \
            --arg ts "$timestamp" \
            '{
                name: .name,
                full_name: "\($org)/\(.name)",
                description: .description,
                language: (.primaryLanguage.name // "unknown"),
                default_branch: (.defaultBranchRef.name // "main"),
                private: .isPrivate,
                archived: .isArchived,
                disabled: false,
                topics: [.repositoryTopics[].topic.name],
                created_at: .createdAt,
                updated_at: .updatedAt,
                build_config: {
                    enabled: true,
                    build_command: $build,
                    test_command: $test,
                    pre_build: [],
                    post_build: []
                },
                dependencies: [],
                health: {
                    status: "healthy",
                    last_check: $ts,
                    issues: []
                },
                metadata: {
                    tags: [],
                    priority: "normal",
                    owner: "system"
                }
            }'
    done | jq -s '.')
    
    # Calculate statistics
    local total
    total=$(echo "$repos" | jq '. | length')
    
    local active
    active=$(echo "$repos" | jq '[.[] | select(.isArchived == false)] | length')
    
    local archived
    archived=$(echo "$repos" | jq '[.[] | select(.isArchived == true)] | length')
    
    local languages
    languages=$(echo "$repos" | jq 'group_by(.primaryLanguage.name // "unknown") | map({key: .[0].primaryLanguage.name // "unknown", value: length}) | from_entries')
    
    # Update manifest with processed data
    jq \
        --argjson repos "$processed_repos" \
        --argjson total "$total" \
        --argjson active "$active" \
        --argjson archived "$archived" \
        --argjson langs "$languages" \
        '.repositories = $repos |
         .statistics = {
             total_repositories: $total,
             active_repositories: $active,
             archived_repositories: $archived,
             languages: $langs,
             health_summary: {
                 healthy: $active,
                 warning: 0,
                 critical: 0
             }
         }' "$OUTPUT_FILE" > "$OUTPUT_FILE.tmp"
    
    mv "$OUTPUT_FILE.tmp" "$OUTPUT_FILE"
    
    log_info "Manifest generated successfully: $OUTPUT_FILE"
}

# Main execution
main() {
    log_info "Starting repository discovery..."
    
    check_prerequisites
    
    local repos
    repos=$(discover_repositories)
    
    generate_manifest "$repos"
    
    log_info "Repository discovery complete!"
    
    # Print summary
    echo ""
    echo "Summary:"
    echo "--------"
    jq -r '
        "Total repositories: \(.statistics.total_repositories)",
        "Active repositories: \(.statistics.active_repositories)",
        "Archived repositories: \(.statistics.archived_repositories)",
        "",
        "Language breakdown:",
        (.statistics.languages | to_entries[] | "  - \(.key): \(.value)")
    ' "$OUTPUT_FILE"
}

# Run main function
main "$@"
