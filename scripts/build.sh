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
# Canonical C source list — must match build-native.sh, build-native.bat, and CI workflows
TLL_C_SOURCES="main.c vm.c value.c json.c builtin.c ffi_builtin.c sqlite_builtin.c crypto_builtin.c password_builtin.c hmac_builtin.c http_client_builtin.c sqlite3.c"

echo "[2/3] Building tllvm..."
cd "$HOST_C"

UNAME=$(uname -s)
if [ "$UNAME" = "Darwin" ]; then
    $CC -O2 -std=gnu99 -D_DARWIN_C_SOURCE -o tllvm $TLL_C_SOURCES -lm -lpthread -framework Security -framework CoreFoundation
else
    $CC -O2 -std=gnu99 -D_POSIX_C_SOURCE=200809L -D_GNU_SOURCE -o tllvm $TLL_C_SOURCES -lm -lpthread -ldl -lssl -lcrypto
fi

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
