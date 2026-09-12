#!/usr/bin/env python3
"""
TLL OS Virtual File System

Real in-memory file system for TLL OS.
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class VirtualFile:
    """Virtual file."""
    path: str
    content: str = ""
    size: int = 0
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)


class TLLVirtualFileSystem:
    """TLL OS Virtual File System."""

    def __init__(self):
        self.files: Dict[str, VirtualFile] = {
            "/": VirtualFile(path="/", content="")
        }
        self.root = "/"

    def read_file(self, path: str) -> Dict:
        """Read a file."""
        if path in self.files:
            f = self.files[path]
            return {
                "path": path,
                "content": f.content,
                "size": f.size,
                "created_at": f.created_at,
                "modified_at": f.modified_at,
                "exists": True
            }
        return {"path": path, "exists": False, "error": "File not found"}

    def write_file(self, path: str, content: str = "") -> Dict:
        """Write a file."""
        now = time.time()
        if path in self.files:
            f = self.files[path]
            f.content = content
            f.size = len(content)
            f.modified_at = now
        else:
            f = VirtualFile(path=path, content=content, size=len(content))
            self.files[path] = f

        return {
            "path": path,
            "written": True,
            "size": len(content),
            "modified_at": now
        }

    def list_dir(self, dir_path: str = "/") -> Dict:
        """List directory."""
        if not dir_path.endswith("/"):
            dir_path += "/"

        entries = []
        for path in self.files:
            if path.startswith(dir_path) and path != dir_path:
                # Get relative path
                rel = path[len(dir_path):]
                if "/" not in rel:
                    f = self.files[path]
                    entries.append({
                        "path": path,
                        "name": rel,
                        "size": f.size,
                        "is_dir": path.endswith("/")
                    })

        return {
            "dir": dir_path,
            "entries": entries,
            "count": len(entries)
        }

    def delete_file(self, path: str) -> Dict:
        """Delete a file."""
        if path in self.files:
            del self.files[path]
            return {"path": path, "deleted": True}
        return {"path": path, "deleted": False, "error": "File not found"}

    def file_exists(self, path: str) -> bool:
        return path in self.files

    def get_stats(self) -> Dict:
        """Get filesystem statistics."""
        total_size = sum(f.size for f in self.files.values())
        return {
            "total_files": len(self.files),
            "total_size_bytes": total_size,
            "root": self.root
        }
