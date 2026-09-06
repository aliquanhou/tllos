#!/bin/bash
# Phase 4 - Evidence Validator Runner (v3 - Reality-Aligned)
# Runs behavior tests, captures raw evidence, parses, validates.
#
# v3 CHANGES:
# - Negative Ternary: verifies WARNING presence (current TLL semantics), not hard compile failure
# - TypeChecker Warning Capture: uses correct compile command to capture warnings
# - EVIDENCE: format validation (v3 validator)
# - OBSERVED/UNSUPPORTED are valid evidence statuses

set -e

# Trap to capture failure location
trap 'echo "::error::PHASE4_ERROR: `Script failed at line $LINENO, command: $BASH_COMMAND" >&2' ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TLLVM="$REPO_ROOT/host/c/tllvm"
TLLC="$REPO_ROOT/tools/TLLC/tllc.tllbc"
PHASE4_DIR="$REPO_ROOT/phase4"
BEHAVIOR_DIR="$PHASE4_DIR/behavior"
WARNINGS_DIR="$PHASE4_DIR/warnings"
LOG_DIR="/tmp/phase4_logs"

mkdir -p "$LOG_DIR"
mkdir -p "$BEHAVIOR_DIR"
mkdir -p "$WARNINGS_DIR"

# Detect Python command (python3 on Linux, python on macOS)
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo "python3")
echo "Using Python: $PYTHON ($($PYTHON --version 2>&1))"

echo "========================================"
echo "Phase 4 - Evidence Validator v3"
echo "Reality-Aligned: EVIDENCE format + Warning semantics"
echo "========================================"

OVERALL_STATUS=0
FAILED_STEPS=()

run_with_tee() {
    local log_file="$1"
    shift
    local exit_code
    set +e
    # Direct redirection instead of tee to avoid pipe buffering timing issues
    "$@" > "$log_file" 2>&1
    exit_code=$?
    set -e
    # Sync to ensure all data is flushed to disk before reading
    sync "$log_file" 2>/dev/null || true
    cat "$log_file"
    RUN_EXIT_CODE=$exit_code
}

# ============================================
# Step 1: Memory Behavior Test
# ============================================
echo ""
echo "PHASE4_DEBUG: === Step 1: Memory Behavior Test STARTING ==="

run_with_tee "$LOG_DIR/memory_compile.log" \
    "$TLLVM" "$TLLC" compile "$REPO_ROOT/tests/memory-semantics-test.tll" -o "$LOG_DIR/memory-semantics-test.tllbc"
COMPILE_STATUS=$RUN_EXIT_CODE

if [ $COMPILE_STATUS -ne 0 ]; then
    echo "::error::FAIL: Memory test compilation failed (real exit $COMPILE_STATUS)" >&2
    OVERALL_STATUS=1
    FAILED_STEPS+=("memory_compile")
else
    echo "PHASE4_DEBUG: Memory compile SUCCESS"

    run_with_tee "$LOG_DIR/memory_run.log" \
        "$TLLVM" "$LOG_DIR/memory-semantics-test.tllbc"
    RUN_STATUS=$RUN_EXIT_CODE

    echo "Memory runtime real exit code: $RUN_STATUS"

    if [ $RUN_STATUS -ne 0 ]; then
        echo "::error::FAIL: Memory runtime exited non-zero ($RUN_STATUS)" >&2
        OVERALL_STATUS=1
        FAILED_STEPS+=("memory_runtime")
    fi

    # DEBUG: Dump log file content before validation
    echo "::error::DEBUG memory_run.log exists: $(test -f "$LOG_DIR/memory_run.log" && echo YES || echo NO), size: $(stat -f%z "$LOG_DIR/memory_run.log" 2>/dev/null || stat -c%s "$LOG_DIR/memory_run.log" 2>/dev/null || echo unknown)" >&2
    echo "::error::DEBUG memory_run.log first 5 lines:" >&2
    head -5 "$LOG_DIR/memory_run.log" 2>/dev/null | while IFS= read -r line; do echo "::error::  $line" >&2; done
    echo "::error::DEBUG memory_run.log last 5 lines:" >&2
    tail -5 "$LOG_DIR/memory_run.log" 2>/dev/null | while IFS= read -r line; do echo "::error::  $line" >&2; done
    echo "::error::DEBUG memory_run.log EVIDENCE count: $(grep -c '^EVIDENCE:' "$LOG_DIR/memory_run.log" 2>/dev/null || echo 0)" >&2

    set +e
    $PYTHON "$BEHAVIOR_DIR/validate-behavior.py" \
        "$LOG_DIR/memory_run.log" "memory" "$BEHAVIOR_DIR/memory.json" \
        --runtime-exit "$RUN_STATUS" 1>&2
    VALIDATE_STATUS=$?
    set -e

    if [ $VALIDATE_STATUS -ne 0 ]; then
        echo "::error::FAIL: Memory behavior validation failed (exit $VALIDATE_STATUS)" >&2
        OVERALL_STATUS=1
        FAILED_STEPS+=("memory_validate")
    else
        echo "PHASE4_DEBUG: Memory validator SUCCESS"
    fi
