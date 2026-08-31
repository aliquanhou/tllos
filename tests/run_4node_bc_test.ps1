# P0-15.17: 4-Node Blockchain Network Test Driver
# Starts 4 independent TLL processes, verifies chain consensus
$ErrorActionPreference = "Continue"
$repo = "C:\Users\Administrator\Doubao\chats\2026-08-29\new-chat-3\tllos"
$tllvm = "$repo\host\c\tllvm.exe"
$testDir = "$repo\tests"
$logDir = "$repo\tests\bc_logs"
if (Test-Path $logDir) { Remove-Item -Recurse -Force $logDir }
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

Write-Host "=== Starting 4-Node Blockchain Network Test ==="

# Start Node A (leader)
Write-Host "Starting Node A..."
$procA = Start-Process -FilePath $tllvm -ArgumentList "tests\bc_node_a.tllbc" -WorkingDirectory $repo -RedirectStandardOutput "$logDir\node_a.log" -RedirectStandardError "$logDir\node_a_err.log" -PassThru -NoNewWindow

Start-Sleep -Seconds 2

# Start Nodes B, C, D
Write-Host "Starting Nodes B, C, D..."
$procB = Start-Process -FilePath $tllvm -ArgumentList "tests\bc_node_b.tllbc" -WorkingDirectory $repo -RedirectStandardOutput "$logDir\node_b.log" -RedirectStandardError "$logDir\node_b_err.log" -PassThru -NoNewWindow
$procC = Start-Process -FilePath $tllvm -ArgumentList "tests\bc_node_c.tllbc" -WorkingDirectory $repo -RedirectStandardOutput "$logDir\node_c.log" -RedirectStandardError "$logDir\node_c_err.log" -PassThru -NoNewWindow
$procD = Start-Process -FilePath $tllvm -ArgumentList "tests\bc_node_d.tllbc" -WorkingDirectory $repo -RedirectStandardOutput "$logDir\node_d.log" -RedirectStandardError "$logDir\node_d_err.log" -PassThru -NoNewWindow

Write-Host "All 4 nodes started. Waiting for completion..."

# Wait for all nodes (max 30 seconds)
$timeout = 30
$elapsed = 0
while ($elapsed -lt $timeout) {
    $allDone = $procA.HasExited -and $procB.HasExited -and $procC.HasExited -and $procD.HasExited
    if ($allDone) { break }
    Start-Sleep -Seconds 1
    $elapsed++
}

# Kill any remaining processes
if (-not $procA.HasExited) { Stop-Process -Id $procA.Id -Force -ErrorAction SilentlyContinue }
if (-not $procB.HasExited) { Stop-Process -Id $procB.Id -Force -ErrorAction SilentlyContinue }
if (-not $procC.HasExited) { Stop-Process -Id $procC.Id -Force -ErrorAction SilentlyContinue }
if (-not $procD.HasExited) { Stop-Process -Id $procD.Id -Force -ErrorAction SilentlyContinue }

Write-Host "`n=== Test Complete ==="
Write-Host "Node A exit code: $($procA.ExitCode)"
Write-Host "Node B exit code: $($procB.ExitCode)"
Write-Host "Node C exit code: $($procC.ExitCode)"
Write-Host "Node D exit code: $($procD.ExitCode)"

# Parse results
Write-Host "`n=== Chain Consensus Results ==="
$results = @{}
foreach ($node in @("a", "b", "c", "d")) {
    $log = Get-Content "$logDir\node_$node.log" -ErrorAction SilentlyContinue
    $resultLine = $log | Select-String "RESULT_NODE_" | Select-Object -First 1
    if ($resultLine) {
        Write-Host "Node $($node.ToUpper()): $($resultLine.Line)"
        if ($resultLine.Line -match "height=(\d+) tip=(\w+)") {
            $results[$node] = @{ height = $Matches[1]; tip = $Matches[2] }
        }
    } else {
        Write-Host "Node $($node.ToUpper()): NO RESULT FOUND"
        Write-Host "  Last 5 lines:"
        $log | Select-Object -Last 5 | ForEach-Object { Write-Host "    $_" }
    }
}

# Verify consensus
if ($results.Count -eq 4) {
    $heights = $results.Values | ForEach-Object { $_.height } | Sort-Object -Unique
    $tips = $results.Values | ForEach-Object { $_.tip } | Sort-Object -Unique
    Write-Host "`n=== Consensus Check ==="
    Write-Host "Unique heights: $($heights -join ', ')"
    Write-Host "Unique tip hashes: $($tips -join ', ')"
    if ($heights.Count -eq 1 -and $tips.Count -eq 1) {
        Write-Host "SUCCESS: All 4 nodes have identical chain (height=$($heights[0]), tip=$($tips[0]))"
        exit 0
    } else {
        Write-Host "FAILURE: Nodes do not agree on chain state"
        exit 1
    }
} else {
    Write-Host "FAILURE: Not all nodes produced results"
    exit 1
}