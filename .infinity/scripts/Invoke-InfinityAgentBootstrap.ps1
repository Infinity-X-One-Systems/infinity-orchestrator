#Requires -Version 7.0
<#
.SYNOPSIS
    Infinity Agent Bootstrap — emits a JSON payload for agent initialisation.

.DESCRIPTION
    Bootstraps an Infinity Orchestrator agent session by:
      1. Attempting to load local memory from .infinity/ACTIVE_MEMORY.md.
      2. If local memory is absent or stale, preferring GitHub-first memory
         retrieval from infinity-core-memory via GitHub App authentication.
      3. Loading the endpoint registry from .infinity/connectors/endpoint-registry.json.
      4. Loading the org repo index from .infinity/ORG_REPO_INDEX.json.
      5. Emitting a structured JSON bootstrap payload that includes instruction
         pointers, memory retrieval plan, and endpoint registry summary.

    The script is DEFENSIVE and IDEMPOTENT:
      - Missing local memory does NOT cause the script to fail; it degrades
        gracefully and records a memory_retrieval_plan in the output payload.
      - It is safe to run multiple times; re-runs do not alter repository state.
      - All tokens are masked immediately after creation (::add-mask::).

.PARAMETER WorkspacePath
    Path to the checked-out infinity-orchestrator workspace.
    Defaults to the current working directory.

.PARAMETER OutputPath
    File path to write the JSON bootstrap payload.
    Defaults to stdout only (no file written).

.PARAMETER MemoryMaxAgeMinutes
    Maximum acceptable age of local ACTIVE_MEMORY.md in minutes before a
    GitHub-first refresh is preferred. Default: 120 (2 hours).

.EXAMPLE
    ./.infinity/scripts/Invoke-InfinityAgentBootstrap.ps1

.EXAMPLE
    ./.infinity/scripts/Invoke-InfinityAgentBootstrap.ps1 -OutputPath /tmp/bootstrap.json

.NOTES
    Environment variables consumed (all optional — script degrades gracefully):
      GITHUB_APP_ID               Numeric GitHub App ID for memory retrieval.
      GITHUB_APP_PRIVATE_KEY      PEM RSA private key for the GitHub App.
      GITHUB_APP_INSTALLATION_ID  Pre-known installation ID (skips discovery).
      MEMORY_REPO_REF             Branch in infinity-core-memory (default: main).
      ORCHESTRATOR_WORKSPACE      Override for WorkspacePath parameter.

    TAP Protocol compliance:
      P-001 — No secrets in output.
      P-007 — Graceful degradation when ACTIVE_MEMORY.md is absent.
#>

