#!/usr/bin/env python3
"""
TLL OS Agent Memory

Short-term, long-term, and skill memory.
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class MemoryEntry:
    """Memory entry."""
    entry_id: str
    content: str
    category: str  # short_term / long_term / skill
    timestamp: float = field(default_factory=time.time)
    importance: float = 0.5


class TLLAgentMemory:
    """TLL OS Agent Memory."""

    def __init__(self):
        self.short_term: List[MemoryEntry] = []
        self.long_term: List[MemoryEntry] = []
        self.skills: List[MemoryEntry] = []
        self.next_id = 0

    def remember(self, content: str, category: str = "short_term",
                 importance: float = 0.5) -> MemoryEntry:
        """Store a memory entry."""
        self.next_id += 1
        entry = MemoryEntry(
            entry_id=f"mem-{self.next_id}",
            content=content,
            category=category,
            importance=importance
        )

        if category == "short_term":
            self.short_term.append(entry)
            # Keep short-term limited
            if len(self.short_term) > 20:
                self.short_term = self.short_term[-20:]
        elif category == "long_term":
            self.long_term.append(entry)
        elif category == "skill":
            self.skills.append(entry)

        return entry

    def recall(self, category: Optional[str] = None,
               limit: int = 10) -> List[Dict]:
        """Recall memories."""
        results = []

        if category is None or category == "short_term":
            for e in self.short_term[-limit:]:
                results.append({
                    "id": e.entry_id,
                    "content": e.content,
                    "category": e.category,
                    "importance": e.importance
                })

        if category is None or category == "long_term":
            for e in self.long_term[-limit:]:
                results.append({
                    "id": e.entry_id,
                    "content": e.content,
                    "category": e.category,
                    "importance": e.importance
                })

        if category == "skill":
            for e in self.skills[-limit:]:
                results.append({
                    "id": e.entry_id,
                    "content": e.content,
                    "category": e.category,
                    "importance": e.importance
                })

        return results

    def get_status(self) -> Dict:
        """Get memory status."""
        return {
            "short_term_count": len(self.short_term),
            "long_term_count": len(self.long_term),
            "skill_count": len(self.skills),
            "total_entries": self.next_id
        }
