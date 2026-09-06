#!/bin/bash
# Phase 4 - Evidence Validator Runner (v2 - Evidence Integrity Fix)
# Runs behavior tests, captures raw evidence, parses, validates.
# Exit code 0 = all validations passed, 1 = validation failed.
#
# EVIDENCE INTEGRITY FIXES (v2):
# - Uses PIPESTATUS[0] to capture TLLVM exit code (not tee's exit code)
# - RUN_STATUS must be 0 for validation to pass
# - compile_exit == 0 AND runtime_exit == 0 AND validator_exit == 0 => PASS
# - process_exit_code is passed to validator and included in evidence JSON
# - Runtime failure != semantic failure: both are tracked separately

set -e

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

echo "========================================"
echo "Phase 4 - Evidence Validator v2"
echo "Evidence Integrity: PIPESTATUS + Runtime Gate"
echo "========================================"

# Track overall status
OVERALL_STATUS=0
FAILED_STEPS=()

# Helper: run a command with tee, capture REAL exit code via PIPESTATUS[0]
# Usage: run_with_tee <log_file> <command...>
# Returns: sets RUN_EXIT_CODE to the real command exit code
run_with_tee() {
    local log_file="$1"
    shift
    set +e
    "$@" 2>&1 | tee "$log_file"
    local exit_code=${PIPESTATUS[0]}
    set -e
    RUN_EXIT_CODE=$exit_code
}

# ============================================
# Step 1: Run Memory Behavior Test
# ============================================
echo ""
echo "=== Step 1: Memory Behavior Test ==="

run_with_tee "$LOG_DIR/memory_compile.log" \
    "$TLLVM" "$TLLC" compile "$REPO_ROOT/tests/memory-semantics-test.tll" -o "$LOG_DIR/memory-semantics-test.tllbc"
COMPILE_STATUS=$RUN_EXIT_CODE

if [ $COMPILE_STATUS -ne 0 ]; then
    echo "FAIL: Memory test compilation failed (real exit $COMPILE_STATUS)"
    OVERALL_STATUS=1
    FAILED_STEPS+=("memory_compile")
else
    echo "PASS: Memory test compiled successfully (exit 0)"

    run_with_tee "$LOG_DIR/memory_run.log" \
        "$TLLVM" "$LOG_DIR/memory-semantics-test.tllbc"
    RUN_STATUS=$RUN_EXIT_CODE

    echo "Memory runtime real exit code: $RUN_STATUS"

    # GATE: runtime exit must be 0
    if [ $RUN_STATUS -ne 0 ]; then
        echo "FAIL: Memory runtime exited non-zero ($RUN_STATUS) - Evidence Gate FAIL"
        OVERALL_STATUS=1
        FAILED_STEPS+=("memory_runtime")
    fi

    # Parse and validate behavior output (pass runtime exit code)
    set +e
    python3 "$BEHAVIOR_DIR/validate-behavior.py" \
        "$LOG_DIR/memory_run.log" "memory" "$BEHAVIOR_DIR/memory.json" \
        --runtime-exit "$RUN_STATUS"
    VALIDATE_STATUS=$?
    set -e

    if [ $VALIDATE_STATUS -ne 0 ]; then
        echo "FAIL: Memory behavior validation failed (exit $VALIDATE_STATUS)"
        OVERALL_STATUS=1
        FAILED_STEPS+=("memory_validate")
    else
        echo "PASS: Memory behavior validation passed"
    fi
fi

# ============================================
# Step 2: Run Evaluation Behavior Test
# ============================================
echo ""
echo "=== Step 2: Evaluation Behavior Test ==="

run_with_tee "$LOG_DIR/evaluation_compile.log" \
    "$TLLVM" "$TLLC" compile "$REPO_ROOT/tests/evaluation-semantics-test.tll" -o "$LOG_DIR/evaluation-semantics-test.tllbc"
COMPILE_STATUS=$RUN_EXIT_CODE

if [ $COMPILE_STATUS -ne 0 ]; then
    echo "FAIL: Evaluation test compilation failed (real exit $COMPILE_STATUS)"
    OVERALL_STATUS=1
    FAILED_STEPS+=("evaluation_compile")
else
    echo "PASS: Evaluation test compiled successfully (exit 0)"

    run_with_tee "$LOG_DIR/evaluation_run.log" \
        "$TLLVM" "$LOG_DIR/evaluation-semantics-test.tllbc"
    RUN_STATUS=$RUN_EXIT_CODE

    echo "Evaluation runtime real exit code: $RUN_STATUS"

    # GATE: runtime exit must be 0
    if [ $RUN_STATUS -ne 0 ]; then
        echo "FAIL: Evaluation runtime exited non-zero ($RUN_STATUS) - Evidence Gate FAIL"
        OVERALL_STATUS=1
        FAILED_STEPS+=("evaluation_runtime")
    fi

    set +e
    python3 "$BEHAVIOR_DIR/validate-behavior.py" \
        "$LOG_DIR/evaluation_run.log" "evaluation" "$BEHAVIOR_DIR/evaluation.json" \
        --runtime-exit "$RUN_STATUS"
    VALIDATE_STATUS=$?
    set -e

    if [ $VALIDATE_STATUS -ne 0 ]; then
        echo "FAIL: Evaluation behavior validation failed (exit $VALIDATE_STATUS)"
        OVERALL_STATUS=1
        FAILED_STEPS+=("evaluation_validate")
    else
        echo "PASS: Evaluation behavior validation passed"
    fi