[CmdletBinding()]
param(
    [string] $WorkspacePath      = '',
    [string] $OutputPath         = '',
    [int]    $MemoryMaxAgeMinutes = 120
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ── Constants ─────────────────────────────────────────────────────────────────
$MEMORY_ORG       = 'Infinity-X-One-Systems'
$MEMORY_REPO      = 'infinity-core-memory'
$GITHUB_API       = 'https://api.github.com'
$SCRIPT_VERSION   = '1.0.0'

# ── Helper: non-shadowing output wrappers ─────────────────────────────────────
function Write-StepHeader {
    param([string]$Message)
    Write-Host "==> $Message"
}

function Write-Info {
    param([string]$Message)
    Write-Host "    $Message"
}

function Write-WarningStatus {
    param([string]$Message)
    Write-Host "::warning::$Message"
}

function Write-ErrorStatus {
    param([string]$Message)
    Write-Host "::error::$Message"
    [Console]::Error.WriteLine($Message)
}

# ── Helper: mask a secret in GitHub Actions logs ──────────────────────────────
function Invoke-MaskSecret {
    param([string]$Secret)
    if (-not [string]::IsNullOrEmpty($Secret)) {
        Write-Host "::add-mask::$Secret"
    }
}

# ── Helper: URL-safe Base64 without padding ───────────────────────────────────
function ConvertTo-Base64Url {
    param([byte[]]$Bytes)
    return [Convert]::ToBase64String($Bytes) `
        -replace '\+', '-' `
        -replace '/', '_' `
        -replace '=', ''
}

# ── Build a short-lived GitHub App JWT (RS256) ────────────────────────────────
function New-GitHubAppJWT {
    param([string]$AppId, [string]$PrivateKeyPem)

    $now        = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $headerB64  = ConvertTo-Base64Url ([Text.Encoding]::UTF8.GetBytes('{"alg":"RS256","typ":"JWT"}'))
    $payloadB64 = ConvertTo-Base64Url ([Text.Encoding]::UTF8.GetBytes(
        "{`"iat`":$($now - 60),`"exp`":$($now + 600),`"iss`":`"$AppId`"}"
    ))
    $signingInput = "$headerB64.$payloadB64"
    $rsa = [System.Security.Cryptography.RSA]::Create()
    try {
        $rsa.ImportFromPem($PrivateKeyPem)
        $sig = $rsa.SignData(
            [Text.Encoding]::UTF8.GetBytes($signingInput),
            [Security.Cryptography.HashAlgorithmName]::SHA256,
            [Security.Cryptography.RSASignaturePadding]::Pkcs1
        )
    }
    finally { $rsa.Dispose() }

    return "$signingInput.$(ConvertTo-Base64Url $sig)"
}

# ── Minimal GitHub API wrapper ────────────────────────────────────────────────
function Invoke-GitHubApi {
    param(
        [string]   $Uri,
        [string]   $Method    = 'GET',
        [string]   $Token,
        [string]   $TokenType = 'Bearer',
        [hashtable]$Body      = $null
    )
    $headers = @{
        'Accept'               = 'application/vnd.github+json'
        'Authorization'        = "$TokenType $Token"
        'X-GitHub-Api-Version' = '2022-11-28'
        'User-Agent'           = 'InfinityOrchestrator-Bootstrap/1.0'
    }
    $params = @{ Uri = $Uri; Method = $Method; Headers = $headers }
    if ($null -ne $Body) {
        $params['Body']        = ($Body | ConvertTo-Json -Depth 10)
        $params['ContentType'] = 'application/json'
    }
    return Invoke-RestMethod @params
}

# ── Attempt GitHub-first memory retrieval ─────────────────────────────────────
function Get-GitHubMemory {
    param(
        [string]$AppId,
        [string]$PrivateKey,
        [string]$InstallId,
        [string]$MemoryRef
    )

    try {
        Write-StepHeader 'Attempting GitHub-first memory retrieval'
        # Normalise \n-escaped newlines that some secret stores produce
        # (GitHub Actions secrets often store the PEM key with literal \n sequences).
        $PrivateKey = $PrivateKey -replace '\\n', "`n"
        $jwt = New-GitHubAppJWT -AppId $AppId -PrivateKeyPem $PrivateKey
        Invoke-MaskSecret -Secret $jwt

        if ([string]::IsNullOrWhiteSpace($InstallId)) {
            Write-Info 'Discovering GitHub App installation...'
            $installations = Invoke-GitHubApi -Uri "$GITHUB_API/app/installations" -Token $jwt
            $install = $installations | Where-Object { $_.account.login -eq $MEMORY_ORG } | Select-Object -First 1
            if ($null -eq $install) {
                Write-WarningStatus "No GitHub App installation found for org '$MEMORY_ORG'. Skipping GitHub-first retrieval."
                return $null
            }
            $InstallId = [string]$install.id
        }

        $tokenResp  = Invoke-GitHubApi -Uri "$GITHUB_API/app/installations/$InstallId/access_tokens" -Method 'POST' -Token $jwt
        $accessToken = $tokenResp.token
        Invoke-MaskSecret -Secret $accessToken

        $contentResp = Invoke-GitHubApi `
            -Uri   "$GITHUB_API/repos/$MEMORY_ORG/$MEMORY_REPO/contents/.infinity/ACTIVE_MEMORY.md?ref=$MemoryRef" `
            -Token $accessToken

        # GitHub API returns base64 content with embedded newlines for readability;
        # strip them before decoding so FromBase64String receives a clean string.
        $rawBase64 = $contentResp.content
        if ([string]::IsNullOrEmpty($rawBase64)) {
            Write-WarningStatus 'GitHub API returned empty content for ACTIVE_MEMORY.md.'
            return $null
        }
        try {
            $memoryContent = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String(($rawBase64 -replace '[\r\n]','')))
        }
        catch {
            Write-WarningStatus "Failed to decode base64 content from GitHub API: $($_.Exception.Message)"
            return $null
        }
        Write-Info "GitHub-first memory retrieved ($($memoryContent.Length) chars)."
        return $memoryContent
    }
    catch {
        Write-WarningStatus "GitHub-first memory retrieval failed: $($_.Exception.Message)"
        return $null
    }
}

