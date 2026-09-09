# TLL Native Builtin Registry Verification Gate (Bidirectional, Tier-Aware)
# P2-01-B11-R1-R2-R3-FINAL-R1: Three-tier semantic classification closure.
#
# ARCHITECTURE:
#   Native Target has NO runtime builtin dispatcher/registry.
#   native_lower.tll generates DIRECT C function calls to Shared Runtime Core.
#   Therefore "builtin binding" = "C-callable semantic surface used by lowering",
#   NOT a runtime dispatch table.
#
# THREE-TIER CLASSIFICATION (canonical source: compiler/native_lower.tll):
#   1. Language-Callable Builtins (nl_builtinFunctions): stable API invocable from TLL source
#   2. Runtime-Internal / Lifecycle APIs (nl_runtimeInternalFunctions): compiler-generated lifecycle
#   3. Test-only Verification APIs (nl_testOnlyFunctions): instrumentation for ownership tests only
#
# Runtime Header = Native ABI declaration surface, NOT a builtin registry.
# Validator classifies header functions into tiers, does NOT assume all = builtins.
#
# DIRECTION A: Canonical Language Builtin Registry -> actual declared/implemented C call surface
#   Every entry in nl_builtinFunctions must exist in runtime headers.
# DIRECTION B: Actual language-callable C call surface -> Canonical Language Builtin Registry
#   Every header function that is language-callable (not runtime-internal, not test-only)
#   must be in nl_builtinFunctions.
# ADDITIONAL: duplicate check, cross-tier contamination check, tier completeness check.

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

Write-Output "=== TLL Native Builtin Registry Verification (Bidirectional, Tier-Aware) ==="
Write-Output ""

# --- Extract all three tiers from native_lower.tll (canonical source) ---
$nativeLowerPath = Join-Path $repoRoot "compiler\native_lower.tll"

function Extract-List {
    param([string]$ListName, [string]$FileContent)
    $result = @()
    $inList = $false
    foreach ($line in $FileContent -split "`n") {
        if ($line -match "let $ListName\s*:") { $inList = $true; continue }
        if ($inList -and $line -match '^\]') { $inList = $false; continue }
        if ($inList -and $line -match '"([A-Za-z_][A-Za-z0-9_]*)"') {
            $result += $Matches[1]
        }
    }
    return $result
}

$lowerContent = Get-Content $nativeLowerPath -Raw
$languageBuiltins = Extract-List -ListName "nl_builtinFunctions" -FileContent $lowerContent
$runtimeInternal = Extract-List -ListName "nl_runtimeInternalFunctions" -FileContent $lowerContent
$testOnly = Extract-List -ListName "nl_testOnlyFunctions" -FileContent $lowerContent

Write-Output "Canonical registry (from compiler/native_lower.tll):"
Write-Output "  Language-Callable Builtins: $($languageBuiltins.Count)"
Write-Output "  Runtime-Internal/Lifecycle: $($runtimeInternal.Count)"
Write-Output "  Test-only Verification:     $($testOnly.Count)"
Write-Output ""

# --- Extract all function declarations from runtime headers (Native ABI surface) ---
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
Write-Output "Runtime Header (Native ABI surface): $($headerAllFunctions.Count) total functions"
Write-Output ""

# --- Classify header functions into tiers ---
# A header function is language-callable if it is NOT runtime-internal and NOT test-only.
$headerLanguageCallable = @()
$headerRuntimeInternal = @()
$headerTestOnly = @()
$headerUnclassified = @()

foreach ($n in $headerAllFunctions) {
    if ($runtimeInternal -contains $n) {
        $headerRuntimeInternal += $n
    } elseif ($testOnly -contains $n) {
        $headerTestOnly += $n
    } elseif ($languageBuiltins -contains $n) {
        $headerLanguageCallable += $n
    } else {
        $headerUnclassified += $n
    }
}

Write-Output "Header classification:"
Write-Output "  Language-Callable: $($headerLanguageCallable.Count)"
Write-Output "  Runtime-Internal:  $($headerRuntimeInternal.Count)"
Write-Output "  Test-only:         $($headerTestOnly.Count)"
Write-Output "  Unclassified:      $($headerUnclassified.Count)"
Write-Output ""

# --- Verification ---
$failures = @()

# Check 1: Duplicate entries within each canonical list
foreach ($tierName in @("languageBuiltins", "runtimeInternal", "testOnly")) {
    $list = Get-Variable -Name $tierName -ValueOnly
    $seen = @{}
    $dupes = @()
    foreach ($n in $list) {
        if ($seen.ContainsKey($n)) { if ($dupes -notcontains $n) { $dupes += $n } }
        else { $seen[$n] = $true }
    }
    if ($dupes.Count -gt 0) {
        $failures += "DUPLICATE in $tierName : $($dupes -join ', ')"
    }
}

