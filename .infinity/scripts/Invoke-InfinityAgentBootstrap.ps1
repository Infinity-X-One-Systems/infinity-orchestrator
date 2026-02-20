#Requires -Version 7.0
<#
.SYNOPSIS
    Bootstraps the Infinity Orchestrator agent workspace without a hard
    dependency on a locally present ACTIVE_MEMORY.md.

.DESCRIPTION
    Resolves the agent workspace context by:
      1. Using a locally present .infinity/ACTIVE_MEMORY.md if it is fresh
         (within $MaxAgeMinutes of the current UTC time).
      2. Falling back to fetching the file directly from the GitHub API when
         the local copy is absent, empty, or stale.
      3. Exposing the resolved memory content via a well-known output variable
         (AGENT_MEMORY_PATH) so downstream scripts can consume it without
         duplicating resolution logic.

    Authentication follows the principle of least privilege:
      - GitHub App (JWT → installation access token) is preferred when
        GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY are set.
      - Falls back to GITHUB_TOKEN (Actions built-in token) when the App
        credentials are absent.
      - If no credentials are available the script degrades gracefully: it
        uses the local copy if present, or exits with a clear error.

    The script is idempotent and safe to call multiple times in the same
    workflow job.

.PARAMETER MaxAgeMinutes
    Maximum acceptable age (in minutes) for a locally cached ACTIVE_MEMORY.md.
    If the file is older than this value it is considered stale and will be
    re-fetched from the API.  Default: 60.

.PARAMETER OrchestratorWorkspace
    Path to the checked-out orchestrator repository.  Defaults to the current
    working directory ($PWD).

.PARAMETER MemorySourceRef
    Branch or ref in Infinity-X-One-Systems/infinity-orchestrator from which
    ACTIVE_MEMORY.md should be fetched when the local copy is stale/absent.
    Default: main.

.EXAMPLE
    ./.infinity/scripts/Invoke-InfinityAgentBootstrap.ps1

    Bootstraps with defaults.  Uses the GitHub App if credentials are
    available, otherwise falls back to GITHUB_TOKEN.

.EXAMPLE
    ./.infinity/scripts/Invoke-InfinityAgentBootstrap.ps1 -MaxAgeMinutes 30

    Forces a re-fetch if the local ACTIVE_MEMORY.md is older than 30 minutes.

.NOTES
    Outputs:
      - Sets the AGENT_MEMORY_PATH environment variable (and the equivalent
        GitHub Actions output if running inside Actions).
      - Writes a step summary to $GITHUB_STEP_SUMMARY when inside Actions.

    Required secrets (when using GitHub App auth):
      GITHUB_APP_ID             — Numeric GitHub App ID.
      GITHUB_APP_PRIVATE_KEY    — PEM-encoded RSA private key.

    Optional secrets:
      GITHUB_APP_INSTALLATION_ID — Pre-known installation ID; skips discovery.
      GITHUB_TOKEN               — Fallback when App credentials are absent.
#>

