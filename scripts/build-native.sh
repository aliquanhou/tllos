#!/bin/bash
# TLL Native Runtime Build Script (Linux/macOS)
# Canonical single source of truth for native build.
# All CI workflows and local builds should use this script.
#
# P2-01-B.6 Build & Source Convergence:
#   Bytecode VM now uses Shared TLL Runtime Core (runtime/) instead of
#   the old host/c/value.c. Bytecode and Native targets share the exact
#   same value semantics, reference counting, and arithmetic implementations.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST_C_DIR="$SCRIPT_DIR/../host/c"
RUNTIME_CORE_DIR="$SCRIPT_DIR/../runtime"

# Canonical C source files — DO NOT modify this list without updating
# build-native.bat and all CI workflows accordingly.
# Shared Runtime Core replaces old host/c/value.c:
#   runtime/value.c      - value creation, refcount, truthy, equals, Array/Map
#   runtime/arithmetic.c - arithmetic and comparison operations
#   runtime/io.c         - basic IO and runtime lifecycle
TLL_C_SOURCES=(
    main.c
    vm.c
    ../../runtime/value.c
    ../../runtime/arithmetic.c
    ../../runtime/io.c
    json.c
    builtin.c
    ffi_builtin.c
    sqlite_builtin.c
    crypto_builtin.c
    password_builtin.c
    hmac_builtin.c
    http_client_builtin.c
    sqlite3.c
)

# Detect platform
UNAME=$(uname -s)

cd "$HOST_C_DIR"

if [ "$UNAME" = "Darwin" ]; then
    echo "[build-native] macOS detected"
    echo "[build-native] Using Shared Runtime Core: $RUNTIME_CORE_DIR"
    gcc -O2 -std=gnu99 -D_DARWIN_C_SOURCE -I../../runtime \
        -o tllvm \
        "${TLL_C_SOURCES[@]}" \
        -lm -lpthread -framework Security -framework CoreFoundation
elif [ "$UNAME" = "Linux" ]; then
    echo "[build-native] Linux detected"
    echo "[build-native] Using Shared Runtime Core: $RUNTIME_CORE_DIR"
    gcc -O2 -std=gnu99 -D_POSIX_C_SOURCE=200809L -D_GNU_SOURCE -I../../runtime \
        -o tllvm \
        "${TLL_C_SOURCES[@]}" \
        -lm -lpthread -ldl -lssl -lcrypto
else
    echo "[build-native] ERROR: Unsupported platform: $UNAME"
    exit 1
fi

echo "[build-native] Build complete: $HOST_C_DIR/tllvm"
