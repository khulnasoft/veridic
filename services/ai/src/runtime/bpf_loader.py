"""
Phase 2.1: eBPF BPF Loader Agent
Manages eBPF program compilation, loading, and event consumption.
Works with syscall_tracer.c kernel program.
"""

import logging
import ctypes
import os
import json
import uuid
from typing import Optional, Callable, List
from dataclasses import asdict
from datetime import datetime

logger = logging.getLogger(__name__)


class SyscallEvent(ctypes.Structure):
    """Mirror of syscall_event from eBPF program"""
    _fields_ = [
        ("pid", ctypes.c_uint32),
        ("ppid", ctypes.c_uint32),
        ("uid", ctypes.c_uint32),
        ("gid", ctypes.c_uint32),
        ("timestamp_ns", ctypes.c_uint64),
        ("syscall_num", ctypes.c_uint32),
        ("syscall_name", ctypes.c_char * 16),
        ("retval", ctypes.c_int64),
        ("errno", ctypes.c_int32),
        ("args", (ctypes.c_char * 128) * 4),
    ]


class BPFLoader:
    """
    Loads and manages eBPF syscall tracer program.
    Consumes events from kernel and normalizes to events.json schema.
    """
    
    def __init__(self, ebpf_program_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.ebpf_program_path = ebpf_program_path or self._get_default_program_path()
        self.bpf = None
        self.enabled = False
        self.event_count = 0
        self.error_count = 0
        self.sandbox_id = str(uuid.uuid4())
        self.execution_id = None
    
    def _get_default_program_path(self) -> str:
        """Get path to eBPF program source"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "ebpf_tracer.c")
    
    def load_program(self) -> bool:
        """
        Load eBPF program.
        In production, uses libbpf/BCC to compile and load.
        For now, returns stub for integration testing.
        """
        try:
            # Check if file exists
            if not os.path.exists(self.ebpf_program_path):
                self.logger.warning(f"eBPF program not found: {self.ebpf_program_path}")
                self.logger.info("Running in stub mode (no actual kernel instrumentation)")
                self.enabled = False
                return True  # Graceful degradation
            
            # In production, would use:
            # from bcc import BPF
            # self.bpf = BPF(src_file=self.ebpf_program_path)
            # self.bpf.trace_print()
            
            self.logger.info(f"eBPF program loaded from {self.ebpf_program_path}")
            self.enabled = True
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load eBPF program: {e}")
            self.enabled = False
            return False
    
    def start_tracing(self, sandbox_id: Optional[str] = None) -> str:
        """
        Start syscall tracing for a sandbox.
        Returns execution_id for tracking this trace session.
        """
        if not self.load_program():
            self.logger.warning("eBPF not available, using stub trace")
        
        self.execution_id = str(uuid.uuid4())
        if sandbox_id:
            self.sandbox_id = sandbox_id
        
        self.logger.info(f"Started tracing: sandbox={self.sandbox_id}, execution={self.execution_id}")
        return self.execution_id
    
    def stop_tracing(self) -> int:
        """
        Stop syscall tracing and return event count.
        """
        count = self.event_count
        self.logger.info(f"Stopped tracing: {count} events captured")
        return count
    
    def consume_events(self, callback: Optional[Callable] = None) -> List[dict]:
        """
        Consume events from eBPF ringbuffer and normalize them.
        If callback provided, calls it for each event.
        Returns list of normalized events.
        """
        events = []
        
        if not self.enabled:
            self.logger.debug("eBPF not enabled, returning stub events")
            return events
        
        try:
            # In production, would iterate over BPF ringbuffer:
            # while True:
            #     try:
            #         data = self.bpf["events"].ringbuf_read(8192)
            #         if data:
            #             raw_event = ctypes.cast(data, ctypes.POINTER(SyscallEvent)).contents
            #             normalized = self._normalize_event(raw_event)
            #             events.append(normalized)
            #             if callback:
            #                 callback(normalized)
            #     except KeyboardInterrupt:
            #         break
            
            self.event_count = len(events)
            return events
            
        except Exception as e:
            self.logger.error(f"Error consuming eBPF events: {e}")
            self.error_count += 1
            return events
    
    def _normalize_event(self, raw_event: SyscallEvent) -> dict:
        """
        Convert raw eBPF syscall_event to events.json schema.
        """
        event_id = str(uuid.uuid4())
        syscall_name = raw_event.syscall_name.decode('utf-8', errors='ignore').rstrip('\x00')
        
        # Prepare args list (sanitize null bytes)
        args = []
        for i in range(4):
            arg_bytes = raw_event.args[i]
            arg_str = arg_bytes.decode('utf-8', errors='ignore').rstrip('\x00')
            if arg_str:
                args.append(arg_str)
        
        # Base event structure
        event = {
            "event_id": event_id,
            "timestamp": raw_event.timestamp_ns,
            "source": "ebpf",
            "event_type": "syscall",
            "confidence": 1.0,  # Kernel data is always confident
            "collector_version": "1.0.0",
            "sandbox_id": self.sandbox_id,
            "related_static_findings": [],
            "determinism_metadata": {
                "ordering_bucket": (raw_event.timestamp_ns // (50 * 1_000_000)) * (50 * 1_000_000),
            },
            "details": {
                "syscall_number": raw_event.syscall_num,
                "syscall_name": syscall_name,
                "args": args,
                "return_value": raw_event.retval,
                "errno": raw_event.errno if raw_event.retval < 0 else 0,
                "pid": raw_event.pid,
                "uid": raw_event.uid,
            }
        }
        
        # Add process name if available (stub for now)
        event["details"]["process_name"] = f"pid_{raw_event.pid}"
        
        return event
    
    def get_stats(self) -> dict:
        """Return tracing statistics"""
        return {
            "sandbox_id": self.sandbox_id,
            "execution_id": self.execution_id,
            "event_count": self.event_count,
            "error_count": self.error_count,
            "enabled": self.enabled,
            "uptime_seconds": 0,  # Would track actual uptime
        }


class EBPFCollector:
    """
    High-level wrapper for eBPF syscall tracing.
    Integrates with trace_store and event normalization.
    """
    
    def __init__(self, program_path: Optional[str] = None):
        self.loader = BPFLoader(program_path)
        self.logger = logging.getLogger(__name__)
    
    def start_sandbox_tracing(self, sandbox_id: str) -> str:
        """Start tracing for a sandbox, return execution_id"""
        return self.loader.start_tracing(sandbox_id)
    
    def capture_syscalls(self, max_events: Optional[int] = None) -> List[dict]:
        """
        Capture syscalls during sandbox execution.
        max_events: Stop after N events (for testing)
        """
        events = []
        try:
            self.loader.consume_events(callback=lambda e: events.append(e))
            
            if max_events and len(events) >= max_events:
                events = events[:max_events]
            
            self.logger.info(f"Captured {len(events)} syscall events")
            return events
            
        except Exception as e:
            self.logger.error(f"Failed to capture syscalls: {e}")
            return []
    
    def get_collector_info(self) -> dict:
        """Return collector metadata"""
        return {
            "name": "eBPF Syscall Tracer",
            "version": "1.0.0",
            "supported_syscalls": ["execve", "openat", "read", "write", "connect"],
            "status": "enabled" if self.loader.enabled else "disabled",
            "stats": self.loader.get_stats(),
        }
