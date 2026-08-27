#!/usr/bin/env bash
# ============================================================
# TLL OS - Run All Tests (Linux/macOS)
# Runs all compiled .tllbc test files and reports results.
# Usage: scripts/run-tests.sh
# ============================================================
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TLLVM_EXE="$REPO_ROOT/host/c/tllvm"

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

# Run acceptance tests
echo "--- Acceptance Tests ---"
for f in "$REPO_ROOT/tests/acceptance/"*.tllbc; do
    [ -f "$f" ] || continue
    TOTAL=$((TOTAL + 1))
    if "$TLLVM_EXE" "$f" >/dev/null 2>&1; then
        echo "  PASS: $(basename "$f")"
        PASSED=$((PASSED + 1))
    else
        echo "  FAIL: $(basename "$f")"
        FAILED=$((FAILED + 1))
    fi
done

# Run regression tests
echo "--- Regression Tests ---"
for f in "$REPO_ROOT/tests/regression/"*.tllbc; do
    [ -f "$f" ] || continue
    TOTAL=$((TOTAL + 1))
    if "$TLLVM_EXE" "$f" >/dev/null 2>&1; then
        echo "  PASS: $(basename "$f")"
        PASSED=$((PASSED + 1))
    else
        echo "  FAIL: $(basename "$f")"
        FAILED=$((FAILED + 1))
    fi
done

# Run regression test directories
for d in "$REPO_ROOT/tests/regression/"*/; do
    [ -d "$d" ] || continue
    if [ -f "$d/main.tllbc" ]; then
        TOTAL=$((TOTAL + 1))
        if "$TLLVM_EXE" "$d/main.tllbc" >/dev/null 2>&1; then
            echo "  PASS: $(basename "$d")/main.tllbc"
            PASSED=$((PASSED + 1))
        else
            echo "  FAIL: $(basename "$d")/main.tllbc"
            FAILED=$((FAILED + 1))
        fi
    fi
done

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
