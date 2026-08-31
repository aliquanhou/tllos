#!/bin/bash
# P0-15.17.3: Blockchain Network CI Test Runner (Linux/macOS)
# Usage: run-bc-network-test.sh <test-name>
#   test-name: bc_node | bc_multi | bc_sync | bc_reconnect | bc_invalid
# Exit code: 0 = all assertions pass, 1 = any assertion fails

set -u

TEST_NAME="$1"
TLLVM="host/c/tllvm"
TLLC="tools/TLLC/tllc.tllbc"
LOG_DIR="/tmp/tll_bc_test_${TEST_NAME}"
TIMEOUT=40

mkdir -p "$LOG_DIR"

# Test configuration: nodes, wait time, assertions
case "$TEST_NAME" in
    bc_node)
        NODES="a b c d"
        LEADER="a"
        WAIT=25
        MIN_HEIGHT=1
        CHECK_TIP_MATCH=1
        CHECK_VALID=1
        ;;
    bc_multi)
        NODES="a b c d"
        LEADER="a"
        WAIT=35
        MIN_HEIGHT=5
        CHECK_TIP_MATCH=1
        CHECK_VALID=1
        ;;
    bc_sync)
        NODES="a b"
        LEADER="a"
        WAIT=30
        MIN_HEIGHT=2
        CHECK_TIP_MATCH=1
        CHECK_VALID=1
        ;;
    bc_reconnect)
        NODES="a b"
        LEADER="a"
        WAIT=35
        MIN_HEIGHT=4
        CHECK_TIP_MATCH=1
        CHECK_VALID=1
        ;;
    bc_invalid)
        NODES="a b"
        LEADER="a"
        WAIT=20
        MIN_HEIGHT=1
        CHECK_TIP_MATCH=0
        CHECK_VALID=1
        CHECK_INVALID_COUNT=1
        CHECK_FORK_COUNT=1
        ;;
    bc_stress)
        NODES="a b c d"
        LEADER="a"
        WAIT=55
        MIN_HEIGHT=1
        CHECK_TIP_MATCH=1
        CHECK_VALID=1
        CHECK_STRESS=1
        ;;
    *)
        echo "ERROR: Unknown test name: $TEST_NAME"
        echo "Usage: $0 <bc_node|bc_multi|bc_sync|bc_reconnect|bc_invalid|bc_stress>"
        exit 1
        ;;
esac

echo "=== Blockchain Network Test: $TEST_NAME ==="
echo "Nodes: $NODES"
echo "Wait: ${WAIT}s, Timeout: ${TIMEOUT}s"

# Step 1: Compile all nodes
echo "--- Compiling test nodes ---"
for node in $NODES; do
    SRC="tests/${TEST_NAME}_${node}.tll"
    BIN="tests/${TEST_NAME}_${node}.tllbc"
    if [ ! -f "$SRC" ]; then
        echo "FAIL: Source not found: $SRC"
        exit 1
    fi
    $TLLVM $TLLC compile "$SRC" -o "$BIN" > "$LOG_DIR/compile_${node}.log" 2>&1
    if [ $? -ne 0 ] || [ ! -f "$BIN" ]; then
        echo "FAIL: Compilation failed for $node"
        cat "$LOG_DIR/compile_${node}.log"
        exit 1
    fi
    echo "  Compiled: $node"
done

# Step 2: Start nodes (leader first, then others with delay)
echo "--- Starting nodes ---"
PIDS=""
for node in $NODES; do
    BIN="tests/${TEST_NAME}_${node}.tllbc"
    $TLLVM "$BIN" > "$LOG_DIR/node_${node}.log" 2>&1 &
    PID=$!
    PIDS="$PIDS $PID"
    echo "  Started node $node (PID=$PID)"
    if [ "$node" = "$LEADER" ]; then
        sleep 2
    else
        sleep 1
    fi
done

# Step 3: Wait for test completion (with timeout)
echo "--- Waiting ${WAIT}s for test execution ---"
ELAPSED=0
while [ $ELAPSED -lt $WAIT ]; do
    # Check if all processes have exited
    ALL_EXITED=1
    for PID in $PIDS; do
        if kill -0 $PID 2>/dev/null; then
            ALL_EXITED=0
            break
        fi
    done
    if [ $ALL_EXITED -eq 1 ]; then
        echo "  All nodes exited early after ${ELAPSED}s"
        break
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

# Step 4: Kill any remaining processes
echo "--- Cleaning up processes ---"
for PID in $PIDS; do
    kill $PID 2>/dev/null || true
done
sleep 1
for PID in $PIDS; do
    kill -9 $PID 2>/dev/null || true
done
# Also kill by pattern to catch any orphans
pkill -f "${TEST_NAME}_" 2>/dev/null || true

# Step 5: Parse results and run assertions
echo "--- Running assertions ---"
FAILURES=0

# Helper: extract field from RESULT line (node name is case-insensitive, RESULT uses uppercase)
get_field() {
    local node="$1"
    local field="$2"
    local node_upper=$(echo "$node" | tr '[:lower:]' '[:upper:]')
    grep "RESULT_NODE_${node_upper}" "$LOG_DIR/node_${node}.log" 2>/dev/null | \
        grep -o "${field}=[^ ]*" | head -1 | cut -d= -f2
}

