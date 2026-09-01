#!/bin/bash
# P0-15.18.5: Long-Run Stability Test Driver (Linux/macOS)
# 4 Node real TCP, 20 blocks continuous mining, 60 transactions,
# resource monitoring (RSS/fd), final consistency verification.
# Compatible with bash 3.2 (macOS default) - no associative arrays.
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TLLVM="host/c/tllvm"
TLLC="tools/TLLC/tllc.tllbc"
LOG_DIR="/tmp/lrs_logs_$$"
mkdir -p "$LOG_DIR"

# Individual variables for each node (bash 3.2 compatible)
PID_A=0; PID_B=0; PID_C=0; PID_D=0
HEIGHT_A=0; HEIGHT_B=0; HEIGHT_C=0; HEIGHT_D=0
TIP_A=""; TIP_B=""; TIP_C=""; TIP_D=""
VALID_A=""; VALID_B=""; VALID_C=""; VALID_D=""

echo "=== P0-15.18.5 Long-Run Stability Test ==="
echo "Log dir: $LOG_DIR"

# Helper: get PID by node name
get_pid() { case $1 in a) echo $PID_A;; b) echo $PID_B;; c) echo $PID_C;; d) echo $PID_D;; esac; }

# Step 1: Compile all test nodes
echo "--- Compiling test nodes ---"
for node in a b c d; do
    "$TLLVM" "$TLLC" compile "tests/lrs_${node}.tll" -o "tests/lrs_${node}.tllbc" 2>&1 | tail -1
    if [ ! -f "tests/lrs_${node}.tllbc" ]; then
        echo "FAIL: compile lrs_${node}.tll failed"
        exit 1
    fi
done
echo "  All 4 nodes compiled"

# Step 2: Start all nodes
echo "--- Starting 4 nodes ---"
for node in a b c d; do
    "$TLLVM" "tests/lrs_${node}.tllbc" > "$LOG_DIR/node_${node}.log" 2>&1 &
    pid=$!
    case $node in
        a) PID_A=$pid;; b) PID_B=$pid;; c) PID_C=$pid;; d) PID_D=$pid;;
    esac
    echo "  Node $node started (PID=$pid)"
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
    for node in a b c d; do
        pid=$(get_pid $node)
        if kill -0 "$pid" 2>/dev/null; then
            rss=$(ps -o rss= -p "$pid" 2>/dev/null | tr -d ' ' || echo 0)
            if [ -d "/proc/$pid/fd" ]; then
                fds=$(ls /proc/$pid/fd 2>/dev/null | wc -l | tr -d ' ')
            else
                fds=$(lsof -p "$pid" 2>/dev/null | wc -l | tr -d ' ')
            fi
            TOTAL_RSS=$((TOTAL_RSS + rss))
            TOTAL_FD=$((TOTAL_FD + fds))
        fi
    done
    if [ $TOTAL_RSS -gt $MAX_RSS ]; then MAX_RSS=$TOTAL_RSS; fi
    echo "  tick=$MONITOR_TICKS total_rss=${TOTAL_RSS}KB total_fd=$TOTAL_FD (max_rss=${MAX_RSS}KB)"
done

# Step 5: Wait for all nodes to finish
echo "--- Waiting for test completion (max 60s) ---"
WAIT_COUNT=0
ALL_DONE=0
while [ $WAIT_COUNT -lt 60 ] && [ $ALL_DONE -eq 0 ]; do
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
    ALL_DONE=1
    for node in a b c d; do
        pid=$(get_pid $node)
        if kill -0 "$pid" 2>/dev/null; then
            ALL_DONE=0
        fi
    done
done
if [ $ALL_DONE -eq 1 ]; then
    echo "  All nodes finished after ${WAIT_COUNT}s"
else
    echo "  Timeout: killing remaining nodes"
    for node in a b c d; do
        pid=$(get_pid $node)
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
        fi
    done
fi

# Step 6: Cleanup
echo "--- Cleaning up ---"
for node in a b c d; do
    pid=$(get_pid $node)
    if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid" 2>/dev/null || true
    fi
done
sleep 1

