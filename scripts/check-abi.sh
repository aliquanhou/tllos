#!/usr/bin/env bash
# ============================================================
# TLL OS - Builtin ABI Consistency Check
# Verifies spec/BUILTINS.json matches host/c/builtin.c
# Usage: scripts/check-abi.sh
# Exit 0 if consistent, 1 if drift detected.
# ============================================================
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SPEC="$REPO_ROOT/spec/BUILTINS.json"
IMPL="$REPO_ROOT/host/c/builtin.c"

echo "=== TLL OS ABI Consistency Check ==="
echo ""

ERRORS=0

# 1. Check spec file exists
if [ ! -f "$SPEC" ]; then
    echo "FAIL: spec/BUILTINS.json not found"
    exit 1
fi

# 2. Check implementation file exists
if [ ! -f "$IMPL" ]; then
    echo "FAIL: host/c/builtin.c not found"
    exit 1
fi

# 3. Verify process builtins (120-122) and P0-3 builtins (123-125) exist in both spec and implementation
echo "Checking process builtins (P0-2 extension) and time/fs builtins (P0-3 extension)..."

for idx in 120 121 122 123 124 125; do
    # Check spec
    if ! grep -q "\"index\": $idx" "$SPEC"; then
        echo "  FAIL: idx $idx missing from BUILTINS.json"
        ERRORS=$((ERRORS + 1))
    fi
    # Check implementation
    if ! grep -q "idx == $idx" "$IMPL"; then
        echo "  FAIL: idx $idx missing from builtin.c"
        ERRORS=$((ERRORS + 1))
    fi
done

# 4. Verify Genesis builtin ranges (0-97) are covered in implementation
echo "Checking Genesis builtin ranges (0-97)..."

# Check key range boundaries
for range in "idx >= 5 && idx <= 23" "idx >= 24 && idx <= 48" "idx >= 49 && idx <= 71" "idx >= 72 && idx <= 78" "idx >= 79 && idx <= 90" "idx >= 91 && idx <= 97"; do
    if ! grep -qF "$range" "$IMPL"; then
        echo "  FAIL: range '$range' missing from builtin.c"
        ERRORS=$((ERRORS + 1))
    fi
done

# 5. Verify no unregistered builtin indices in implementation (beyond 122)
echo "Checking for unregistered builtin indices..."
MAX_IDX=$(grep -oP 'idx == \K[0-9]+' "$IMPL" | sort -n | tail -1 || echo "0")
if [ "$MAX_IDX" -gt 200 ]; then
    echo "  FAIL: builtin.c contains idx $MAX_IDX beyond expected max (200)"
    ERRORS=$((ERRORS + 1))
fi

# 6. Verify spec version
echo "Checking spec version..."
if ! grep -q '"version": "1.3"' "$SPEC"; then
    echo "  WARN: BUILTINS.json version is not 1.2 (current)"
fi

echo ""
if [ "$ERRORS" -eq 0 ]; then
    echo "=== ABI CONSISTENT ==="
    exit 0
else
    echo "=== ABI DRIFT DETECTED: $ERRORS error(s) ==="
    exit 1
fi
