#!/usr/bin/env python3
"""
Phase 4 - Behavior Test Validator (v3 - Reality-Aligned Evidence)
Parses and validates behavior test output (Memory/Evaluation/Ternary).

v3 CHANGES:
- Parses EVIDENCE: TEST_ID=... EXPECTED=... ACTUAL=... STATUS=... format
- OBSERVED status tests (Memory) are valid evidence, not failures
- UNSUPPORTED status records capability gaps
- process_exit_code is mandatory for VALIDATION PASSED

Usage: python3 validate-behavior.py <log_file> <test_name> <output_json> [--runtime-exit N]

Exit codes:
  0 - All validations passed
  1 - Some validations failed
  2 - File not found or parse error
"""

import json
import re
import sys
import os
import argparse

def parse_evidence_log(log_path, test_name, runtime_exit=None):
    """Parse behavior test log into structured evidence records."""
    if not os.path.exists(log_path):
        print(f"ERROR: Log file not found: {log_path}")
        return None

    with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    tests = []

    # Parse EVIDENCE: TEST_ID=... EXPECTED=... ACTUAL=... STATUS=...
    # Format: EVIDENCE: TEST_ID=eval.function_arg_order EXPECTED=A,B,C ACTUAL=A,B,C STATUS=PASS
    evidence_pattern = re.compile(
        r'^EVIDENCE:\s+TEST_ID=([^\s]+)\s+EXPECTED=([^\s]+(?:\s+[^\s]+)*?)\s+ACTUAL=([^\s]+(?:\s+[^\s]+)*?)\s+STATUS=(\w+)',
        re.MULTILINE
    )

    for match in evidence_pattern.finditer(content):
        test_id = match.group(1).strip()
        expected = match.group(2).strip()
        actual = match.group(3).strip()
        status = match.group(4).strip()

        tests.append({
            "test_id": test_id,
            "test_name": test_id,
            "status": status,
            "expected": expected,
            "actual": actual,
            "details": f"EXPECTED={expected} ACTUAL={actual}"
        })

    # Fallback: also parse old PASS:/FAIL: format for backward compatibility
    if not tests:
        result_pattern = re.compile(
            r'^(PASS|FAIL):\s+(.+?)(?:\s+\((.+)\))?$',
            re.MULTILINE
        )
        for match in result_pattern.finditer(content):
            status = match.group(1)
            name = match.group(2).strip()
            tests.append({
                "test_id": f"{test_name}_{len(tests)+1:03d}",
                "test_name": name,
                "status": status,
                "expected": None,
                "actual": None,
                "details": match.group(3) if match.group(3) else ""
            })

    # Count by status
    passed = len([t for t in tests if t['status'] == 'PASS'])
    failed = len([t for t in tests if t['status'] == 'FAIL'])
    observed = len([t for t in tests if t['status'] == 'OBSERVED'])
    unsupported = len([t for t in tests if t['status'] == 'UNSUPPORTED'])

    result = {
        "metadata": {
            "test_name": test_name,
            "log_file": os.path.basename(log_path),
            "process_exit_code": runtime_exit,
            "total_evidence": len(tests),
            "passed": passed,
            "failed": failed,
            "observed": observed,
            "unsupported": unsupported,
            "validator_version": "3.0"
        },
        "tests": tests
    }

    return result

def validate_behavior(result):
    """Validate behavior test results with Reality-Aligned Evidence."""
    errors = []

    if result is None:
        return 2, ["Failed to parse behavior log"]

    meta = result['metadata']
    tests = result['tests']

    print(f"=== Behavior Validation v3: {meta['test_name']} ===")
    print(f"Process exit code: {meta['process_exit_code']}")
    print(f"Total evidence records: {meta['total_evidence']}")
    print(f"  PASS: {meta['passed']}")
    print(f"  FAIL: {meta['failed']}")
    print(f"  OBSERVED: {meta['observed']}")
    print(f"  UNSUPPORTED: {meta['unsupported']}")

    # GATE 1: Runtime exit code must be 0
    if meta['process_exit_code'] is None:
        errors.append("process_exit_code not provided")
        print("  FAIL: process_exit_code missing")
    elif meta['process_exit_code'] != 0:
        errors.append(f"Runtime exited non-zero ({meta['process_exit_code']})")
        print(f"  FAIL: Runtime exit code {meta['process_exit_code']} != 0")
    else:
        print("  PASS: Runtime exit code == 0")

    # GATE 2: Evidence records must exist
    if meta['total_evidence'] == 0:
        errors.append("No evidence records found")
        print("  FAIL: No evidence records found")
    else:
        print("  PASS: Evidence records exist")

    # GATE 3: test_id uniqueness
    test_ids = [t['test_id'] for t in tests]
    if len(test_ids) != len(set(test_ids)):
        errors.append("Duplicate test_ids found")
        print("  FAIL: Duplicate test_ids")
    else:
        print("  PASS: test_ids unique")

    # GATE 4: EXPECTED == ACTUAL for PASS tests
    # OBSERVED and UNSUPPORTED are valid statuses, not failures
    expected_actual_mismatch = 0
    for t in tests:
        if t['status'] == 'PASS':
            if t['expected'] != t['actual']:
                expected_actual_mismatch += 1
                errors.append(
                    f"PASS with EXPECTED != ACTUAL in '{t['test_id']}': "
                    f"expected='{t['expected']}', actual='{t['actual']}'"
                )

    if expected_actual_mismatch > 0:
        print(f"  FAIL: {expected_actual_mismatch} PASS test(s) with EXPECTED != ACTUAL")
    else:
        print("  PASS: All PASS tests have EXPECTED == ACTUAL")

    # GATE 5: No FAIL tests
    if meta['failed'] > 0:
        errors.append(f"{meta['failed']} test(s) FAILED")
        print(f"  FAIL: {meta['failed']} test(s) FAILED")
        for t in tests:
            if t['status'] == 'FAIL':
                print(f"    - {t['test_id']}: {t['details']}")
    else:
        print("  PASS: No FAIL tests")

    # Final determination
    if errors:
        print(f"\n=== VALIDATION FAILED: {len(errors)} error(s) ===")
        for e in errors[:20]:
            print(f"  - {e}")
        return 1, errors
    else:
        print(f"\n=== VALIDATION PASSED ===")
        print(f"  runtime_exit == 0 AND evidence records exist AND no FAIL tests")
        return 0, []

def main():
    parser = argparse.ArgumentParser(description='Validate behavior test output (v3)')
    parser.add_argument('log_file', help='Path to test log file')
    parser.add_argument('test_name', help='Name of the test suite')
    parser.add_argument('output_json', help='Path to output JSON file')
    parser.add_argument('--runtime-exit', type=int, default=None,
                        help='Process exit code of the test runtime')
    args = parser.parse_args()

    result = parse_evidence_log(args.log_file, args.test_name, args.runtime_exit)
    if result is None:
        sys.exit(2)

    os.makedirs(os.path.dirname(args.output_json) or '.', exist_ok=True)
    with open(args.output_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    exit_code, errors = validate_behavior(result)
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
