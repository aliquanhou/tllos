#!/usr/bin/env python3
"""
Phase 4 - Behavior Test Validator (v2 - Evidence Integrity)
Parses and validates behavior test output (Memory/Evaluation/Ternary).

EVIDENCE INTEGRITY FIXES (v2):
- Accepts --runtime-exit to include process exit code in evidence
- Validates EXPECTED == ACTUAL for each test (not just PASS/FAIL format)
- Runtime failure (exit != 0) != semantic failure (test assertions)
- process_exit_code is mandatory for VALIDATION PASSED

Usage: python3 validate-behavior.py <log_file> <test_name> <output_json> [--runtime-exit N]

Exit codes:
  0 - All validations passed (runtime_exit==0 AND all tests PASS AND expected==actual)
  1 - Some validations failed
  2 - File not found or parse error
"""

import json
import re
import sys
import os
import argparse

def parse_behavior_log(log_path, test_name, runtime_exit=None):
    """Parse behavior test log into structured records."""
    if not os.path.exists(log_path):
        print(f"ERROR: Log file not found: {log_path}")
        return None

    with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    tests = []

    # Parse test result lines with EXPECTED/ACTUAL
    # Format 1: "PASS: test_name (EXPECTED: X, ACTUAL: Y)"
    # Format 2: "FAIL: test_name (EXPECTED: X, ACTUAL: Y)"
    # Format 3: "PASS: test_name"
    # Format 4: "OBSERVED: description"

    result_pattern = re.compile(
        r'^(PASS|FAIL):\s+(.+?)(?:\s+\((.+)\))?$',
        re.MULTILINE
    )

    # Parse EXPECTED/ACTUAL from details
    # IMPORTANT: Values may contain commas (e.g., "A,B,C"), so we cannot
    # use [^,)]+ which truncates at the first comma. We parse intelligently:
    # EXPECTED: <value> , ACTUAL: <value>
    # or
    # EXPECTED: <value> ACTUAL: <value>
    def parse_expected_actual(details_str):
        """Parse EXPECTED and ACTUAL values, handling commas within values."""
        if not details_str:
            return None, None

        expected = None
        actual = None

        # Try pattern: EXPECTED: ... ACTUAL: ... (ACTUAL acts as delimiter)
        exp_match = re.search(r'EXPECTED:\s*(.+?)\s*(?:,?\s*)ACTUAL:', details_str, re.IGNORECASE)
        if exp_match:
            expected = exp_match.group(1).strip()

        # ACTUAL: everything after ACTUAL: until end of string
        act_match = re.search(r'ACTUAL:\s*(.+?)\s*$', details_str, re.IGNORECASE)
        if act_match:
            actual = act_match.group(1).strip()

        # Fallback: if only EXPECTED found, try to get value after comma
        if expected is None:
            simple_exp = re.search(r'EXPECTED:\s*([^,]+?)(?:,|$)', details_str, re.IGNORECASE)
            if simple_exp:
                expected = simple_exp.group(1).strip()

        if actual is None:
            simple_act = re.search(r'ACTUAL:\s*([^,]+?)(?:,|$)', details_str, re.IGNORECASE)
            if simple_act:
                actual = simple_act.group(1).strip()

        return expected, actual

    for match in result_pattern.finditer(content):
        status = match.group(1)
        name = match.group(2).strip()
        details = match.group(3) if match.group(3) else ""

        expected, actual = parse_expected_actual(details)

        tests.append({
            "test_id": f"{test_name}_{len(tests)+1:03d}",
            "test_name": name,
            "status": status,
            "expected": expected,
            "actual": actual,
            "details": details
        })

    # Parse OBSERVED lines (for Memory tests - actual behavior observation)
    observations = []
    observed_pattern = re.compile(r'^OBSERVED:\s+(.+)$', re.MULTILINE)
    for match in observed_pattern.finditer(content):
        observations.append(match.group(1).strip())

    # Parse summary markers
    passed = len([t for t in tests if t['status'] == 'PASS'])
    failed = len([t for t in tests if t['status'] == 'FAIL'])

    all_passed = "ALL TESTS PASSED" in content or "ALL TESTS RAN SUCCESSFULLY" in content
    some_failed = "SOME TESTS FAILED" in content

    result = {
        "metadata": {
            "test_name": test_name,
            "log_file": os.path.basename(log_path),
            "process_exit_code": runtime_exit,
            "total_tests": len(tests),
            "passed": passed,
            "failed": failed,
            "all_passed_marker": all_passed,
            "some_failed_marker": some_failed,
            "observations_count": len(observations),
            "validator_version": "2.0"
        },
        "tests": tests,
        "observations": observations
    }

    return result

