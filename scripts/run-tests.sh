#!/usr/bin/env bash
# ============================================================
# TLL OS - Run All Tests (Linux/macOS)
# Supports stdout comparison via .expected.txt files.
# Non-zero exit code: name test file exitN.tll (e.g. exit42.tll)
# Usage: scripts/run-tests.sh
# ============================================================
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TLLVM_EXE="$REPO_ROOT/host/c/tllvm"
TMPFILE="$REPO_ROOT/.test_out.txt"

# Detect timeout command (Linux: timeout, macOS: gtimeout from coreutils)
# If neither exists, run without timeout protection.
TIMEOUT_CMD=""
if command -v timeout >/dev/null 2>&1; then
    TIMEOUT_CMD="timeout"
elif command -v gtimeout >/dev/null 2>&1; then
    TIMEOUT_CMD="gtimeout"
fi

echo "=== TLL OS Run Tests (Linux/macOS) ==="
if [ -n "$TIMEOUT_CMD" ]; then
    echo "Using $TIMEOUT_CMD for test timeout (10s)"
else
    echo "WARNING: no timeout command found, running without timeout protection"
fi
echo ""

# Ensure tllvm exists
if [ ! -f "$TLLVM_EXE" ]; then
    echo "Building tllvm first..."
    "$REPO_ROOT/scripts/build.sh"
fi

TOTAL=0
PASSED=0
FAILED=0

run_test() {
    local tllbc="$1"
    local display="$2"
    TOTAL=$((TOTAL + 1))
    local basename="$(basename "$tllbc" .tllbc)"
    local expected=0
    # Non-zero exit code convention: exitN.tllbc -> expected N
    if [[ "$basename" == exit* ]]; then
        expected="${basename#exit}"
    fi
    # DEBUG: scope test compile diagnostics
    echo "  DEBUG: compile_cmd=$TLLVM_EXE $TLLC_BC compile $f -o $out"
    echo "  DEBUG: compile_rc=$compile_rc"
    echo "  DEBUG: arg0=$TLLVM_EXE"
    echo "  DEBUG: arg1=$TLLC_BC"
    echo "  DEBUG: arg2=compile"
    echo "  DEBUG: arg3=$f"
    echo "  DEBUG: arg4=-o"
    echo "  DEBUG: arg5=$out"
    echo "  DEBUG: === OUTPUT ==="
    cat "$TMPFILE"
    echo "  DEBUG: === END OUTPUT ==="
    echo "  DEBUG: file exists=$([ -f "$out" ] && echo yes || echo no)"
    # Run
    set +e
    if [ -n "$TIMEOUT_CMD" ]; then
        $TIMEOUT_CMD 10 "$TLLVM_EXE" "$out" >"$TMPFILE" 2>&1
    else
        "$TLLVM_EXE" "$out" >"$TMPFILE" 2>&1
    fi
    run_rc=$?
    set -e
    if [ "$run_rc" -eq 124 ]; then
        echo "  FAIL: $display (timeout - possible infinite loop)"
        FAILED=$((FAILED + 1))
    elif [ "$run_rc" -ne 0 ]; then
        echo "  FAIL: $display (exit=$run_rc)"
        cat "$TMPFILE"
        FAILED=$((FAILED + 1))
    elif ! grep -q "PASS" "$TMPFILE" 2>/dev/null; then
        echo "  FAIL: $display (no PASS marker)"
        cat "$TMPFILE"
        FAILED=$((FAILED + 1))
    elif grep -q "FAIL" "$TMPFILE" 2>/dev/null; then
        echo "  FAIL: $display (contains FAIL)"
        cat "$TMPFILE"
        FAILED=$((FAILED + 1))
    else
        # Assertion Hard Gate: compare actual source count vs independent expected value
        actual_asserts=$(grep -c 'FAIL [0-9]' "$f" 2>/dev/null || echo 0)
        expected_asserts=$(get_expected_asserts "$test_name")
        if [ "$actual_asserts" -ne "$expected_asserts" ]; then
            echo "  FAIL: $display (assertion count mismatch: expected=$expected_asserts, actual=$actual_asserts)"
            echo "    If you added/removed assertions, update EXPECTED_ASSERTS in this script."
            FAILED=$((FAILED + 1))
        else
            echo "  PASS: $display ($actual_asserts/$expected_asserts assertions verified)"
            PASSED=$((PASSED + 1))
            SCOPE_ASSERTS=$((SCOPE_ASSERTS + actual_asserts))
        fi
    fi
    rm -f "$out"
done

# Assertion Hard Gate: verify total
if [ "$SCOPE_ASSERTS" -ne "$EXPECTED_TOTAL_ASSERTS" ]; then
    echo "FAIL: Scope assertion total mismatch: expected=$EXPECTED_TOTAL_ASSERTS, actual=$SCOPE_ASSERTS"
    FAILED=$((FAILED + 1))
else
    echo "  Scope assertion total: $SCOPE_ASSERTS/$EXPECTED_TOTAL_ASSERTS (HARD GATE PASS)"
fi

rm -f "$TMPFILE"

echo ""
echo "=== Test Results ==="
echo "Total:  $TOTAL"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "Scope assertions verified: $SCOPE_ASSERTS/$EXPECTED_TOTAL_ASSERTS (HARD GATE)"
echo ""

if [ "$FAILED" -gt 0 ]; then
    echo "SOME TESTS FAILED"
    exit 1
else
    echo "ALL TESTS PASSED"
    exit 0
fi
