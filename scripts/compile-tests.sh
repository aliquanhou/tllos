#!/usr/bin/env bash
# ============================================================
# TLL OS - Compile All Tests (Linux/macOS)
# Compiles all .tll test files to .tllbc using tllc.
# Usage: scripts/compile-tests.sh
# ============================================================
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TLLVM_EXE="$REPO_ROOT/host/c/tllvm"
TLLC_BC="$REPO_ROOT/tools/TLLC/tllc.tllbc"

echo "=== TLL OS Compile Tests (Linux/macOS) ==="
echo ""

# Ensure tllc exists
if [ ! -f "$TLLC_BC" ]; then
    echo "[1/4] Bootstrapping tllc first..."
    "$REPO_ROOT/scripts/bootstrap-tllc.sh"
fi

# Compile acceptance tests
echo "[2/4] Compiling acceptance tests..."
ACCEPT_DIR="$REPO_ROOT/tests/acceptance"
COUNT=0
FAILED=0
for f in "$ACCEPT_DIR"/*.tll; do
    [ -f "$f" ] || continue
    COUNT=$((COUNT + 1))
    out="${f%.tll}.tllbc"
    if "$TLLVM_EXE" "$TLLC_BC" compile "$f" -o "$out" >/dev/null 2>&1; then
        echo "  OK:   $(basename "$f")"
    else
        echo "  FAIL: $(basename "$f")"
        FAILED=$((FAILED + 1))
    fi
done
echo "  Acceptance: $COUNT files, $FAILED failures"

# Compile regression tests (single files)
echo "[3/4] Compiling regression tests (single files)..."
REG_DIR="$REPO_ROOT/tests/regression"
COUNT=0
FAILED=0
for f in "$REG_DIR"/*.tll; do
    [ -f "$f" ] || continue
    COUNT=$((COUNT + 1))
    out="${f%.tll}.tllbc"
    if "$TLLVM_EXE" "$TLLC_BC" compile "$f" -o "$out" >/dev/null 2>&1; then
        echo "  OK:   $(basename "$f")"
    else
        echo "  FAIL: $(basename "$f")"
        FAILED=$((FAILED + 1))
    fi
done
echo "  Regression: $COUNT files, $FAILED failures"

# Compile regression test directories
echo "[4/4] Compiling regression test directories..."
for d in "$REG_DIR"/*/; do
    [ -d "$d" ] || continue
    if [ -f "$d/main.tll" ]; then
        out="${d}main.tllbc"
        if "$TLLVM_EXE" "$TLLC_BC" compile "$d/main.tll" -o "$out" >/dev/null 2>&1; then
            echo "  OK:   $(basename "$d")/main.tll"
        else
            echo "  FAIL: $(basename "$d")/main.tll"
        fi
    fi
done

echo ""
echo "=== Test Compilation Complete ==="
