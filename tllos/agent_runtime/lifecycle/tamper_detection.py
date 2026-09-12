#!/usr/bin/env python3
"""
TLL OS Tamper Detection

Verifies evidence integrity: before_hash, after_hash, action_hash, ledger_hash
"""

import hashlib
import json
from pathlib import Path


def compute_file_hash(file_path):
    """Compute SHA256 hash of a file."""
    path = Path(file_path)
    if not path.exists():
        return None
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_json_hash(data):
    """Compute SHA256 hash of JSON data."""
    serialized = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.sha256(serialized).hexdigest()


class TamperDetector:
    def __init__(self):
        self.evidence = {}

    def register_action(self, action_id, before_hash, after_hash):
        """Register action with before/after hashes."""
        self.evidence[action_id] = {
            "before_hash": before_hash,
            "after_hash": after_hash,
            "action_hash": compute_json_hash({
                "action_id": action_id,
                "before": before_hash,
                "after": after_hash
            })
        }

    def verify_action(self, action_id, expected_before, expected_after):
        """Verify action hasn't been tampered with."""
        if action_id not in self.evidence:
            return False, "Action not found"

        record = self.evidence[action_id]
        if record["before_hash"] != expected_before:
            return False, "Before hash mismatch"
        if record["after_hash"] != expected_after:
            return False, "After hash mismatch"
        return True, "Verified"

    def verify_integrity(self):
        """Verify all evidence hashes."""
        results = {}
        for action_id, record in self.evidence.items():
            expected_action_hash = compute_json_hash({
                "action_id": action_id,
                "before": record["before_hash"],
                "after": record["after_hash"]
            })
            if record["action_hash"] == expected_action_hash:
                results[action_id] = "VERIFIED"
            else:
                results[action_id] = "TAMPERED"
        return results


if __name__ == "__main__":
    detector = TamperDetector()
    detector.register_action("action_001", "abc123", "def456")
    print("Register: action_001")
    verified, msg = detector.verify_action("action_001", "abc123", "def456")
    print(f"Verify: {verified} - {msg}")
    results = detector.verify_integrity()
    print(f"Integrity: {results}")