def validate_behavior(result):
    """Validate behavior test results with Evidence Integrity."""
    errors = []

    if result is None:
        return 2, ["Failed to parse behavior log"]

    meta = result['metadata']
    tests = result['tests']

    print(f"=== Behavior Validation v2: {meta['test_name']} ===")
    print(f"Process exit code: {meta['process_exit_code']}")
    print(f"Total tests: {meta['total_tests']}")
    print(f"Passed: {meta['passed']}")
    print(f"Failed: {meta['failed']}")

    # ============================================
    # GATE 1: Runtime exit code must be 0
    # ============================================
    if meta['process_exit_code'] is None:
        errors.append("process_exit_code not provided - cannot verify runtime integrity")
        print("  FAIL: process_exit_code missing")
    elif meta['process_exit_code'] != 0:
        errors.append(f"Runtime exited non-zero ({meta['process_exit_code']}) - Evidence Gate FAIL")
        print(f"  FAIL: Runtime exit code {meta['process_exit_code']} != 0")
    else:
        print("  PASS: Runtime exit code == 0")

    # ============================================
    # GATE 2: Test records must exist
    # ============================================
    if meta['total_tests'] == 0:
        errors.append("No test records found - log may be empty or format unrecognized")
        print("  FAIL: No test records found")
    else:
        print("  PASS: Test records exist")

    # ============================================
    # GATE 3: test_id uniqueness
    # ============================================
    test_ids = [t['test_id'] for t in tests]
    if len(test_ids) != len(set(test_ids)):
        errors.append("Duplicate test_ids found")
        print("  FAIL: Duplicate test_ids")
    else:
        print("  PASS: test_ids unique")

    # ============================================
    # GATE 4: All tests must have required fields
    # ============================================
    missing_fields = 0
    for t in tests:
        if not t.get('test_name') or not t.get('status'):
            missing_fields += 1
    if missing_fields > 0:
        errors.append(f"{missing_fields} records missing required fields")
        print(f"  FAIL: {missing_fields} records missing fields")
    else:
        print("  PASS: All records have required fields")

    # ============================================
    # GATE 5: EXPECTED == ACTUAL validation
    # IMPORTANT: PASS + missing EXPECTED/ACTUAL must FAIL (unless OBSERVED-based test)
    # Memory tests use OBSERVED format (architect decision: don't presuppose answers)
    # Evaluation/Ternary tests MUST have EXPECTED/ACTUAL for PASS to be valid
    # ============================================
    has_observations = len(result.get('observations', [])) > 0
    expected_actual_mismatch = 0
    missing_expected_actual = 0
    for t in tests:
        if t['expected'] is not None and t['actual'] is not None:
            if t['expected'] != t['actual']:
                expected_actual_mismatch += 1
                errors.append(
                    f"EXPECTED/ACTUAL mismatch in '{t['test_name']}': "
                    f"expected='{t['expected']}', actual='{t['actual']}'"
                )
        elif t['status'] == 'PASS':
            # PASS tests without EXPECTED/ACTUAL:
            # - If this is an OBSERVED-based test (Memory), it's allowed
            # - Otherwise, it MUST FAIL (evidence integrity requirement)
            if not has_observations:
                missing_expected_actual += 1
                errors.append(
                    f"PASS test '{t['test_name']}' missing EXPECTED/ACTUAL - "
                    f"evidence integrity requires explicit expected vs actual"
                )
            else:
                missing_expected_actual += 1

    if expected_actual_mismatch > 0:
        print(f"  FAIL: {expected_actual_mismatch} test(s) with EXPECTED != ACTUAL")
    else:
        print("  PASS: All EXPECTED == ACTUAL (where provided)")

    if missing_expected_actual > 0:
        if has_observations:
            print(f"  INFO: {missing_expected_actual} OBSERVED-based PASS test(s) without EXPECTED/ACTUAL (allowed for Memory)")
        else:
            print(f"  FAIL: {missing_expected_actual} PASS test(s) missing EXPECTED/ACTUAL - evidence integrity violation")

    # ============================================
    # GATE 6: No FAIL tests
    # ============================================
    if meta['failed'] > 0:
        errors.append(f"{meta['failed']} test(s) FAILED")
        print(f"  FAIL: {meta['failed']} test(s) FAILED")
        for t in tests:
            if t['status'] == 'FAIL':
                print(f"    - {t['test_name']}: {t['details']}")
    else:
        print("  PASS: All tests passed")

    # ============================================
    # GATE 7: Marker consistency
    # ============================================
    if meta['all_passed_marker'] and meta['failed'] > 0:
        errors.append("Marker says ALL PASSED but some tests FAILED")
        print("  FAIL: Marker inconsistency")

    if meta['some_failed_marker'] and meta['failed'] == 0 and meta['process_exit_code'] == 0:
        errors.append("Marker says SOME FAILED but no tests failed and runtime exit 0")
        print("  FAIL: Marker inconsistency (false positive)")

    # ============================================
    # Final determination
    # ============================================
    if errors:
        print(f"\n=== VALIDATION FAILED: {len(errors)} error(s) ===")
        for e in errors[:20]:
            print(f"  - {e}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors")
        return 1, errors
    else:
        print(f"\n=== VALIDATION PASSED ===")
        print(f"  runtime_exit == 0 AND all tests PASS AND expected == actual")
        return 0, []

def main():
    parser = argparse.ArgumentParser(description='Validate behavior test output (v2)')
    parser.add_argument('log_file', help='Path to test log file')
    parser.add_argument('test_name', help='Name of the test suite')
    parser.add_argument('output_json', help='Path to output JSON file')
    parser.add_argument('--runtime-exit', type=int, default=None,
                        help='Process exit code of the test runtime (mandatory for validation)')
    args = parser.parse_args()

    result = parse_behavior_log(args.log_file, args.test_name, args.runtime_exit)
    if result is None:
        sys.exit(2)

    # Write parsed result (always, even if validation fails)
    os.makedirs(os.path.dirname(args.output_json) or '.', exist_ok=True)
    with open(args.output_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Validate
    exit_code, errors = validate_behavior(result)
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
