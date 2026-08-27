#!/usr/bin/env bash
# ============================================================
# TLL OS - Bootstrap tllc CLI Tool (Linux/macOS)
# Compiles tools/TLLC/ from source using the compiler seed.
# Uses file-swap with pre-defined compiler/bootstrap_tllc.tll.
# Usage: scripts/bootstrap-tllc.sh
# ============================================================
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST_C="$REPO_ROOT/host/c"
TLLVM_EXE="$HOST_C/tllvm"
COMPILER_DIR="$REPO_ROOT/compiler"
COMPILER_TLL="$COMPILER_DIR/compiler.tll"
COMPILER_BC="$COMPILER_DIR/compiler.tllbc"
BOOTSTRAP_TLL="$COMPILER_DIR/bootstrap_tllc.tll"
TLLC_BC="$REPO_ROOT/tools/TLLC/tllc.tllbc"

echo "=== TLL OS Bootstrap tllc (Linux/macOS) ==="
echo ""

# Step 1: Ensure tllvm exists
if [ ! -f "$TLLVM_EXE" ]; then
    echo "[1/4] Building tllvm first..."
    "$REPO_ROOT/scripts/build.sh"
else
    echo "[1/4] tllvm already available"
fi

# Step 2: Swap compiler.tll with bootstrap entry
echo "[2/4] Swapping compiler.tll with bootstrap entry..."
cp "$COMPILER_TLL" "$COMPILER_TLL.bootstrap_backup"
cp "$BOOTSTRAP_TLL" "$COMPILER_TLL"

# Cleanup function
cleanup() {
    echo "Restoring compiler.tll..."
    cp "$COMPILER_TLL.bootstrap_backup" "$COMPILER_TLL"
    rm -f "$COMPILER_TLL.bootstrap_backup"
    rm -f "$COMPILER_DIR/compiler_self_compiled.tllbc"
}
trap cleanup EXIT

# Step 3: Two-stage compile
echo "[3/4] Compiling tllc (two-stage bootstrap)..."
cd "$COMPILER_DIR"

# Stage 1: seed compiler compiles bootstrap entry
echo "  Stage 1: seed compiles bootstrap compiler..."
"$TLLVM_EXE" "$COMPILER_BC"

if [ ! -f "$COMPILER_DIR/compiler_self_compiled.tllbc" ]; then
    echo "ERROR: Stage 1 output not found"
    exit 1
fi

# Stage 2: bootstrap compiler compiles tllc
echo "  Stage 2: bootstrap compiler compiles tllc..."
"$TLLVM_EXE" "$COMPILER_DIR/compiler_self_compiled.tllbc"

# Step 4: Verify
echo "[4/4] Verifying output..."
if [ -f "$TLLC_BC" ]; then
    echo "SUCCESS: tllc.tllbc built"
    echo "  Size: $(wc -c < "$TLLC_BC") bytes"
else
    echo "ERROR: tllc.tllbc not found after build"
    exit 1
fi

echo ""
echo "=== Bootstrap Complete ==="
echo "Usage: host/c/tllvm tools/TLLC/tllc.tllbc <command> [options]"
echo "  help      Show help"
echo "  compile   Compile .tll to .tllbc"
echo "  check     Compile check (no output)"
echo "  info      Inspect .tllbc bytecode"
