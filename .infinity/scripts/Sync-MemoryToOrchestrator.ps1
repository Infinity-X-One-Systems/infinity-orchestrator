#Requires -Version 7.0
<#
.SYNOPSIS
    Syncs memory artifacts from infinity-core-memory into the infinity-orchestrator workspace.

.DESCRIPTION
    Authenticates to GitHub as a GitHub App, optionally discovers the installation
    for the Infinity-X-One-Systems organisation, mints a short-lived installation
    access token, clones the memory source repository, copies the canonical memory
    artifacts into the orchestrator workspace, validates the result, then commits
    and pushes only when a change is detected (idempotent).

    The script is compatible with both Windows (PowerShell 7+) and Ubuntu runners.

.ENVIRONMENT VARIABLES
    Required:
      GITHUB_APP_ID             Numeric GitHub App ID.
      GITHUB_APP_PRIVATE_KEY    PEM-encoded RSA private key (literal newlines or
                                \n-escaped sequences are both accepted).

    Optional:
      GITHUB_APP_INSTALLATION_ID  Pre-known installation ID; skips auto-discovery.
      MEMORY_REPO_REF             Branch/ref in the source repo (default: main).
      ORCHESTRATOR_WORKSPACE      Path to the checked-out orchestrator repo
                                  (default: current working directory).

.NOTES
    Run inside GitHub Actions where ::add-mask:: is honoured, or set
    ACTIONS_RUNTIME_TOKEN to any non-empty value to enable masking output.
    Tokens are never passed as process arguments; they are written only to a
    temporary local git config entry that is removed in a finally block.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ── Constants ─────────────────────────────────────────────────────────────────
$MEMORY_ORG  = 'Infinity-X-One-Systems'
$MEMORY_REPO = 'infinity-core-memory'
$GITHUB_API  = 'https://api.github.com'

# ── Helper: non-shadowing wrappers for host output ───────────────────────────
function Write-StepHeader {
    param([string]$Message)
    Write-Host "==> $Message"
}

function Write-ErrorStatus {
    param([string]$Message)
    Write-Host "::error::$Message"
    # Also write to stderr so callers that inspect $LASTEXITCODE see it.
    [Console]::Error.WriteLine($Message)
}

function Write-WarningStatus {
    param([string]$Message)
    Write-Host "::warning::$Message"
}

# ── Helper: mask a secret in GitHub Actions logs ─────────────────────────────
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
        'User-Agent'           = 'InfinityOrchestrator-MemorySync/1.0'
    }

    $params = @{ Uri = $Uri; Method = $Method; Headers = $headers }

    if ($null -ne $Body) {
        $params['Body']        = ($Body | ConvertTo-Json -Depth 10)
        $params['ContentType'] = 'application/json'
    }

    return Invoke-RestMethod @params
}

# ── Redact a secret value from a string (belt-and-suspenders) ────────────────
function Remove-TokenFromString {
    param([string]$Text, [string]$Secret)
    if ([string]::IsNullOrEmpty($Secret)) { return $Text }
    return $Text -replace [regex]::Escape($Secret), '***'
}

# ════════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════════

Write-StepHeader 'Validating required environment variables'

$AppId      = $env:GITHUB_APP_ID
$PrivateKey = $env:GITHUB_APP_PRIVATE_KEY
$InstallId  = $env:GITHUB_APP_INSTALLATION_ID    # optional
$MemoryRef  = if ($env:MEMORY_REPO_REF)           { $env:MEMORY_REPO_REF }           else { 'main' }
$Workspace  = if ($env:ORCHESTRATOR_WORKSPACE)    { $env:ORCHESTRATOR_WORKSPACE }    else { $PWD.Path }

if ([string]::IsNullOrWhiteSpace($AppId)) {
    Write-ErrorStatus 'GITHUB_APP_ID environment variable is required but not set.'
    exit 1
}
if ([string]::IsNullOrWhiteSpace($PrivateKey)) {
    Write-ErrorStatus 'GITHUB_APP_PRIVATE_KEY environment variable is required but not set.'
    exit 1
}

