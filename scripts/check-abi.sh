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

# 5. Full-set ABI index consistency check (not just max index)
# Extract complete index sets from both spec and implementation, compare as sets
echo "Checking full ABI index set consistency between spec and implementation..."

# 5a. Extract all indices from spec (BUILTINS.json)
SPEC_INDICES=$(grep -oE '"index": [0-9]+' "$SPEC" 2>/dev/null | awk '{print $2}' | sort -n | uniq || true)
SPEC_COUNT=$(printf '%s\n' "$SPEC_INDICES" | grep -c . 2>/dev/null || echo 0)
echo "  Spec declared indices: $SPEC_COUNT (range 0-97, 120-145, 221-222)"

# 5b. Extract all explicit idx == N from implementation (excludes range checks like idx >= 5 && idx <= 23)
IMPL_INDICES=$(grep -oE 'idx == [0-9]+' "$IMPL" 2>/dev/null | awk '{print $3}' | sort -n | uniq || true)
IMPL_COUNT=$(printf '%s\n' "$IMPL_INDICES" | grep -c . 2>/dev/null || echo 0)
echo "  Implementation explicit idx == N: $IMPL_COUNT"

# 5c. Check every implementation explicit index is declared in spec (prevents undeclared builtins)
UNDECLARED=$(comm -13 <(printf '%s\n' "$SPEC_INDICES") <(printf '%s\n' "$IMPL_INDICES") 2>/dev/null || true)
if [ -n "$UNDECLARED" ]; then
    echo "  FAIL: implementation has indices not declared in spec: $UNDECLARED"
    ERRORS=$((ERRORS + 1))
else
    echo "  PASS: all implementation explicit indices are declared in spec"
fi

# 5d. Check spec extension indices (120+) are all implemented explicitly (Genesis 0-97 covered by range checks in step 4)
SPEC_EXT=$(printf '%s\n' "$SPEC_INDICES" | awk '$1 >= 120' 2>/dev/null || true)
MISSING_IMPL=$(comm -23 <(printf '%s\n' "$SPEC_EXT") <(printf '%s\n' "$IMPL_INDICES") 2>/dev/null || true)
if [ -n "$MISSING_IMPL" ]; then
    echo "  FAIL: spec extension indices missing from implementation: $MISSING_IMPL"
    ERRORS=$((ERRORS + 1))
else
    echo "  PASS: all spec extension indices (120+) are implemented"
fi
# 6. Verify spec version
echo "Checking spec version..."
if ! grep -q '"version": "1.3"' "$SPEC"; then
    echo "  WARN: BUILTINS.json version is not 1.3 (current)"
fi

echo ""
if [ "$ERRORS" -eq 0 ]; then
    echo "=== ABI CONSISTENT ==="
    exit 0
else
    echo "=== ABI DRIFT DETECTED: $ERRORS error(s) ==="
    exit 1
fi
