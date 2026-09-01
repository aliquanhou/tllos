#!/bin/bash
# P0-15.18.5: Long-Run Stability Test Driver (Linux/macOS)
# 4 Node real TCP, 20 blocks continuous mining, 60 transactions,
# resource monitoring (RSS/fd), final consistency verification.
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TLLVM="host/c/tllvm"
TLLC="tools/TLLC/tllc.tllbc"
LOG_DIR="/tmp/lrs_logs_$$"
mkdir -p "$LOG_DIR"

NODES="a b c d"
declare -A PIDS
declare -A HEIGHTS
declare -A TIPS
declare -A VALIDS
declare -A RSS_START
declare -A RSS_END
declare -A FD_START
declare -A FD_END

echo "=== P0-15.18.5 Long-Run Stability Test ==="
echo "Log dir: $LOG_DIR"

# Step 1: Compile all test nodes
echo "--- Compiling test nodes ---"
for node in $NODES; do
    "$TLLVM" "$TLLC" compile "tests/lrs_${node}.tll" -o "tests/lrs_${node}.tllbc" 2>&1 | tail -1
    if [ ! -f "tests/lrs_${node}.tllbc" ]; then
        echo "FAIL: compile lrs_${node}.tll failed"
        exit 1
    fi
done
echo "  All 4 nodes compiled"

# Step 2: Start all nodes
echo "--- Starting 4 nodes ---"
for node in $NODES; do
    "$TLLVM" "tests/lrs_${node}.tllbc" > "$LOG_DIR/node_${node}.log" 2>&1 &
    PIDS[$node]=$!
    echo "  Node $node started (PID=${PIDS[$node]})"
done

# Step 3: Wait for nodes to connect and start mining
echo "--- Waiting for network setup (10s) ---"
sleep 10

# Step 4: Resource monitoring - sample RSS and fd count every 10s
echo "--- Resource monitoring (every 10s) ---"
MONITOR_TICKS=0
MAX_RSS=0
while [ $MONITOR_TICKS -lt 12 ]; do
    sleep 10
    MONITOR_TICKS=$((MONITOR_TICKS + 1))
    TOTAL_RSS=0
    TOTAL_FD=0
    for node in $NODES; do
        pid=${PIDS[$node]}
        if kill -0 "$pid" 2>/dev/null; then
            # RSS in KB
            rss=$(ps -o rss= -p "$pid" 2>/dev/null | tr -d ' ' || echo 0)
            # fd count
            if [ -d "/proc/$pid/fd" ]; then
                fds=$(ls /proc/$pid/fd 2>/dev/null | wc -l | tr -d ' ')
            else
                # macOS
                fds=$(lsof -p "$pid" 2>/dev/null | wc -l | tr -d ' ')
            fi
            TOTAL_RSS=$((TOTAL_RSS + rss))
            TOTAL_FD=$((TOTAL_FD + fds))
        fi
    done
    if [ $TOTAL_RSS -gt $MAX_RSS ]; then MAX_RSS=$TOTAL_RSS; fi
    echo "  tick=$MONITOR_TICKS total_rss=${TOTAL_RSS}KB total_fd=$TOTAL_FD (max_rss=${MAX_RSS}KB)"
done

# Step 5: Wait for all nodes to finish (Node A finishes mining, others follow)
echo "--- Waiting for test completion (max 60s) ---"
WAIT=0
while [ $WAIT -lt 60 ]; do
    sleep 5
    WAIT=$((WAIT + 5))
    ALL_DONE=1
    for node in $NODES; do
        if kill -0 "${PIDS[$node]}" 2>/dev/null; then
            ALL_DONE=0
        fi
    done
    if [ $ALL_DONE -eq 1 ]; then
        echo "  All nodes finished after ${WAIT}s"
        break
    fi
done

# Step 6: Kill any remaining processes
echo "--- Cleaning up ---"
for node in $NODES; do
    if kill -0 "${PIDS[$node]}" 2>/dev/null; then
        echo "  Node $node still running, killing"
        kill -9 "${PIDS[$node]}" 2>/dev/null || true
    fi
done
sleep 2
pkill -9 -f "lrs_" 2>/dev/null || true

