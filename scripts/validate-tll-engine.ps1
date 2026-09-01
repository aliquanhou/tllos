# TLL OS .tll-engine/ Validation Script (Windows PowerShell)
# Validates the structure, schema, and consistency of the AI Native Engineering Foundation.
# Usage: scripts\validate-tll-engine.ps1 [-Strict]

param(
    [switch]$Strict
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$EngineDir = Join-Path $RepoRoot ".tll-engine"

$Errors = 0
$Warnings = 0

Write-Host "=========================================="
Write-Host "TLL OS .tll-engine/ Validation"
Write-Host "=========================================="
Write-Host "Engine dir: $EngineDir"
Write-Host "Strict mode: $($Strict.IsPresent)"
Write-Host ""

function Write-ErrorMsg($msg) {
    Write-Host "  [ERROR] $msg" -ForegroundColor Red
    $script:Errors++
}

function Write-WarningMsg($msg) {
    Write-Host "  [WARNING] $msg" -ForegroundColor Yellow
    $script:Warnings++
}

function Write-InfoMsg($msg) {
    Write-Host "  [INFO] $msg" -ForegroundColor Cyan
}

function Test-FileExists($filepath) {
    if (-not (Test-Path $filepath -PathType Leaf)) {
        Write-ErrorMsg "Missing required file: $filepath"
        return $false
    }
    return $true
}

function Test-JsonValid($filepath) {
    try {
        $null = Get-Content $filepath -Raw -Encoding UTF8 | ConvertFrom-Json
        return $true
    } catch {
        Write-ErrorMsg "Invalid JSON: $filepath"
        return $false
    }
}

function Test-JsonField($filepath, $field) {
    try {
        $data = Get-Content $filepath -Raw -Encoding UTF8 | ConvertFrom-Json
        $keys = $field -split '\.'
        $obj = $data
        foreach ($k in $keys) {
            if ($obj.PSObject.Properties.Name -contains $k) {
                $obj = $obj.$k
            } else {
                Write-ErrorMsg "Missing required field '$field' in $filepath"
                return $false
            }
        }
        return $true
    } catch {
        return $false
    }
}

# --- Step 1: Directory structure ---
Write-Host "[Step 1] Checking directory structure..."

$RequiredDirs = @(
    "identity",
    "truth",
    "protocol",
    "cognition",
    "evidence\ci",
    "evidence\benchmark",
    "evidence\audit",
    "version"
)

foreach ($dir in $RequiredDirs) {
    $fullPath = Join-Path $EngineDir $dir
    if (-not (Test-Path $fullPath -PathType Container)) {
        Write-ErrorMsg "Missing required directory: .tll-engine\$dir"
    }
}

if ($Errors -eq 0) {
    Write-InfoMsg "All required directories present"
}
Write-Host ""

# --- Step 2: Required files ---
Write-Host "[Step 2] Checking required files..."

$RequiredFiles = @(
    "identity\root.json",
    "identity\agents.json",
    "truth\architecture.json",
    "truth\language.json",
    "truth\runtime.json",
    "truth\capability.json",
    "protocol\development.yaml",
    "protocol\testing.yaml",
    "protocol\audit.yaml",
    "cognition\graph.json",
    "cognition\dependency.json",
    "cognition\decisions.json",
    "version\manifest.json"
)

foreach ($f in $RequiredFiles) {
    $fullPath = Join-Path $EngineDir $f
    Test-FileExists $fullPath | Out-Null
}

if ($Errors -eq 0) {
    Write-InfoMsg "All required files present"
}
Write-Host ""

# --- Step 3: JSON validity ---
Write-Host "[Step 3] Validating JSON files..."

$JsonFiles = @(
    "identity\root.json",
    "identity\agents.json",
    "truth\architecture.json",
    "truth\language.json",
    "truth\runtime.json",
    "truth\capability.json",
    "cognition\graph.json",
    "cognition\dependency.json",
    "cognition\decisions.json",
    "version\manifest.json"
)

foreach ($f in $JsonFiles) {
    $fullPath = Join-Path $EngineDir $f
    if (Test-Path $fullPath -PathType Leaf) {
        Test-JsonValid $fullPath | Out-Null
    }
}

# Also validate evidence files
$EvidenceDirs = @("evidence\ci", "evidence\benchmark", "evidence\audit")
foreach ($ed in $EvidenceDirs) {
    $edPath = Join-Path $EngineDir $ed
    if (Test-Path $edPath -PathType Container) {
        Get-ChildItem $edPath -Filter "*.json" | ForEach-Object {
            Test-JsonValid $_.FullName | Out-Null
        }
    }
}

if ($Errors -eq 0) {
    Write-InfoMsg "All JSON files valid"
}
Write-Host ""

# --- Step 4: Required fields in Truth files ---
Write-Host "[Step 4] Checking required fields in Truth files..."

$TruthFiles = @(
    "truth\architecture.json",
    "truth\language.json",
    "truth\runtime.json",
    "truth\capability.json"
)

foreach ($f in $TruthFiles) {
    $fullPath = Join-Path $EngineDir $f
    if (Test-Path $fullPath -PathType Leaf) {
        Test-JsonField $fullPath "schema_version" | Out-Null
        Test-JsonField $fullPath "name" | Out-Null
        Test-JsonField $fullPath "version" | Out-Null
        Test-JsonField $fullPath "hash" | Out-Null
        Test-JsonField $fullPath "created_at" | Out-Null
    }
}

# Check capability.json has capability_categories
$capPath = Join-Path $EngineDir "truth\capability.json"
if (Test-Path $capPath -PathType Leaf) {
    Test-JsonField $capPath "capability_categories" | Out-Null
    Test-JsonField $capPath "production_readiness" | Out-Null
}

if ($Errors -eq 0) {
    Write-InfoMsg "All required fields present in Truth files"
}
Write-Host ""

# --- Step 5: Evidence schema check ---
Write-Host "[Step 5] Checking Evidence schema..."

foreach ($ed in $EvidenceDirs) {
    $edPath = Join-Path $EngineDir $ed
    if (Test-Path $edPath -PathType Container) {
        Get-ChildItem $edPath -Filter "*.json" | ForEach-Object {
            Test-JsonField $_.FullName "schema_version" | Out-Null
            Test-JsonField $_.FullName "evidence_type" | Out-Null
            Test-JsonField $_.FullName "id" | Out-Null
            Test-JsonField $_.FullName "proves" | Out-Null
            Test-JsonField $_.FullName "does_not_prove" | Out-Null
            Test-JsonField $_.FullName "confidence" | Out-Null
            Test-JsonField $_.FullName "hash" | Out-Null
            Test-JsonField $_.FullName "provenance_chain" | Out-Null
        }
    }
}

if ($Errors -eq 0) {
    Write-InfoMsg "All Evidence files have required schema fields"
}
Write-Host ""

# --- Step 6: Manifest consistency ---
Write-Host "[Step 6] Checking Version Manifest consistency..."

$manifestPath = Join-Path $EngineDir "version\manifest.json"
if (Test-Path $manifestPath -PathType Leaf) {
    Test-JsonField $manifestPath "foundation_version" | Out-Null
    Test-JsonField $manifestPath "components" | Out-Null
    Test-JsonField $manifestPath "immutable_core_rules" | Out-Null
    Test-JsonField $manifestPath "version_chain" | Out-Null

    # Check that manifest lists all components
    try {
        $manifest = Get-Content $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $components = $manifest.components.PSObject.Properties.Name
        foreach ($comp in @("identity", "truth", "protocol", "cognition", "evidence")) {
            if ($components -notcontains $comp) {
                Write-ErrorMsg "Manifest missing component: $comp"
            }
        }
    } catch {
        # JSON already validated above, ignore here
    }
}

if ($Errors -eq 0) {
    Write-InfoMsg "Version Manifest consistent"
}
Write-Host ""

# --- Step 7: YAML basic check ---
Write-Host "[Step 7] Checking Protocol YAML files..."

$YamlFiles = @(
    "protocol\development.yaml",
    "protocol\testing.yaml",
    "protocol\audit.yaml"
)

foreach ($f in $YamlFiles) {
    $fullPath = Join-Path $EngineDir $f
    if (Test-Path $fullPath -PathType Leaf) {
        $content = Get-Content $fullPath -Raw -Encoding UTF8
        if ([string]::IsNullOrWhiteSpace($content)) {
            Write-ErrorMsg "Empty YAML file: $f"
        }
        if ($content -notmatch "schema_version") {
            Write-WarningMsg "YAML file missing schema_version: $f"
        }
    }
}

if ($Errors -eq 0) {
    Write-InfoMsg "All Protocol YAML files valid (basic check)"
}
Write-Host ""

# --- Summary ---
Write-Host "=========================================="
Write-Host "Validation Summary"
Write-Host "=========================================="
Write-Host "Errors:   $Errors"
Write-Host "Warnings: $Warnings"
Write-Host ""

if ($Errors -gt 0) {
    Write-Host "RESULT: FAIL" -ForegroundColor Red
    Write-Host "Fix the errors above before committing."
    exit 1
}

if ($Strict -and $Warnings -gt 0) {
    Write-Host "RESULT: FAIL (strict mode, warnings treated as errors)" -ForegroundColor Red
    exit 1
}

Write-Host "RESULT: PASS" -ForegroundColor Green
Write-Host ".tll-engine/ structure and schema are valid."
exit 0
