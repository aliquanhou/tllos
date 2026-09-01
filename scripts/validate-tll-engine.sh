#!/bin/bash
# TLL OS .tll-engine/ Validation Script (Linux/macOS)
# Validates the structure, schema, and consistency of the AI Native Engineering Foundation.
# Usage: scripts/validate-tll-engine.sh [--strict]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENGINE_DIR="$REPO_ROOT/.tll-engine"

ERRORS=0
WARNINGS=0
STRICT=0

if [ "$1" = "--strict" ]; then
    STRICT=1
fi

echo "=========================================="
echo "TLL OS .tll-engine/ Validation"
echo "=========================================="
echo "Engine dir: $ENGINE_DIR"
echo "Strict mode: $STRICT"
echo ""

# --- Helper functions ---
error() {
    echo "  [ERROR] $1"
    ERRORS=$((ERRORS + 1))
}

warning() {
    echo "  [WARNING] $1"
    WARNINGS=$((WARNINGS + 1))
}

info() {
    echo "  [INFO] $1"
}

check_file_exists() {
    local filepath="$1"
    if [ ! -f "$filepath" ]; then
        error "Missing required file: $filepath"
        return 1
    fi
    return 0
}

check_json_valid() {
    local filepath="$1"
    if ! command -v python3 &>/dev/null; then
        warning "python3 not available, skipping JSON validation for $filepath"
        return 0
    fi
    if ! python3 -c "import json; json.load(open('$filepath'))" 2>/dev/null; then
        error "Invalid JSON: $filepath"
        return 1
    fi
    return 0
}

check_json_field() {
    local filepath="$1"
    local field="$2"
    if ! command -v python3 &>/dev/null; then
        return 0
    fi
    if ! python3 -c "
import json, sys
data = json.load(open('$filepath'))
keys = '$field'.split('.')
obj = data
for k in keys:
    if isinstance(obj, dict) and k in obj:
        obj = obj[k]
    else:
        sys.exit(1)
sys.exit(0)
" 2>/dev/null; then
        error "Missing required field '$field' in $filepath"
        return 1
    fi
    return 0
}

# --- Step 1: Directory structure ---
echo "[Step 1] Checking directory structure..."

