"""
Phase 2.1: Syscall Context Mapping
Maps syscall events to vulnerability types.
Enables static-to-runtime correlation in Phase 2.2.
"""

import logging
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class VulnerabilityType(Enum):
    """Phase 1 vulnerability types that eBPF can inform"""
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    SSRF = "ssrf"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    RACE_CONDITION = "race_condition"
    TIMING_ORACLE = "timing_oracle"
    INFORMATION_DISCLOSURE = "information_disclosure"
    SYMLINK_ATTACK = "symlink_attack"


@dataclass
class SyscallContext:
    """Context extracted from syscall event"""
    syscall_name: str
    args: List[str]
    return_value: int
    errno: int
    pid: int
    uid: int


class SyscallContextMapper:
    """
    Maps syscall events to vulnerability contexts.
    Links syscall behavior to Phase 1 static findings.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.syscall_to_vuln_types = self._build_syscall_mapping()
        self.context_rules = self._build_context_rules()
    
    def _build_syscall_mapping(self) -> Dict[str, Set[VulnerabilityType]]:
        """
        Map syscalls to potential vulnerability types.
        Used for pre-filtering static findings.
        """
        return {
            "execve": {
                VulnerabilityType.COMMAND_INJECTION,
                VulnerabilityType.PRIVILEGE_ESCALATION,
            },
            "openat": {
                VulnerabilityType.PATH_TRAVERSAL,
                VulnerabilityType.SYMLINK_ATTACK,
                VulnerabilityType.INFORMATION_DISCLOSURE,
            },
            "read": {
                VulnerabilityType.INFORMATION_DISCLOSURE,
                VulnerabilityType.TIMING_ORACLE,
            },
            "write": {
                VulnerabilityType.PATH_TRAVERSAL,
                VulnerabilityType.INFORMATION_DISCLOSURE,
            },
            "connect": {
                VulnerabilityType.SSRF,
            },
        }
    
    def _build_context_rules(self) -> Dict[str, List[Dict]]:
        """
        Rules for identifying vulnerability evidence in syscall context.
        Each rule checks syscall args/return for suspicious patterns.
        """
        return {
            "command_injection": [
                {
                    "syscall": "execve",
                    "checks": [
                        ("arg_contains", 0, ["/bin/sh", "/bin/bash", "cmd", "powershell"]),
                        ("arg_contains", 0, ["||", "&&", ";", "|", "`"]),  # Shell metacharacters
                    ]
                },
            ],
            "path_traversal": [
                {
                    "syscall": "openat",
                    "checks": [
                        ("arg_contains", 0, ["..", "/etc/", "/root", "/var"]),
                        ("arg_contains", 0, ["../../../../", "..\\..\\..\\..\\"])  # Traversal patterns
                    ]
                },
            ],
            "race_condition": [
                {
                    "syscall": "openat",
                    "checks": [
                        ("success", True),
                        # If path was traversable and succeeded, might indicate TOCTOU
                    ]
                },
            ],
            "symlink_attack": [
                {
                    "syscall": "openat",
                    "checks": [
                        ("permission_denied", False),  # Successful open might indicate symlink traversal
                    ]
                },
            ],
            "information_disclosure": [
                {
                    "syscall": "read",
                    "checks": [
                        ("arg_contains", 0, ["/etc/passwd", "/etc/shadow", ".ssh", ".aws", ".config"])
                    ]
                },
                {
                    "syscall": "openat",
                    "checks": [
                        ("arg_contains", 0, [".env", "secret", "key", "password", "token"])
                    ]
                },
            ],
            "ssrf": [
                {
                    "syscall": "connect",
                    "checks": [
                        ("arg_contains", 1, ["127.0.0.1", "localhost", "169.254", "10.0", "172.16"])
                    ]
                },
            ],
        }
    
    def map_syscall_to_vulns(self, syscall_name: str) -> Set[VulnerabilityType]:
        """
        Get all vulnerability types that could be related to this syscall.
        """
        return self.syscall_to_vuln_types.get(syscall_name, set())
    
    def extract_context(self, event: dict) -> Optional[SyscallContext]:
        """
        Extract and validate syscall context from normalized event.
        """
        try:
            details = event.get("details", {})
            
            return SyscallContext(
                syscall_name=details.get("syscall_name", "unknown"),
                args=details.get("args", []),
                return_value=details.get("return_value", 0),
                errno=details.get("errno", 0),
                pid=details.get("pid", 0),
                uid=details.get("uid", 0),
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting context: {e}")
            return None
    
    def identify_evidence(self, context: SyscallContext) -> Dict[str, float]:
        """
        Identify evidence in syscall that supports/refutes vulnerability claims.
        Returns mapping of vuln_type -> confidence (0.0-1.0).
        """
        evidence = {}
        
        # Get potential vulns for this syscall
        potential_vulns = self.map_syscall_to_vulns(context.syscall_name)
        
        for vuln_type in potential_vulns:
            # Check context rules for this vuln type
            confidence = self._evaluate_rules(vuln_type, context)
            if confidence > 0.0:
                evidence[vuln_type.value] = confidence
        
        return evidence
    
    def _evaluate_rules(self, vuln_type: VulnerabilityType, context: SyscallContext) -> float:
        """
        Evaluate evidence rules for a vulnerability type.
        Returns confidence score (0.0-1.0).
        """
        rules = self.context_rules.get(vuln_type.value, [])
        
        if not rules:
            return 0.0
        
        # Check if any rule matches (OR logic)
        for rule in rules:
            if rule.get("syscall") != context.syscall_name:
                continue
            
            # Evaluate all checks in rule (AND logic)
            checks = rule.get("checks", [])
            all_pass = True
            match_count = 0
            
            for check_type, check_arg, check_values in checks:
                if check_type == "arg_contains":
                    arg_idx = check_arg
                    if arg_idx < len(context.args):
                        arg_value = context.args[arg_idx]
                        if any(value in arg_value for value in check_values):
                            match_count += 1
                        else:
                            all_pass = False
                
                elif check_type == "success":
                    expected = check_arg
                    is_success = context.return_value >= 0
                    if is_success == expected:
                        match_count += 1
                    else:
                        all_pass = False
                
                elif check_type == "permission_denied":
                    expected = check_arg
                    is_denied = context.errno == 13  # EACCES
                    if is_denied != expected:  # Inverse logic: if NOT denied, interesting
                        match_count += 1
                    else:
                        all_pass = False
            
            # If rule has multiple checks, all must pass
            if all_pass and match_count > 0:
                # Confidence = number of matched checks / total checks
                confidence = match_count / len(checks) if checks else 0.5
                return min(confidence, 1.0)  # Cap at 1.0
        
        return 0.0
    
    def correlate_with_static_finding(
        self,
        static_finding: dict,
        syscall_events: List[dict],
    ) -> Dict[str, any]:
        """
        Correlate a Phase 1 static finding with syscall events.
        Returns correlation result with evidence.
        """
        finding_type = static_finding.get("type", "unknown")
        finding_line = static_finding.get("line", -1)
        
        # Find events that could be related
        related_events = []
        confidence_scores = []
        
        for event in syscall_events:
            context = self.extract_context(event)
            if not context:
                continue
            
            # Map syscall to potential vulns
            potential = self.map_syscall_to_vulns(context.syscall_name)
            if finding_type not in [v.value for v in potential]:
                continue
            
            # Evaluate evidence
            evidence = self.identify_evidence(context)
            if finding_type in evidence:
                related_events.append(event)
                confidence_scores.append(evidence[finding_type])
        
        # Compute overall correlation confidence
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
        else:
            avg_confidence = 0.0
        
        return {
            "finding_id": static_finding.get("id", "unknown"),
            "finding_type": finding_type,
            "related_events_count": len(related_events),
            "correlation_confidence": avg_confidence,
            "evidence_events": related_events[:10],  # Limit to first 10
        }


class SyscallCorrelationEngine:
    """
    High-level engine for correlating static findings with eBPF syscall events.
    Used in Phase 2.2 for enhanced verdict computation.
    """
    
    def __init__(self):
        self.mapper = SyscallContextMapper()
        self.logger = logging.getLogger(__name__)
    
    def correlate_findings_with_trace(
        self,
        static_findings: List[dict],
        syscall_events: List[dict],
    ) -> Dict[str, any]:
        """
        Correlate Phase 1 findings with Phase 2 syscall trace.
        Returns structured correlation results.
        """
        results = {
            "total_findings": len(static_findings),
            "total_events": len(syscall_events),
            "correlations": [],
            "uncorrelated_findings": [],
        }
        
        for finding in static_findings:
            correlation = self.mapper.correlate_with_static_finding(finding, syscall_events)
            
            if correlation["related_events_count"] > 0:
                results["correlations"].append(correlation)
            else:
                results["uncorrelated_findings"].append(finding.get("id"))
        
        results["correlation_rate"] = (
            len(results["correlations"]) / len(static_findings) * 100
            if static_findings else 0.0
        )
        
        return results