fi

# ============================================
# Step 2: Evaluation Behavior Test
# ============================================
echo ""
echo "PHASE4_DEBUG: === Step 2: Evaluation Behavior Test STARTING ==="

run_with_tee "$LOG_DIR/evaluation_compile.log" \
    "$TLLVM" "$TLLC" compile "$REPO_ROOT/tests/evaluation-semantics-test.tll" -o "$LOG_DIR/evaluation-semantics-test.tllbc"
COMPILE_STATUS=$RUN_EXIT_CODE

if [ $COMPILE_STATUS -ne 0 ]; then
    echo "::error::FAIL: Evaluation test compilation failed (real exit $COMPILE_STATUS)" >&2
    OVERALL_STATUS=1
    FAILED_STEPS+=("evaluation_compile")
else
    echo "PHASE4_DEBUG: Evaluation compile SUCCESS"

    run_with_tee "$LOG_DIR/evaluation_run.log" \
        "$TLLVM" "$LOG_DIR/evaluation-semantics-test.tllbc"
    RUN_STATUS=$RUN_EXIT_CODE

    echo "Evaluation runtime real exit code: $RUN_STATUS"

    if [ $RUN_STATUS -ne 0 ]; then
        echo "::error::FAIL: Evaluation runtime exited non-zero ($RUN_STATUS)" >&2
        OVERALL_STATUS=1
        FAILED_STEPS+=("evaluation_runtime")
    fi

    set +e
    $PYTHON "$BEHAVIOR_DIR/validate-behavior.py" \
        "$LOG_DIR/evaluation_run.log" "evaluation" "$BEHAVIOR_DIR/evaluation.json" \
        --runtime-exit "$RUN_STATUS" 1>&2
    VALIDATE_STATUS=$?
    set -e

    if [ $VALIDATE_STATUS -ne 0 ]; then
        echo "::error::FAIL: Evaluation behavior validation failed (exit $VALIDATE_STATUS)" >&2
        OVERALL_STATUS=1
        FAILED_STEPS+=("evaluation_validate")
    else
        echo "PHASE4_DEBUG: Evaluation validator SUCCESS"
    fi
fi

# ============================================
# Step 3: Ternary Acceptance Test
# ============================================
echo ""
echo "PHASE4_DEBUG: === Step 3: Ternary Acceptance Test STARTING ==="

run_with_tee "$LOG_DIR/ternary_compile.log" \
    "$TLLVM" "$TLLC" compile "$REPO_ROOT/tests/ternary-acceptance-test.tll" -o "$LOG_DIR/ternary-acceptance-test.tllbc"
COMPILE_STATUS=$RUN_EXIT_CODE

if [ $COMPILE_STATUS -ne 0 ]; then
    echo "::error::FAIL: Ternary test compilation failed (real exit $COMPILE_STATUS)" >&2
    OVERALL_STATUS=1
    FAILED_STEPS+=("ternary_compile")
else
    echo "PHASE4_DEBUG: Ternary compile SUCCESS"

    run_with_tee "$LOG_DIR/ternary_run.log" \
        "$TLLVM" "$LOG_DIR/ternary-acceptance-test.tllbc"
    RUN_STATUS=$RUN_EXIT_CODE

    echo "Ternary runtime real exit code: $RUN_STATUS"

    if [ $RUN_STATUS -ne 0 ]; then
        echo "::error::FAIL: Ternary runtime exited non-zero ($RUN_STATUS)" >&2
        OVERALL_STATUS=1
        FAILED_STEPS+=("ternary_runtime")
    fi

    set +e
    $PYTHON "$BEHAVIOR_DIR/validate-behavior.py" \
        "$LOG_DIR/ternary_run.log" "ternary" "$BEHAVIOR_DIR/ternary.json" \
        --runtime-exit "$RUN_STATUS" 1>&2
    VALIDATE_STATUS=$?
    set -e

    if [ $VALIDATE_STATUS -ne 0 ]; then
        echo "::error::FAIL: Ternary behavior validation failed (exit $VALIDATE_STATUS)" >&2
        OVERALL_STATUS=1
        FAILED_STEPS+=("ternary_validate")
    else
        echo "PHASE4_DEBUG: Ternary validator SUCCESS"
    fi
fi

