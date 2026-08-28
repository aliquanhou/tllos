#!/usr/bin/env pwsh
# TLL ABI Consistency Checker v2
# Verifies that spec/ABI files match actual implementation

param(
    [string]$RepoRoot = "."
)

$ErrorActionPreference = "Stop"
$issues = @()
$warnings = @()

Write-Host "=== TLL ABI Consistency Checker v2 ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check BUILTINS.json exists and parse
$builtinsJson = Join-Path $RepoRoot "spec/BUILTINS.json"
$specIndices = @{}
if (-not (Test-Path $builtinsJson)) {
    $issues += "spec/BUILTINS.json not found"
} else {
    Write-Host "[1/7] spec/BUILTINS.json: FOUND" -ForegroundColor Green
    try {
        $json = Get-Content $builtinsJson -Raw | ConvertFrom-Json
        $totalDefined = $json.total_defined
        Write-Host "       total_defined: $totalDefined"
        Write-Host "       total_range: $($json.total_range)"
        # Extract all indices from modules
        foreach ($module in $json.modules.PSObject.Properties) {
            foreach ($fn in $module.Value.functions) {
                $specIndices[$fn.index] = $module.Name + "." + $fn.name
            }
        }
        Write-Host "       functions in spec: $($specIndices.Count)"
    } catch {
        $issues += "Failed to parse BUILTINS.json: $_"
    }
}

# 2. Check HOST_ABI.md exists
$hostAbiMd = Join-Path $RepoRoot "spec/HOST_ABI.md"
if (-not (Test-Path $hostAbiMd)) {
    $issues += "spec/HOST_ABI.md not found"
} else {
    Write-Host "[2/7] spec/HOST_ABI.md: FOUND" -ForegroundColor Green
}

# 3. Check builtin.c exists and extract case indices
$builtinC = Join-Path $RepoRoot "host/c/builtin.c"
$implIndices = @{}
if (-not (Test-Path $builtinC)) {
    $issues += "host/c/builtin.c not found"
} else {
    Write-Host "[3/7] host/c/builtin.c: FOUND" -ForegroundColor Green
    $content = Get-Content $builtinC
    foreach ($line in $content) {
        if ($line -match '^\s*case\s+(\d+)\s*:') {
            $idx = [int]$Matches[1]
            $implIndices[$idx] = $line.Trim()
        }
        if ($line -match 'if\s*\(idx\s*==\s*(\d+)\)') {
            $idx = [int]$Matches[1]
            $implIndices[$idx] = $line.Trim()
        }
        if ($line -match 'if\s*\(idx\s*>=\s*(\d+)\s*&&\s*idx\s*<=\s*(\d+)\)') {
            $start = [int]$Matches[1]
            $end = [int]$Matches[2]
            for ($i = $start; $i -le $end; $i++) {
                $implIndices[$i] = "range $start-$end"
            }
        }
    }
    Write-Host "       case statements: $($implIndices.Count)"
}

# 4. Check for stale "STUB" markers in HOST_ABI.md
if (Test-Path $hostAbiMd) {
    $stubCount = (Get-Content $hostAbiMd | Select-String -Pattern "STUB|stub" -CaseSensitive:$false | Measure-Object).Count
    if ($stubCount -gt 0) {
        $warnings += "HOST_ABI.md contains $stubCount 'STUB' markers - verify if these are still accurate"
        Write-Host "[4/7] HOST_ABI.md STUB markers: $stubCount (WARNING)" -ForegroundColor Yellow
    } else {
        Write-Host "[4/7] HOST_ABI.md STUB markers: 0" -ForegroundColor Green
    }
}

# 5. Check README version
$readme = Join-Path $RepoRoot "README.md"
if (Test-Path $readme) {
    $versionMatch = Get-Content $readme | Select-String -Pattern "version-P0--(\d+)"
    if ($versionMatch) {
        $readmeVersion = $versionMatch.Matches[0].Groups[1].Value
        Write-Host "[5/7] README version: P0-$readmeVersion" -ForegroundColor Green
    } else {
        $warnings += "README version badge not found or unrecognized"
        Write-Host "[5/7] README version: NOT FOUND (WARNING)" -ForegroundColor Yellow
    }
}

# 6. Check spec vs implementation consistency
if ($specIndices.Count -gt 0 -and $implIndices.Count -gt 0) {
    Write-Host "[6/7] Spec vs Implementation consistency:" -ForegroundColor Cyan
    $missingInImpl = @()
    $missingInSpec = @()
    foreach ($idx in $specIndices.Keys) {
        if (-not $implIndices.ContainsKey($idx)) {
            $missingInImpl += "$idx ($($specIndices[$idx]))"
        }
    }
    foreach ($idx in $implIndices.Keys) {
        if (-not $specIndices.ContainsKey($idx)) {
            $missingInSpec += "$idx ($($implIndices[$idx]))"
        }
    }
    if ($missingInImpl.Count -gt 0) {
        $issues += "Spec defines $($missingInImpl.Count) builtins not found in builtin.c: $($missingInImpl -join ', ')"
        Write-Host "       Spec-only (missing in impl): $($missingInImpl.Count) (ERROR)" -ForegroundColor Red
    } else {
        Write-Host "       Spec-only (missing in impl): 0" -ForegroundColor Green
    }
    if ($missingInSpec.Count -gt 0) {
        $warnings += "builtin.c has $($missingInSpec.Count) case statements not in BUILTINS.json: $($missingInSpec -join ', ')"
        Write-Host "       Impl-only (missing in spec): $($missingInSpec.Count) (WARNING)" -ForegroundColor Yellow
    } else {
        Write-Host "       Impl-only (missing in spec): 0" -ForegroundColor Green
    }
}

# 7. Check total_defined matches actual count
if ($specIndices.Count -gt 0) {
    Write-Host "[7/7] total_defined consistency:" -ForegroundColor Cyan
    if ($totalDefined -ne $specIndices.Count) {
        $warnings += "BUILTINS.json total_defined=$totalDefined but actual function count=$($specIndices.Count)"
        Write-Host "       total_defined=$totalDefined, actual=$($specIndices.Count) (WARNING)" -ForegroundColor Yellow
    } else {
        Write-Host "       total_defined=$totalDefined matches actual count" -ForegroundColor Green
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
