#!/bin/bash
# P0-15.18.4: Fault Injection Kill-9 Test Runner (Linux/macOS)
# Usage: run-fi-kill-test.sh <test-name>
#   test-name: fi_kill9 | fi_multi
# Exit code: 0 = all assertions pass, 1 = any assertion fails
#
# Uses real independent processes + real TCP, no mocks.

set -u

TEST_NAME="$1"
TLLVM="host/c/tllvm"
TLLC="tools/TLLC/tllc.tllbc"
LOG_DIR="/tmp/tll_fi_${TEST_NAME}"
NODES="a b c d"

# Determine test file prefix
if [ "$TEST_NAME" = "fi_multi" ]; then
    TEST_PREFIX="fi_multi"
else
    TEST_PREFIX="fi_kill"
fi

mkdir -p "$LOG_DIR"

echo "=== Fault Injection Test: $TEST_NAME ==="

# Step 1: Compile all nodes
echo "--- Compiling test nodes ---"
for node in $NODES; do
    src="tests/${TEST_PREFIX}_${node}.tll"
    bin="tests/${TEST_PREFIX}_${node}.tllbc"
    if [ ! -f "$src" ]; then
        echo "FAIL: Source not found: $src"
        exit 1
    fi
    $TLLVM $TLLC compile "$src" -o "$bin" > "$LOG_DIR/compile_${node}.log" 2>&1
    if [ $? -ne 0 ] || [ ! -f "$bin" ]; then
        echo "FAIL: Compilation failed for node $node"
        cat "$LOG_DIR/compile_${node}.log"
        exit 1
    fi
    echo "  Compiled: $node"
done

# Step 2: Start all nodes
echo "--- Starting all nodes ---"
declare -A PIDS
for node in $NODES; do
    bin="tests/${TEST_PREFIX}_${node}.tllbc"
    $TLLVM "$bin" > "$LOG_DIR/node_${node}.log" 2>&1 &
    PIDS[$node]=$!
    echo "  Started node $node (PID=${PIDS[$node]})"
    sleep 2
done

# Step 3: Wait for initial sync
echo "--- Waiting for initial sync (20s) ---"
sleep 20

# Step 4: Fault injection based on test type
if [ "$TEST_NAME" = "fi_kill9" ]; then
    # Scenario 1: Kill-9 Node B
    echo "--- KILL-9 Node B (PID=${PIDS[b]}) ---"
    kill -9 ${PIDS[b]} 2>/dev/null
    sleep 2
    echo "  Node B killed. Other nodes continue."

    # Wait for Node A to mine more blocks while B is down
    echo "--- Waiting for Node A to mine blocks while B is down (25s) ---"
    sleep 25

    # Restart Node B
    echo "--- Restarting Node B ---"
    bin="tests/${TEST_PREFIX}_b.tllbc"
    $TLLVM "$bin" > "$LOG_DIR/node_b_restart.log" 2>&1 &
    PIDS[b]=$!
    echo "  Node B restarted (PID=${PIDS[b]})"

    # Wait for reconnect and sync
    echo "--- Waiting for Node B reconnect and sync (35s) ---"
    sleep 35

elif [ "$TEST_NAME" = "fi_multi" ]; then
    # Scenario 6: Multi-node consecutive faults
    # Kill B
    echo "--- KILL-9 Node B (PID=${PIDS[b]}) ---"
    kill -9 ${PIDS[b]} 2>/dev/null
    sleep 2
    echo "  Node B killed."

    # Wait, then kill C
    echo "--- Waiting (15s), then KILL-9 Node C ---"
    sleep 15
    kill -9 ${PIDS[c]} 2>/dev/null
    echo "  Node C killed (PID=${PIDS[c]})."

    # Wait for Node A to mine more blocks
    echo "--- Waiting for Node A to mine blocks (20s) ---"
    sleep 20

    # Restart B
    echo "--- Restarting Node B ---"
    bin="tests/${TEST_PREFIX}_b.tllbc"
    $TLLVM "$bin" > "$LOG_DIR/node_b_restart.log" 2>&1 &
    PIDS[b]=$!
    echo "  Node B restarted (PID=${PIDS[b]})"

    # Wait for B sync, then restart C
    echo "--- Waiting for B sync (20s), then restart Node C ---"
    sleep 20
    bin="tests/${TEST_PREFIX}_c.tllbc"
    $TLLVM "$bin" > "$LOG_DIR/node_c_restart.log" 2>&1 &
    PIDS[c]=$!
    echo "  Node C restarted (PID=${PIDS[c]})"

    # Wait for all sync
    echo "--- Waiting for all nodes sync (30s) ---"
    sleep 30
fi

# Step 5: Wait for all nodes to finish or timeout
echo "--- Waiting for test completion (max 30s) ---"
sleep 30

# Step 6: Kill remaining processes
echo "--- Cleaning up processes ---"
for node in $NODES; do
    if [ -n "${PIDS[$node]}" ]; then
        kill -9 ${PIDS[$node]} 2>/dev/null
    fi
done
sleep 1
pkill -9 -f "${TEST_PREFIX}_" 2>/dev/null || true

# Step 7: Parse results and run assertions
echo "--- Running assertions ---"
FAILURES=0

declare -A HEIGHTS
declare -A TIPS
declare -A VALIDS

for node in $NODES; do
    # Use restart log if exists and non-empty, otherwise original log
    log="$LOG_DIR/node_${node}_restart.log"
    if [ ! -f "$log" ] || [ ! -s "$log" ]; then
        log="$LOG_DIR/node_${node}.log"
    fi

    if [ ! -f "$log" ]; then
        echo "FAIL: Node $node log not found"
        FAILURES=$((FAILURES + 1))
        continue
    fi

    log_size=$(wc -c < "$log" 2>/dev/null || echo 0)
    echo "  Node $node log: $log ($log_size bytes)"

    result_line=$(grep "RESULT_NODE_$(echo $node | tr '[:lower:]' '[:upper:]')" "$log" | tail -1)
    if [ -z "$result_line" ]; then
        echo "FAIL: Node $node has no RESULT line (may have crashed or timed out)"
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
    if [ "$h" -lt 2 ] 2>/dev/null; then
        echo "FAIL: Node $node height=$h (expected >= 2)"
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
orphans=$(pgrep -f "${TEST_PREFIX}_" 2>/dev/null || true)
if [ -n "$orphans" ]; then
    echo "FAIL: Orphan tllvm processes still running: $orphans"
    FAILURES=$((FAILURES + 1))
    pkill -9 -f "${TEST_PREFIX}_" 2>/dev/null || true
else
    echo "  No orphan processes"
fi

# Step 8: Report result
echo "---"
if [ "$FAILURES" -eq 0 ]; then
    echo "PASS: $TEST_NAME - all assertions passed"
    echo "Logs saved to: $LOG_DIR"
    exit 0
else
    echo "FAIL: $TEST_NAME - $FAILURES assertion(s) failed"
    echo "=== Node logs (for debugging) ==="
    for node in $NODES; do
        log="$LOG_DIR/node_${node}_restart.log"
        if [ ! -f "$log" ] || [ ! -s "$log" ]; then
            log="$LOG_DIR/node_${node}.log"
        fi
        echo "--- node_${node}.log (last 20 lines) ---"
        if [ -f "$log" ]; then
            tail -20 "$log" | sed 's/^/  /'
        else
            echo "  (log not found)"
        fi
    done
    echo "Logs saved to: $LOG_DIR"
    exit 1
fi
