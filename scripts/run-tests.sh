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
    # Run test with optional timeout (prevents infinite loops from hanging CI)
    set +e
    if [ -n "$TIMEOUT_CMD" ]; then
        $TIMEOUT_CMD 10 "$TLLVM_EXE" "$tllbc" >"$TMPFILE" 2>&1
    else
        "$TLLVM_EXE" "$tllbc" >"$TMPFILE" 2>&1
    fi
    local actual=$?
    set -e
    # timeout exit code 124 means test timed out
    if [ "$actual" -eq 124 ]; then
        echo "  FAIL: $display (timeout after 10s - possible infinite loop)"
        FAILED=$((FAILED + 1))
        return
    fi
    if [ "$actual" != "$expected" ]; then
        echo "  FAIL: $display (exit=$actual expected=$expected)"
        FAILED=$((FAILED + 1))
        return
    fi
    # Stdout comparison if .expected.txt exists
    local expected_txt="${tllbc%.tllbc}.expected.txt"
    if [ -f "$expected_txt" ]; then
        if ! diff -q "$TMPFILE" "$expected_txt" >/dev/null 2>&1; then
            echo "  FAIL: $display (stdout mismatch)"
            FAILED=$((FAILED + 1))
            return
        fi
    fi
    echo "  PASS: $display"
    PASSED=$((PASSED + 1))
}

# Run acceptance tests
echo "--- Acceptance Tests ---"
for f in "$REPO_ROOT/tests/acceptance/"*.tllbc; do
    [ -f "$f" ] || continue
    run_test "$f" "$(basename "$f")"
done

# Run regression tests
echo "--- Regression Tests ---"
for f in "$REPO_ROOT/tests/regression/"*.tllbc; do
    [ -f "$f" ] || continue
    run_test "$f" "$(basename "$f")"
done

# Run regression test directories
echo "--- Regression Test Directories ---"
for d in "$REPO_ROOT/tests/regression/"*/; do
    [ -d "$d" ] || continue
    # Skip tests that expect compile errors (test.json with expectError: true)
    # These should fail at compile time, not be run
    if [ -f "$d/test.json" ]; then
        if grep -q "expectError.*true" "$d/test.json" 2>/dev/null; then
            echo "  SKIP: $(basename "$d")/ (expects compile error)"
            continue
        fi
    fi
    if [ -f "$d/main.tllbc" ]; then
        run_test "$d/main.tllbc" "$(basename "$d")/main.tllbc"
    fi
done

rm -f "$TMPFILE"

# Run scope semantics tests (P0-15.18.4-RUNTIME.4: Compiler Semantic Guardrail)
# These tests are compiled on-the-fly from .tll source, then run.
echo "--- Scope Semantics Tests ---"
SCOPE_ASSERTS=0

# === ASSERTION HARD GATE ===
# Independent golden values. These are NOT derived from source at runtime.
# If someone adds/removes an assertion in a test file, they MUST update
# the corresponding value here. Mismatch causes CI FAIL.
# Uses case statement instead of declare -A for bash 3.2 compatibility (macOS).
get_expected_asserts() {
    case "$1" in
        scope_01_global_local) echo 8 ;;
        scope_02_shadowing) echo 11 ;;
        scope_03_params) echo 10 ;;
        scope_04_nested_fn) echo 10 ;;
        scope_05_closure) echo 9 ;;
        scope_06_block) echo 14 ;;
        scope_07_coroutine) echo 5 ;;
        scope_08_multi_fn_recursion) echo 6 ;;
        scope_09_return_lifetime) echo 12 ;;
        scope_10_complete_chain) echo 10 ;;
        *) echo 0 ;;
    esac
}
EXPECTED_TOTAL_ASSERTS=95

TLLC_BC="$REPO_ROOT/tools/TLLC/tllc.tllbc"
for f in "$REPO_ROOT/tests/scope/"*.tll; do
    [ -f "$f" ] || continue
    TOTAL=$((TOTAL + 1))
    display="$(basename "$f")"
    test_name="$(basename "$f" .tll)"
    out="${f%.tll}.tllbc"
    # Compile
    set +e
    "$TLLVM_EXE" "$TLLC_BC" compile "$f" -o "$out" >"$TMPFILE" 2>&1
    compile_rc=$?
    set -e
    if [ "$compile_rc" -ne 0 ]; then
        echo "  FAIL: $display (compile error)"
        cat "$TMPFILE"
        FAILED=$((FAILED + 1))
        continue
    fi
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
