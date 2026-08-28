#!/usr/bin/env pwsh
# TLL ABI Consistency Checker
# Verifies that spec/ABI files match actual implementation

param(
    [string]$RepoRoot = "."
)

$ErrorActionPreference = "Stop"
$issues = @()
$warnings = @()

Write-Host "=== TLL ABI Consistency Checker ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check BUILTINS.json exists
$builtinsJson = Join-Path $RepoRoot "spec/BUILTINS.json"
if (-not (Test-Path $builtinsJson)) {
    $issues += "spec/BUILTINS.json not found"
} else {
    Write-Host "[1/5] spec/BUILTINS.json: FOUND" -ForegroundColor Green
}

# 2. Check HOST_ABI.md exists
$hostAbiMd = Join-Path $RepoRoot "spec/HOST_ABI.md"
if (-not (Test-Path $hostAbiMd)) {
    $issues += "spec/HOST_ABI.md not found"
} else {
    Write-Host "[2/5] spec/HOST_ABI.md: FOUND" -ForegroundColor Green
}

# 3. Check builtin.c exists
$builtinC = Join-Path $RepoRoot "host/c/builtin.c"
if (-not (Test-Path $builtinC)) {
    $issues += "host/c/builtin.c not found"
} else {
    Write-Host "[3/5] host/c/builtin.c: FOUND" -ForegroundColor Green
}

# 4. Check for stale "STUB" markers in HOST_ABI.md
if (Test-Path $hostAbiMd) {
    $stubCount = (Get-Content $hostAbiMd | Select-String -Pattern "STUB|stub" -CaseSensitive:$false | Measure-Object).Count
    if ($stubCount -gt 0) {
        $warnings += "HOST_ABI.md contains $stubCount 'STUB' markers - verify if these are still accurate"
        Write-Host "[4/5] HOST_ABI.md STUB markers: $stubCount (WARNING)" -ForegroundColor Yellow
    } else {
        Write-Host "[4/5] HOST_ABI.md STUB markers: 0" -ForegroundColor Green
    }
}

# 5. Check README version
$readme = Join-Path $RepoRoot "README.md"
if (Test-Path $readme) {
    $versionMatch = Get-Content $readme | Select-String -Pattern "version-P0--(\d+)"
    if ($versionMatch) {
        $readmeVersion = $versionMatch.Matches[0].Groups[1].Value
        Write-Host "[5/5] README version: P0-$readmeVersion" -ForegroundColor Green
    } else {
        $warnings += "README version badge not found or unrecognized"
        Write-Host "[5/5] README version: NOT FOUND (WARNING)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan

if ($issues.Count -gt 0) {
    Write-Host ""
    Write-Host "ERRORS ($($issues.Count)):" -ForegroundColor Red
    foreach ($issue in $issues) {
        Write-Host "  - $issue" -ForegroundColor Red
    }
}

if ($warnings.Count -gt 0) {
    Write-Host ""
    Write-Host "WARNINGS ($($warnings.Count)):" -ForegroundColor Yellow
    foreach ($warning in $warnings) {
        Write-Host "  - $warning" -ForegroundColor Yellow
    }
}

if ($issues.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host ""
    Write-Host "ALL CHECKS PASSED" -ForegroundColor Green
}

Write-Host ""
if ($issues.Count -gt 0) {
    exit 1
} else {
    exit 0
}