# Check 2: Cross-tier contamination (a function appearing in more than one canonical list)
$allCanonical = $languageBuiltins + $runtimeInternal + $testOnly
$tierCounts = @{}
foreach ($n in $allCanonical) {
    if (-not $tierCounts.ContainsKey($n)) { $tierCounts[$n] = 0 }
    $tierCounts[$n]++
}
$crossContam = @()
foreach ($k in $tierCounts.Keys) {
    if ($tierCounts[$k] -gt 1) { $crossContam += $k }
}
if ($crossContam.Count -gt 0) {
    $failures += "CROSS-TIER CONTAMINATION (function in multiple canonical lists): $($crossContam -join ', ')"
}

# Check 3: Runtime-internal or test-only functions incorrectly in language-builtin list
# (This is the inverse of cross-tier: nl_builtinFunctions should not contain runtime-internal or test-only names)
$badInLanguage = @()
foreach ($n in $languageBuiltins) {
    if ($runtimeInternal -contains $n) { $badInLanguage += "$n (runtime-internal)" }
    if ($testOnly -contains $n) { $badInLanguage += "$n (test-only)" }
}
if ($badInLanguage.Count -gt 0) {
    $failures += "MISCLASSIFIED in nl_builtinFunctions: $($badInLanguage -join ', ')"
}

# Direction A: Canonical Language Builtin Registry -> actual declared C call surface
# Every language-builtin must exist in runtime headers
$missingBinding = @()
foreach ($n in $languageBuiltins) {
    if ($headerAllFunctions -notcontains $n) {
        $missingBinding += $n
    }
}
if ($missingBinding.Count -gt 0) {
    $failures += "DIRECTION-A (registry -> binding): Language builtins missing from runtime header: $($missingBinding -join ', ')"
}

# Direction B: Actual language-callable C call surface -> Canonical Language Builtin Registry
# Every header function that is language-callable must be in nl_builtinFunctions
# "Language-callable" = not runtime-internal, not test-only, and not unclassified
# Unclassified header functions are reported separately (they need a tier decision)
$missingRegistry = @()
foreach ($n in $headerLanguageCallable) {
    if ($languageBuiltins -notcontains $n) {
        $missingRegistry += $n
    }
}
if ($missingRegistry.Count -gt 0) {
    $failures += "DIRECTION-B (binding -> registry): Language-callable header functions missing from registry: $($missingRegistry -join ', ')"
}

# Check 4: Unclassified header functions (need tier decision)
if ($headerUnclassified.Count -gt 0) {
    $failures += "UNCLASSIFIED header functions (need tier decision: language/runtime-internal/test-only): $($headerUnclassified -join ', ')"
}

# Check 5: Runtime-internal canonical list matches header runtime-internal
$riMissingHeader = @()
foreach ($n in $runtimeInternal) {
    if ($headerRuntimeInternal -notcontains $n) { $riMissingHeader += $n }
}
if ($riMissingHeader.Count -gt 0) {
    $failures += "RUNTIME-INTERNAL canonical entries missing from header: $($riMissingHeader -join ', ')"
}

# Check 6: Test-only canonical list matches header test-only
$toMissingHeader = @()
foreach ($n in $testOnly) {
    if ($headerTestOnly -notcontains $n) { $toMissingHeader += $n }
}
if ($toMissingHeader.Count -gt 0) {
    $failures += "TEST-ONLY canonical entries missing from header: $($toMissingHeader -join ', ')"
}

# --- Report ---
Write-Output "=== Verification Results ==="
Write-Output ""

if ($failures.Count -eq 0) {
    Write-Output "Architecture: Native direct C-call surface (NO runtime dispatcher)"
    Write-Output "Canonical source: compiler/native_lower.tll (three-tier lists)"
    Write-Output "Runtime Header: Native ABI declaration surface (NOT a builtin registry)"
    Write-Output ""
    Write-Output "Tier counts (canonical):"
    Write-Output "  Language-Callable Builtins: $($languageBuiltins.Count)"
    Write-Output "  Runtime-Internal/Lifecycle: $($runtimeInternal.Count)"
    Write-Output "  Test-only Verification:     $($testOnly.Count)"
    Write-Output ""
    Write-Output "Tier counts (header):"
    Write-Output "  Language-Callable: $($headerLanguageCallable.Count)"
    Write-Output "  Runtime-Internal:  $($headerRuntimeInternal.Count)"
    Write-Output "  Test-only:         $($headerTestOnly.Count)"
    Write-Output "  Unclassified:      0"
    Write-Output ""
    Write-Output "Duplicates: 0"
    Write-Output "Cross-tier contamination: 0"
    Write-Output "Misclassification: 0"
    Write-Output "Direction A (registry -> binding): ALL PRESENT"
    Write-Output "Direction B (binding -> registry): ALL PRESENT"
    Write-Output "Runtime lifecycle != builtin: CONFIRMED"
    Write-Output "Test-only instrumentation != stable builtin: CONFIRMED"
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
