#!/usr/bin/env bash
# Portfolio Audit Script
# Collects repository metadata for both the Infinity-X-One-Systems org and the
# InfinityXOneSystems user account, then writes a Markdown report.
#
# Usage:
#   GH_TOKEN=<token> ./scripts/portfolio-audit.sh [--output-dir reports]
#
# Environment variables:
#   GH_TOKEN          GitHub token (must have repo read + org read access)
#   ORG_NAME          Org to audit (default: Infinity-X-One-Systems)
#   USER_NAME         User to audit (default: InfinityXOneSystems)
#   OUTPUT_DIR        Directory for report files (default: reports)
#   REPORT_DATE       ISO date for report filename (default: today)

set -euo pipefail

# ── Constants ────────────────────────────────────────────────────────────────

ORG_NAME="${ORG_NAME:-Infinity-X-One-Systems}"
USER_NAME="${USER_NAME:-InfinityXOneSystems}"
OUTPUT_DIR="${OUTPUT_DIR:-reports}"
REPORT_DATE="${REPORT_DATE:-$(date -u +"%Y-%m-%d")}"
REPORT_FILE="${OUTPUT_DIR}/portfolio-audit-${REPORT_DATE}.md"
JSON_FILE="${OUTPUT_DIR}/portfolio-audit-${REPORT_DATE}.json"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ── Logging helpers ───────────────────────────────────────────────────────────

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ── Prerequisites ─────────────────────────────────────────────────────────────

check_prerequisites() {
    log_info "Checking prerequisites..."

    local missing=0
    for cmd in gh jq; do
        if ! command -v "$cmd" &>/dev/null; then
            log_error "Required command not found: $cmd"
            missing=1
        fi
    done
    [ "$missing" -eq 0 ] || exit 1

    log_info "Prerequisites OK."
}

# ── Repository fetch helpers ──────────────────────────────────────────────────

