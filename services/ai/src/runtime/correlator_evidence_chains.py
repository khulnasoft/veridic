"""
Phase 2.2: Evidence Chain Correlator
Extends Phase 2.0 stateless correlation with exploit chain building.
Maps syscall → network event → static finding with evidence scores.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import hashlib
import json

logger = logging.getLogger(__name__)


class ExploitChainType(Enum):
    """Types of exploitability chains"""
    SSRF = "ssrf"  # Static SSRF + connect() to internal IP + HTTP request
    COMMAND_INJECTION = "command_injection"  # Static injection + execve() + connect()
    DATA_EXFILTRATION = "data_exfiltration"  # Static vuln + file read + network egress
    PATH_TRAVERSAL = "path_traversal"  # Static path traversal + open() to /etc files
    AUTH_BYPASS = "auth_bypass"  # Static auth logic + bypass detection
    RACE_CONDITION = "race_condition"  # Static race + fork/clone + timing


@dataclass
class EvidenceLink:
    """Single evidence item in a chain"""
    finding_id: str
    event_id: str
    event_type: str  # syscall, network, file_access
    evidence_type: str  # e.g., "execve_call", "http_request", "file_open"
    confidence: float  # 0-1
    timestamp: int  # nanoseconds
    details: Dict = field(default_factory=dict)


@dataclass
class ExploitChain:
    """Complete exploit chain with evidence"""
    chain_id: str
    chain_type: ExploitChainType
    static_finding_id: str
    evidence_links: List[EvidenceLink] = field(default_factory=list)
    exploitability_score: float = 0.0  # 0-100
    attack_scenario: str = ""
    requires_auth: bool = False
    
    def add_evidence(self, link: EvidenceLink) -> None:
        """Add evidence link to chain"""
        self.evidence_links.append(link)
    
    def calculate_exploitability(self) -> float:
        """Calculate exploitability based on evidence chain"""
        if not self.evidence_links:
            return 0.0
        
        # Each evidence link increases exploitability
        base = 50.0  # Static finding base
        chain_strength = min(len(self.evidence_links) * 15.0, 40.0)  # Max 40 points
        confidence_boost = min(
            sum(link.confidence for link in self.evidence_links) / len(self.evidence_links) * 10.0,
            10.0
        )
        
        return min(base + chain_strength + confidence_boost, 100.0)


class EvidenceChainCorrelator:
    """
    Builds exploitability chains linking static findings to runtime events.
    Stateless: all inputs provided, no internal state.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def correlate_exploit_chains(
        self,
        static_findings: List[Dict],
        syscall_events: List[Dict],
        network_events: List[Dict],
        file_events: List[Dict]
    ) -> List[ExploitChain]:
        """
        Build exploit chains from events.
        
        Args:
            static_findings: Phase 1 vulnerability findings
            syscall_events: eBPF syscall events
            network_events: mitmproxy network events
            file_events: eBPF file access events
        
        Returns:
            List of detected exploit chains with evidence
        """
        chains = []
        
        for finding in static_findings:
            finding_type = finding.get("type", "unknown")
            finding_id = finding.get("id")
            
            # Match chains based on finding type
            if finding_type == "ssrf":
                chain = self._build_ssrf_chain(finding_id, syscall_events, network_events)
                if chain:
                    chains.append(chain)
            
            elif finding_type == "sql_injection" or finding_type == "command_injection":
                chain = self._build_injection_chain(finding_id, finding_type, syscall_events, network_events)
                if chain:
                    chains.append(chain)
            
            elif finding_type == "path_traversal":
                chain = self._build_path_traversal_chain(finding_id, syscall_events, file_events)
                if chain:
                    chains.append(chain)
        
        return chains
    
    def _build_ssrf_chain(self, finding_id: str, syscall_events: List[Dict], network_events: List[Dict]) -> Optional[ExploitChain]:
        """SSRF: finding + internal IP connect + HTTP request"""
        chain = ExploitChain(
            chain_id=self._generate_chain_id(finding_id, "ssrf"),
            chain_type=ExploitChainType.SSRF,
            static_finding_id=finding_id,
            attack_scenario="Server initiated request to internal service"
        )
        
        # Look for connect() to internal IPs
        internal_ips = ["127.0.0.1", "localhost", "169.254.169.254"]
        for event in syscall_events:
            if event.get("details", {}).get("syscall_name") == "connect":
                dest_ip = event.get("details", {}).get("destination_ip")
                if any(ip in str(dest_ip) for ip in internal_ips):
                    chain.add_evidence(EvidenceLink(
                        finding_id=finding_id,
                        event_id=event.get("event_id"),
                        event_type="syscall",
                        evidence_type="connect_internal",
                        confidence=0.9,
                        timestamp=event.get("timestamp"),
                        details={"destination_ip": dest_ip}
                    ))
        
        # Look for HTTP requests to internal destinations
        for event in network_events:
            url = event.get("details", {}).get("url", "")
            dest_ip = event.get("details", {}).get("destination_ip")
            if any(ip in url or ip in str(dest_ip) for ip in internal_ips):
                chain.add_evidence(EvidenceLink(
                    finding_id=finding_id,
                    event_id=event.get("event_id"),
                    event_type="network",
                    evidence_type="http_internal_request",
                    confidence=0.85,
                    timestamp=event.get("timestamp"),
                    details={"url": url, "method": event.get("details", {}).get("method")}
                ))
        
        if len(chain.evidence_links) >= 2:  # Full SSRF chain
            chain.exploitability_score = chain.calculate_exploitability()
            return chain
        
        return None
    
    def _build_injection_chain(self, finding_id: str, finding_type: str, syscall_events: List[Dict], network_events: List[Dict]) -> Optional[ExploitChain]:
        """Command injection: finding + execve + outbound connection"""
        chain = ExploitChain(
            chain_id=self._generate_chain_id(finding_id, finding_type),
            chain_type=ExploitChainType.COMMAND_INJECTION if finding_type == "command_injection" else ExploitChainType.SSRF,
            static_finding_id=finding_id,
            attack_scenario="User-controlled input reaches shell execution"
        )
        
        # Look for execve (shell execution)
        suspicious_commands = ["/bin/sh", "/bin/bash", "cmd.exe", "powershell"]
        for event in syscall_events:
            if event.get("details", {}).get("syscall_name") == "execve":
                exec_args = event.get("details", {}).get("args", [])
                if any(cmd in str(exec_args) for cmd in suspicious_commands):
                    chain.add_evidence(EvidenceLink(
                        finding_id=finding_id,
                        event_id=event.get("event_id"),
                        event_type="syscall",
                        evidence_type="execve_shell",
                        confidence=0.95,
                        timestamp=event.get("timestamp"),
                        details={"command": exec_args}
                    ))
        
        # Look for outbound network connections (exfiltration)
        for event in network_events:
            chain.add_evidence(EvidenceLink(
                finding_id=finding_id,
                event_id=event.get("event_id"),
                event_type="network",
                evidence_type="outbound_connection",
                confidence=0.8,
                timestamp=event.get("timestamp"),
                details={"destination": event.get("details", {}).get("destination_ip")}
            ))
        
        if len(chain.evidence_links) >= 2:
            chain.exploitability_score = chain.calculate_exploitability()
            return chain
        
        return None
    
    def _build_path_traversal_chain(self, finding_id: str, syscall_events: List[Dict], file_events: List[Dict]) -> Optional[ExploitChain]:
        """Path traversal: finding + open(/etc) or similar sensitive path"""
        chain = ExploitChain(
            chain_id=self._generate_chain_id(finding_id, "path_traversal"),
            chain_type=ExploitChainType.PATH_TRAVERSAL,
            static_finding_id=finding_id,
            attack_scenario="Path traversal reaches sensitive system files"
        )
        
        # Look for open() of sensitive paths
        sensitive_paths = ["/etc/passwd", "/etc/shadow", "/root/.ssh", "C:\\Windows\\System32"]
        for event in syscall_events:
            if event.get("details", {}).get("syscall_name") == "openat":
                pathname = event.get("details", {}).get("pathname", "")
                if any(path in pathname for path in sensitive_paths):
                    chain.add_evidence(EvidenceLink(
                        finding_id=finding_id,
                        event_id=event.get("event_id"),
                        event_type="syscall",
                        evidence_type="open_sensitive_file",
                        confidence=0.95,
                        timestamp=event.get("timestamp"),
                        details={"file": pathname}
                    ))
        
        for event in file_events:
            path = event.get("details", {}).get("path", "")
            if any(sensitive in path for sensitive in sensitive_paths):
                chain.add_evidence(EvidenceLink(
                    finding_id=finding_id,
                    event_id=event.get("event_id"),
                    event_type="file_access",
                    evidence_type="sensitive_file_access",
                    confidence=0.9,
                    timestamp=event.get("timestamp"),
                    details={"file": path}
                ))
        
        if len(chain.evidence_links) >= 1:
            chain.exploitability_score = chain.calculate_exploitability()
            return chain
        
        return None
    
    def _generate_chain_id(self, finding_id: str, chain_type: str) -> str:
        """Generate deterministic chain ID"""
        data = f"{finding_id}_{chain_type}".encode()
        return hashlib.sha256(data).hexdigest()[:16]
    
    def score_chain_confidence(self, chain: ExploitChain) -> float:
        """
        Calculate overall confidence in exploit chain.
        Based on evidence quality and completeness.
        """
        if not chain.evidence_links:
            return 0.0
        
        # Average confidence of all evidence
        avg_evidence_confidence = sum(link.confidence for link in chain.evidence_links) / len(chain.evidence_links)
        
        # Bonus for complete chain (multiple evidence types)
        evidence_types = set(link.event_type for link in chain.evidence_links)
        type_diversity_bonus = min(len(evidence_types) * 0.1, 0.3)
        
        return min(avg_evidence_confidence + type_diversity_bonus, 1.0)