# Normalise \n-escaped newlines that some secret stores produce.
$PrivateKey = $PrivateKey -replace '\\n', "`n"

# ── Generate JWT ──────────────────────────────────────────────────────────────
Write-StepHeader 'Generating GitHub App JWT'
$jwt = New-GitHubAppJWT -AppId $AppId -PrivateKeyPem $PrivateKey
Invoke-MaskSecret -Secret $jwt

# ── Resolve installation ID ───────────────────────────────────────────────────
if ([string]::IsNullOrWhiteSpace($InstallId)) {
    Write-StepHeader "Discovering GitHub App installation for org: $MEMORY_ORG"
    $installations = Invoke-GitHubApi -Uri "$GITHUB_API/app/installations" -Token $jwt
    $installation  = $installations |
                     Where-Object { $_.account.login -eq $MEMORY_ORG } |
                     Select-Object -First 1

    if ($null -eq $installation) {
        Write-ErrorStatus (
            "No installation found for organisation '$MEMORY_ORG'. " +
            "Ensure the GitHub App is installed on that org and that " +
            "GITHUB_APP_ID refers to the correct App."
        )
        exit 1
    }
    $InstallId = [string]$installation.id
    Write-StepHeader "Resolved installation ID: $InstallId"
}
else {
    Write-StepHeader "Using provided installation ID: $InstallId"
}

# ── Mint installation access token ────────────────────────────────────────────
Write-StepHeader 'Minting installation access token'
$tokenResponse = Invoke-GitHubApi `
    -Uri    "$GITHUB_API/app/installations/$InstallId/access_tokens" `
    -Method 'POST' `
    -Token  $jwt

$accessToken = $tokenResponse.token
Invoke-MaskSecret -Secret $accessToken

# ── Clone memory repository to a temp directory ───────────────────────────────
$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) `
    "infinity-memory-$([System.Guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $tempDir | Out-Null