# ════════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════════

Write-StepHeader "Infinity Agent Bootstrap v$SCRIPT_VERSION"

# ── Resolve workspace path ────────────────────────────────────────────────────
if ([string]::IsNullOrWhiteSpace($WorkspacePath)) {
    $WorkspacePath = if ($env:ORCHESTRATOR_WORKSPACE) { $env:ORCHESTRATOR_WORKSPACE } else { $PWD.Path }
}
Write-Info "Workspace: $WorkspacePath"

# ── Read env vars (all optional) ─────────────────────────────────────────────
$AppId      = $env:GITHUB_APP_ID             ?? ''
$PrivateKey = $env:GITHUB_APP_PRIVATE_KEY    ?? ''
$InstallId  = $env:GITHUB_APP_INSTALLATION_ID ?? ''
$MemoryRef  = if ($env:MEMORY_REPO_REF) { $env:MEMORY_REPO_REF } else { 'main' }

$hasAppCreds = (-not [string]::IsNullOrWhiteSpace($AppId)) -and (-not [string]::IsNullOrWhiteSpace($PrivateKey))

# ── Bootstrap payload initialisation ─────────────────────────────────────────
$payload = [ordered]@{
    schema_version    = '1.0.0'
    bootstrap_time    = [System.DateTime]::UtcNow.ToString('o')
    script_version    = $SCRIPT_VERSION
    workspace         = $WorkspacePath
    memory_status     = 'unknown'
    memory_source     = $null
    memory_age_minutes = $null
    memory_content_lines = $null
    memory_retrieval_plan = [ordered]@{
        local_path     = '.infinity/ACTIVE_MEMORY.md'
        github_source  = "$MEMORY_ORG/$MEMORY_REPO"
        github_ref     = $MemoryRef
        github_auth    = if ($hasAppCreds) { 'github-app' } else { 'unavailable' }
        strategy       = 'local-first-then-github'
    }
    endpoint_registry = $null
    org_repo_index    = $null
    tap_policy        = [ordered]@{
        version        = '1.0.0'
        policy_path    = '.infinity/policies/tap-protocol.md'
        rules_active   = @('P-001','P-003','P-005','P-007')
    }
    instruction_pointers = [ordered]@{
        active_memory          = '.infinity/ACTIVE_MEMORY.md'
        agent_entrypoint       = '.infinity/AGENT_ENTRYPOINT.md'
        endpoint_registry_json = '.infinity/connectors/endpoint-registry.json'
        endpoint_registry_md   = '.infinity/connectors/endpoint-registry.md'
        auth_matrix            = '.infinity/connectors/auth-matrix.md'
        tap_policy             = '.infinity/policies/tap-protocol.md'
        governance_runbook     = '.infinity/runbooks/governance-enforcement.md'
        memory_sync_runbook    = '.infinity/runbooks/memory-sync.md'
        org_repo_index_json    = '.infinity/ORG_REPO_INDEX.json'
        org_repo_index_md      = '.infinity/ORG_REPO_INDEX.md'
    }
    warnings = [System.Collections.Generic.List[string]]::new()
    decision_log = [ordered]@{
        actor            = 'agent-bootstrap'
        policy_rules_checked = @('P-001','P-007')
        decision         = 'allowed'
        justification    = ''
    }
}

