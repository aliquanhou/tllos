#!/usr/bin/env python3
"""
TLL OS Desktop Host - Evidence Panel
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime


class EvidencePanel:
    def __init__(self, host_dir):
        self.host_dir = Path(host_dir)

    def get_status(self):
        snapshots_dir = self.host_dir / "snapshots"
        latest_snapshot = snapshots_dir / "latest_snapshot.json"

        hash_str = ""
        timestamp = ""

        if latest_snapshot.exists():
            with open(latest_snapshot, 'r') as f:
                content = f.read()
            h = hashlib.sha256(content.encode()).hexdigest()
            hash_str = h[:16]
            timestamp = datetime.now().isoformat()

        return {
            "hash": hash_str,
            "timestamp": timestamp
        }

    def render(self):
        status = self.get_status()
        return f"🔐 EVIDENCE\n  SHA256: {status['hash']}\n  Time: {status['timestamp']}"
