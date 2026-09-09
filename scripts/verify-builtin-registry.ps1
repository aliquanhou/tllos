# TLL Native Builtin Registry Verification Gate (Bidirectional)
# P2-01-B11-R1-R2-R3-FINAL: Ensures canonical Language-Callable Builtin Registry
# in native_lower.tll is bidirectionally consistent with actual native bindings
# in runtime headers, with explicit runtime-internal API exclusion.
#
# Direction A: Canonical registry -> actual native binding
#   registry entry missing from runtime header => FAIL
# Direction B: Actual language-callable native binding -> canonical registry
#   runtime header language-callable function missing from registry => FAIL
# Additional: duplicate entries, runtime-internal misclassification => FAIL

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

Write-Output "=== TLL Native Builtin Registry Verification (Bidirectional) ==="
Write-Output ""

# --- Extract lowering registry (language-callable builtins) ---
$nativeLowerPath = Join-Path $repoRoot "compiler\native_lower.tll"
$loweringBuiltins = @()
$inList = $false
$listName = ""
foreach ($line in Get-Content $nativeLowerPath) {
    if ($line -match 'let (nl_\w+Functions)\s*:') {
        $listName = $Matches[1]
        $inList = $true
        continue
    }
    if ($inList -and $line -match '^\]') {
        $inList = $false
        $listName = ""
        continue
    }
    if ($inList -and $line -match '"([A-Za-z_][A-Za-z0-9_]*)"') {
        $name = $Matches[1]
        if ($listName -eq "nl_builtinFunctions") {
            $loweringBuiltins += $name
        }
    }
}
Write-Output "Canonical registry (nl_builtinFunctions): $($loweringBuiltins.Count) entries"

# --- Extract runtime-internal API list from lowering ---
$loweringRuntimeInternal = @()
$inList = $false
foreach ($line in Get-Content $nativeLowerPath) {
    if ($line -match 'let nl_runtimeInternalFunctions') { $inList = $true; continue }
    if ($inList -and $line -match '^\]') { $inList = $false; continue }
    if ($inList -and $line -match '"([A-Za-z_][A-Za-z0-9_]*)"') {
        $loweringRuntimeInternal += $Matches[1]
    }
}
Write-Output "Runtime-internal API (nl_runtimeInternalFunctions): $($loweringRuntimeInternal.Count) entries"
Write-Output ""

# --- Extract all function declarations from runtime headers ---
$headerAllFunctions = @()
$headers = @("runtime\tll_runtime.h", "native\runtime\tll_native.h")
foreach ($h in $headers) {
    $p = Join-Path $repoRoot $h
    if (-not (Test-Path $p)) { continue }
    $c = Get-Content $p -Raw
    # Match function declarations: return_type function_name(
    # Use \s* (not \s+) to allow "char *func" with no space after *
    $ms = [regex]::Matches($c, '(?:TLLValue|void|int|char\s*\*|TLLArray\s*\*|TLLMap\s*\*|TLLClosureEnv\s*\*)\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(')
    foreach ($m in $ms) {
        $n = $m.Groups[1].Value
        if ($headerAllFunctions -notcontains $n) { $headerAllFunctions += $n }
    }
}
Write-Output "Runtime header all functions: $($headerAllFunctions.Count) entries"

# --- Classify header functions: language-callable vs runtime-internal ---
# Runtime-internal / lifecycle API (explicit exclusion list)
$runtimeInternalNames = @("tll_runtime_init", "tll_runtime_cleanup", "tll_native_init", "tll_native_cleanup")
$headerLanguageCallable = @()
$headerRuntimeInternal = @()
foreach ($n in $headerAllFunctions) {
    if ($runtimeInternalNames -contains $n) {
        $headerRuntimeInternal += $n
    } else {
        $headerLanguageCallable += $n
    }
}
Write-Output "Runtime header language-callable: $($headerLanguageCallable.Count) entries"
Write-Output "Runtime header runtime-internal: $($headerRuntimeInternal.Count) entries"
Write-Output ""

# --- Verification ---
$failures = @()

# Check 1: Duplicate entries in lowering registry
$seen = @{}
$duplicates = @()
foreach ($n in $loweringBuiltins) {
    if ($seen.ContainsKey($n)) {
        if ($duplicates -notcontains $n) { $duplicates += $n }
    } else {
        $seen[$n] = $true
    }
}
if ($duplicates.Count -gt 0) {
    $failures += "DUPLICATE: Duplicate entries in lowering registry: $($duplicates -join ', ')"
}

# Check 2: Runtime-internal API misclassified into language-callable registry
$misclassified = @()
foreach ($n in $loweringBuiltins) {
    if ($runtimeInternalNames -contains $n) {
        $misclassified += $n
    }
}
if ($misclassified.Count -gt 0) {
    $failures += "MISCLASSIFIED: Runtime-internal API in language-callable registry: $($misclassified -join ', ')"
}

# Direction A: Canonical registry -> actual native binding
# Every entry in lowering registry must exist in runtime header
$missingBinding = @()
foreach ($n in $loweringBuiltins) {
    if ($headerAllFunctions -notcontains $n) {
        $missingBinding += $n
    }
}
if ($missingBinding.Count -gt 0) {
    $failures += "DIRECTION-A (registry -> binding): Registry entries missing from runtime header: $($missingBinding -join ', ')"
}

# Direction B: Actual language-callable native binding -> canonical registry
# Every language-callable function in runtime header must be in lowering registry
$missingRegistry = @()
foreach ($n in $headerLanguageCallable) {
    if ($loweringBuiltins -notcontains $n) {
        $missingRegistry += $n
    }
}
if ($missingRegistry.Count -gt 0) {
    $failures += "DIRECTION-B (binding -> registry): Language-callable header functions missing from registry: $($missingRegistry -join ', ')"
}

# --- Report ---
Write-Output "=== Verification Results ==="
Write-Output ""

if ($failures.Count -eq 0) {
    Write-Output "Canonical source: compiler/native_lower.tll (nl_builtinFunctions)"
    Write-Output "Binding source: runtime/tll_runtime.h + native/runtime/tll_native.h"
    Write-Output "Registry count: $($loweringBuiltins.Count)"
    Write-Output "Language-callable binding count: $($headerLanguageCallable.Count)"
    Write-Output "Runtime-internal binding count: $($headerRuntimeInternal.Count)"
    Write-Output "Duplicates: 0"
    Write-Output "Misclassified: 0"
    Write-Output "Direction A (registry -> binding): ALL PRESENT"
    Write-Output "Direction B (binding -> registry): ALL PRESENT"
    Write-Output ""
    Write-Output "=== BUILTIN REGISTRY VERIFICATION: PASS ==="
    exit 0
} else {
    Write-Output "FAILURES FOUND: $($failures.Count)"
    Write-Output ""
    foreach ($f in $failures) {
        Write-Output "  [FAIL] $f"
    }
    Write-Output ""
    Write-Output "=== BUILTIN REGISTRY VERIFICATION: FAIL ==="
    exit 1
}
