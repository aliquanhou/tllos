#!/usr/bin/env bash
# ============================================================
# TLL OS - Build Native Launcher (Linux/macOS)
# Usage: scripts/build.sh
# ============================================================
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST_C="$REPO_ROOT/host/c"
TLLVM_EXE="$HOST_C/tllvm"

echo "=== TLL OS Build (Linux/macOS) ==="
echo ""

# Step 1: Check for C compiler
echo "[1/3] Checking C compiler..."
if command -v gcc &> /dev/null; then
    CC=gcc
elif command -v clang &> /dev/null; then
    CC=clang
else
    echo "ERROR: No C compiler found (gcc or clang required)"
    echo "Install with: sudo apt-get install gcc  (Ubuntu/Debian)"
    echo "            or: brew install gcc        (macOS)"
    exit 1
fi
echo "Using compiler: $CC"

# Step 2: Build tllvm
echo "[2/3] Building tllvm..."
cd "$HOST_C"
$CC -O2 -std=c99 -D_WIN32=0 -o tllvm main.c vm.c value.c json.c builtin.c -lm

# Step 3: Verify
echo "[3/3] Verifying build..."
if [ -f "$TLLVM_EXE" ]; then
    echo "SUCCESS: tllvm built successfully"
    echo "Size: $(wc -c < "$TLLVM_EXE") bytes"
else
    echo "ERROR: tllvm not found after build"
    exit 1
fi

echo ""
echo "=== Build Complete ==="
echo "Native launcher: $TLLVM_EXE"
echo ""
echo "Next steps:"
echo "  scripts/bootstrap-tllc.sh    - Build tllc CLI tool"
echo "  scripts/compile-tests.sh     - Compile all test .tll files"
echo "  scripts/run-tests.sh         - Run all tests"
