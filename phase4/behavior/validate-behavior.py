#!/usr/bin/env python3
"""
Phase 4 - Behavior Test Validator
Parses and validates behavior test output (Memory/Evaluation/Ternary).

Usage: python3 validate-behavior.py <test_log_file> <test_name> <output_json>

Exit codes:
  0 - All tests passed
  1 - Some tests failed
  2 - File not found or parse error
"""

import json
import re
import sys
import os
import argparse

def parse_behavior_log(log_path, test_name):
    """Parse behavior test log into structured records."""
    if not os.path.exists(log_path):
        print(f"ERROR: Log file not found: {log_path}")
        return None

    with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    tests = []

    # Parse PASS/FAIL lines
    # Pattern: "PASS: test name (details)" or "FAIL: test name (details)"
    pass_pattern = re.compile(r'^PASS:\s+(.+?)(?:\s+\((.+)\))?$', re.MULTILINE)
    fail_pattern = re.compile(r'^FAIL:\s+(.+?)(?:\s+\((.+)\))?$', re.MULTILINE)

    # Also parse OBSERVED lines (for Memory tests)
    observed_pattern = re.compile(r'^OBSERVED:\s+(.+)$', re.MULTILINE)

    for match in pass_pattern.finditer(content):
        tests.append({
            "test_id": f"{test_name}_{len(tests)+1:03d}",
            "test_name": match.group(1).strip(),
            "status": "PASS",
            "details": match.group(2) if match.group(2) else ""
        })

    for match in fail_pattern.finditer(content):
        tests.append({
            "test_id": f"{test_name}_{len(tests)+1:03d}",
            "test_name": match.group(1).strip(),
            "status": "FAIL",
            "details": match.group(2) if match.group(2) else ""
        })

    # Parse OBSERVED lines as evidence
    observations = []
    for match in observed_pattern.finditer(content):
        observations.append(match.group(1).strip())

    # Parse summary
    passed = len([t for t in tests if t['status'] == 'PASS'])
    failed = len([t for t in tests if t['status'] == 'FAIL'])

    # Check for "ALL TESTS PASSED" or "SOME TESTS FAILED"
    all_passed = "ALL TESTS PASSED" in content or "ALL TESTS RAN SUCCESSFULLY" in content
    some_failed = "SOME TESTS FAILED" in content

    result = {
        "metadata": {
            "test_name": test_name,
            "log_file": os.path.basename(log_path),
            "total_tests": len(tests),
            "passed": passed,
            "failed": failed,
            "all_passed_marker": all_passed,
            "some_failed_marker": some_failed,
            "observations_count": len(observations)
        },
        "tests": tests,
        "observations": observations
    }

    return result

def validate_behavior(result):
    """Validate behavior test results."""
    errors = []

    if result is None:
        return 2, ["Failed to parse behavior log"]

    meta = result['metadata']
    tests = result['tests']

    print(f"=== Behavior Validation: {meta['test_name']} ===")
    print(f"Total tests: {meta['total_tests']}")
    print(f"Passed: {meta['passed']}")
    print(f"Failed: {meta['failed']}")

    # Check test records exist
    if meta['total_tests'] == 0:
        errors.append("No test records found - log may be empty or format unrecognized")
        print("  FAIL: No test records found")
    else:
        print("  PASS: Test records exist")

    # Check test_id uniqueness
    test_ids = [t['test_id'] for t in tests]
    if len(test_ids) != len(set(test_ids)):
        errors.append("Duplicate test_ids found")
        print("  FAIL: Duplicate test_ids")
    else:
        print("  PASS: test_ids unique")

    # Check all tests have required fields
    missing_fields = 0
    for t in tests:
        if not t.get('test_name') or not t.get('status'):
            missing_fields += 1
    if missing_fields > 0:
        errors.append(f"{missing_fields} records missing required fields")
        print(f"  FAIL: {missing_fields} records missing fields")
    else:
        print("  PASS: All records have required fields")

    # Check PASS/FAIL consistency
    if meta['failed'] > 0:
        errors.append(f"{meta['failed']} test(s) FAILED")
        print(f"  FAIL: {meta['failed']} test(s) FAILED")
        # Show failed tests
        for t in tests:
            if t['status'] == 'FAIL':
                print(f"    - {t['test_name']}: {t['details']}")
    else:
        print("  PASS: All tests passed")

    # Check marker consistency
    if meta['all_passed_marker'] and meta['failed'] > 0:
        errors.append("Marker says ALL PASSED but some tests FAILED")
        print("  FAIL: Marker inconsistency")

    if errors:
        print(f"\n=== VALIDATION FAILED: {len(errors)} error(s) ===")
        return 1, errors
    else:
        print(f"\n=== VALIDATION PASSED ===")
        return 0, []

def main():
    parser = argparse.ArgumentParser(description='Validate behavior test output')
    parser.add_argument('log_file', help='Path to test log file')
    parser.add_argument('test_name', help='Name of the test suite')
    parser.add_argument('output_json', help='Path to output JSON file')
    args = parser.parse_args()

    result = parse_behavior_log(args.log_file, args.test_name)
    if result is None:
        sys.exit(2)

    # Write parsed result
    os.makedirs(os.path.dirname(args.output_json) or '.', exist_ok=True)
    with open(args.output_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Validate
    exit_code, errors = validate_behavior(result)
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
