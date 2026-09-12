#!/usr/bin/env python3
"""
TLL OS Process Manager

Real process management for TLL OS.
"""

import time
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class VirtualProcess:
    """Virtual process."""
    pid: int
    name: str
    status: str = "RUNNING"  # RUNNING / STOPPED / ERROR
    started_at: float = field(default_factory=time.time)
    cpu_usage: float = 0.0
    memory_mb: int = 0


class TLLProcessManager:
    """TLL OS Process Manager."""

    def __init__(self):
        self.processes: Dict[int, VirtualProcess] = {}
        self.next_pid = 1
        # Kernel process always running
        self._start_process("tll-kernel", 512)

    def _start_process(self, name: str, memory_mb: int = 64) -> VirtualProcess:
        """Start a new process."""
        pid = self.next_pid
        self.next_pid += 1
        proc = VirtualProcess(pid=pid, name=name, memory_mb=memory_mb)
        self.processes[pid] = proc
        return proc

    def start_process(self, name: str, memory_mb: int = 64) -> Dict:
        """Start a new process."""
        proc = self._start_process(name, memory_mb)
        return {
            "pid": proc.pid,
            "name": proc.name,
            "status": proc.status,
            "memory_mb": proc.memory_mb
        }

    def stop_process(self, pid: int) -> Dict:
        """Stop a process."""
        if pid in self.processes:
            proc = self.processes[pid]
            proc.status = "STOPPED"
            return {
                "pid": pid,
                "name": proc.name,
                "status": proc.status
            }
        return {"pid": pid, "error": "Process not found"}

    def list_processes(self) -> Dict:
        """List all processes."""
        procs = []
        for pid, proc in self.processes.items():
            procs.append({
                "pid": proc.pid,
                "name": proc.name,
                "status": proc.status,
                "memory_mb": proc.memory_mb,
                "started_at": proc.started_at
            })

        running = sum(1 for p in self.processes.values() if p.status == "RUNNING")
        return {
            "processes": procs,
            "total": len(procs),
            "running": running
        }

    def get_process(self, pid: int) -> Optional[VirtualProcess]:
        """Get process by PID."""
        return self.processes.get(pid)

    def get_stats(self) -> Dict:
        """Get process statistics."""
        total_memory = sum(p.memory_mb for p in self.processes.values())
        running = sum(1 for p in self.processes.values() if p.status == "RUNNING")
        return {
            "total_processes": len(self.processes),
            "running_processes": running,
            "total_memory_mb": total_memory
        }