# ── Step 1: Try local memory ──────────────────────────────────────────────────
Write-StepHeader 'Step 1: Checking local ACTIVE_MEMORY.md'

$localMemoryPath = Join-Path $WorkspacePath '.infinity' 'ACTIVE_MEMORY.md'
$localMemoryFound = Test-Path $localMemoryPath
$memoryContent    = $null

if ($localMemoryFound) {
    $rawContent = Get-Content -Raw $localMemoryPath
    if (-not [string]::IsNullOrWhiteSpace($rawContent)) {
        $fileInfo = Get-Item $localMemoryPath
        $ageMinutes = [int]([System.DateTime]::UtcNow - $fileInfo.LastWriteTimeUtc).TotalMinutes

        Write-Info "Local ACTIVE_MEMORY.md found ($($rawContent.Split("`n").Count) lines, age: ${ageMinutes}m)."

        if ($ageMinutes -le $MemoryMaxAgeMinutes) {
            $memoryContent = $rawContent
            $payload.memory_status        = 'local-fresh'
            $payload.memory_source        = 'local'
            $payload.memory_age_minutes   = $ageMinutes
            $payload.memory_content_lines = $rawContent.Split("`n").Count
        }
        else {
            Write-WarningStatus "Local ACTIVE_MEMORY.md is ${ageMinutes}m old (threshold: ${MemoryMaxAgeMinutes}m). Preferring GitHub-first."
            $payload.memory_status = 'local-stale'
            $payload.warnings.Add("Local ACTIVE_MEMORY.md is stale (${ageMinutes}m). GitHub-first retrieval will be attempted.")
        }
    }
    else {
        Write-WarningStatus 'Local ACTIVE_MEMORY.md is empty.'
        $payload.memory_status = 'local-empty'
        $payload.warnings.Add('Local ACTIVE_MEMORY.md is empty.')
    }
}
else {
    Write-WarningStatus 'Local ACTIVE_MEMORY.md not found — this is expected on a clean checkout.'
    $payload.memory_status = 'local-missing'
    $payload.warnings.Add('Local ACTIVE_MEMORY.md not found. Attempting GitHub-first retrieval.')
}

# ── Step 2: GitHub-first retrieval if needed ─────────────────────────────────
if ($null -eq $memoryContent) {
    Write-StepHeader 'Step 2: GitHub-first memory retrieval'
    if ($hasAppCreds) {
        $githubMemory = Get-GitHubMemory -AppId $AppId -PrivateKey $PrivateKey `
                                          -InstallId $InstallId -MemoryRef $MemoryRef
        if ($null -ne $githubMemory) {
            $memoryContent = $githubMemory
            $payload.memory_status        = 'github-retrieved'
            $payload.memory_source        = "github:$MEMORY_ORG/$MEMORY_REPO@$MemoryRef"
            $payload.memory_content_lines = $githubMemory.Split("`n").Count
        }
        else {
            $payload.memory_status = 'github-unavailable'
            $payload.warnings.Add('GitHub-first memory retrieval returned no content.')
        }
    }
    else {
        Write-WarningStatus 'GitHub App credentials not set — skipping GitHub-first retrieval. Set GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY to enable.'
        $payload.memory_status = 'degraded-no-credentials'
        $payload.warnings.Add('GITHUB_APP_ID or GITHUB_APP_PRIVATE_KEY not set. Running in degraded mode without memory.')
    }
}