fi

# ============================================
# Step 3: Run Ternary Acceptance Test
# ============================================
echo ""
echo "=== Step 3: Ternary Acceptance Test ==="

run_with_tee "$LOG_DIR/ternary_compile.log" \
    "$TLLVM" "$TLLC" compile "$REPO_ROOT/tests/ternary-acceptance-test.tll" -o "$LOG_DIR/ternary-acceptance-test.tllbc"
COMPILE_STATUS=$RUN_EXIT_CODE

if [ $COMPILE_STATUS -ne 0 ]; then
    echo "FAIL: Ternary test compilation failed (real exit $COMPILE_STATUS)"
    OVERALL_STATUS=1
    FAILED_STEPS+=("ternary_compile")
else
    echo "PASS: Ternary test compiled successfully (exit 0)"

    run_with_tee "$LOG_DIR/ternary_run.log" \
        "$TLLVM" "$LOG_DIR/ternary-acceptance-test.tllbc"
    RUN_STATUS=$RUN_EXIT_CODE

    echo "Ternary runtime real exit code: $RUN_STATUS"

    # GATE: runtime exit must be 0
    if [ $RUN_STATUS -ne 0 ]; then
        echo "FAIL: Ternary runtime exited non-zero ($RUN_STATUS) - Evidence Gate FAIL"
        OVERALL_STATUS=1
        FAILED_STEPS+=("ternary_runtime")
    fi

    set +e
    python3 "$BEHAVIOR_DIR/validate-behavior.py" \
        "$LOG_DIR/ternary_run.log" "ternary" "$BEHAVIOR_DIR/ternary.json" \
        --runtime-exit "$RUN_STATUS"
    VALIDATE_STATUS=$?
    set -e

    if [ $VALIDATE_STATUS -ne 0 ]; then
        echo "FAIL: Ternary behavior validation failed (exit $VALIDATE_STATUS)"
        OVERALL_STATUS=1
        FAILED_STEPS+=("ternary_validate")
    else
        echo "PASS: Ternary behavior validation passed"
    fi
fi

# ============================================
# Step 4: Capture TypeChecker Warnings
# ============================================
echo ""
echo "=== Step 4: Capture TypeChecker Warnings ==="
cd "$REPO_ROOT/compiler"

run_with_tee "$LOG_DIR/typechecker_raw.log" \
    "$TLLVM" compiler.tllbc
TC_STATUS=$RUN_EXIT_CODE

cd "$REPO_ROOT"

echo "TypeChecker real exit status: $TC_STATUS"
# Note: TypeChecker producing warnings is EXPECTED behavior.
# Execution failure (crash, exit != 0) is different from expected warnings.
# We capture both raw output and exit status for analysis.

# Parse warnings
set +e
python3 "$WARNINGS_DIR/parse-warnings.py" "$LOG_DIR/typechecker_raw.log" "$WARNINGS_DIR/warnings.json"
PARSE_STATUS=$?
set -e

if [ $PARSE_STATUS -ne 0 ]; then
    echo "FAIL: Warning parsing failed (exit $PARSE_STATUS)"
    OVERALL_STATUS=1
    FAILED_STEPS+=("warning_parse")
else
    echo "PASS: Warning parsing completed"

    # Validate raw warnings (without classification - that's a separate step)
    set +e
    python3 "$WARNINGS_DIR/validate-warnings.py" "$WARNINGS_DIR/warnings.json"
    VALIDATE_STATUS=$?
    set -e

    echo "Warning validation exit status: $VALIDATE_STATUS (raw capture stage - classification pending)"
fi

# ============================================
# Step 5: Summary
# ============================================
echo ""
echo "========================================"
echo "Phase 4 - Evidence Validator v2 Summary"
echo "========================================"
echo "Overall status: $([ $OVERALL_STATUS -eq 0 ] && echo 'PASS' || echo 'FAIL')"
echo "Failed steps: ${#FAILED_STEPS[@]}"
for step in "${FAILED_STEPS[@]}"; do
    echo "  - $step"
done

echo ""
echo "Evidence Integrity Gates:"
echo "  - Pipeline exit code: PIPESTATUS[0] (real command exit, not tee)"
echo "  - Runtime exit gate: runtime_exit != 0 => FAIL"
echo "  - Compile exit gate: compile_exit != 0 => FAIL"
echo "  - Validator exit gate: validator_exit != 0 => FAIL"
echo "  - process_exit_code included in evidence JSON"

echo ""
echo "Artifacts:"
echo "  Behavior logs: $LOG_DIR/"
echo "  Behavior JSON: $BEHAVIOR_DIR/"
echo "  Warnings raw: $LOG_DIR/typechecker_raw.log"
echo "  Warnings JSON: $WARNINGS_DIR/warnings.json"

exit $OVERALL_STATUS