# Check each node has RESULT line and meets minimum height
for node in $NODES; do
    LOG="$LOG_DIR/node_${node}.log"
    if [ ! -f "$LOG" ]; then
        echo "FAIL: Node $node log not found"
        FAILURES=$((FAILURES + 1))
        continue
    fi
    if ! grep -qi "RESULT_NODE_${node}" "$LOG"; then
        echo "FAIL: Node $node has no RESULT line (may have crashed or timed out)"
        echo "  Last 10 lines of node_${node}.log:"
        tail -10 "$LOG" | sed 's/^/    /'
        FAILURES=$((FAILURES + 1))
        continue
    fi

    HEIGHT=$(get_field "$node" "height")
    VALID=$(get_field "$node" "valid")
    TIP=$(get_field "$node" "tip")

    echo "  Node $node: height=$HEIGHT tip=$TIP valid=$VALID"

    # Check minimum height
    if [ -n "$HEIGHT" ] && [ "$HEIGHT" -lt "$MIN_HEIGHT" ] 2>/dev/null; then
        echo "FAIL: Node $node height=$HEIGHT < minimum=$MIN_HEIGHT"
        FAILURES=$((FAILURES + 1))
    fi

    # Check valid=true
    if [ "$CHECK_VALID" = "1" ] && [ "$VALID" != "true" ]; then
        echo "FAIL: Node $node valid=$VALID (expected true)"
        FAILURES=$((FAILURES + 1))
    fi
done

# Check tip hash match across all nodes
if [ "$CHECK_TIP_MATCH" = "1" ]; then
    FIRST_TIP=""
    for node in $NODES; do
        TIP=$(get_field "$node" "tip")
        if [ -z "$TIP" ]; then
            echo "FAIL: Node $node has no tip hash"
            FAILURES=$((FAILURES + 1))
            continue
        fi
        if [ -z "$FIRST_TIP" ]; then
            FIRST_TIP="$TIP"
        elif [ "$TIP" != "$FIRST_TIP" ]; then
            echo "FAIL: Tip hash mismatch - first node=$FIRST_TIP node $node=$TIP"
            FAILURES=$((FAILURES + 1))
        fi
    done
    if [ -n "$FIRST_TIP" ]; then
        echo "  All nodes tip hash match: $FIRST_TIP"
    fi
fi

# Check invalid block count (for bc_invalid test)
if [ "${CHECK_INVALID_COUNT:-0}" = "1" ]; then
    INVALID=$(get_field "a" "invalid")
    if [ -z "$INVALID" ] || [ "$INVALID" -lt 1 ] 2>/dev/null; then
        echo "FAIL: Node A invalidBlockCount=$INVALID (expected >= 1)"
        FAILURES=$((FAILURES + 1))
    else
        echo "  Node A rejected $INVALID invalid blocks"
    fi
fi

# Check fork count (for bc_invalid test)
if [ "${CHECK_FORK_COUNT:-0}" = "1" ]; then
    FORKS=$(get_field "a" "forks")
    if [ -z "$FORKS" ] || [ "$FORKS" -lt 1 ] 2>/dev/null; then
        echo "FAIL: Node A forkCount=$FORKS (expected >= 1)"
        FAILURES=$((FAILURES + 1))
    else
        echo "  Node A detected $FORKS forks"
    fi
fi

# Check stress test metrics (mempool overflow + high transaction count)
if [ "${CHECK_STRESS:-0}" = "1" ]; then
    LOG_A="$LOG_DIR/node_a.log"
    if [ -f "$LOG_A" ]; then
        # STRESS_SUBMITTED is on its own line
        SUBMITTED=$(grep -oP 'STRESS_SUBMITTED=\K\d+' "$LOG_A" | head -1)
        if [ -z "$SUBMITTED" ] || [ "$SUBMITTED" -lt 100 ] 2>/dev/null; then
            echo "FAIL: Node A STRESS_SUBMITTED=$SUBMITTED (expected >= 100)"
            FAILURES=$((FAILURES + 1))
        else
            echo "  Node A submitted $SUBMITTED transactions"
        fi
        # Verify mempool capacity=50 overflow behavior
        if grep -q "Mempool size after submission: 50" "$LOG_A"; then
            echo "  Node A mempool capacity=50 enforced (size=50 after 120 submissions)"
        else
            echo "FAIL: Node A mempool capacity=50 not enforced (expected 'Mempool size after submission: 50')"
            FAILURES=$((FAILURES + 1))
        fi
        # Verify block contains 50 transactions (mempool full block)
        if grep -q "Block mined:.*txs=50" "$LOG_A"; then
            echo "  Node A mined block with 50 transactions (full mempool block)"
        else
            echo "FAIL: Node A did not mine a block with 50 transactions"
            FAILURES=$((FAILURES + 1))
        fi
    else
        echo "FAIL: Node A log not found for stress check"
        FAILURES=$((FAILURES + 1))
    fi
fi

# Step 6: Report result
echo "---"
if [ $FAILURES -eq 0 ]; then
    echo "PASS: $TEST_NAME - all assertions passed"
    echo "Logs saved to: $LOG_DIR"
    exit 0
else
    echo "FAIL: $TEST_NAME - $FAILURES assertion(s) failed"
    echo "=== Node logs (for debugging) ==="
    for node in $NODES; do
        echo "--- node_${node}.log (last 30 lines) ---"
        tail -30 "$LOG_DIR/node_${node}.log" 2>/dev/null | sed 's/^/  /'
    done
    echo "Logs saved to: $LOG_DIR"
    exit 1
fi