[CmdletBinding()]
param(
    [Parameter()]
    [ValidateRange(1, 1440)]
    [int]$MaxAgeMinutes = 60,

    [Parameter()]
    [string]$OrchestratorWorkspace = $PWD.Path,

    [Parameter()]
    [string]$MemorySourceRef = 'main'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ── Constants ─────────────────────────────────────────────────────────────────
$ORCHESTRATOR_ORG   = 'Infinity-X-One-Systems'
$ORCHESTRATOR_REPO  = 'infinity-orchestrator'
$MEMORY_FILE_PATH   = '.infinity/ACTIVE_MEMORY.md'
$GITHUB_API         = 'https://api.github.com'

# ── Helper: non-shadowing wrappers ────────────────────────────────────────────
function Write-StepHeader {
    param([string]$Message)
    Write-Host "==> $Message"
}

function Write-ErrorStatus {
    param([string]$Message)
    Write-Host "::error::$Message"
    [Console]::Error.WriteLine($Message)
}

function Write-WarningStatus {
    param([string]$Message)
    Write-Host "::warning::$Message"
}

function Write-Info {
    param([string]$Message)
    Write-Host "    $Message"
}

# ── Helper: mask a secret in GitHub Actions logs ─────────────────────────────
function Invoke-MaskSecret {
    param([string]$Secret)
    if (-not [string]::IsNullOrEmpty($Secret)) {
        Write-Host "::add-mask::$Secret"
    }
}

# ── Helper: set an Actions output variable ────────────────────────────────────
function Set-ActionsOutput {
    param([string]$Name, [string]$Value)
    if ($env:GITHUB_OUTPUT) {
        "$Name=$Value" | Out-File -FilePath $env:GITHUB_OUTPUT -Encoding utf8 -Append
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

# ── Build a short-lived GitHub App JWT (RS256) ───────────────────────────────
function New-GitHubAppJWT {
    param(
        [string]$AppId,
        [string]$PrivateKeyPem
    )

    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $iat = $now - 60    # 60 seconds in the past (clock-skew tolerance)
    $exp = $now + 600   # 10-minute expiry (GitHub maximum)

    $headerB64  = ConvertTo-Base64Url -Bytes (
        [Text.Encoding]::UTF8.GetBytes('{"alg":"RS256","typ":"JWT"}')
    )
    $payloadB64 = ConvertTo-Base64Url -Bytes (
        [Text.Encoding]::UTF8.GetBytes(
            "{`"iat`":$iat,`"exp`":$exp,`"iss`":`"$AppId`"}"
        )
    )

    $signingInput = "$headerB64.$payloadB64"

    $rsa = [System.Security.Cryptography.RSA]::Create()
    try {
        $rsa.ImportFromPem($PrivateKeyPem)
        $sigBytes = $rsa.SignData(
            [Text.Encoding]::UTF8.GetBytes($signingInput),
            [Security.Cryptography.HashAlgorithmName]::SHA256,
            [Security.Cryptography.RSASignaturePadding]::Pkcs1
        )
    }
    finally {
        $rsa.Dispose()
    }

    return "$signingInput.$(ConvertTo-Base64Url -Bytes $sigBytes)"
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
        'User-Agent'           = 'InfinityOrchestrator-AgentBootstrap/1.0'
    }

    $params = @{ Uri = $Uri; Method = $Method; Headers = $headers }

    if ($null -ne $Body) {
        $params['Body']        = ($Body | ConvertTo-Json -Depth 10)
        $params['ContentType'] = 'application/json'
    }

    return Invoke-RestMethod @params
}

# ── Resolve an access token using whichever credentials are available ─────────
function Resolve-AccessToken {
    $AppId      = $env:GITHUB_APP_ID
    $PrivateKey = $env:GITHUB_APP_PRIVATE_KEY
    $InstallId  = $env:GITHUB_APP_INSTALLATION_ID
    $GitHubToken = $env:GITHUB_TOKEN

    # Prefer GitHub App when credentials are present.
    if (-not [string]::IsNullOrWhiteSpace($AppId) -and
        -not [string]::IsNullOrWhiteSpace($PrivateKey)) {

        Write-StepHeader 'Authenticating via GitHub App'
        $PrivateKey = $PrivateKey -replace '\\n', "`n"
        $jwt = New-GitHubAppJWT -AppId $AppId -PrivateKeyPem $PrivateKey
        Invoke-MaskSecret -Secret $jwt

        if ([string]::IsNullOrWhiteSpace($InstallId)) {
            Write-Info "Discovering installation for org: $ORCHESTRATOR_ORG"
            $installations = Invoke-GitHubApi -Uri "$GITHUB_API/app/installations" -Token $jwt
            $installation  = $installations |
                             Where-Object { $_.account.login -eq $ORCHESTRATOR_ORG } |
                             Select-Object -First 1
            if ($null -eq $installation) {
                throw "No GitHub App installation found for org '$ORCHESTRATOR_ORG'."
            }
            $InstallId = [string]$installation.id
            Write-Info "Resolved installation ID: $InstallId"
        }

        $tokenResponse = Invoke-GitHubApi `
            -Uri    "$GITHUB_API/app/installations/$InstallId/access_tokens" `
            -Method 'POST' `
            -Token  $jwt
        $accessToken = $tokenResponse.token
        Invoke-MaskSecret -Secret $accessToken
        return $accessToken
    }

    # Fall back to GITHUB_TOKEN (Actions built-in).
    if (-not [string]::IsNullOrWhiteSpace($GitHubToken)) {
        Write-WarningStatus (
            'GITHUB_APP_ID/GITHUB_APP_PRIVATE_KEY not set. ' +
            'Falling back to GITHUB_TOKEN — read-only access assumed.'
        )
        return $GitHubToken
    }

    return $null
}

# ── Fetch ACTIVE_MEMORY.md via the GitHub Contents API ───────────────────────
function Get-MemoryFromApi {
    param([string]$Token, [string]$Ref)

    $uri = "$GITHUB_API/repos/$ORCHESTRATOR_ORG/$ORCHESTRATOR_REPO/contents/$MEMORY_FILE_PATH?ref=$Ref"
    Write-Info "Fetching: $uri"

    $authHeaders = @{
        'Accept'               = 'application/vnd.github.raw+json'
        'Authorization'        = "Bearer $Token"
        'X-GitHub-Api-Version' = '2022-11-28'
        'User-Agent'           = 'InfinityOrchestrator-AgentBootstrap/1.0'
    }

    $content = Invoke-RestMethod -Uri $uri -Method GET -Headers $authHeaders
    return $content
}

# ── Check if the local memory file is fresh enough ───────────────────────────
function Test-LocalMemoryFresh {
    param([string]$FilePath, [int]$MaxAgeMinutes)

    if (-not (Test-Path $FilePath)) { return $false }

    $content = Get-Content -Raw -Path $FilePath
    if ([string]::IsNullOrWhiteSpace($content)) { return $false }

    $lastWrite = (Get-Item $FilePath).LastWriteTimeUtc
    $ageMinutes = ([DateTimeOffset]::UtcNow - $lastWrite).TotalMinutes
    if ($ageMinutes -gt $MaxAgeMinutes) {
        Write-Info "Local ACTIVE_MEMORY.md is $([math]::Round($ageMinutes, 1)) minutes old (threshold: $MaxAgeMinutes min)."
        return $false
    }

    return $true
}

# ════════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════════

Write-StepHeader 'Infinity Agent Bootstrap — starting'
Write-Info "Workspace : $OrchestratorWorkspace"
Write-Info "Max age   : $MaxAgeMinutes minutes"
Write-Info "Source ref: $MemorySourceRef"

$localMemoryPath = Join-Path $OrchestratorWorkspace $MEMORY_FILE_PATH

# ── Step 1: Check whether a fresh local copy exists ───────────────────────────
Write-StepHeader 'Checking local ACTIVE_MEMORY.md'

if (Test-LocalMemoryFresh -FilePath $localMemoryPath -MaxAgeMinutes $MaxAgeMinutes) {
    Write-Info 'Local ACTIVE_MEMORY.md is present and fresh — skipping API fetch.'
    $memoryContent = Get-Content -Raw -Path $localMemoryPath
}
else {
    # ── Step 2: Fetch from GitHub API ─────────────────────────────────────────
    Write-StepHeader 'Fetching ACTIVE_MEMORY.md from GitHub API'

    $accessToken = Resolve-AccessToken

    if ($null -eq $accessToken) {
        # No auth available — use local copy if it exists (even if stale).
        if (Test-Path $localMemoryPath) {
            $content = Get-Content -Raw -Path $localMemoryPath
            if (-not [string]::IsNullOrWhiteSpace($content)) {
                Write-WarningStatus (
                    'No GitHub credentials available. ' +
                    'Using stale local ACTIVE_MEMORY.md as fallback.'
                )
                $memoryContent = $content
            }
            else {
                Write-ErrorStatus (
                    'No GitHub credentials available and local ACTIVE_MEMORY.md is empty. ' +
                    'Set GITHUB_APP_ID + GITHUB_APP_PRIVATE_KEY or GITHUB_TOKEN.'
                )
                exit 1
            }
        }
        else {
            Write-ErrorStatus (
                'No GitHub credentials available and no local ACTIVE_MEMORY.md found. ' +
                'Set GITHUB_APP_ID + GITHUB_APP_PRIVATE_KEY or GITHUB_TOKEN.'
            )
            exit 1
        }
    }
    else {
        try {
            $memoryContent = Get-MemoryFromApi -Token $accessToken -Ref $MemorySourceRef

            # Persist to disk for subsequent steps in the same job.
            $destDir = Split-Path $localMemoryPath -Parent
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            Set-Content -Path $localMemoryPath -Value $memoryContent -Encoding utf8 -NoNewline
            Write-Info "Saved fetched memory to: $localMemoryPath"
        }
        catch {
            # API fetch failed — try the local stale copy as a last resort.
            if (Test-Path $localMemoryPath) {
                $staleContent = Get-Content -Raw -Path $localMemoryPath
                if (-not [string]::IsNullOrWhiteSpace($staleContent)) {
                    Write-WarningStatus "API fetch failed ($($_.Exception.Message)). Using stale local copy."
                    $memoryContent = $staleContent
                }
                else {
                    Write-ErrorStatus "API fetch failed and local ACTIVE_MEMORY.md is empty: $($_.Exception.Message)"
                    exit 1
                }
            }
            else {
                Write-ErrorStatus "API fetch failed and no local ACTIVE_MEMORY.md exists: $($_.Exception.Message)"
                exit 1
            }
        }
    }
}

# ── Step 3: Validate the resolved content ────────────────────────────────────
Write-StepHeader 'Validating resolved memory content'

if ([string]::IsNullOrWhiteSpace($memoryContent)) {
    Write-ErrorStatus 'Resolved ACTIVE_MEMORY.md content is empty. Aborting bootstrap.'
    exit 1
}

$lineCount = ($memoryContent -split "`n").Count
Write-Info "Memory content: $lineCount lines"

# ── Step 4: Export well-known output ─────────────────────────────────────────
Write-StepHeader 'Exporting AGENT_MEMORY_PATH'

$env:AGENT_MEMORY_PATH = $localMemoryPath
Set-ActionsOutput -Name 'memory_path' -Value $localMemoryPath
Set-ActionsOutput -Name 'memory_lines' -Value $lineCount

Write-Info "AGENT_MEMORY_PATH = $localMemoryPath"

# ── Step 5: Write GitHub Actions step summary ────────────────────────────────
if ($env:GITHUB_STEP_SUMMARY) {
    @"
## Agent Bootstrap Summary

| Field | Value |
|-------|-------|
| Memory path | ``$localMemoryPath`` |
| Lines | $lineCount |
| Max age (min) | $MaxAgeMinutes |
| Source ref | ``$MemorySourceRef`` |
| Timestamp | $(([System.DateTime]::UtcNow).ToString('yyyy-MM-ddTHH:mm:ssZ')) |
"@ | Out-File -FilePath $env:GITHUB_STEP_SUMMARY -Encoding utf8 -Append
}

Write-StepHeader 'Agent bootstrap complete.'
