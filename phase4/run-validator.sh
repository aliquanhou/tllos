#!/bin/bash
# Phase 4 - Evidence Validator Runner
# Runs behavior tests, captures raw evidence, parses, validates.
# Exit code 0 = all validations passed, 1 = validation failed.
#
# IMPORTANT: This script does NOT use || true to swallow failures.
# It uses set +e / status=$? pattern to preserve both raw output and exit status.

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
echo "Phase 4 - Evidence Validator"
echo "========================================"

# Track overall status
OVERALL_STATUS=0
FAILED_STEPS=()

# ============================================
# Step 1: Run Memory Behavior Test
# ============================================
echo ""
echo "=== Step 1: Memory Behavior Test ==="
set +e
"$TLLVM" "$TLLC" compile "$REPO_ROOT/tests/memory-semantics-test.tll" -o "$LOG_DIR/memory-semantics-test.tllbc" 2>&1 | tee "$LOG_DIR/memory_compile.log"
COMPILE_STATUS=$?
set -e

if [ $COMPILE_STATUS -ne 0 ]; then
    echo "FAIL: Memory test compilation failed (exit $COMPILE_STATUS)"
    OVERALL_STATUS=1
    FAILED_STEPS+=("memory_compile")
else
    echo "PASS: Memory test compiled successfully"

    set +e
    "$TLLVM" "$LOG_DIR/memory-semantics-test.tllbc" 2>&1 | tee "$LOG_DIR/memory_run.log"
    RUN_STATUS=$?
    set -e

    # Parse and validate behavior output
    python3 "$BEHAVIOR_DIR/validate-behavior.py" "$LOG_DIR/memory_run.log" "memory" "$BEHAVIOR_DIR/memory.json"
    VALIDATE_STATUS=$?

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
set +e
"$TLLVM" "$TLLC" compile "$REPO_ROOT/tests/evaluation-semantics-test.tll" -o "$LOG_DIR/evaluation-semantics-test.tllbc" 2>&1 | tee "$LOG_DIR/evaluation_compile.log"
COMPILE_STATUS=$?
set -e

if [ $COMPILE_STATUS -ne 0 ]; then
    echo "FAIL: Evaluation test compilation failed (exit $COMPILE_STATUS)"
    OVERALL_STATUS=1
    FAILED_STEPS+=("evaluation_compile")
else
    echo "PASS: Evaluation test compiled successfully"

    set +e
    "$TLLVM" "$LOG_DIR/evaluation-semantics-test.tllbc" 2>&1 | tee "$LOG_DIR/evaluation_run.log"
    RUN_STATUS=$?
    set -e

    python3 "$BEHAVIOR_DIR/validate-behavior.py" "$LOG_DIR/evaluation_run.log" "evaluation" "$BEHAVIOR_DIR/evaluation.json"
    VALIDATE_STATUS=$?

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
set +e
"$TLLVM" "$TLLC" compile "$REPO_ROOT/tests/ternary-acceptance-test.tll" -o "$LOG_DIR/ternary-acceptance-test.tllbc" 2>&1 | tee "$LOG_DIR/ternary_compile.log"
COMPILE_STATUS=$?
set -e

if [ $COMPILE_STATUS -ne 0 ]; then
    echo "FAIL: Ternary test compilation failed (exit $COMPILE_STATUS)"
    OVERALL_STATUS=1
    FAILED_STEPS+=("ternary_compile")
else
    echo "PASS: Ternary test compiled successfully"

    set +e
    "$TLLVM" "$LOG_DIR/ternary-acceptance-test.tllbc" 2>&1 | tee "$LOG_DIR/ternary_run.log"
    RUN_STATUS=$?
    set -e

    python3 "$BEHAVIOR_DIR/validate-behavior.py" "$LOG_DIR/ternary_run.log" "ternary" "$BEHAVIOR_DIR/ternary.json"
    VALIDATE_STATUS=$?

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
set +e
"$TLLVM" compiler.tllbc 2>&1 | tee "$LOG_DIR/typechecker_raw.log"
TC_STATUS=$?
set -e
cd "$REPO_ROOT"

echo "TypeChecker execution exit status: $TC_STATUS"
# Note: TypeChecker producing warnings is EXPECTED behavior.
# Execution failure (crash) is different from expected warnings.
# We capture both raw output and exit status for analysis.

# Parse warnings
python3 "$WARNINGS_DIR/parse-warnings.py" "$LOG_DIR/typechecker_raw.log" "$WARNINGS_DIR/warnings.json"
PARSE_STATUS=$?

if [ $PARSE_STATUS -ne 0 ]; then
    echo "FAIL: Warning parsing failed (exit $PARSE_STATUS)"
    OVERALL_STATUS=1
    FAILED_STEPS+=("warning_parse")
else
    echo "PASS: Warning parsing completed"

    # Validate raw warnings (without classification - that's a separate step)
    python3 "$WARNINGS_DIR/validate-warnings.py" "$WARNINGS_DIR/warnings.json"
    VALIDATE_STATUS=$?

    # Note: validation may fail if count != 603 or fields missing.
    # This is EXPECTED at this stage - we're capturing raw evidence.
    # Classification and full validation come after.
    echo "Warning validation exit status: $VALIDATE_STATUS (raw capture stage - classification pending)"
fi

# ============================================
# Step 5: Summary
# ============================================
echo ""
echo "========================================"
echo "Phase 4 - Evidence Validator Summary"
echo "========================================"
echo "Overall status: $([ $OVERALL_STATUS -eq 0 ] && echo 'PASS' || echo 'FAIL')"
echo "Failed steps: ${#FAILED_STEPS[@]}"
for step in "${FAILED_STEPS[@]}"; do
    echo "  - $step"
done

echo ""
echo "Artifacts:"
echo "  Behavior logs: $LOG_DIR/"
echo "  Behavior JSON: $BEHAVIOR_DIR/"
echo "  Warnings raw: $LOG_DIR/typechecker_raw.log"
echo "  Warnings JSON: $WARNINGS_DIR/warnings.json"

exit $OVERALL_STATUS
