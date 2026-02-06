"""
Phase 2.3: AI Reasoning Input Contract
Defines canonical JSON format for evidence graphs entering AI reasoning.
Enforces strict determinism: same evidence → same verdict (no variance).
Also includes "AI cannot introduce new facts" schema validation.
"""

import json
import hashlib
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any, Set
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class Severity(Enum):
    """Standard severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VerdictType(Enum):
    """AI verdict outcomes"""
    CONFIRMED = "confirmed"  # Evidence supports finding
    UPGRADED = "upgraded"  # Runtime evidence makes worse
    DOWNGRADED = "downgraded"  # Runtime evidence shows benign
    CONFLICTED = "conflicted"  # Cannot reconcile evidence
    INSUFFICIENT = "insufficient"  # Not enough evidence


@dataclass
class StaticFinding:
    """Static analysis finding (Phase 1)"""
    finding_id: str
    type: str  # sql_injection, xss, path_traversal, etc.
    severity: Severity
    line_number: int
    file_path: str
    code_snippet: str
    cwe_id: str
    
    def to_dict(self) -> Dict:
        return {
            "finding_id": self.finding_id,
            "type": self.type,
            "severity": self.severity.value,
            "line_number": self.line_number,
            "file_path": self.file_path,
            "code_snippet": self.code_snippet,
            "cwe_id": self.cwe_id
        }


@dataclass
class RuntimeEvidence:
    """Single runtime event (Phase 2.1 or 2.2)"""
    event_id: str
    event_type: str  # syscall, network, file_access
    syscall_name: Optional[str]  # execve, openat, connect, etc.
    timestamp_ns: int
    process_pid: int
    details: Dict[str, Any]  # syscall args, network headers, etc.
    confidence: float = 1.0  # Always 1.0 for kernel data
    
    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "syscall_name": self.syscall_name,
            "timestamp_ns": self.timestamp_ns,
            "process_pid": self.process_pid,
            "details": self.details,
            "confidence": self.confidence
        }


@dataclass
class EvidenceChain:
    """Complete chain linking static + runtime"""
    chain_id: str
    chain_type: str  # ssrf, command_injection, data_exfiltration, etc.
    static_finding: StaticFinding
    evidence: List[RuntimeEvidence]
    exploitability_score: float = 0.0  # 0-100
    
    def to_dict(self) -> Dict:
        return {
            "chain_id": self.chain_id,
            "chain_type": self.chain_type,
            "static_finding": self.static_finding.to_dict(),
            "evidence": [e.to_dict() for e in self.evidence],
            "exploitability_score": self.exploitability_score
        }


@dataclass
class AIReasoningInput:
    """Canonical input for AI reasoning (deterministic, hashable)"""
    sandbox_session_id: str
    findings: List[StaticFinding]
    evidence_chains: List[EvidenceChain]
    conflicting_findings: List[tuple] = None  # (finding1_id, finding2_id, conflict_type)
    
    def __post_init__(self):
        if self.conflicting_findings is None:
            self.conflicting_findings = []
    
    def to_dict(self) -> Dict:
        """Convert to deterministic dict (sorted keys, ordered lists)"""
        return {
            "sandbox_session_id": self.sandbox_session_id,
            "findings": sorted([f.to_dict() for f in self.findings], key=lambda x: x["finding_id"]),
            "evidence_chains": sorted([c.to_dict() for c in self.evidence_chains], key=lambda x: x["chain_id"]),
            "conflicting_findings": sorted(self.conflicting_findings, key=lambda x: (x[0], x[1]))
        }
    
    def to_json(self, sort_keys: bool = True) -> str:
        """Serialize to deterministic JSON (required for hashing)"""
        return json.dumps(self.to_dict(), sort_keys=sort_keys, separators=(',', ':'))
    
    def compute_hash(self) -> str:
        """SHA256 of input for reproducibility tracking"""
        return hashlib.sha256(self.to_json().encode()).hexdigest()


@dataclass
class AIReasoningOutput:
    """AI verdict (deterministic, hashable)"""
    sandbox_session_id: str
    findings_verdicts: Dict[str, Dict]  # finding_id → {verdict, severity, confidence, reasoning}
    conflicts_resolved: Dict[str, str]  # conflict_id → resolution_type
    new_facts_attempted: List[str] = None  # Hallucination guard: any new facts AI tried to introduce
    reasoning_hash: str = ""  # SHA256 of output for reproducibility
    
    def __post_init__(self):
        if self.new_facts_attempted is None:
            self.new_facts_attempted = []
    
    def to_dict(self) -> Dict:
        """Convert to deterministic dict"""
        return {
            "sandbox_session_id": self.sandbox_session_id,
            "findings_verdicts": self.findings_verdicts,
            "conflicts_resolved": self.conflicts_resolved,
            "new_facts_attempted": sorted(self.new_facts_attempted),
            "reasoning_hash": self.reasoning_hash
        }
    
    def to_json(self, sort_keys: bool = True) -> str:
        """Serialize to deterministic JSON"""
        return json.dumps(self.to_dict(), sort_keys=sort_keys, separators=(',', ':'))
    
    def compute_hash(self) -> str:
        """SHA256 of output for reproducibility tracking"""
        return hashlib.sha256(self.to_json().encode()).hexdigest()


class HallucinationGuard:
    """
    Schema validator that enforces:
    "AI cannot introduce new facts"
    
    Allowed references: static findings + runtime events in input
    Disallowed: references to events/findings not in input
    """
    
    def __init__(self, input_contract: AIReasoningInput):
        self.input_contract = input_contract
        self._allowed_finding_ids: Set[str] = {f.finding_id for f in input_contract.findings}
        self._allowed_event_ids: Set[str] = set()
        for chain in input_contract.evidence_chains:
            for event in chain.evidence:
                self._allowed_event_ids.add(event.event_id)
    
    def validate_output(self, output: AIReasoningOutput) -> tuple[bool, List[str]]:
        """
        Validate that output only references existing findings/events.
        Returns (is_valid, list_of_violations)
        """
        violations = []
        
        for finding_id, verdict in output.findings_verdicts.items():
            # Every verdict must reference a known finding
            if finding_id not in self._allowed_finding_ids:
                violations.append(f"Unknown finding referenced: {finding_id}")
            
            # Check reasoning for event references
            reasoning = verdict.get("reasoning", "")
            for event_id in self._allowed_event_ids:
                # If reasoning mentions an event, that's fine (it's in input)
                pass
            
            # Any mention of unknown event IDs is a hallucination
            for token in reasoning.split():
                if token.startswith("event_") and token not in self._allowed_event_ids:
                    violations.append(f"Hallucination: Unknown event referenced: {token}")
        
        return len(violations) == 0, violations


class DeterminismValidator:
    """
    Validates strict determinism:
    - Same input → same output (temperature=0 + fixed prompts)
    - Output hash must be deterministic
    - Variance detection (should be 0)
    """
    
    def __init__(self, input_hash: str, first_output: AIReasoningOutput):
        self.input_hash = input_hash
        self.canonical_output_hash = first_output.compute_hash()
    
    def validate_consistency(self, output: AIReasoningOutput) -> tuple[bool, Optional[str]]:
        """
        Check if output matches canonical (strict determinism).
        Returns (is_consistent, error_message)
        """
        output_hash = output.compute_hash()
        if output_hash == self.canonical_output_hash:
            return True, None
        return False, f"Output hash mismatch: {output_hash} vs {self.canonical_output_hash}"