# Fetch repositories for a GitHub entity (org or user).
# Returns a JSON array of enriched repo objects or an empty array on failure.
#
# Args:
#   $1  entity type: "org" or "user"
#   $2  entity name (org or username)
fetch_repos() {
    local entity_type="$1"
    local entity_name="$2"

    log_info "Fetching repos for ${entity_type}: ${entity_name}"

    local raw
    if ! raw=$(gh repo list "$entity_name" \
        --json name,visibility,isArchived,pushedAt,defaultBranchRef,openIssues \
        --limit 1000 2>&1); then
        log_warn "gh repo list failed for ${entity_type} '${entity_name}': ${raw}"
        log_warn "Required permissions: 'repo' scope for user repos; 'read:org' + app installation for org repos."
        echo "[]"
        return
    fi

    # Enrich with open PR count — best-effort per repo (P-007 graceful degradation).
    # gh repo list does not expose openPullRequests, so we fetch it separately for each repo.
    local enriched
    enriched=$(echo "$raw" | jq --arg entity "$entity_name" --arg etype "$entity_type" '
        map({
            name:            .name,
            full_name:       ($entity + "/" + .name),
            entity_type:     $etype,
            visibility:      .visibility,
            archived:        .isArchived,
            pushed_at:       (.pushedAt // "unknown"),
            default_branch:  (.defaultBranchRef.name // "main"),
            open_issues:     (.openIssues // 0),
            open_prs:        null
        })
    ')

    # Populate open_prs for each repo (best-effort; skipped on API failure).
    local count full_name updated_repos repo
    updated_repos="[]"
    while IFS= read -r repo; do
        full_name=$(echo "$repo" | jq -r '.full_name')
        count=$(fetch_open_pr_count "$full_name")
        repo=$(echo "$repo" | jq --argjson c "$count" '.open_prs = $c')
        updated_repos=$(echo "$updated_repos" | jq --argjson r "$repo" '. + [$r]')
    done < <(echo "$enriched" | jq -c '.[]')

    echo "$updated_repos"
}

# Fetch open PR count for a single repo (best-effort; returns 0 on failure).
fetch_open_pr_count() {
    local full_name="$1"
    local count
    if ! count=$(gh api "repos/${full_name}/pulls?state=open&per_page=100" \
        --jq 'length' 2>/dev/null); then
        echo 0
        return
    fi
    echo "$count"
}

# ── Markdown report builder ───────────────────────────────────────────────────

build_markdown_report() {
    local org_repos="$1"
    local user_repos="$2"
    local timestamp="$3"

    local org_total   user_total
    org_total=$(echo  "$org_repos"  | jq 'length')
    user_total=$(echo "$user_repos" | jq 'length')

    local org_active  user_active
    org_active=$(echo  "$org_repos"  | jq '[.[] | select(.archived == false)] | length')
    user_active=$(echo "$user_repos" | jq '[.[] | select(.archived == false)] | length')

    local org_archived user_archived
    org_archived=$(echo  "$org_repos"  | jq '[.[] | select(.archived == true)] | length')
    user_archived=$(echo "$user_repos" | jq '[.[] | select(.archived == true)] | length')

    {
        echo "# Portfolio Audit Report"
        echo ""
        echo "> **Generated:** \`${timestamp}\`  "
        echo "> **Workflow:** \`portfolio-audit.yml\`  "
        echo "> **Report date:** \`${REPORT_DATE}\`"
        echo ""
        echo "---"
        echo ""
        echo "## Summary"
        echo ""
        echo "| Entity | Total | Active | Archived |"
        echo "|--------|-------|--------|----------|"
        echo "| Org: \`${ORG_NAME}\` | ${org_total} | ${org_active} | ${org_archived} |"
        echo "| User: \`${USER_NAME}\` | ${user_total} | ${user_active} | ${user_archived} |"
        echo ""
        echo "---"
        echo ""

        # ── Org repos ──
        echo "## Org Repositories — \`${ORG_NAME}\`"
        echo ""
        if [ "$org_total" -eq 0 ]; then
            echo "> ⚠️ No repositories found. Check that \`INFINITY_APP_TOKEN\` is set and the"
            echo "> GitHub App is installed org-wide with **Read access to members** and **metadata**."
        else
            echo "| Repository | Visibility | Archived | Default Branch | Open Issues | Open PRs | Last Push |"
            echo "|------------|------------|----------|---------------|-------------|----------|-----------|"
            echo "$org_repos" | jq -r '.[] |
                "| `\(.name)` | \(.visibility) | \(if .archived then "✅" else "—" end) | `\(.default_branch)` | \(.open_issues) | \(.open_prs // "—") | \(.pushed_at[:10]) |"'
        fi
        echo ""
        echo "---"
        echo ""

        # ── User repos ──
        echo "## User Repositories — \`${USER_NAME}\`"
        echo ""
        if [ "$user_total" -eq 0 ]; then
            echo "> ℹ️ No repositories found. The \`INFINITY_APP_TOKEN\` may not have access to"
            echo "> personal user repositories. This is expected if the token is org-scoped."
            echo "> See required permissions in the workflow documentation."
        else
            echo "| Repository | Visibility | Archived | Default Branch | Open Issues | Open PRs | Last Push |"
            echo "|------------|------------|----------|---------------|-------------|----------|-----------|"
            echo "$user_repos" | jq -r '.[] |
                "| `\(.name)` | \(.visibility) | \(if .archived then "✅" else "—" end) | `\(.default_branch)` | \(.open_issues) | \(.open_prs // "—") | \(.pushed_at[:10]) |"'
        fi
        echo ""
        echo "---"
        echo ""
        echo "*Auto-generated by the \`portfolio-audit\` workflow. Do not edit manually.*"
        echo "*To refresh, trigger the workflow from the Actions tab or push to \`main\`.*"
    } > "$REPORT_FILE"

    log_info "Markdown report written to: ${REPORT_FILE}"
}

# ── JSON report builder ───────────────────────────────────────────────────────

build_json_report() {
    local org_repos="$1"
    local user_repos="$2"
    local timestamp="$3"

    jq -n \
        --arg ts        "$timestamp" \
        --arg date      "$REPORT_DATE" \
        --arg org       "$ORG_NAME" \
        --arg user      "$USER_NAME" \
        --argjson org_repos  "$org_repos" \
        --argjson user_repos "$user_repos" \
        '{
            version:      "1.0.0",
            generated_at: $ts,
            report_date:  $date,
            generated_by: "portfolio-audit.yml",
            note:         "Auto-generated by the portfolio-audit workflow. Do not edit manually.",
            org:  { name: $org,  repositories: $org_repos  },
            user: { name: $user, repositories: $user_repos },
            statistics: {
                org: {
                    total:    ($org_repos  | length),
                    active:   ($org_repos  | map(select(.archived == false)) | length),
                    archived: ($org_repos  | map(select(.archived == true))  | length)
                },
                user: {
                    total:    ($user_repos | length),
                    active:   ($user_repos | map(select(.archived == false)) | length),
                    archived: ($user_repos | map(select(.archived == true))  | length)
                }
            }
        }' > "$JSON_FILE"

    log_info "JSON report written to: ${JSON_FILE}"
}

# ── Main ──────────────────────────────────────────────────────────────────────

main() {
    log_info "Portfolio Audit starting..."
    log_info "Org:  ${ORG_NAME}"
    log_info "User: ${USER_NAME}"
    log_info "Output directory: ${OUTPUT_DIR}"

    check_prerequisites

    mkdir -p "$OUTPUT_DIR"

    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # Fetch repositories (best-effort for both; failures produce empty arrays per P-007)
    local org_repos user_repos
    org_repos=$(fetch_repos  "org"  "$ORG_NAME")
    user_repos=$(fetch_repos "user" "$USER_NAME")

    # Build reports
    build_markdown_report "$org_repos" "$user_repos" "$timestamp"
    build_json_report     "$org_repos" "$user_repos" "$timestamp"

    # Print summary
    echo ""
    log_info "Audit complete."
    log_info "  Org repos found  : $(echo "$org_repos"  | jq 'length')"
    log_info "  User repos found : $(echo "$user_repos" | jq 'length')"
    log_info "  Markdown report  : ${REPORT_FILE}"
    log_info "  JSON report      : ${JSON_FILE}"
}

main "$@"
