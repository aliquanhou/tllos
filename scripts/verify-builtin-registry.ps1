# TLL Native Builtin Registry Verification Gate
# Ensures nl_builtinFunctions in native_lower.tll matches runtime headers.

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

Write-Output "=== TLL Native Builtin Registry Verification ==="

# Extract builtins from native_lower.tll
$nativeLowerPath = Join-Path $repoRoot "compiler\native_lower.tll"
$loweringBuiltins = @()
$inList = $false
foreach ($line in Get-Content $nativeLowerPath) {
    if ($line -match 'let nl_builtinFunctions') { $inList = $true; continue }
    if ($inList -and $line -match '^\]') { $inList = $false; continue }
    if ($inList -and $line -match '"(tll_[^"]+)"') {
        $loweringBuiltins += $Matches[1]
    }
}
Write-Output "Lowering builtins: $($loweringBuiltins.Count)"

# Extract builtins from runtime headers
$headerBuiltins = @()
$headers = @("runtime\tll_runtime.h", "native\runtime\tll_native.h")
foreach ($h in $headers) {
    $p = Join-Path $repoRoot $h
    if (-not (Test-Path $p)) { continue }
    $c = Get-Content $p -Raw
    $ms = [regex]::Matches($c, '(?:TLLValue|void|int|char\s*\*|TLLArray\s*\*|TLLMap\s*\*)\s+(tll_[A-Za-z0-9_]+)\s*\(')
    foreach ($m in $ms) {
        $n = $m.Groups[1].Value
        if ($headerBuiltins -notcontains $n) { $headerBuiltins += $n }
    }
}
Write-Output "Header builtins: $($headerBuiltins.Count)"
Write-Output ""

# Compare
$missingInLowering = @()
foreach ($n in $headerBuiltins) {
    if ($loweringBuiltins -notcontains $n) { $missingInLowering += $n }
}

$pass = $true
if ($missingInLowering.Count -gt 0) {
    Write-Output "FAIL: Header functions missing from lowering registry:"
    foreach ($n in $missingInLowering) { Write-Output "  - $n" }
    $pass = $false
}

if ($pass) {
    Write-Output "=== BUILTIN REGISTRY VERIFICATION: PASS ==="
    exit 0
} else {
    Write-Output "=== BUILTIN REGISTRY VERIFICATION: FAIL ==="
    exit 1
}
