#!/usr/bin/env python3
"""
Phase 4 - TypeChecker Warning Validator
Validates warnings.json schema and completeness.

Usage: python3 validate-warnings.py <warnings_json_file> [--expected-count N]

Exit codes:
  0 - All validations passed
  1 - Validation failed
  2 - File not found or invalid JSON
"""

import json
import sys
import os
import argparse

def validate_warnings(json_path, expected_count=None):
    """Validate warnings.json structure and content."""
    errors = []
    warnings_list = []

    if not os.path.exists(json_path):
        print(f"ERROR: File not found: {json_path}")
        return 2, []

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        return 2, []

    # Check structure
    if 'warnings' not in data:
        errors.append("Missing 'warnings' array")
        return 1, errors

    warnings_list = data['warnings']
    actual_count = len(warnings_list)

    print(f"=== Warning Validation Report ===")
    print(f"File: {json_path}")
    print(f"Actual warning count: {actual_count}")

    if expected_count is not None:
        print(f"Expected count: {expected_count}")
        if actual_count != expected_count:
            errors.append(f"Count mismatch: expected {expected_count}, got {actual_count}")
            print(f"  FAIL: Count mismatch")
        else:
            print(f"  PASS: Count matches expected {expected_count}")

    # Validate each record
    seen_ids = set()
    empty_source_file = 0
    empty_message = 0
    invalid_line = 0
    missing_category = 0
    missing_reason = 0
    missing_capability = 0

    for i, w in enumerate(warnings_list):
        # Check warning_id (if present)
        if 'warning_id' in w:
            wid = w['warning_id']
            if wid in seen_ids:
                errors.append(f"Duplicate warning_id: {wid}")
            seen_ids.add(wid)

        # Check source_file
        if not w.get('source_file') or w['source_file'] == 'unknown':
            empty_source_file += 1

        # Check source_line
        line = w.get('source_line', 0)
        if not isinstance(line, int) or line < 0 or line > 100000:
            invalid_line += 1

        # Check message
        if not w.get('message'):
            empty_message += 1

        # Check category (only if classification has been done)
        if 'category' in w:
            if not w['category']:
                missing_category += 1
            elif w['category'] not in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                errors.append(f"Invalid category '{w['category']}' at record {i}")
        else:
            missing_category += 1

        # Check reason
        if not w.get('reason'):
            missing_reason += 1

        # Check capability_id
        if not w.get('capability_id'):
            missing_capability += 1

    # Report field validation
    print(f"\n=== Field Validation ===")
    print(f"Records with empty/unknown source_file: {empty_source_file}")
    print(f"Records with invalid source_line: {invalid_line}")
    print(f"Records with empty message: {empty_message}")
    print(f"Records missing category: {missing_category}")
    print(f"Records missing reason: {missing_reason}")
    print(f"Records missing capability_id: {missing_capability}")
    print(f"Unique warning_ids: {len(seen_ids)}")

    # Hard failures (these cause CI failure)
    if actual_count == 0:
        errors.append("No warnings parsed - raw log may be empty or format unrecognized")

    if empty_message == actual_count and actual_count > 0:
        errors.append("All records have empty messages - parsing likely failed")

    # Classification completeness check (only if expected_count is set and count matches)
    if expected_count and actual_count == expected_count:
        if missing_category > 0:
            errors.append(f"Classification incomplete: {missing_category}/{actual_count} records missing category")
        if missing_reason > 0:
            errors.append(f"Classification incomplete: {missing_reason}/{actual_count} records missing reason")
        if missing_capability > 0:
            errors.append(f"Classification incomplete: {missing_capability}/{actual_count} records missing capability_id")

    # Print errors
    if errors:
        print(f"\n=== VALIDATION FAILED: {len(errors)} error(s) ===")
        for e in errors[:20]:  # Show first 20 errors
            print(f"  - {e}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors")
        return 1, errors
    else:
        print(f"\n=== VALIDATION PASSED ===")
        return 0, []

def main():
    parser = argparse.ArgumentParser(description='Validate TypeChecker warnings JSON')
    parser.add_argument('json_file', help='Path to warnings.json')
    parser.add_argument('--expected-count', type=int, default=None,
                        help='Expected warning count (e.g., 603)')
    parser.add_argument('--strict', action='store_true',
                        help='Strict mode: require all classification fields')
    args = parser.parse_args()

    exit_code, errors = validate_warnings(args.json_file, args.expected_count)
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
