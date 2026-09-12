#!/usr/bin/env python3
"""
TLL OS World Model

Agent's understanding of its digital environment.
"""

import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class WorldObject:
    """An object in the TLL World."""
    object_id: str
    name: str
    type: str  # window / file / process / app / service
    state: str = "ACTIVE"  # ACTIVE / INACTIVE / DESTROYED
    dependencies: List[str] = field(default_factory=list)  # object_ids this depends on
    dependents: List[str] = field(default_factory=list)  # object_ids that depend on this
    metadata: Dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class TLLWorldModel:
    """TLL OS World Model - Agent's understanding of environment."""

    def __init__(self):
        self.objects: Dict[str, WorldObject] = {}
        self.agent_objects: Dict[str, str] = {}  # agent_id -> list of object_ids
        self.history: List[Dict] = []

    def add_object(self, name: str, type: str, object_id: str = None,
                   dependencies: List[str] = None, metadata: Dict = None) -> WorldObject:
        """Add an object to the world."""
        if object_id is None:
            object_id = f"obj-{len(self.objects) + 1:04d}"

        obj = WorldObject(
            object_id=object_id,
            name=name,
            type=type,
            dependencies=dependencies or [],
            metadata=metadata or {}
        )
        self.objects[object_id] = obj

        # Update reverse dependencies
        for dep_id in obj.dependencies:
            if dep_id in self.objects:
                self.objects[dep_id].dependents.append(object_id)

        self.history.append({
            "action": "add_object",
            "object_id": object_id,
            "timestamp": time.time()
        })

        return obj

    def get_object(self, object_id: str) -> Optional[WorldObject]:
        """Get object by ID."""
        return self.objects.get(object_id)

    def find_by_name(self, name: str) -> List[WorldObject]:
        """Find objects by name."""
        return [obj for obj in self.objects.values() if name.lower() in obj.name.lower()]

    def get_dependencies(self, object_id: str, recursive: bool = True) -> Set[str]:
        """Get all dependencies of an object."""
        obj = self.objects.get(object_id)
        if not obj:
            return set()

        result = set()
        to_visit = list(obj.dependencies)

        while to_visit:
            dep_id = to_visit.pop()
            if dep_id in result:
                continue
            result.add(dep_id)
            if recursive and dep_id in self.objects:
                to_visit.extend(self.objects[dep_id].dependencies)

        return result

    def get_dependents(self, object_id: str, recursive: bool = True) -> Set[str]:
        """Get all objects that depend on this one."""
        obj = self.objects.get(object_id)
        if not obj:
            return set()

        result = set()
        to_visit = list(obj.dependents)

        while to_visit:
            dep_id = to_visit.pop()
            if dep_id in result:
                continue
            result.add(dep_id)
            if recursive and dep_id in self.objects:
                to_visit.extend(self.objects[dep_id].dependents)

        return result

    def get_impact_scope(self, object_id: str) -> Dict:
        """Get full impact scope if this object is modified/destroyed."""
        obj = self.objects.get(object_id)
        if not obj:
            return {"error": "Object not found"}

        dependents = self.get_dependents(object_id)
        dependencies = self.get_dependencies(object_id)

        return {
            "object_id": object_id,
            "name": obj.name,
            "type": obj.type,
            "direct_dependents": len(obj.dependents),
            "total_dependents": len(dependents),
            "direct_dependencies": len(obj.dependencies),
            "total_dependencies": len(dependencies),
            "impact_level": self._calculate_impact_level(len(dependents)),
            "affected_objects": [self.objects[oid].name for oid in dependents if oid in self.objects]
        }

    def _calculate_impact_level(self, dependent_count: int) -> str:
        """Calculate impact level based on dependent count."""
        if dependent_count == 0:
            return "LOW"
        elif dependent_count <= 2:
            return "MEDIUM"
        elif dependent_count <= 5:
            return "HIGH"
        else:
            return "CRITICAL"

    def list_objects(self, type_filter: str = None) -> Dict:
        """List all objects in the world."""
        objects = []
        for obj in self.objects.values():
            if type_filter and obj.type != type_filter:
                continue
            objects.append({
                "id": obj.object_id,
                "name": obj.name,
                "type": obj.type,
                "state": obj.state,
                "dependencies": len(obj.dependencies),
                "dependents": len(obj.dependents)
            })

        return {
            "objects": objects,
            "count": len(objects)
        }

    def get_world_summary(self) -> Dict:
        """Get summary of the world."""
        type_counts = {}
        for obj in self.objects.values():
            type_counts[obj.type] = type_counts.get(obj.type, 0) + 1

        return {
            "total_objects": len(self.objects),
            "by_type": type_counts,
            "history_events": len(self.history)
        }
