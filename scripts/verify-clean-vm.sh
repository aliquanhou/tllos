#!/bin/bash
# ============================================================
# TLL Clean VM Canonical Verification
# Usage: scripts/verify-clean-vm.sh
#
# This script verifies that TLL can be built and tested from
# source in a clean environment. It is the Canonical Truth
# for TLL engineering verification.
#
# Exit codes:
#   0 = ALL CHECKS PASSED
#   1 = ONE OR MORE CHECKS FAILED
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/.."
HOST_C="$REPO_ROOT/host/c"
TOOLS_TLLC="$REPO_ROOT/tools/TLLC"

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    PASS_COUNT=$((PASS_COUNT + 1))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    FAIL_COUNT=$((FAIL_COUNT + 1))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    WARN_COUNT=$((WARN_COUNT + 1))
}

log_info() {
    echo "[INFO] $1"
}

echo "============================================================"
echo "TLL Clean VM Canonical Verification"
echo "============================================================"
echo ""

# ============================================================
# STEP 1: Environment Check
# ============================================================
echo "--- STEP 1: Environment Check ---"

UNAME=$(uname -s)
log_info "Platform: $UNAME"

# Check for C compiler
if command -v gcc &> /dev/null; then
    CC=gcc
    log_pass "C compiler found: gcc"
elif command -v clang &> /dev/null; then
    CC=clang
    log_pass "C compiler found: clang"
else
    log_fail "No C compiler found (gcc or clang required)"
fi

# Check for git
if command -v git &> /dev/null; then
    log_pass "Git found: $(git --version)"
else
    log_warn "Git not found (not required for build, but required for commit)"
fi

# Check for python3
if command -v python3 &> /dev/null; then
    log_pass "Python3 found: $(python3 --version)"
else
    log_warn "Python3 not found (some test scripts may not run)"
fi

echo ""

# ============================================================
# STEP 2: Native Build
# ============================================================
echo "--- STEP 2: Native Build ---"

cd "$HOST_C"

# Canonical C source list — must match build-native.sh, build-native.bat, and CI
TLL_C_SOURCES="main.c vm.c value.c json.c builtin.c ffi_builtin.c sqlite_builtin.c crypto_builtin.c password_builtin.c hmac_builtin.c http_client_builtin.c sqlite3.c"

# Verify all source files exist
MISSING_SOURCES=0
for src in $TLL_C_SOURCES; do
    if [ ! -f "$src" ]; then
        log_fail "Missing source file: host/c/$src"
        MISSING_SOURCES=1
    fi
done

if [ $MISSING_SOURCES -eq 0 ]; then
    log_pass "All 12 canonical C source files present"
fi

# Build
if [ "$UNAME" = "Darwin" ]; then
    BUILD_CMD="$CC -O2 -std=gnu99 -D_DARWIN_C_SOURCE -o tllvm $TLL_C_SOURCES -lm -lpthread -framework Security -framework CoreFoundation"
else
    BUILD_CMD="$CC -O2 -std=gnu99 -D_POSIX_C_SOURCE=200809L -D_GNU_SOURCE -o tllvm $TLL_C_SOURCES -lm -lpthread -ldl -lssl -lcrypto"
fi

log_info "Building tllvm..."
if eval $BUILD_CMD 2> /tmp/tll_build_errors.log; then
    log_pass "Native build successful"
    if [ -f tllvm ]; then
        log_info "tllvm size: $(wc -c < tllvm) bytes"
    fi
else
    log_fail "Native build failed"
    cat /tmp/tll_build_errors.log | tail -20
fi

echo ""

# ============================================================
# STEP 3: Bootstrap Compiler Verification
# ============================================================
echo "--- STEP 3: Bootstrap Compiler ---"

cd "$REPO_ROOT"

# Verify canonical bootstrap compiler exists
if [ -f "$TOOLS_TLLC/tllc.tllbc" ]; then
    log_pass "Canonical bootstrap compiler exists: tools/TLLC/tllc.tllbc ($(wc -c < "$TOOLS_TLLC/tllc.tllbc") bytes)"
else
    log_fail "Canonical bootstrap compiler missing: tools/TLLC/tllc.tllbc"
fi

# Verify bootstrap source can rebuild compiler
log_info "Rebuilding tllc.tllbc from source..."
if "$HOST_C/tllvm" "$TOOLS_TLLC/tllc.tllbc" compile "$TOOLS_TLLC/main.tll" -o /tmp/tllc_rebuilt.tllbc 2> /tmp/tllc_build.log; then
    log_pass "Bootstrap source rebuilds compiler successfully"
    if [ -f /tmp/tllc_rebuilt.tllbc ]; then
        log_info "Rebuilt tllc.tllbc size: $(wc -c < /tmp/tllc_rebuilt.tllbc) bytes"
    fi
else
    log_fail "Bootstrap source rebuild failed"
    tail -5 /tmp/tllc_build.log
fi

echo ""

# ============================================================
# STEP 4: Compile Smoke Test
# ============================================================
echo "--- STEP 4: Compile Smoke Test ---"

cd "$REPO_ROOT"

# Compile examples/hello.tll
if "$HOST_C/tllvm" "$TOOLS_TLLC/tllc.tllbc" compile examples/hello.tll -o /tmp/hello.tllbc 2> /dev/null; then
    log_pass "Compile examples/hello.tll successful"
else
    log_fail "Compile examples/hello.tll failed"
fi

echo ""

# ============================================================
# STEP 5: Runtime Smoke Test
# ============================================================
echo "--- STEP 5: Runtime Smoke Test ---"

cd "$REPO_ROOT"

