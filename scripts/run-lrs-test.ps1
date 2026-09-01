# P0-15.18.5: Long-Run Stability Test Driver (Windows)
# 4 Node real TCP, 20 blocks continuous mining, resource monitoring, final consistency.
param(
    [string]$TestName = "lrs"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$TLLVM = "host\c\tllvm.exe"
$TLLC = "tools\TLLC\tllc.tllbc"
$LogDir = "$env:TEMP\lrs_logs_$([System.Guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

$Nodes = @("a", "b", "c", "d")
$Pids = @{}
$Heights = @{}
$Tips = @{}
$Valids = @{}
$MaxRss = 0

Write-Output "=== P0-15.18.5 Long-Run Stability Test (Windows) ==="
Write-Output "Log dir: $LogDir"

# Step 1: Compile all test nodes
Write-Output "--- Compiling test nodes ---"
foreach ($node in $Nodes) {
    & $TLLVM $TLLC compile "tests\lrs_$node.tll" -o "tests\lrs_$node.tllbc" 2>&1 | Select-Object -Last 1
    if (-not (Test-Path "tests\lrs_$node.tllbc")) {
        Write-Output "FAIL: compile lrs_$node.tll failed"
        exit 1
    }
}
Write-Output "  All 4 nodes compiled"

# Step 2: Start all nodes
Write-Output "--- Starting 4 nodes ---"
foreach ($node in $Nodes) {
    $proc = Start-Process -FilePath $TLLVM -ArgumentList "tests\lrs_$node.tllbc" -RedirectStandardOutput "$LogDir\node_$node.log" -RedirectStandardError "$LogDir\node_$node.err" -PassThru -NoNewWindow
    $Pids[$node] = $proc.Id
    Write-Output "  Node $node started (PID=$($proc.Id))"
}

# Step 3: Wait for network setup
Write-Output "--- Waiting for network setup (10s) ---"
Start-Sleep -Seconds 10

# Step 4: Resource monitoring
Write-Output "--- Resource monitoring (every 10s) ---"
for ($tick = 1; $tick -le 12; $tick++) {
    Start-Sleep -Seconds 10
    $totalRss = 0
    $totalFd = 0
    foreach ($node in $Nodes) {
        $nodePid = $Pids[$node]
        $proc = Get-Process -Id $nodePid -ErrorAction SilentlyContinue
        if ($proc) {
            $totalRss += $proc.WorkingSet64 / 1KB
            $totalFd += $proc.HandleCount
        }
    }
    if ($totalRss -gt $MaxRss) { $MaxRss = $totalRss }
    Write-Output "  tick=$tick total_rss=$([math]::Round($totalRss))KB total_fd=$totalFd (max_rss=$([math]::Round($MaxRss))KB)"
}

# Step 5: Wait for completion
Write-Output "--- Waiting for test completion (max 60s) ---"
$wait = 0
while ($wait -lt 60) {
    Start-Sleep -Seconds 5
    $wait += 5
    $allDone = $true
    foreach ($node in $Nodes) {
        $proc = Get-Process -Id $Pids[$node] -ErrorAction SilentlyContinue
        if ($proc -and -not $proc.HasExited) { $allDone = $false }
    }
    if ($allDone) {
        Write-Output "  All nodes finished after ${wait}s"
        break
    }
}

# Step 6: Cleanup
Write-Output "--- Cleaning up ---"
foreach ($node in $Nodes) {
    $proc = Get-Process -Id $Pids[$node] -ErrorAction SilentlyContinue
    if ($proc -and -not $proc.HasExited) {
        Write-Output "  Node $node still running, killing"
        Stop-Process -Id $Pids[$node] -Force -ErrorAction SilentlyContinue
    }
}
Start-Sleep -Seconds 2
Get-Process -Name "tllvm" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*lrs_*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Step 7: Parse results
Write-Output "--- Running assertions ---"
$failures = 0

foreach ($node in $Nodes) {
    $log = "$LogDir\node_$node.log"
    if (-not (Test-Path $log)) {
        Write-Output "FAIL: Node $node log not found"
        $failures++
        continue
    }

    $resultLine = Get-Content $log | Select-String "RESULT_NODE_$($node.ToUpper())" | Select-Object -Last 1
    if (-not $resultLine) {
        Write-Output "FAIL: Node $node has no RESULT line"
        Write-Output "  Last 10 lines:"
        Get-Content $log -Tail 10 | ForEach-Object { Write-Output "    $_" }
        $failures++
        continue
    }

    $line = $resultLine.Line
    if ($line -match 'height=(\d+)') { $h = $Matches[1] } else { $h = "0" }
    if ($line -match 'tip=(\S+)') { $t = $Matches[1] } else { $t = "" }
    if ($line -match 'valid=(\S+)') { $v = $Matches[1] } else { $v = "false" }
    $Heights[$node] = $h
    $Tips[$node] = $t
    $Valids[$node] = $v
    Write-Output "  Node $node : height=$h tip=$t valid=$v"

    if ($v -ne "true") {
        Write-Output "FAIL: Node $node valid=$v (expected true)"
        $failures++
    }
    if ([int]$h -lt 20) {
        Write-Output "FAIL: Node $node height=$h (expected >= 20)"
        $failures++
    }
}

# Check heights match
$firstNode = $Nodes[0]
$firstHeight = $Heights[$firstNode]
foreach ($node in $Nodes) {
    if ($Heights[$node] -and $Heights[$node] -ne $firstHeight) {
        Write-Output "FAIL: Height mismatch - first=$firstHeight node $node=$($Heights[$node])"
        $failures++
    }
}
if ($firstHeight) { Write-Output "  All nodes height match: $firstHeight" }

# Check tips match
$firstTip = $Tips[$firstNode]
foreach ($node in $Nodes) {
    if ($Tips[$node] -and $Tips[$node] -ne $firstTip) {
        Write-Output "FAIL: Tip hash mismatch - first=$firstTip node $node=$($Tips[$node])"
        $failures++
    }
}
if ($firstTip) { Write-Output "  All nodes tip hash match: $firstTip" }

# Check no orphan processes
$orphans = Get-Process -Name "tllvm" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*lrs_*" }
if ($orphans) {
    Write-Output "FAIL: Orphan tllvm processes still running"
    $failures++
    $orphans | Stop-Process -Force -ErrorAction SilentlyContinue
} else {
    Write-Output "  No orphan processes"
}

Write-Output "  Max total RSS during test: $([math]::Round($MaxRss))KB ($([math]::Round($MaxRss / 1024))MB)"

# Step 8: Report
Write-Output "---"
if ($failures -eq 0) {
    Write-Output "PASS: P0-15.18.5 Long-Run Stability - all assertions passed"
    Write-Output "  4 nodes, 20 blocks, 60 transactions, ~130s continuous run"
    Write-Output "  All nodes: height=$firstHeight tip=$firstTip valid=true"
    Write-Output "  Max RSS: $([math]::Round($MaxRss))KB, no orphan processes"
    Write-Output "Logs saved to: $LogDir"
    exit 0
} else {
    Write-Output "FAIL: P0-15.18.5 Long-Run Stability - $failures assertion(s) failed"
    Write-Output "=== Node logs (last 20 lines each) ==="
    foreach ($node in $Nodes) {
        Write-Output "--- node_$node.log ---"
        Get-Content "$LogDir\node_$node.log" -Tail 20 | ForEach-Object { Write-Output "  $_" }
    }
    Write-Output "Logs saved to: $LogDir"
    exit 1
}
