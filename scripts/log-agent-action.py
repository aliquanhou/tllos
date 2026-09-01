#!/usr/bin/env python3
"""
TLL OS Agent Operation Audit Log Generator
Generates immutable audit logs for all Agent operations.

This is part of P0-16.1 TLL Engineering Enforcement Layer.
It ensures every Agent operation has a traceable, hash-chained audit record.

Usage:
    python3 scripts/log-agent-action.py \
        --agent-id agent_doubao_bootstrap_001 \
        --operation-type code_change \
        --phase P0-16.1 \
        --title "Add .tll-engine CI validation" \
        --description "Added validate-tll-engine steps to CI workflow" \
        --files-modified .github/workflows/ci.yml \
        --ci-run-id 124
"""

import json
import os
import sys
import argparse
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path


class AuditLogGenerator:
    def __init__(self, engine_dir, agent_id, operation_type, phase, title,
                 description="", files_modified=None, ci_run_id=None,
                 ci_status=None, claims_made=None, evidence_submitted=None,
                 known_limitations=None, next_steps=None, parent_audit_id=None):
        self.engine_dir = Path(engine_dir).resolve()
        self.agent_id = agent_id
        self.operation_type = operation_type
        self.phase = phase
        self.title = title
        self.description = description
        self.files_modified = files_modified or []
        self.ci_run_id = ci_run_id
        self.ci_status = ci_status
        self.claims_made = claims_made or []
        self.evidence_submitted = evidence_submitted or []
        self.known_limitations = known_limitations or []
        self.next_steps = next_steps or []
        self.parent_audit_id = parent_audit_id

        # Load agent info from registry
        self.agent_info = self._load_agent_info()

    def _load_agent_info(self):
        """Load agent info from identity/agents.json."""
        agents_file = self.engine_dir / 'identity' / 'agents.json'
        try:
            with open(agents_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for agent in data.get('agents', []):
                if agent.get('agent_id') == self.agent_id:
                    return agent
            for human in data.get('human_contributors', []):
                if human.get('contributor_id') == self.agent_id:
                    return human
        except Exception:
            pass
        return {'agent_name': self.agent_id, 'level': 'unknown'}

    def _get_git_commit_sha(self):
        """Get current git commit SHA."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True, text=True, cwd=self.engine_dir.parent
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def _get_git_diff_stats(self):
        """Get git diff stats for modified files."""
        file_stats = []
        for filepath in self.files_modified:
            try:
                result = subprocess.run(
                    ['git', 'diff', '--numstat', '--', filepath],
                    capture_output=True, text=True, cwd=self.engine_dir.parent
                )
                if result.returncode == 0 and result.stdout.strip():
                    parts = result.stdout.strip().split('\t')
                    if len(parts) >= 3:
                        file_stats.append({
                            'path': filepath,
                            'change_type': 'modified',
                            'lines_added': int(parts[0]) if parts[0].isdigit() else 0,
                            'lines_deleted': int(parts[1]) if parts[1].isdigit() else 0
                        })
                        continue
            except Exception:
                pass
            file_stats.append({
                'path': filepath,
                'change_type': 'modified',
                'lines_added': 0,
                'lines_deleted': 0
            })
        return file_stats

    def _find_latest_audit_id(self):
        """Find the latest audit log ID to use as parent."""
        audit_dir = self.engine_dir / 'audit'
        if not audit_dir.exists():
            return None
        audit_files = sorted(audit_dir.glob('audit-*.json'))
        if audit_files:
            # Get the latest one
            latest = audit_files[-1]
            try:
                with open(latest, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get('audit_id')
            except Exception:
                pass
        return None

    def _compute_hash(self, content):
        """Compute SHA-256 hash of content (first 16 chars)."""
        return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()[:16]

    def generate(self):
        """Generate the audit log."""
        timestamp = datetime.now(timezone.utc).isoformat()
        date_str = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')

        # Get git info
        commit_sha = self._get_git_commit_sha()
        file_stats = self._get_git_diff_stats()

        # Find parent audit ID if not specified
        if not self.parent_audit_id:
            self.parent_audit_id = self._find_latest_audit_id()

        # Build audit log content (without hash, for hashing)
        content = {
            "schema_version": "1.0",
            "timestamp": timestamp,
            "agent_id": self.agent_id,
            "agent_name": self.agent_info.get('agent_name', self.agent_info.get('name', self.agent_id)),
            "agent_level": self.agent_info.get('level', 'unknown'),
            "operation_type": self.operation_type,
            "phase": self.phase,
            "title": self.title,
            "description": self.description,
            "scope": {
                "allowed": [],
                "forbidden": [],
                "actual": [self.operation_type]
            },
            "files_modified": file_stats,
            "verification": {
                "local_tests": "SKIP",
                "ci_run_id": self.ci_run_id,
                "ci_status": self.ci_status,
                "claim_evidence_check": "SKIP",
                "tll_engine_validation": "SKIP"
            },
            "claims_made": self.claims_made,
            "evidence_submitted": self.evidence_submitted,
            "known_limitations": self.known_limitations,
            "next_steps": self.next_steps,
            "commit_sha": commit_sha,
            "parent_audit_id": self.parent_audit_id,
            "provenance_chain": [
                f"Agent: {self.agent_id}",
                f"Operation: {self.operation_type}",
                f"Phase: {self.phase}",
                f"Commit: {commit_sha[:8] if commit_sha else 'unknown'}",
                "Auto-generated by scripts/log-agent-action.py"
            ]
        }

        # Compute hash
        content_hash = self._compute_hash(content)

        # Add audit_id and hash
        audit_id = f"audit-{date_str}-{content_hash[:8]}"
        content['audit_id'] = audit_id
        content['hash'] = content_hash

        return content

    def save(self, audit_log):
        """Save audit log to .tll-engine/audit/ directory."""
        audit_dir = self.engine_dir / 'audit'
        audit_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{audit_log['audit_id']}.json"
        filepath = audit_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(audit_log, f, indent=2, ensure_ascii=False)

        return filepath

    def run(self):
        """Generate and save audit log."""
        print("=" * 60)
        print("TLL OS Agent Operation Audit Log Generator")
        print("=" * 60)
        print(f"Agent ID:    {self.agent_id}")
        print(f"Agent Name:  {self.agent_info.get('agent_name', self.agent_info.get('name', 'unknown'))}")
        print(f"Operation:   {self.operation_type}")
        print(f"Phase:       {self.phase}")
        print(f"Title:       {self.title}")
        print(f"Files:       {len(self.files_modified)}")
        print()

        print("[1/3] Generating audit log...")
        audit_log = self.generate()
        print(f"  Audit ID: {audit_log['audit_id']}")
        print(f"  Timestamp: {audit_log['timestamp']}")
        print(f"  Parent: {audit_log['parent_audit_id'] or 'none (first in chain)'}")
        print(f"  Hash: {audit_log['hash']}")
        print()

        print("[2/3] Saving audit log...")
        filepath = self.save(audit_log)
        print(f"  Saved to: {filepath}")
        print(f"  File size: {filepath.stat().st_size} bytes")
        print()

        print("[3/3] Validating audit log...")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            required_fields = ['schema_version', 'audit_id', 'timestamp', 'agent_id',
                               'operation_type', 'phase', 'title', 'hash', 'provenance_chain']
            missing = [f for f in required_fields if f not in loaded]
            if missing:
                print(f"  [ERROR] Missing fields: {missing}")
                return 1
            print("  Validation: PASS")
        except Exception as e:
            print(f"  [ERROR] Validation failed: {e}")
            return 1

        print()
        print("=" * 60)
        print("RESULT: SUCCESS")
        print(f"Audit log generated: {filepath}")
        print("=" * 60)
        return 0


def main():
    parser = argparse.ArgumentParser(description='TLL OS Agent Operation Audit Log Generator')
    parser.add_argument('--agent-id', required=True,
                        help='Agent identifier (from identity/agents.json)')
    parser.add_argument('--operation-type', required=True,
                        choices=['code_change', 'truth_update', 'evidence_submit',
                                 'protocol_change', 'identity_change', 'audit_log'],
                        help='Type of operation')
    parser.add_argument('--phase', required=True,
                        help='Phase identifier (e.g., P0-16.1)')
    parser.add_argument('--title', required=True,
                        help='Short description of the operation')
    parser.add_argument('--description', default='',
                        help='Detailed description')
    parser.add_argument('--files-modified', nargs='*', default=[],
                        help='List of modified file paths')
    parser.add_argument('--ci-run-id', default=None,
                        help='GitHub Actions Run ID')
    parser.add_argument('--ci-status', default=None,
                        choices=['success', 'failure', 'pending'],
                        help='CI run status')
    parser.add_argument('--claims-made', nargs='*', default=[],
                        help='List of capability claims made')
    parser.add_argument('--evidence-submitted', nargs='*', default=[],
                        help='List of evidence file paths or IDs')
    parser.add_argument('--known-limitations', nargs='*', default=[],
                        help='List of known limitations')
    parser.add_argument('--next-steps', nargs='*', default=[],
                        help='List of recommended next steps')
    parser.add_argument('--parent-audit-id', default=None,
                        help='Parent audit log ID (auto-detected if not specified)')
    parser.add_argument('--engine-dir', default='.tll-engine',
                        help='Path to .tll-engine directory')
    args = parser.parse_args()

    generator = AuditLogGenerator(
        engine_dir=args.engine_dir,
        agent_id=args.agent_id,
        operation_type=args.operation_type,
        phase=args.phase,
        title=args.title,
        description=args.description,
        files_modified=args.files_modified,
        ci_run_id=args.ci_run_id,
        ci_status=args.ci_status,
        claims_made=args.claims_made,
        evidence_submitted=args.evidence_submitted,
        known_limitations=args.known_limitations,
        next_steps=args.next_steps,
        parent_audit_id=args.parent_audit_id
    )

    exit_code = generator.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