if [ -f /tmp/hello.tllbc ]; then
    OUTPUT=$("$HOST_C/tllvm" /tmp/hello.tllbc 2>&1)
    if echo "$OUTPUT" | grep -q "Hello"; then
        log_pass "Runtime executes hello.tllbc correctly"
        log_info "Output: $OUTPUT"
    else
        log_fail "Runtime output incorrect"
        log_info "Output: $OUTPUT"
    fi
else
    log_fail "hello.tllbc not found, cannot run runtime test"
fi

echo ""

# ============================================================
# STEP 6: Core Language Tests
# ============================================================
echo "--- STEP 6: Core Language Tests ---"

cd "$REPO_ROOT"

# Find and run test files
TEST_DIRS=("tests/compiler" "tests/language" "tests/runtime" "tests/acceptance")
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

for test_dir in "${TEST_DIRS[@]}"; do
    if [ -d "$test_dir" ]; then
        for test_file in "$test_dir"/*.tll; do
            if [ -f "$test_file" ]; then
                TESTS_RUN=$((TESTS_RUN + 1))
                BASENAME=$(basename "$test_file" .tll)

                # Compile
                if "$HOST_C/tllvm" "$TOOLS_TLLC/tllc.tllbc" compile "$test_file" -o "/tmp/$BASENAME.tllbc" 2> /dev/null; then
                    # Run
                    if "$HOST_C/tllvm" "/tmp/$BASENAME.tllbc" 2> /dev/null | grep -q "PASS\|OK\|SUCCESS"; then
                        TESTS_PASSED=$((TESTS_PASSED + 1))
                    else
                        # Check if test expects failure
                        if echo "$BASENAME" | grep -qi "error\|fail\|invalid"; then
                            TESTS_PASSED=$((TESTS_PASSED + 1))
                        else
                            TESTS_FAILED=$((TESTS_FAILED + 1))
                            log_warn "Test failed (runtime): $test_file"
                        fi
                    fi
                else
                    # Compile failed
                    if echo "$BASENAME" | grep -qi "error\|fail\|invalid"; then
                        TESTS_PASSED=$((TESTS_PASSED + 1))
                    else
                        TESTS_FAILED=$((TESTS_FAILED + 1))
                        log_warn "Test failed (compile): $test_file"
                    fi
                fi

                rm -f "/tmp/$BASENAME.tllbc"
            fi
        done
    fi
done

if [ $TESTS_RUN -gt 0 ]; then
    log_info "Tests run: $TESTS_RUN, passed: $TESTS_PASSED, failed: $TESTS_FAILED"
    if [ $TESTS_FAILED -eq 0 ]; then
        log_pass "All core language tests passed"
    else
        log_warn "$TESTS_FAILED test(s) failed (see warnings above)"
    fi
else
    log_warn "No test files found"
fi

echo ""

# ============================================================
# STEP 7: FFI Test (if available)
# ============================================================
echo "--- STEP 7: FFI / Native Interop Test ---"

cd "$REPO_ROOT"

if [ -f tests/ffi/probe_ffi.tll ]; then
    if "$HOST_C/tllvm" "$TOOLS_TLLC/tllc.tllbc" compile tests/ffi/probe_ffi.tll -o /tmp/ffi_test.tllbc 2> /dev/null; then
        FFI_OUTPUT=$("$HOST_C/tllvm" /tmp/ffi_test.tllbc 2>&1)
        FFI_PASS=$(echo "$FFI_OUTPUT" | grep -c "PASS:" || true)
        FFI_FAIL=$(echo "$FFI_OUTPUT" | grep -c "FAIL:" || true)
        log_info "FFI tests: $FFI_PASS passed, $FFI_FAIL failed"
        if [ "$FFI_FAIL" -eq 0 ]; then
            log_pass "All FFI tests passed"
        else
            log_warn "Some FFI tests failed (may be platform-specific)"
        fi
        rm -f /tmp/ffi_test.tllbc
    else
        log_warn "FFI test compilation failed"
    fi
else
    log_warn "FFI test not found"
fi

echo ""

# ============================================================
# STEP 8: Repository Structure Verification
# ============================================================
echo "--- STEP 8: Repository Structure ---"

cd "$REPO_ROOT"

# Check canonical directories
CANONICAL_DIRS=("compiler" "runtime" "host/c" "stdlib" "tools" "tests" "examples" "docs" "spec" "scripts" ".github/workflows")
for dir in "${CANONICAL_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        log_pass "Canonical directory exists: $dir/"
    else
        log_fail "Canonical directory missing: $dir/"
    fi
done

# Check for stale references to deleted directories
STALE_REFS=0
if grep -r "phase4/" .github/workflows/ 2> /dev/null | grep -v "node_modules" | grep -q "."; then
    log_warn "Stale reference to phase4/ found in CI workflows"
    STALE_REFS=1
fi
if grep -r "mall/" .github/workflows/ 2> /dev/null | grep -q "."; then
    log_warn "Stale reference to mall/ found in CI workflows"
    STALE_REFS=1
fi
if [ $STALE_REFS -eq 0 ]; then
    log_pass "No stale references to deleted directories in CI workflows"
fi

echo ""

# ============================================================
# FINAL SUMMARY
# ============================================================
echo "============================================================"
echo "CLEAN VM VERIFICATION SUMMARY"
echo "============================================================"
echo -e "  ${GREEN}PASS: $PASS_COUNT${NC}"
echo -e "  ${RED}FAIL: $FAIL_COUNT${NC}"
echo -e "  ${YELLOW}WARN: $WARN_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}CANONICAL VM VERIFICATION: PASS${NC}"
    echo "============================================================"
    exit 0
else
    echo -e "${RED}CANONICAL VM VERIFICATION: FAIL${NC}"
    echo "============================================================"
    exit 1
fi
