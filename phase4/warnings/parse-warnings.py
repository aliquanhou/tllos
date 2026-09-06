#!/usr/bin/env python3
"""
Phase 4 - TypeChecker Warning Parser
Parses raw TypeChecker warning output into machine-readable warnings.json.

Usage: python3 parse-warnings.py <raw_log_file> <output_json_file>

This script does NOT classify warnings. It only extracts raw records.
Classification is done separately by classify-warnings.py based on evidence.
"""

import json
import re
import sys
import os

def parse_warnings(raw_log_path):
    """Parse TypeChecker warning log into structured records."""
    if not os.path.exists(raw_log_path):
        print(f"ERROR: Raw log file not found: {raw_log_path}")
        return None

    with open(raw_log_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    warnings = []

    # Pattern 1: Standard TypeChecker warning format
    # "  Line 123: message text"
    pattern_line = re.compile(r'^\s+Line\s+(\d+):\s+(.+)$', re.MULTILINE)

    # Pattern 2: Alternative format with source file
    # "file.tll:123: message"
    pattern_file = re.compile(r'^([^\s:]+\.tll):(\d+):\s+(.+)$', re.MULTILINE)

    # Track current source file context
    current_file = "unknown"

    for line in content.split('\n'):
        # Check for file context markers
        file_match = re.match(r'^(?:Compiling|Processing|Checking)\s+(.+\.tll)', line)
        if file_match:
            current_file = file_match.group(1).strip()
            continue

        # Pattern 1: Line N: message
        line_match = pattern_line.match(line)
        if line_match:
            warnings.append({
                "source_file": current_file,
                "source_line": int(line_match.group(1)),
                "message": line_match.group(2).strip()
            })
            continue

        # Pattern 2: file.tll:123: message
        file_line_match = pattern_file.match(line)
        if file_line_match:
            warnings.append({
                "source_file": file_line_match.group(1),
                "source_line": int(file_line_match.group(2)),
                "message": file_line_match.group(3).strip()
            })
            continue

    # Extract total reported count
    total_match = re.search(r'Type checking done,\s*errors=(\d+)', content)
    total_reported = int(total_match.group(1)) if total_match else None

    # Also check for "N type warning(s)"
    warning_count_match = re.search(r'(\d+)\s+type warning', content)
    warning_count_reported = int(warning_count_match.group(1)) if warning_count_match else None

    result = {
        "metadata": {
            "raw_log_file": os.path.basename(raw_log_path),
            "total_reported_by_compiler": total_reported,
            "warning_count_reported": warning_count_reported,
            "parsed_count": len(warnings),
            "parser_version": "1.0"
        },
        "warnings": warnings
    }

    return result

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 parse-warnings.py <raw_log_file> <output_json_file>")
        sys.exit(1)

    raw_log_path = sys.argv[1]
    output_path = sys.argv[2]

    result = parse_warnings(raw_log_path)
    if result is None:
        sys.exit(1)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Parsed {result['metadata']['parsed_count']} warnings")
    print(f"Compiler reported: {result['metadata']['total_reported_by_compiler']}")
    print(f"Output written to: {output_path}")

    # Exit with 0 even if count mismatch - validation is separate
    sys.exit(0)

if __name__ == '__main__':
    main()
