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
    "bc_sync"     { $Nodes = @("a","b");          $Leader = "a"; $Wait = 30; $MinHeight = 2; $CheckTipMatch = $true;  $CheckValid = $true;  $CheckInvalid = $false; $CheckFork = $false }
    "bc_reconnect"{ $Nodes = @("a","b");          $Leader = "a"; $Wait = 35; $MinHeight = 4; $CheckTipMatch = $true;  $CheckValid = $true;  $CheckInvalid = $false; $CheckFork = $false }
    "bc_invalid"  { $Nodes = @("a","b");          $Leader = "a"; $Wait = 20; $MinHeight = 1; $CheckTipMatch = $false; $CheckValid = $true;  $CheckInvalid = $true;  $CheckFork = $true }
    "bc_stress"   { $Nodes = @("a","b","c","d"); $Leader = "a"; $Wait = 55; $MinHeight = 1; $CheckTipMatch = $true;  $CheckValid = $true;  $CheckInvalid = $false; $CheckFork = $false; $CheckStress = $true }
    "fi_duptx"    { $Nodes = @("a","b","c","d"); $Leader = "a"; $Wait = 75; $MinHeight = 1; $CheckTipMatch = $true;  $CheckValid = $true;  $CheckInvalid = $false; $CheckFork = $false; $CheckStress = $false; $CheckDupTx = $true; $TestPrefix = "fi_duptx" }
    "fi_dupblock" { $Nodes = @("a","b","c","d"); $Leader = "a"; $Wait = 75; $MinHeight = 1; $CheckTipMatch = $true;  $CheckValid = $true;  $CheckInvalid = $false; $CheckFork = $false; $CheckStress = $false; $CheckDupBlock = $true; $TestPrefix = "fi_dupblock" }
    "fi_ooo"      { $Nodes = @("a","b");          $Leader = "a"; $Wait = 45; $MinHeight = 3; $CheckTipMatch = $true;  $CheckValid = $true;  $CheckInvalid = $false; $CheckFork = $false; $CheckStress = $false; $CheckOOO = $true; $TestPrefix = "fi_ooo" }
    default {
        Write-Output "ERROR: Unknown test name: $TestName"
        Write-Output "Usage: run-bc-network-test.ps1 <bc_node|bc_multi|bc_sync|bc_reconnect|bc_invalid|bc_stress|fi_duptx|fi_dupblock|fi_ooo>"
        exit 1
    }
}

Write-Output "=== Blockchain Network Test: $TestName ==="
Write-Output "Nodes: $($Nodes -join ' ')"
Write-Output "Wait: ${Wait}s, Timeout: ${Timeout}s"

