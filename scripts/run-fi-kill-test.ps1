# P0-15.18.4 Fault Injection Test Runner (Windows)
# Usage: run-fi-kill-test.ps1 <test-name>
#   test-name: fi_kill9 | fi_multi
# Exit code: 0 = all assertions pass, 1 = any assertion fails
#
# Uses [System.Diagnostics.Process] with async output reading for reliable log capture.

param(
    [Parameter(Mandatory=$true)]
    [string]$TestName
)

$ErrorActionPreference = "Stop"
$TLLVM = "host\c\tllvm.exe"
$TLLC = "tools\TLLC\tllc.tllbc"
$LogDir = "$env:TEMP\tll_fi_$TestName"
$Nodes = @("a","b","c","d")
$TestPrefix = if ($TestName -eq "fi_multi") { "fi_multi" } else { "fi_kill" }

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Write-Output "=== Fault Injection Test: $TestName ==="

# Helper: start a node process with reliable async log capture
function Start-TestNode {
    param([string]$Node, [string]$LogSuffix = "")
    $bin = "tests\${TestPrefix}_${Node}.tllbc"
    $logFile = "$LogDir\node_${Node}${LogSuffix}.log"
    $errFile = "$LogDir\node_${Node}${LogSuffix}_err.log"

    # Initialize log files
    "" | Out-File -FilePath $logFile -Encoding utf8
    "" | Out-File -FilePath $errFile -Encoding utf8

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo.FileName = (Resolve-Path $TLLVM).Path
    $process.StartInfo.Arguments = "`"$bin`""
    $process.StartInfo.UseShellExecute = $false
    $process.StartInfo.RedirectStandardOutput = $true
    $process.StartInfo.RedirectStandardError = $true
    $process.StartInfo.CreateNoWindow = $true
    $process.StartInfo.WorkingDirectory = (Get-Location).Path

    # Async output handlers
    $outAction = {
        param($sender, $e)
        if ($e.Data -ne $null) {
            Add-Content -Path $Event.MessageData -Value $e.Data
        }
    }
    $errAction = {
        param($sender, $e)
        if ($e.Data -ne $null) {
            Add-Content -Path $Event.MessageData -Value $e.Data
        }
    }

    $outEvent = Register-ObjectEvent -InputObject $process -EventName OutputDataReceived -Action $outAction -MessageData $logFile
    $errEvent = Register-ObjectEvent -InputObject $process -EventName ErrorDataReceived -Action $errAction -MessageData $errFile

    $process.Start() | Out-Null
    $process.BeginOutputReadLine()
    $process.BeginErrorReadLine()

    Write-Output "  Started node $Node (PID=$($process.Id), log=$logFile)"
    return @{ Process = $process; OutEvent = $outEvent; ErrEvent = $errEvent; LogFile = $logFile }
}

# Helper: stop a node process and clean up events
function Stop-TestNode {
    param($NodeInfo, [bool]$Force = $false)
    if ($NodeInfo -and -not $NodeInfo.Process.HasExited) {
        if ($Force) {
            $NodeInfo.Process.Kill()
        } else {
            $NodeInfo.Process.CloseMainWindow() | Out-Null
            Start-Sleep -Milliseconds 500
            if (-not $NodeInfo.Process.HasExited) {
                $NodeInfo.Process.Kill()
            }
        }
        $NodeInfo.Process.WaitForExit(5000) | Out-Null
    }
    # Flush remaining output
    Start-Sleep -Milliseconds 500
    # Unregister events
    if ($NodeInfo.OutEvent) { Unregister-Event -SubscriptionId $NodeInfo.OutEvent.Id -ErrorAction SilentlyContinue }
    if ($NodeInfo.ErrEvent) { Unregister-Event -SubscriptionId $NodeInfo.ErrEvent.Id -ErrorAction SilentlyContinue }
}

# Step 1: Compile all nodes
Write-Output "--- Compiling test nodes ---"
foreach ($node in $Nodes) {
    $src = "tests\${TestPrefix}_${node}.tll"
    $bin = "tests\${TestPrefix}_${node}.tllbc"
    & $TLLVM $TLLC compile $src -o $bin 2>&1 | Out-File "$LogDir\compile_${node}.log"
    if (($LASTEXITCODE -ne 0) -or (-not (Test-Path $bin))) {
        Write-Output "FAIL: Compilation failed for node $node"
        Get-Content "$LogDir\compile_${node}.log"
        exit 1
    }
    Write-Output "  Compiled: $node"
}

# Step 2: Start all nodes
Write-Output "--- Starting all nodes ---"
$NodeInfos = @{}
foreach ($node in $Nodes) {
    $NodeInfos[$node] = Start-TestNode -Node $node
    Start-Sleep -Seconds 2
}

# Step 3: Wait for initial sync
Write-Output "--- Waiting for initial sync (20s) ---"
Start-Sleep -Seconds 20

# Check initial state
function Get-NodeHeight {
    param([string]$Node, [string]$LogSuffix = "")
    $log = "$LogDir\node_${Node}${LogSuffix}.log"
    if (Test-Path $log) {
        $line = Select-String -Path $log -Pattern "height=(\d+)" | Select-Object -Last 1
        if ($line -and $line.Matches.Count -gt 0) {
            return [int]$line.Matches[0].Groups[1].Value
        }
    }
    return -1
}

$initHeightA = Get-NodeHeight "a"
$initHeightB = Get-NodeHeight "b"
Write-Output "  Initial heights: A=$initHeightA, B=$initHeightB"

# Step 4: Fault injection based on test type
if ($TestName -eq "fi_kill9") {
    # Scenario 1: Kill-9 Node B
    Write-Output "--- KILL-9 Node B (PID=$($NodeInfos['b'].Process.Id)) ---"
    Stop-TestNode -NodeInfo $NodeInfos['b'] -Force $true
    Start-Sleep -Seconds 2
    Write-Output "  Node B killed. Other nodes continue."

    # Wait for Node A to mine more blocks while B is down
    Write-Output "--- Waiting for Node A to mine blocks while B is down (25s) ---"
    Start-Sleep -Seconds 25

    $heightADown = Get-NodeHeight "a"
    Write-Output "  Node A height while B down: $heightADown"

    # Restart Node B
    Write-Output "--- Restarting Node B ---"
    $NodeInfos['b'] = Start-TestNode -Node "b" -LogSuffix "_restart"
    Write-Output "  Node B restarted (PID=$($NodeInfos['b'].Process.Id))"

    # Wait for reconnect and sync
    Write-Output "--- Waiting for Node B reconnect and sync (35s) ---"
    Start-Sleep -Seconds 35

} elseif ($TestName -eq "fi_multi") {
    # Scenario 6: Multi-node consecutive faults
    # Kill B
    Write-Output "--- KILL-9 Node B (PID=$($NodeInfos['b'].Process.Id)) ---"
    Stop-TestNode -NodeInfo $NodeInfos['b'] -Force $true
    Start-Sleep -Seconds 2
    Write-Output "  Node B killed."

    # Wait, then kill C
    Write-Output "--- Waiting (15s), then KILL-9 Node C ---"
    Start-Sleep -Seconds 15
    Stop-TestNode -NodeInfo $NodeInfos['c'] -Force $true
    Write-Output "  Node C killed (PID=$($NodeInfos['c'].Process.Id))."

    # Wait for Node A to mine more blocks
    Write-Output "--- Waiting for Node A to mine blocks (20s) ---"
    Start-Sleep -Seconds 20

    # Restart B
    Write-Output "--- Restarting Node B ---"
    $NodeInfos['b'] = Start-TestNode -Node "b" -LogSuffix "_restart"
    Write-Output "  Node B restarted (PID=$($NodeInfos['b'].Process.Id))"

    # Wait for B sync, then restart C
    Write-Output "--- Waiting for B sync (20s), then restart Node C ---"
    Start-Sleep -Seconds 20
    $NodeInfos['c'] = Start-TestNode -Node "c" -LogSuffix "_restart"
    Write-Output "  Node C restarted (PID=$($NodeInfos['c'].Process.Id))"

    # Wait for all sync
    Write-Output "--- Waiting for all nodes sync (30s) ---"
    Start-Sleep -Seconds 30
}

# Step 5: Wait for all nodes to finish or timeout
Write-Output "--- Waiting for test completion (max 30s) ---"
$elapsed = 0
while ($elapsed -lt 30) {
    $allExited = $true
    foreach ($node in $Nodes) {
        if ($NodeInfos[$node] -and -not $NodeInfos[$node].Process.HasExited) {
            $allExited = $false
            break
        }
    }
    if ($allExited) { break }
    Start-Sleep -Seconds 2
    $elapsed += 2
}

# Step 6: Kill remaining processes and clean up
Write-Output "--- Cleaning up processes ---"
foreach ($node in $Nodes) {
    if ($NodeInfos[$node]) {
        Stop-TestNode -NodeInfo $NodeInfos[$node] -Force $true
    }
}
Start-Sleep -Seconds 1
Get-Process -Name "tllvm" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*${TestPrefix}_*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Step 7: Parse results and run assertions
Write-Output "--- Running assertions ---"
$failures = 0

# Check all nodes have RESULT line and valid=true
$heights = @{}
$tips = @{}
$valids = @{}
foreach ($node in $Nodes) {
    # Use restart log if exists (for killed/restarted nodes), otherwise original log
    $log = "$LogDir\node_${node}_restart.log"
    if (-not (Test-Path $log) -or ((Get-Item $log).Length -lt 10)) {
        $log = "$LogDir\node_${node}.log"
    }

    if (-not (Test-Path $log)) {
        Write-Output "FAIL: Node $node log not found"
        $failures++
        continue
    }

    $logSize = (Get-Item $log).Length
    Write-Output "  Node $node log: $log ($logSize bytes)"

    $resultLine = Select-String -Path $log -Pattern "RESULT_NODE_$($node.ToUpper())" | Select-Object -Last 1
    if (-not $resultLine) {
        Write-Output "FAIL: Node $node has no RESULT line (may have crashed or timed out)"
        Write-Output "  Last 10 lines:"
        Get-Content $log -Tail 10 | ForEach-Object { Write-Output "    $_" }
        $failures++
        continue
    }
    $h = [regex]::Match($resultLine.Line, "height=(\d+)").Groups[1].Value
    $t = [regex]::Match($resultLine.Line, "tip=([^\s]+)").Groups[1].Value
    $v = [regex]::Match($resultLine.Line, "valid=([^\s]+)").Groups[1].Value
    $heights[$node] = [int]$h
    $tips[$node] = $t
    $valids[$node] = $v
    Write-Output "  Node $node : height=$h tip=$t valid=$v"

    if ($v -ne "true") {
        Write-Output "FAIL: Node $node valid=$v (expected true)"
        $failures++
    }
    if ([int]$h -lt 2) {
        Write-Output "FAIL: Node $node height=$h (expected >= 2)"
        $failures++
    }
}

# Check all heights match
$firstHeight = $heights[$Nodes[0]]
foreach ($node in $Nodes) {
    if ($heights.ContainsKey($node) -and $heights[$node] -ne $firstHeight) {
        Write-Output "FAIL: Height mismatch - first=$firstHeight node $node=$($heights[$node])"
        $failures++
    }
}
if ($firstHeight) {
    Write-Output "  All nodes height match: $firstHeight"
}

# Check all tip hashes match
$firstTip = $tips[$Nodes[0]]
foreach ($node in $Nodes) {
    if ($tips.ContainsKey($node) -and $tips[$node] -ne $firstTip) {
        Write-Output "FAIL: Tip hash mismatch - first=$firstTip node $node=$($tips[$node])"
        $failures++
    }
}
if ($firstTip) {
    Write-Output "  All nodes tip hash match: $firstTip"
}

# Check no orphan processes
$orphans = Get-Process -Name "tllvm" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*${TestPrefix}_*" }
if ($orphans) {
    Write-Output "FAIL: Orphan tllvm processes still running: $($orphans.Id -join ', ')"
    $failures++
    $orphans | Stop-Process -Force -ErrorAction SilentlyContinue
} else {
    Write-Output "  No orphan processes"
}

# Step 8: Report result
Write-Output "---"
if ($failures -eq 0) {
    Write-Output "PASS: $TestName - all assertions passed"
    Write-Output "Logs saved to: $LogDir"
    exit 0
} else {
    Write-Output "FAIL: $TestName - $failures assertion(s) failed"
    Write-Output "=== Node logs (for debugging) ==="
    foreach ($node in $Nodes) {
        $log = "$LogDir\node_${node}_restart.log"
        if (-not (Test-Path $log) -or ((Get-Item $log).Length -lt 10)) {
            $log = "$LogDir\node_${node}.log"
        }
        Write-Output "--- node_${node}.log (last 20 lines) ---"
        if (Test-Path $log) {
            Get-Content $log -Tail 20 | ForEach-Object { Write-Output "  $_" }
        } else {
            Write-Output "  (log not found)"
        }
    }
    Write-Output "Logs saved to: $LogDir"
    exit 1
}
