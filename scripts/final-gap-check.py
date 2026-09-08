#!/usr/bin/env python3
"""
TLL Language Fundamental Final GAP Matrix - Exact Count Auditor
自动统计 Final GAP Matrix 中的能力项状态，并验证 UNKNOWN = 0 和 sum(statuses) == TOTAL。

用法: python audit/final-gap-check.py <final_gap_matrix.md>
"""

import sys
import re
from collections import Counter

VALID_STATUSES = [
    "SEALED",
    "COMPLETE",
    "PARTIAL",
    "MISSING",
    "BLOCKED",
    "NOT_DESIGNED",
    "DEFERRED",
    "NOT_APPLICABLE",
    "UNKNOWN",
]

def parse_matrix(filepath):
    """解析 Final GAP Matrix，提取每个能力项的状态。"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    capabilities = []

    # 匹配表格行: | ID | Domain | Capability | ... | Status | ... |
    # 状态列通常在表格中明确标注
    lines = content.split('\n')
    in_table = False
    header_found = False

    for line in lines:
        # 检测表格开始
        if line.strip().startswith('|') and 'Status' in line:
            header_found = True
            in_table = True
            continue

        if in_table and line.strip().startswith('|'):
            # 跳过分隔行
            if re.match(r'^\|[\s\-:|]+\|$', line.strip()):
                continue

            cells = [c.strip() for c in line.strip().split('|')[1:-1]]

            # 查找状态列
            status = None
            for cell in cells:
                cell_upper = cell.upper().strip()
                # 匹配状态（可能包含 ✅ ❌ ⚠️ 等符号）
                for vs in VALID_STATUSES:
                    if vs in cell_upper:
                        status = vs
                        break
                if status:
                    break

            if status:
                # 尝试提取 ID 和 Capability
                cap_id = cells[0] if len(cells) > 0 else "UNKNOWN"
                capability = cells[2] if len(cells) > 2 else "UNKNOWN"
                domain = cells[1] if len(cells) > 1 else "UNKNOWN"

                capabilities.append({
                    'id': cap_id,
                    'domain': domain,
                    'capability': capability,
                    'status': status,
                })
        elif in_table and not line.strip().startswith('|'):
            # 表格结束
            in_table = False

    return capabilities

def check_forbidden_content(filepath):
    """检查 Final Matrix 中是否包含禁止的内容。"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    forbidden_patterns = [
        (r'~', '波浪号 (~) - 必须使用精确数字'),
        (r'approximately', 'approximately - 必须使用精确数字'),
        (r'待统计', '待统计 - 必须完成统计'),
        (r'待验证', '待验证 - 必须完成验证'),
        (r'摘要', '摘要 - 必须展开为逐项审计'),
        (r'TBD', 'TBD - 必须确定'),
        (r'初步', '初步 - 必须基于证据'),
    ]

    findings = []
    for pattern, description in forbidden_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            findings.append((description, len(matches)))

    return findings

def main():
    if len(sys.argv) < 2:
        print("Usage: python audit/final-gap-check.py <final_gap_matrix.md>")
        sys.exit(1)

    filepath = sys.argv[1]

    print("=" * 70)
    print("TLL Language Fundamental Final GAP Matrix - Exact Count Auditor")
    print("=" * 70)
    print(f"\nFile: {filepath}\n")

    # 解析矩阵
    capabilities = parse_matrix(filepath)

    if not capabilities:
        print("WARNING: No capabilities found in matrix.")
        print("The matrix may not be in the expected table format.")
        print("Expected format: | ID | Domain | Capability | ... | Status | ... |")
        sys.exit(1)

    # 统计状态
    status_counts = Counter(cap['status'] for cap in capabilities)
    total = len(capabilities)

    print("-" * 70)
    print("STATUS COUNTS")
    print("-" * 70)
    for status in VALID_STATUSES:
        count = status_counts.get(status, 0)
        percentage = (count / total * 100) if total > 0 else 0
        print(f"  {status:20s} = {count:4d}  ({percentage:5.1f}%)")

    print(f"  {'TOTAL':20s} = {total:4d}  (100.0%)")

    # 验证 sum(statuses) == TOTAL
    sum_statuses = sum(status_counts.get(s, 0) for s in VALID_STATUSES)
    print(f"\n  Sum of all statuses = {sum_statuses}")
    print(f"  TOTAL               = {total}")
    if sum_statuses == total:
        print("  ✅ sum(statuses) == TOTAL")
    else:
        print(f"  ❌ sum(statuses) != TOTAL (diff = {total - sum_statuses})")

    # 验证 UNKNOWN = 0
    unknown_count = status_counts.get("UNKNOWN", 0)
    print(f"\n  UNKNOWN count = {unknown_count}")
    if unknown_count == 0:
        print("  ✅ UNKNOWN = 0")
    else:
        print(f"  ❌ UNKNOWN != 0 (must be 0 for Phase 4 seal)")
        print("\n  UNKNOWN capabilities:")
        for cap in capabilities:
            if cap['status'] == 'UNKNOWN':
                print(f"    - {cap['id']}: {cap['capability']} [{cap['domain']}]")

    # 检查禁止内容
    print("\n" + "-" * 70)
    print("FORBIDDEN CONTENT CHECK")
    print("-" * 70)
    forbidden_findings = check_forbidden_content(filepath)
    if forbidden_findings:
        for description, count in forbidden_findings:
            print(f"  ❌ {description}: {count} occurrences")
    else:
        print("  ✅ No forbidden content found")

    # 按域统计
    print("\n" + "-" * 70)
    print("PER-DOMAIN COUNTS")
    print("-" * 70)
    domain_counts = Counter(cap['domain'] for cap in capabilities)
    for domain, count in sorted(domain_counts.items()):
        print(f"  {domain:40s} = {count:4d}")

    # 最终判定
    print("\n" + "=" * 70)
    print("FINAL VERDICT")
    print("=" * 70)

    all_pass = True
    if unknown_count != 0:
        print("  ❌ UNKNOWN != 0")
        all_pass = False
    if sum_statuses != total:
        print("  ❌ sum(statuses) != TOTAL")
        all_pass = False
    if forbidden_findings:
        print("  ❌ Forbidden content found")
        all_pass = False

    if all_pass:
        print("  ✅ ALL CHECKS PASSED")
        print("  ✅ Phase 4 READY FOR ARCHITECT FINAL ACCEPTANCE")
        sys.exit(0)
    else:
        print("  ❌ CHECKS FAILED")
        print("  ❌ Phase 4 = NOT SEALED")
        print("  ❌ Phase 5 = BLOCKED")
        sys.exit(1)

if __name__ == "__main__":
    main()