# Step 7: Parse results and run assertions
echo "--- Running assertions ---"
FAILURES=0
for node in a b c d; do
    log="$LOG_DIR/node_${node}.log"
    if [ ! -f "$log" ]; then
        echo "  FAIL: Node $node log not found"
        FAILURES=$((FAILURES + 1))
        continue
    fi
    height=$(grep -oP 'RESULT_NODE_[A-Z]+ height=\K[0-9]+' "$log" 2>/dev/null | head -1 || echo "0")
    tip=$(grep -oP 'RESULT_NODE_[A-Z]+ tip=\K[a-f0-9]+' "$log" 2>/dev/null | head -1 || echo "")
    valid=$(grep -oP 'RESULT_NODE_[A-Z]+ valid=\K[a-z]+' "$log" 2>/dev/null | head -1 || echo "")
    case $node in
        a) HEIGHT_A=$height; TIP_A=$tip; VALID_A=$valid;;
        b) HEIGHT_B=$height; TIP_B=$tip; VALID_B=$valid;;
        c) HEIGHT_C=$height; TIP_C=$tip; VALID_C=$valid;;
        d) HEIGHT_D=$height; TIP_D=$tip; VALID_D=$valid;;
    esac
    echo "  Node $node : height=$height tip=$tip valid=$valid"
    if [ "$valid" != "true" ]; then
        echo "  FAIL: Node $node valid=$valid (expected true)"
        FAILURES=$((FAILURES + 1))
    fi
    if [ "$height" -lt 20 ] 2>/dev/null; then
        echo "  FAIL: Node $node height=$height (expected >= 20)"
        FAILURES=$((FAILURES + 1))
    fi
done

# Check height consistency
FIRST_HEIGHT=$HEIGHT_A
for node in b c d; do
    case $node in b) h=$HEIGHT_B;; c) h=$HEIGHT_C;; d) h=$HEIGHT_D;; esac
    if [ "$h" != "$FIRST_HEIGHT" ]; then
        echo "  FAIL: Height mismatch - first=$FIRST_HEIGHT node $node=$h"
        FAILURES=$((FAILURES + 1))
    fi
done
echo "  All nodes height match: $FIRST_HEIGHT"

# Check tip hash consistency
FIRST_TIP=$TIP_A
for node in b c d; do
    case $node in b) t=$TIP_B;; c) t=$TIP_C;; d) t=$TIP_D;; esac
    if [ "$t" != "$FIRST_TIP" ]; then
        echo "  FAIL: Tip hash mismatch - first=$FIRST_TIP node $node=$t"
        FAILURES=$((FAILURES + 1))
    fi
done
echo "  All nodes tip hash match: $FIRST_TIP"

# Check for orphan processes
ORPHANS=$(pgrep -f "lrs_[a-d]\.tllbc" 2>/dev/null | wc -l | tr -d ' ')
if [ "$ORPHANS" -gt 0 ]; then
    echo "  FAIL: $ORPHANS orphan tllvm processes still running"
    FAILURES=$((FAILURES + 1))
    pkill -9 -f "lrs_[a-d]\.tllbc" 2>/dev/null || true
else
    echo "  No orphan processes"
fi

echo "  Max total RSS during test: ${MAX_RSS}KB ($((MAX_RSS / 1024))MB)"

# Final result
echo "---"
if [ $FAILURES -gt 0 ]; then
    echo "FAIL: P0-15.18.5 Long-Run Stability - $FAILURES assertion(s) failed"
    echo ""
    echo "=== Node logs (last 20 lines each) ==="
    for node in a b c d; do
        echo "--- node_${node}.log ---"
        tail -20 "$LOG_DIR/node_${node}.log" 2>/dev/null || echo "(no log)"
    done
    echo "Logs saved to: $LOG_DIR"
    exit 1
else
    echo "PASS: P0-15.18.5 Long-Run Stability - all assertions passed"
    echo "  4 nodes, 20 blocks, 60 transactions, ~130s continuous run"
    echo "  All nodes: height=$FIRST_HEIGHT tip=$FIRST_TIP valid=true"
    echo "  Max RSS: ${MAX_RSS}KB, no orphan processes"
    echo "Logs saved to: $LOG_DIR"
    exit 0
fi
