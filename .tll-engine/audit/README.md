# TLL OS Agent Operation Audit Log

> This directory contains immutable audit logs of all Agent operations on TLL OS.
> Audit logs are append-only. Once written, they cannot be modified.
> This is part of P0-16.1 TLL Engineering Enforcement Layer.

## Audit Log Format

Each audit log is a JSON file with the following schema:

```json
{
  "schema_version": "1.0",
  "audit_id": "audit-YYYYMMDD-HHMMSS-<short-hash>",
  "timestamp": "ISO 8601 UTC timestamp",
  "agent_id": "Agent identifier (from identity/agents.json)",
  "agent_name": "Agent human-readable name",
  "operation_type": "code_change | truth_update | evidence_submit | protocol_change | identity_change | audit_log",
  "phase": "P0-XX.X phase identifier",
  "title": "Short description of the operation",
  "description": "Detailed description of what was done",
  "scope": {
    "allowed": ["List of allowed actions"],
    "forbidden": ["List of forbidden actions"],
    "actual": ["List of actual actions taken"]
  },
  "files_modified": [
    {
      "path": "file path",
      "change_type": "added | modified | deleted",
      "lines_added": 0,
      "lines_deleted": 0
    }
  ],
  "verification": {
    "local_tests": "PASS | FAIL | SKIP",
    "ci_run_id": "GitHub Actions Run ID or null",
    "ci_status": "success | failure | pending | null",
    "claim_evidence_check": "PASS | FAIL | SKIP",
    "tll_engine_validation": "PASS | FAIL | SKIP"
  },
  "claims_made": [
    "List of capability claims made in this operation"
  ],
  "evidence_submitted": [
    "List of evidence file paths or IDs"
  ],
  "known_limitations": [
    "List of known limitations or caveats"
  ],
  "next_steps": [
    "List of recommended next steps"
  ],
  "commit_sha": "Git commit SHA or null",
  "parent_audit_id": "Previous audit log ID in the chain, or null",
  "hash": "SHA-256 hash of this audit log content (first 16 chars)",
  "provenance_chain": [
    "List of provenance steps"
  ]
}
```

## Operation Types

| Type | Description |
|------|-------------|
| `code_change` | Modification to source code (compiler, vm, stdlib, tests) |
| `truth_update` | Modification to .tll-engine/truth/ files |
| `evidence_submit` | Submission of new evidence files |
| `protocol_change` | Modification to .tll-engine/protocol/ files |
| `identity_change` | Modification to .tll-engine/identity/ files |
| `audit_log` | This audit log itself (meta) |

## Audit Log Chain

Audit logs form a hash chain:
- Each audit log has a `parent_audit_id` pointing to the previous log
- Each audit log has a `hash` of its content
- This creates an immutable chain that cannot be modified without detection

## Generating Audit Logs

Use the script:
```bash
python3 scripts/log-agent-action.py \
    --agent-id agent_doubao_bootstrap_001 \
    --operation-type code_change \
    --phase P0-16.1 \
    --title "Add .tll-engine CI validation" \
    --description "Added validate-tll-engine steps to CI workflow" \
    --files-modified .github/workflows/ci.yml \
    --ci-run-id 124
```

## Audit Log Rules

1. **Append-only**: Audit logs cannot be modified after creation
2. **Every Agent operation must have an audit log**: No code change without audit
3. **Audit logs must reference commit SHA**: Every audit log must reference the git commit it describes
4. **Audit logs must be honest**: Known limitations must be disclosed
5. **Audit logs must have evidence**: Claims must reference evidence files
6. **Independent audit required**: Constructing Agent cannot audit its own work

## Current Audit Logs

| Audit ID | Date | Phase | Operation | Agent |
|----------|------|-------|-----------|-------|
| (see audit log files) | | | | |