REQUIRED_DIRS=(
    "identity"
    "truth"
    "protocol"
    "cognition"
    "evidence/ci"
    "evidence/benchmark"
    "evidence/audit"
    "version"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$ENGINE_DIR/$dir" ]; then
        error "Missing required directory: .tll-engine/$dir"
    fi
done

if [ $ERRORS -eq 0 ]; then
    info "All required directories present"
fi
echo ""

# --- Step 2: Required files ---
echo "[Step 2] Checking required files..."

REQUIRED_FILES=(
    "identity/root.json"
    "identity/agents.json"
    "truth/architecture.json"
    "truth/language.json"
    "truth/runtime.json"
    "truth/capability.json"
    "protocol/development.yaml"
    "protocol/testing.yaml"
    "protocol/audit.yaml"
    "cognition/graph.json"
    "cognition/dependency.json"
    "cognition/decisions.json"
    "version/manifest.json"
)

for f in "${REQUIRED_FILES[@]}"; do
    check_file_exists "$ENGINE_DIR/$f"
done

if [ $ERRORS -eq 0 ]; then
    info "All required files present"
fi
echo ""

# --- Step 3: JSON validity ---
echo "[Step 3] Validating JSON files..."

JSON_FILES=(
    "identity/root.json"
    "identity/agents.json"
    "truth/architecture.json"
    "truth/language.json"
    "truth/runtime.json"
    "truth/capability.json"
    "cognition/graph.json"
    "cognition/dependency.json"
    "cognition/decisions.json"
    "version/manifest.json"
)

for f in "${JSON_FILES[@]}"; do
    if [ -f "$ENGINE_DIR/$f" ]; then
        check_json_valid "$ENGINE_DIR/$f"
    fi
done

# Also validate evidence files if they exist
for f in "$ENGINE_DIR"/evidence/ci/*.json "$ENGINE_DIR"/evidence/benchmark/*.json "$ENGINE_DIR"/evidence/audit/*.json; do
    if [ -f "$f" ]; then
        check_json_valid "$f"
    fi
done

if [ $ERRORS -eq 0 ]; then
    info "All JSON files valid"
fi
echo ""

# --- Step 4: Required fields in Truth files ---
echo "[Step 4] Checking required fields in Truth files..."

TRUTH_FILES=(
    "truth/architecture.json"
    "truth/language.json"
    "truth/runtime.json"
    "truth/capability.json"
)

for f in "${TRUTH_FILES[@]}"; do
    if [ -f "$ENGINE_DIR/$f" ]; then
        check_json_field "$ENGINE_DIR/$f" "schema_version"
        check_json_field "$ENGINE_DIR/$f" "name"
        check_json_field "$ENGINE_DIR/$f" "version"
        check_json_field "$ENGINE_DIR/$f" "hash"
        check_json_field "$ENGINE_DIR/$f" "created_at"
    fi
done

# Check capability.json has capability_categories
if [ -f "$ENGINE_DIR/truth/capability.json" ]; then
    check_json_field "$ENGINE_DIR/truth/capability.json" "capability_categories"
    check_json_field "$ENGINE_DIR/truth/capability.json" "production_readiness"
fi

if [ $ERRORS -eq 0 ]; then
    info "All required fields present in Truth files"
fi
echo ""

# --- Step 5: Evidence schema check ---
echo "[Step 5] Checking Evidence schema..."

if command -v python3 &>/dev/null; then
    for f in "$ENGINE_DIR"/evidence/ci/*.json "$ENGINE_DIR"/evidence/benchmark/*.json "$ENGINE_DIR"/evidence/audit/*.json; do
        if [ -f "$f" ]; then
            check_json_field "$f" "schema_version"
            check_json_field "$f" "evidence_type"
            check_json_field "$f" "id"
            check_json_field "$f" "proves"
            check_json_field "$f" "does_not_prove"
            check_json_field "$f" "confidence"
            check_json_field "$f" "hash"
            check_json_field "$f" "provenance_chain"
        fi
    done
    if [ $ERRORS -eq 0 ]; then
        info "All Evidence files have required schema fields"
    fi
else
    warning "python3 not available, skipping Evidence schema check"
fi
echo ""

# --- Step 6: Manifest consistency ---
echo "[Step 6] Checking Version Manifest consistency..."

if [ -f "$ENGINE_DIR/version/manifest.json" ]; then
    check_json_field "$ENGINE_DIR/version/manifest.json" "foundation_version"
    check_json_field "$ENGINE_DIR/version/manifest.json" "components"
    check_json_field "$ENGINE_DIR/version/manifest.json" "immutable_core_rules"
    check_json_field "$ENGINE_DIR/version/manifest.json" "version_chain"

    # Check that manifest lists all components
    if command -v python3 &>/dev/null; then
        COMPONENTS=$(python3 -c "
import json
data = json.load(open('$ENGINE_DIR/version/manifest.json'))
print(' '.join(data['components'].keys()))
" 2>/dev/null)
        for comp in identity truth protocol cognition evidence; do
            if ! echo "$COMPONENTS" | grep -q "$comp"; then
                error "Manifest missing component: $comp"
            fi
        done
    fi
fi

if [ $ERRORS -eq 0 ]; then
    info "Version Manifest consistent"
fi
echo ""

# --- Step 7: YAML basic check (non-empty, has key fields) ---
echo "[Step 7] Checking Protocol YAML files..."

YAML_FILES=(
    "protocol/development.yaml"
    "protocol/testing.yaml"
    "protocol/audit.yaml"
)

for f in "${YAML_FILES[@]}"; do
    if [ -f "$ENGINE_DIR/$f" ]; then
        # Basic check: file is non-empty and contains schema_version
        if [ ! -s "$ENGINE_DIR/$f" ]; then
            error "Empty YAML file: $f"
        fi
        if ! grep -q "schema_version" "$ENGINE_DIR/$f" 2>/dev/null; then
            warning "YAML file missing schema_version: $f"
        fi
    fi
done

if [ $ERRORS -eq 0 ]; then
    info "All Protocol YAML files valid (basic check)"
fi
echo ""

# --- Summary ---
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo "Errors:   $ERRORS"
echo "Warnings: $WARNINGS"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo "RESULT: FAIL"
    echo "Fix the errors above before committing."
    exit 1
fi

if [ $STRICT -eq 1 ] && [ $WARNINGS -gt 0 ]; then
    echo "RESULT: FAIL (strict mode, warnings treated as errors)"
    exit 1
fi

echo "RESULT: PASS"
echo ".tll-engine/ structure and schema are valid."
exit 0