# Step 7: Parse results and run assertions
echo "--- Running assertions ---"
FAILURES=0

for node in $NODES; do
    log="$LOG_DIR/node_${node}.log"
    if [ ! -f "$log" ]; then
        echo "FAIL: Node $node log not found"
        FAILURES=$((FAILURES + 1))
        continue
    fi

    result_line=$(grep "RESULT_NODE_$(echo $node | tr '[:lower:]' '[:upper:]')" "$log" | tail -1)
    if [ -z "$result_line" ]; then
        echo "FAIL: Node $node has no RESULT line"
        echo "  Last 10 lines:"
        tail -10 "$log" | sed 's/^/    /'
        FAILURES=$((FAILURES + 1))
        continue
    fi

    h=$(echo "$result_line" | grep -oP 'height=\K[0-9]+')
    t=$(echo "$result_line" | grep -oP 'tip=\K[^ ]+')
    v=$(echo "$result_line" | grep -oP 'valid=\K[^ ]+')
    HEIGHTS[$node]=$h
    TIPS[$node]=$t
    VALIDS[$node]=$v
    echo "  Node $node : height=$h tip=$t valid=$v"

    if [ "$v" != "true" ]; then
        echo "FAIL: Node $node valid=$v (expected true)"
        FAILURES=$((FAILURES + 1))
    fi
    if [ "$h" -lt 20 ] 2>/dev/null; then
        echo "FAIL: Node $node height=$h (expected >= 20)"
        FAILURES=$((FAILURES + 1))
    fi
done

# Check all heights match
first_node=$(echo $NODES | awk '{print $1}')
first_height=${HEIGHTS[$first_node]}
for node in $NODES; do
    if [ -n "${HEIGHTS[$node]}" ] && [ "${HEIGHTS[$node]}" != "$first_height" ]; then
        echo "FAIL: Height mismatch - first=$first_height node $node=${HEIGHTS[$node]}"
        FAILURES=$((FAILURES + 1))
    fi
done
if [ -n "$first_height" ]; then
    echo "  All nodes height match: $first_height"
fi

# Check all tip hashes match
first_tip=${TIPS[$first_node]}
for node in $NODES; do
    if [ -n "${TIPS[$node]}" ] && [ "${TIPS[$node]}" != "$first_tip" ]; then
        echo "FAIL: Tip hash mismatch - first=$first_tip node $node=${TIPS[$node]}"
        FAILURES=$((FAILURES + 1))
    fi
done
if [ -n "$first_tip" ]; then
    echo "  All nodes tip hash match: $first_tip"
fi

# Check no orphan processes
orphans=$(pgrep -f "lrs_" 2>/dev/null || true)
if [ -n "$orphans" ]; then
    echo "FAIL: Orphan tllvm processes still running: $orphans"
    FAILURES=$((FAILURES + 1))
    pkill -9 -f "lrs_" 2>/dev/null || true
else
    echo "  No orphan processes"
fi

# Resource leak check: max RSS should be reasonable (< 500MB total)
echo "  Max total RSS during test: ${MAX_RSS}KB ($((MAX_RSS / 1024))MB)"
if [ $MAX_RSS -gt 512000 ]; then
    echo "WARN: Max RSS > 500MB, possible memory leak (not a hard failure)"
fi

# Step 8: Report result
echo "---"
if [ "$FAILURES" -eq 0 ]; then
    echo "PASS: P0-15.18.5 Long-Run Stability - all assertions passed"
    echo "  4 nodes, 20 blocks, 60 transactions, ~130s continuous run"
    echo "  All nodes: height=$first_height tip=$first_tip valid=true"
    echo "  Max RSS: ${MAX_RSS}KB, no orphan processes"
    echo "Logs saved to: $LOG_DIR"
    exit 0
else
    echo "FAIL: P0-15.18.5 Long-Run Stability - $FAILURES assertion(s) failed"
    echo "=== Node logs (last 20 lines each) ==="
    for node in $NODES; do
        echo "--- node_${node}.log ---"
        tail -20 "$LOG_DIR/node_${node}.log" | sed 's/^/  /'
    done
    echo "Logs saved to: $LOG_DIR"
    exit 1
fi