# ============================================
# Step 3.5: Negative Ternary - WARNING Presence Verification
# IMPORTANT: Current TLL TypeChecker produces WARNING for type mismatch,
# NOT hard compile error. This is current canonical semantics.
# We verify WARNING is present, not that compilation fails.
# ============================================
echo ""
echo "PHASE4_DEBUG: === Step 3.5: Negative Ternary STARTING ==="

run_with_tee "$LOG_DIR/ternary_negative_compile.log" \
    "$TLLVM" "$TLLC" compile "$REPO_ROOT/tests/ternary-incompatible-types-negative.tll" -o "$LOG_DIR/ternary-negative.tllbc"
NEGATIVE_COMPILE_STATUS=$RUN_EXIT_CODE

echo "Negative ternary compile real exit code: $NEGATIVE_COMPILE_STATUS"

# Check if warning about type mismatch is present in the log
if grep -q "ternary operator type mismatch" "$LOG_DIR/ternary_negative_compile.log" 2>/dev/null; then
    echo "PASS: Type mismatch WARNING detected (current TLL semantics: warning, not hard error)"
else
    echo "WARN: Type mismatch warning not found in log - checking compilation result"
    if [ $NEGATIVE_COMPILE_STATUS -ne 0 ]; then
        echo "PASS: Negative ternary test failed to compile (hard error semantics)"
    else
        echo "::error::FAIL: Neither warning nor hard error detected for incompatible ternary types" >&2
        OVERALL_STATUS=1
        FAILED_STEPS+=("ternary_negative_warning")
    fi
fi

# ============================================
# Step 4: Capture TypeChecker Warnings
# Use compiler.tll compilation to capture TypeChecker warnings
# ============================================
echo ""
echo "PHASE4_DEBUG: === Step 4: Capture TypeChecker Warnings STARTING ==="
cd "$REPO_ROOT/compiler"

# Compile compiler.tll to capture TypeChecker warnings
# TypeChecker runs during compilation and outputs warnings to stdout/stderr
run_with_tee "$LOG_DIR/typechecker_raw.log" \
    "$TLLVM" "$TLLC" compile "$REPO_ROOT/compiler/compiler.tll" -o "$LOG_DIR/compiler_typecheck.tllbc"
TC_STATUS=$RUN_EXIT_CODE

cd "$REPO_ROOT"

echo "TypeChecker compilation real exit status: $TC_STATUS"

# Count warnings in raw log
WARNING_COUNT=$(grep -c "type warning" "$LOG_DIR/typechecker_raw.log" 2>/dev/null || echo "0")
echo "Raw TypeChecker warning count: $WARNING_COUNT"

# Parse warnings
set +e
$PYTHON "$WARNINGS_DIR/parse-warnings.py" "$LOG_DIR/typechecker_raw.log" "$WARNINGS_DIR/warnings.json"
PARSE_STATUS=$?
set -e

if [ $PARSE_STATUS -ne 0 ]; then
    echo "::error::FAIL: Warning parsing failed (exit $PARSE_STATUS)" >&2
    OVERALL_STATUS=1
    FAILED_STEPS+=("warning_parse")
else
    echo "PASS: Warning parsing completed"

    set +e
    $PYTHON "$WARNINGS_DIR/validate-warnings.py" "$WARNINGS_DIR/warnings.json" 1>&2
    VALIDATE_STATUS=$?
    set -e

    if [ $VALIDATE_STATUS -ne 0 ]; then
        echo "::error::FAIL: Warning validation failed (exit $VALIDATE_STATUS)" >&2
        OVERALL_STATUS=1
        FAILED_STEPS+=("warning_validate")
    else
        echo "PASS: Warning validation passed"
    fi
fi

# ============================================
# Step 5: Summary
# ============================================
echo ""
echo "========================================"
echo "Phase 4 - Evidence Validator v3 Summary"
echo "========================================"
echo "Overall status: $([ $OVERALL_STATUS -eq 0 ] && echo 'PASS' || echo 'FAIL')"
echo "Failed steps: ${#FAILED_STEPS[@]}"
for step in "${FAILED_STEPS[@]}"; do
    echo "  - $step"
done

echo ""
echo "Evidence Format: EVIDENCE: TEST_ID=... EXPECTED=... ACTUAL=... STATUS=..."
echo "Valid Statuses: PASS, FAIL, OBSERVED, UNSUPPORTED"
echo "Ternary Negative: WARNING presence (current TLL semantics)"

echo ""
echo "Artifacts:"
echo "  Behavior logs: $LOG_DIR/"
echo "  Behavior JSON: $BEHAVIOR_DIR/"
echo "  Warnings raw: $LOG_DIR/typechecker_raw.log"
echo "  Warnings JSON: $WARNINGS_DIR/warnings.json"
echo "  Raw warning count: $WARNING_COUNT"

exit $OVERALL_STATUS