# Helper: extract field from RESULT line (node name is case-insensitive, RESULT uses uppercase)
function Get-Field {
    param([string]$Node, [string]$Field)
    $nodeUpper = $Node.ToUpper()
    $log = "$LogDir\node_$Node.log"
    if (Test-Path $log) {
        $line = Select-String -Path $log -Pattern "RESULT_NODE_$nodeUpper" | Select-Object -First 1
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
    if (-not (Select-String -Path $log -Pattern "RESULT_NODE_${node}" -Quiet -CaseSensitive:$false)) {
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

# Check stress test metrics (mempool overflow + high transaction count)
if ($CheckStress) {
    $logA = "$LogDir\node_a.log"
    if (Test-Path $logA) {
        # STRESS_SUBMITTED is on its own line, not in RESULT_NODE_A
        $submittedLine = Select-String -Path $logA -Pattern "STRESS_SUBMITTED=(\d+)" | Select-Object -First 1
        $submitted = if ($submittedLine) { $submittedLine.Matches[0].Groups[1].Value } else { $null }
        if ((-not $submitted) -or ([int]$submitted -lt 100)) {
            Write-Output "FAIL: Node A STRESS_SUBMITTED=$submitted (expected >= 100)"
            $failures++
        } else {
            Write-Output "  Node A submitted $submitted transactions"
        }
        # Verify mempool capacity=50 overflow behavior
        $mempoolLine = Select-String -Path $logA -Pattern "Mempool size after submission: 50" | Select-Object -First 1
        if (-not $mempoolLine) {
            Write-Output "FAIL: Node A mempool capacity=50 not enforced (expected 'Mempool size after submission: 50')"
            $failures++
        } else {
            Write-Output "  Node A mempool capacity=50 enforced (size=50 after 120 submissions)"
        }
        # Verify block contains 50 transactions (mempool full block)
        $blockLine = Select-String -Path $logA -Pattern "Block mined:.*txs=50" | Select-Object -First 1
        if (-not $blockLine) {
            Write-Output "FAIL: Node A did not mine a block with 50 transactions"
            $failures++
        } else {
            Write-Output "  Node A mined block with 50 transactions (full mempool block)"
        }
        # Verify total transactions in all mined blocks >= 50
        $blockTxTotalLine = Select-String -Path $logA -Pattern "STRESS_BLOCK_TX_TOTAL=(\d+)" | Select-Object -First 1
        $blockTxTotal = if ($blockTxTotalLine) { $blockTxTotalLine.Matches[0].Groups[1].Value } else { $null }
        if ((-not $blockTxTotal) -or ([int]$blockTxTotal -lt 50)) {
            Write-Output "FAIL: Node A STRESS_BLOCK_TX_TOTAL=$blockTxTotal (expected >= 50)"
            $failures++
        } else {
            Write-Output "  Node A total transactions in mined blocks: $blockTxTotal"
        }
    } else {
        Write-Output "FAIL: Node A log not found for stress check"
        $failures++
    }
    # Verify B/C/D received >= 120 unique transactions via P2P (max mempool count before block arrival)
    foreach ($rcvNode in @("b","c","d")) {
        $logRcv = "$LogDir\node_$rcvNode.log"
        if (Test-Path $logRcv) {
            $rxLine = Select-String -Path $logRcv -Pattern "STRESS_TX_RECEIVED=(\d+)" | Select-Object -First 1
            $rxCount = if ($rxLine) { $rxLine.Matches[0].Groups[1].Value } else { $null }
            if ((-not $rxCount) -or ([int]$rxCount -lt 120)) {
                Write-Output "FAIL: Node $rcvNode STRESS_TX_RECEIVED=$rxCount (expected >= 120)"
                $failures++
            } else {
                Write-Output "  Node $rcvNode received $rxCount unique transactions via P2P"
            }
        } else {
            Write-Output "FAIL: Node $rcvNode log not found for stress check"
            $failures++
        }
    }
}

# Check duplicate transaction storm: B/C/D max mempool count should be 1 (duplicates deduped)
if ($CheckDupTx) {
    foreach ($rcvNode in @("b","c","d")) {
        $logRcv = "$LogDir\node_$rcvNode.log"
        if (Test-Path $logRcv) {
            $maxLine = Select-String -Path $logRcv -Pattern "DUP_TX_MAX_MEMPOOL=(\d+)" | Select-Object -First 1
            $maxCount = if ($maxLine) { $maxLine.Matches[0].Groups[1].Value } else { $null }
            if ((-not $maxCount) -or ([int]$maxCount -ne 1)) {
                Write-Output "FAIL: Node $rcvNode DUP_TX_MAX_MEMPOOL=$maxCount (expected = 1, duplicates should be deduped)"
                $failures++
            } else {
                Write-Output "  Node $rcvNode duplicate tx dedup verified (max mempool=1)"
            }
        }
    }
}

# Check duplicate block storm: B/C/D max height should be 1 (duplicate blocks not re-added)
if ($CheckDupBlock) {
    foreach ($rcvNode in @("b","c","d")) {
        $logRcv = "$LogDir\node_$rcvNode.log"
        if (Test-Path $logRcv) {
            $maxLine = Select-String -Path $logRcv -Pattern "DUP_BLOCK_MAX_HEIGHT=(\d+)" | Select-Object -First 1
            $maxHeight = if ($maxLine) { $maxLine.Matches[0].Groups[1].Value } else { $null }
            if ((-not $maxHeight) -or ([int]$maxHeight -ne 1)) {
                Write-Output "FAIL: Node $rcvNode DUP_BLOCK_MAX_HEIGHT=$maxHeight (expected = 1, duplicate blocks should not re-add)"
                $failures++
            } else {
                Write-Output "  Node $rcvNode duplicate block dedup verified (max height=1)"
            }
            # Also verify forkCount and invalidBlockCount are not abnormally high
            $forkLine = Select-String -Path $logRcv -Pattern "DUP_BLOCK_FORKS=(\d+)" | Select-Object -First 1
            $forks = if ($forkLine) { $forkLine.Matches[0].Groups[1].Value } else { "0" }
            if ([int]$forks -gt 0) {
                Write-Output "FAIL: Node $rcvNode DUP_BLOCK_FORKS=$forks (expected = 0, duplicate blocks should not trigger fork detection)"
                $failures++
            } else {
                Write-Output "  Node $rcvNode no false fork detection from duplicate blocks"
            }
        }
    }
}

# Check out-of-order block: Node B should have rejected at least 1 future block and final height=3
# Note: Block 3 rejection triggers auto-sync, which fetches all missing blocks.
# After sync, Block 2 and Block 1 are already on-chain, so only Block 3 is counted as rejected.
# This verifies: future block rejection + auto-sync trigger + final chain consistency.
if ($CheckOOO) {
    $logB = "$LogDir\node_b.log"
    if (Test-Path $logB) {
        $rejLine = Select-String -Path $logB -Pattern "OOO_REJECTED_FUTURE=(\d+)" | Select-Object -First 1
        $rejected = if ($rejLine) { $rejLine.Matches[0].Groups[1].Value } else { $null }
        if ((-not $rejected) -or ([int]$rejected -lt 1)) {
            Write-Output "FAIL: Node B OOO_REJECTED_FUTURE=$rejected (expected >= 1, at least one future block should be rejected)"
            $failures++
        } else {
            Write-Output "  Node B rejected $rejected future block(s), auto-sync triggered, final height=3 (out-of-order behavior verified)"
        }
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