try {
    Write-StepHeader "Cloning $MEMORY_ORG/$MEMORY_REPO @ $MemoryRef"

    $cloneUrl = "https://x-access-token:$accessToken@github.com/$MEMORY_ORG/$MEMORY_REPO.git"
    # Capture git output so we can redact the token before printing.
    $cloneOutput = git clone --depth 1 --branch $MemoryRef $cloneUrl $tempDir 2>&1
    $cloneOutput | ForEach-Object { Write-Host (Remove-TokenFromString $_ $accessToken) }

    if ($LASTEXITCODE -ne 0) {
        Write-ErrorStatus "git clone failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }

    $sourceInfinity = Join-Path $tempDir '.infinity'
    if (-not (Test-Path $sourceInfinity)) {
        Write-ErrorStatus "Source repository '$MEMORY_REPO' does not contain a .infinity directory."
        exit 1
    }

    # ── Copy memory artifacts ─────────────────────────────────────────────────
    Write-StepHeader 'Copying memory artifacts into orchestrator workspace'
    $destInfinity = Join-Path $Workspace '.infinity'
    New-Item -ItemType Directory -Path $destInfinity -Force | Out-Null

    # Mandatory: ACTIVE_MEMORY.md
    $srcActive = Join-Path $sourceInfinity 'ACTIVE_MEMORY.md'
    if (-not (Test-Path $srcActive)) {
        Write-ErrorStatus '.infinity/ACTIVE_MEMORY.md not found in the source repository.'
        exit 1
    }
    Copy-Item -Path $srcActive `
              -Destination (Join-Path $destInfinity 'ACTIVE_MEMORY.md') `
              -Force
    Write-Host '  Copied ACTIVE_MEMORY.md'

    # Optional: AGENT_ENTRYPOINT.md
    $srcEntry = Join-Path $sourceInfinity 'AGENT_ENTRYPOINT.md'
    if (Test-Path $srcEntry) {
        Copy-Item -Path $srcEntry `
                  -Destination (Join-Path $destInfinity 'AGENT_ENTRYPOINT.md') `
                  -Force
        Write-Host '  Copied AGENT_ENTRYPOINT.md'
    }

    # Optional subdirectories: policies, runbooks, schema
    foreach ($subDir in @('policies', 'runbooks', 'schema')) {
        $srcSub  = Join-Path $sourceInfinity $subDir
        $destSub = Join-Path $destInfinity   $subDir
        if (Test-Path $srcSub) {
            New-Item -ItemType Directory -Path $destSub -Force | Out-Null
            Copy-Item -Path (Join-Path $srcSub '*') `
                      -Destination $destSub `
                      -Recurse -Force
            Write-Host "  Copied $subDir/**"
        }
    }

    # ── Validate ACTIVE_MEMORY.md is present and non-empty ───────────────────
    Write-StepHeader 'Validating synced ACTIVE_MEMORY.md'
    $destActive = Join-Path $destInfinity 'ACTIVE_MEMORY.md'
    if (-not (Test-Path $destActive)) {
        Write-ErrorStatus '.infinity/ACTIVE_MEMORY.md is missing after sync. Aborting.'
        exit 1
    }
    $content = Get-Content -Raw -Path $destActive
    if ([string]::IsNullOrWhiteSpace($content)) {
        Write-ErrorStatus '.infinity/ACTIVE_MEMORY.md is empty after sync. Aborting.'
        exit 1
    }
    Write-Host '  ACTIVE_MEMORY.md is present and non-empty.'

    # ── Commit and push if changes exist ──────────────────────────────────────
    Write-StepHeader 'Checking for changes in orchestrator workspace'
    Push-Location $Workspace
    try {
        git add -- '.infinity'
        $statusOutput = git status --porcelain -- '.infinity'

        if ([string]::IsNullOrWhiteSpace($statusOutput)) {
            Write-StepHeader 'No changes detected — workspace is already up-to-date.'
        }
        else {
            Write-StepHeader 'Changes detected — committing and pushing'

            $currentName = git config user.name 2>$null
            if ([string]::IsNullOrWhiteSpace($currentName)) {
                git config user.name  'github-actions[bot]'
                git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
            }

            $syncTime = [System.DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
            git commit -m "chore(memory): sync from infinity-core-memory

- Source : $MEMORY_ORG/$MEMORY_REPO @ $MemoryRef
- Synced : $syncTime
- Trigger: memory-sync workflow (automated)"

            if ($LASTEXITCODE -ne 0) {
                Write-ErrorStatus "git commit failed with exit code $LASTEXITCODE"
                exit $LASTEXITCODE
            }

            # Configure a scoped credential for the push so the token is stored
            # in the local .git/config (not in a process argument) and removed
            # immediately afterwards.
            $credsB64 = [Convert]::ToBase64String(
                [Text.Encoding]::UTF8.GetBytes("x-access-token:$accessToken")
            )
            git config --local 'http.https://github.com/.extraheader' `
                "Authorization: Basic $credsB64"
            try {
                $pushOutput = git push origin HEAD 2>&1
                $pushOutput | ForEach-Object {
                    Write-Host (Remove-TokenFromString $_ $accessToken)
                }
                if ($LASTEXITCODE -ne 0) {
                    Write-ErrorStatus "git push failed with exit code $LASTEXITCODE"
                    exit $LASTEXITCODE
                }
            }
            finally {
                git config --local --unset 'http.https://github.com/.extraheader'
            }

            Write-StepHeader 'Memory sync committed and pushed successfully.'
        }
    }
    finally {
        Pop-Location
    }

}
finally {
    # Always remove the temp clone to avoid leaving tokens on disk.
    if (Test-Path $tempDir) {
        Remove-Item -Recurse -Force $tempDir
    }
}

Write-StepHeader 'Memory sync complete.'
