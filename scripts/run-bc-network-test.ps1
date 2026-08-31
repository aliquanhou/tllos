# P0-15.17.3: Blockchain Network CI Test Runner (Windows)
# Usage: run-bc-network-test.ps1 <test-name>
#   test-name: bc_node | bc_multi | bc_sync | bc_reconnect | bc_invalid
# Exit code: 0 = all assertions pass, 1 = any assertion fails

param(
    [Parameter(Mandatory=$true)]
    [string]$TestName
)

$ErrorActionPreference = "Stop"
$TLLVM = "host\c\tllvm.exe"
$TLLC = "tools\TLLC\tllc.tllbc"
$LogDir = "$env:TEMP\tll_bc_test_$TestName"
$Timeout = 40

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# Test configuration
switch ($TestName) {
    "bc_node"     { $Nodes = @("a","b","c","d"); $Leader = "a"; $Wait = 25; $MinHeight = 1; $CheckTipMatch = $true;  $CheckValid = $true;  $CheckInvalid = $false; $CheckFork = $false }
    "bc_multi"    { $Nodes = @("a","b","c","d"); $Leader = "a"; $Wait = 35; $MinHeight = 5; $CheckTipMatch = $true;  $CheckValid = $true;  $CheckInvalid = $false; $CheckFork = $false }
    "bc_sync"     { $Nodes = @("a","b");          $Leader = "a"; $Wait = 20; $MinHeight = 2; $CheckTipMatch = $true;  $CheckValid = $true;  $CheckInvalid = $false; $CheckFork = $false }
    "bc_reconnect"{ $Nodes = @("a","b");          $Leader = "a"; $Wait = 35; $MinHeight = 4; $CheckTipMatch = $true;  $CheckValid = $true;  $CheckInvalid = $false; $CheckFork = $false }
    "bc_invalid"  { $Nodes = @("a","b");          $Leader = "a"; $Wait = 20; $MinHeight = 1; $CheckTipMatch = $false; $CheckValid = $true;  $CheckInvalid = $true;  $CheckFork = $true }
    default {
        Write-Output "ERROR: Unknown test name: $TestName"
        Write-Output "Usage: run-bc-network-test.ps1 <bc_node|bc_multi|bc_sync|bc_reconnect|bc_invalid>"
        exit 1
    }
}

Write-Output "=== Blockchain Network Test: $TestName ==="
Write-Output "Nodes: $($Nodes -join ' ')"
Write-Output "Wait: ${Wait}s, Timeout: ${Timeout}s"

# Helper: extract field from RESULT line
function Get-Field {
    param([string]$Node, [string]$Field)
    $log = "$LogDir\node_$Node.log"
    if (Test-Path $log) {
        $line = Select-String -Path $log -Pattern "RESULT_NODE_$Node" | Select-Object -First 1
        if ($line) {
            $match = [regex]::Match($line.Line, "${Field}=([^\s]+)")
            if ($match.Success) { return $match.Groups[1].Value }
        }
    }
    return $null
}

# Step 1: Compile all nodes
Write-Output "--- Compiling test nodes ---"
foreach ($node in $Nodes) {
    $src = "tests\${TestName}_${node}.tll"
    $bin = "tests\${TestName}_${node}.tllbc"
    if (-not (Test-Path $src)) {
        Write-Output "FAIL: Source not found: $src"
        exit 1
    }
    & $TLLVM $TLLC compile $src -o $bin 2>&1 | Out-File "$LogDir\compile_${node}.log"
    if (($LASTEXITCODE -ne 0) -or (-not (Test-Path $bin))) {
        Write-Output "FAIL: Compilation failed for $node"
        Get-Content "$LogDir\compile_${node}.log"
        exit 1
    }
    Write-Output "  Compiled: $node"
}

# Step 2: Start nodes
Write-Output "--- Starting nodes ---"
$Procs = @()
foreach ($node in $Nodes) {
    $bin = "tests\${TestName}_${node}.tllbc"
    $proc = Start-Process -FilePath $TLLVM -ArgumentList $bin -RedirectStandardOutput "$LogDir\node_${node}.log" -RedirectStandardError "$LogDir\node_${node}_err.log" -PassThru -NoNewWindow
    $Procs += $proc
    Write-Output "  Started node $node (PID=$($proc.Id))"
    if ($node -eq $Leader) { Start-Sleep -Seconds 2 } else { Start-Sleep -Seconds 1 }
}

