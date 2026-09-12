#!/usr/bin/env python3
"""
TLL OS Agent Registry

Install, list, remove Agent packages.
Agent is the first citizen of TLL OS.
"""

import json
import os
from typing import Dict, List, Optional


class TLLAgentRegistry:
    """Registry for installed Agent packages."""

    def __init__(self, packages_dir: str = "packages"):
        self.packages_dir = packages_dir
        os.makedirs(packages_dir, exist_ok=True)
        self.installed = {}  # agent_id -> package_info
        self._load_installed()

    def _load_installed(self):
        """Load installed agents from registry."""
        registry_file = os.path.join(self.packages_dir, "registry.json")
        if os.path.exists(registry_file):
            with open(registry_file, 'r', encoding='utf-8') as f:
                self.installed = json.load(f)

    def _save_registry(self):
        """Save registry to disk."""
        registry_file = os.path.join(self.packages_dir, "registry.json")
        with open(registry_file, 'w', encoding='utf-8') as f:
            json.dump(self.installed, f, ensure_ascii=False, indent=2)

    def install(self, package_path: str) -> Dict:
        """Install an Agent package."""
        manifest_file = os.path.join(package_path, "manifest.json")
        if not os.path.exists(manifest_file):
            return {"success": False, "error": "No manifest.json"}

        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        agent_id = manifest.get("name", "unknown")
        self.installed[agent_id] = {
            "manifest": manifest,
            "path": package_path,
            "status": "installed",
            "permissions": self._load_permissions(package_path)
        }
        self._save_registry()
        return {"success": True, "agent_id": agent_id}

    def _load_permissions(self, package_path: str) -> List[str]:
        """Load permissions from package."""
        perm_file = os.path.join(package_path, "permissions.json")
        if os.path.exists(perm_file):
            with open(perm_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("permissions", [])
        return []

    def list_agents(self) -> List[Dict]:
        """List all installed agents."""
        result = []
        for agent_id, info in self.installed.items():
            result.append({
                "id": agent_id,
                "name": info["manifest"].get("name", agent_id),
                "version": info["manifest"].get("version", "1.0"),
                "provider": info["manifest"].get("provider", "local"),
                "status": info.get("status", "unknown"),
                "permissions": info.get("permissions", [])
            })
        return result

    def remove(self, agent_id: str) -> Dict:
        """Remove an Agent package."""
        if agent_id in self.installed:
            del self.installed[agent_id]
            self._save_registry()
            return {"success": True}
        return {"success": False, "error": "Not found"}
