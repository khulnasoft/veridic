"""
Phase 2.1: Event Normalization Pipeline
Converts raw syscall events from eBPF into events.json schema.
Handles sanitization, field mapping, and schema validation.
"""

import logging
import json
import hashlib
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class SyscallCategory(Enum):
    """Map syscalls to vulnerability categories for correlation hints"""
    COMMAND_INJECTION = ["execve", "system", "popen"]
    PATH_TRAVERSAL = ["openat", "open", "stat", "access"]
    SSRF = ["connect", "sendto", "sendmsg"]
    FILE_ACCESS = ["read", "write", "open", "close"]
    PRIVILEGE = ["setuid", "setgid", "chmod"]
    MEMORY = ["mmap", "mprotect", "brk"]


class EventNormalizer:
    """
    Normalizes raw syscall events to events.json schema.
    Ensures consistent field naming, sanitization, and validation.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.syscall_map = self._build_syscall_map()
    
    def _build_syscall_map(self) -> dict:
        """Map syscall numbers to names and categories"""
        return {
            59: ("execve", SyscallCategory.COMMAND_INJECTION),
            257: ("openat", SyscallCategory.PATH_TRAVERSAL),
            0: ("read", SyscallCategory.FILE_ACCESS),
            1: ("write", SyscallCategory.FILE_ACCESS),
            42: ("connect", SyscallCategory.SSRF),
        }
    
    def normalize(self, raw_event: dict) -> dict:
        """
        Convert raw eBPF syscall event to events.json schema.
        Handles field mapping, sanitization, and validation.
        """
        try:
            # Extract core fields
            event_id = raw_event.get("event_id") or str(uuid.uuid4())
            timestamp = raw_event.get("timestamp", 0)
            sandbox_id = raw_event.get("sandbox_id", str(uuid.uuid4()))
            
            # Map syscall
            syscall_num = raw_event["details"].get("syscall_number", 0)
            syscall_name = raw_event["details"].get("syscall_name", "unknown")
            syscall_category = None
            
            if syscall_num in self.syscall_map:
                mapped_name, category = self.syscall_map[syscall_num]
                syscall_name = mapped_name
                syscall_category = category
            
            # Sanitize args
            args = self._sanitize_args(raw_event["details"].get("args", []))
            
            # Build normalized event
            normalized = {
                "event_id": event_id,
                "timestamp": timestamp,
                "source": "ebpf",
                "event_type": "syscall",
                "confidence": 1.0,  # Kernel events are always confident
                "collector_version": "1.0.0",
                "sandbox_id": sandbox_id,
                "related_static_findings": self._infer_related_findings(syscall_name, args),
                "details": {
                    "syscall_number": syscall_num,
                    "syscall_name": syscall_name,
                    "args": args,
                    "return_value": raw_event["details"].get("return_value", 0),
                    "errno": raw_event["details"].get("errno", 0),
                    "pid": raw_event["details"].get("pid", 0),
                    "uid": raw_event["details"].get("uid", 0),
                    "process_name": raw_event["details"].get("process_name", "unknown"),
                },
                "determinism_metadata": {
                    "ordering_bucket": (timestamp // (50 * 1_000_000)) * (50 * 1_000_000),
                    "hash": self._compute_event_hash(raw_event),
                }
            }
            
            # Validate against schema
            if self._validate_event(normalized):
                return normalized
            else:
                self.logger.warning(f"Event failed validation: {event_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error normalizing event: {e}")
            return None
    
    def _sanitize_args(self, args: List[str], max_length: int = 256) -> List[str]:
        """
        Sanitize syscall arguments.
        - Limit length to prevent buffer overflows in logs
        - Remove null bytes and control characters
        - Preserve path information
        """
        sanitized = []
        
        for arg in args:
            if not arg:
                continue
            
            # Remove null bytes and control characters
            clean_arg = arg.replace('\x00', '').replace('\n', ' ').replace('\r', ' ')
            
            # Truncate to max_length
            if len(clean_arg) > max_length:
                clean_arg = clean_arg[:max_length] + "..."
            
            sanitized.append(clean_arg)
        
        return sanitized
    
    def _infer_related_findings(self, syscall_name: str, args: List[str]) -> List[str]:
        """
        Infer which Phase 1 static findings this syscall might relate to.
        Used for pre-filtering in correlation.
        """
        findings = []
        
        # Command injection patterns (execve with interesting args)
        if syscall_name == "execve":
            if args and any(x in args[0].lower() for x in ["/bin/sh", "/bin/bash", "cmd", "powershell"]):
                findings.append("command_injection_hint")
        
        # Path traversal patterns (openat with ".." or absolute paths)
        if syscall_name == "openat":
            if args and any(x in args[0] for x in ["..", "/etc/", "/var/", "/home"]):
                findings.append("path_traversal_hint")
        
        # SSRF patterns (connect to localhost or private IPs)
        if syscall_name == "connect":
            # These would be populated by network event, not syscall
            pass
        
        return findings
    
    def _compute_event_hash(self, event: dict) -> str:
        """
        Compute SHA256 hash of event (excluding timestamp).
        Used for determinism checking.
        """
        # Remove timestamp and hash fields
        event_copy = {}
        for k, v in event.items():
            if k not in ["timestamp", "event_id", "determinism_metadata"]:
                event_copy[k] = v
        
        # Serialize and hash
        event_json = json.dumps(event_copy, sort_keys=True, default=str)
        return hashlib.sha256(event_json.encode()).hexdigest()
    
    def _validate_event(self, event: dict) -> bool:
        """
        Validate event against events.json schema.
        Checks required fields and type correctness.
        """
        required_fields = [
            "event_id",
            "timestamp",
            "source",
            "event_type",
            "confidence",
            "collector_version",
            "sandbox_id",
            "details"
        ]
        
        for field in required_fields:
            if field not in event:
                self.logger.warning(f"Missing required field: {field}")
                return False
        
        # Type checks
        if not isinstance(event["event_id"], str):
            return False
        if not isinstance(event["timestamp"], int):
            return False
        if not isinstance(event["confidence"], (int, float)):
            return False
        if not 0.0 <= event["confidence"] <= 1.0:
            return False
        
        return True


class NormalizationPipeline:
    """
    Full pipeline for consuming raw events and outputting normalized events.
    Handles batching, filtering, and stats.
    """
    
    def __init__(self):
        self.normalizer = EventNormalizer()
        self.logger = logging.getLogger(__name__)
        self.stats = {
            "total_input": 0,
            "successfully_normalized": 0,
            "validation_failures": 0,
            "exceptions": 0,
        }
    
    def process_events(self, raw_events: List[dict]) -> List[dict]:
        """
        Process batch of raw events through normalization.
        Returns list of valid normalized events.
        """
        normalized = []
        
        for raw_event in raw_events:
            self.stats["total_input"] += 1
            
            try:
                normalized_event = self.normalizer.normalize(raw_event)
                
                if normalized_event:
                    normalized.append(normalized_event)
                    self.stats["successfully_normalized"] += 1
                else:
                    self.stats["validation_failures"] += 1
                    
            except Exception as e:
                self.logger.error(f"Exception during normalization: {e}")
                self.stats["exceptions"] += 1
        
        return normalized
    
    def get_stats(self) -> dict:
        """Return normalization statistics"""
        total = self.stats["total_input"]
        normalized = self.stats["successfully_normalized"]
        success_rate = (normalized / total * 100) if total > 0 else 0.0
        
        return {
            **self.stats,
            "success_rate_percent": success_rate,
        }