# ── Step 3: Load endpoint registry ───────────────────────────────────────────
Write-StepHeader 'Step 3: Loading endpoint registry'
$registryPath = Join-Path $WorkspacePath '.infinity' 'connectors' 'endpoint-registry.json'
if (Test-Path $registryPath) {
    try {
        $registryJson = Get-Content -Raw $registryPath | ConvertFrom-Json -AsHashtable
        $categoryCount = ($registryJson.categories ?? @{}).Count
        $payload.endpoint_registry = [ordered]@{
            status         = 'loaded'
            path           = '.infinity/connectors/endpoint-registry.json'
            version        = $registryJson.version ?? 'unknown'
            category_count = $categoryCount
        }
        Write-Info "Endpoint registry loaded ($categoryCount categories)."
    }
    catch {
        Write-WarningStatus "Failed to parse endpoint registry: $($_.Exception.Message)"
        $payload.endpoint_registry = [ordered]@{ status = 'parse-error'; error = $_.Exception.Message }
        $payload.warnings.Add("Endpoint registry parse error: $($_.Exception.Message)")
    }
}
else {
    $payload.endpoint_registry = [ordered]@{ status = 'not-found'; path = '.infinity/connectors/endpoint-registry.json' }
    $payload.warnings.Add('Endpoint registry not found at .infinity/connectors/endpoint-registry.json.')
}

# ── Step 4: Load org repo index ───────────────────────────────────────────────
Write-StepHeader 'Step 4: Loading org repo index'
$indexPath = Join-Path $WorkspacePath '.infinity' 'ORG_REPO_INDEX.json'
if (Test-Path $indexPath) {
    try {
        $indexJson = Get-Content -Raw $indexPath | ConvertFrom-Json -AsHashtable
        $payload.org_repo_index = [ordered]@{
            status       = 'loaded'
            path         = '.infinity/ORG_REPO_INDEX.json'
            last_updated = $indexJson.last_updated ?? 'unknown'
            total_repos  = $indexJson.statistics.total ?? 0
            active_repos = $indexJson.statistics.active ?? 0
        }
        Write-Info "Org repo index loaded (total: $($indexJson.statistics.total ?? 0))."
    }
    catch {
        Write-WarningStatus "Failed to parse org repo index: $($_.Exception.Message)"
        $payload.org_repo_index = [ordered]@{ status = 'parse-error'; error = $_.Exception.Message }
        $payload.warnings.Add("Org repo index parse error: $($_.Exception.Message)")
    }
}
else {
    $payload.org_repo_index = [ordered]@{ status = 'not-found'; path = '.infinity/ORG_REPO_INDEX.json' }
    $payload.warnings.Add('Org repo index not found. Trigger org-repo-index workflow to generate it.')
}

# ── Finalise decision log ─────────────────────────────────────────────────────
$decisionStatus = if ($payload.memory_status -in @('local-fresh','github-retrieved')) {
    'allowed'
} elseif ($payload.memory_status -in @('degraded-no-credentials','github-unavailable','local-missing','local-empty','local-stale')) {
    'degraded'
} else {
    'allowed'
}

$payload.decision_log.decision      = $decisionStatus
$payload.decision_log.justification = "Memory status: $($payload.memory_status). Warnings: $($payload.warnings.Count)."

# ── Emit JSON bootstrap payload ───────────────────────────────────────────────
Write-StepHeader 'Emitting bootstrap payload'
$jsonPayload = $payload | ConvertTo-Json -Depth 10

Write-Host $jsonPayload

if (-not [string]::IsNullOrWhiteSpace($OutputPath)) {
    $jsonPayload | Set-Content -Path $OutputPath -Encoding UTF8
    Write-Info "Bootstrap payload written to: $OutputPath"
}

Write-StepHeader "Bootstrap complete. Status: $decisionStatus | Memory: $($payload.memory_status)"

# Exit with a non-zero code only on hard failures, not on degraded mode
if ($decisionStatus -eq 'denied') {
    exit 1
}
exit 0
