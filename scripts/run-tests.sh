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

echo "=== TLL OS Run Tests (Linux/macOS) ==="
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
    # Run test (set +e to capture non-zero exit codes, then restore)
    set +e
    "$TLLVM_EXE" "$tllbc" >"$TMPFILE" 2>&1
    local actual=$?
    set -e
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
    if [ -f "$d/main.tllbc" ]; then
        run_test "$d/main.tllbc" "$(basename "$d")/main.tllbc"
    fi
done

rm -f "$TMPFILE"

echo ""
echo "=== Test Results ==="
echo "Total:  $TOTAL"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ "$FAILED" -gt 0 ]; then
    echo "SOME TESTS FAILED"
    exit 1
else
    echo "ALL TESTS PASSED"
    exit 0
fi