# Step 3: Wait for test completion
Write-Output "--- Waiting ${Wait}s for test execution ---"
$elapsed = 0
while ($elapsed -lt $Wait) {
    $allExited = $true
    foreach ($p in $Procs) {
        if (-not $p.HasExited) { $allExited = $false; break }
    }
    if ($allExited) {
        Write-Output "  All nodes exited early after ${elapsed}s"
        break
    }
    Start-Sleep -Seconds 2
    $elapsed += 2
}

# Step 4: Kill remaining processes
Write-Output "--- Cleaning up processes ---"
foreach ($p in $Procs) {
    if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
}
Start-Sleep -Seconds 1
# Kill by pattern to catch orphans
Get-Process -Name "tllvm" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*${TestName}_*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Step 5: Parse results and run assertions
Write-Output "--- Running assertions ---"
$failures = 0

foreach ($node in $Nodes) {
    $log = "$LogDir\node_${node}.log"
    if (-not (Test-Path $log)) {
        Write-Output "FAIL: Node $node log not found"
        $failures++
        continue
    }
    if (-not (Select-String -Path $log -Pattern "RESULT_NODE_${node}" -Quiet)) {
        Write-Output "FAIL: Node $node has no RESULT line (may have crashed or timed out)"
        Write-Output "  Last 10 lines of node_${node}.log:"
        Get-Content $log -Tail 10 | ForEach-Object { Write-Output "    $_" }
        $failures++
        continue
    }

    $height = Get-Field $node "height"
    $valid = Get-Field $node "valid"
    $tip = Get-Field $node "tip"

    Write-Output "  Node $node : height=$height tip=$tip valid=$valid"

    if ($height -and ([int]$height -lt $MinHeight)) {
        Write-Output "FAIL: Node $node height=$height < minimum=$MinHeight"
        $failures++
    }
    if ($CheckValid -and ($valid -ne "true")) {
        Write-Output "FAIL: Node $node valid=$valid (expected true)"
        $failures++
    }
}

# Check tip hash match
if ($CheckTipMatch) {
    $firstTip = $null
    foreach ($node in $Nodes) {
        $tip = Get-Field $node "tip"
        if (-not $tip) {
            Write-Output "FAIL: Node $node has no tip hash"
            $failures++
            continue
        }
        if (-not $firstTip) { $firstTip = $tip }
        elseif ($tip -ne $firstTip) {
            Write-Output "FAIL: Tip hash mismatch - first=$firstTip node $node=$tip"
            $failures++
        }
    }
    if ($firstTip) { Write-Output "  All nodes tip hash match: $firstTip" }
}

# Check invalid block count
if ($CheckInvalid) {
    $invalid = Get-Field "a" "invalid"
    if ((-not $invalid) -or ([int]$invalid -lt 1)) {
        Write-Output "FAIL: Node A invalidBlockCount=$invalid (expected >= 1)"
        $failures++
    } else {
        Write-Output "  Node A rejected $invalid invalid blocks"
    }
}

# Check fork count
if ($CheckFork) {
    $forks = Get-Field "a" "forks"
    if ((-not $forks) -or ([int]$forks -lt 1)) {
        Write-Output "FAIL: Node A forkCount=$forks (expected >= 1)"
        $failures++
    } else {
        Write-Output "  Node A detected $forks forks"
    }
}

# Step 6: Report result
Write-Output "---"
if ($failures -eq 0) {
    Write-Output "PASS: $TestName - all assertions passed"
    Write-Output "Logs saved to: $LogDir"
    exit 0
} else {
    Write-Output "FAIL: $TestName - $failures assertion(s) failed"
    Write-Output "=== Node logs (for debugging) ==="
    foreach ($node in $Nodes) {
        Write-Output "--- node_${node}.log (last 30 lines) ---"
        Get-Content "$LogDir\node_${node}.log" -Tail 30 -ErrorAction SilentlyContinue | ForEach-Object { Write-Output "  $_" }
    }
    Write-Output "Logs saved to: $LogDir"
    exit 1
}
