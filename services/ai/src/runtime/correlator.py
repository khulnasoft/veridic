"""
Phase 2.0: Correlation Model (Stateless)
Links static findings to runtime events.
No state — accepts findings, events, returns correlations.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class VulnerabilityCategory(Enum):
    """Classification for correlation matching"""
    INJECTION = "injection"
    SSRF = "ssrf"
    PATH_TRAVERSAL = "path_traversal"
    AUTH_BYPASS = "auth_bypass"
    RACE_CONDITION = "race_condition"
    MEMORY_UNSAFE = "memory_unsafe"
    TIMING_ORACLE = "timing_oracle"
    XSS = "xss"
    CSRF = "csrf"
    XXEXML = "xxe_xml"


@dataclass
class CorrelationRule:
    """Rule for matching events to static findings"""
    finding_type: str
    event_sources: List[str]  # ebpf, mitmproxy, etc.
    matchers: List[str]  # Patterns to match
    confidence_boost: float  # 0-1


class CorrelationModel:
    """
    Stateless correlation engine.
    Maps runtime events → static findings → exploitability scoring.
    """
    
    def __init__(self):
        self.rules = self._build_rules()
        self.logger = logging.getLogger(__name__)
    
    def _build_rules(self) -> dict:
        """Define correlation rules (no engine coupling)"""
        return {
            "sql_injection": CorrelationRule(
                finding_type="sql_injection",
                event_sources=["mitmproxy"],
                matchers=["UNION SELECT", "DROP TABLE", "'; --", "OR 1=1"],
                confidence_boost=0.3,
            ),
            "ssrf": CorrelationRule(
                finding_type="ssrf",
                event_sources=["mitmproxy"],
                matchers=["localhost", "127.0.0.1", "169.254.169.254"],
                confidence_boost=0.4,
            ),
            "path_traversal": CorrelationRule(
                finding_type="path_traversal",
                event_sources=["ebpf"],
                matchers=["../", "..\\", "/etc/passwd"],
                confidence_boost=0.35,
            ),
            "xss": CorrelationRule(
                finding_type="xss",
                event_sources=["mitmproxy"],
                matchers=["<script>", "javascript:", "onclick="],
                confidence_boost=0.25,
            ),
            "race_condition": CorrelationRule(
                finding_type="race_condition",
                event_sources=["ebpf"],
                matchers=["clone", "fork", "pthread_create"],
                confidence_boost=0.2,
            ),
        }
    
    def correlate(
        self,
        static_findings: List[dict],
        runtime_events: List[dict],
    ) -> List[dict]:
        """
        Core correlation logic: map events to findings.
        Returns enriched findings with exploitability scores.
        """
        correlated = []
        
        for finding in static_findings:
            finding_type = finding.get("type", "").lower()
            supporting_events = []
            max_confidence = 0.0
            
            # Match events to this finding
            for event in runtime_events:
                event_source = event.get("source", "")
                event_details = event.get("details", {})
                
                match_score = self._match_event_to_finding(
                    finding_type, event_source, event_details
                )
                
                if match_score > 0:
                    supporting_events.append({
                        "event_id": event.get("event_id"),
                        "match_score": match_score,
                        "source": event_source,
                    })
                    max_confidence = max(max_confidence, match_score)
            
            # Compute exploitability
            exploitability = self._compute_exploitability(
                finding_type, supporting_events, finding.get("severity")
            )
            
            correlated.append({
                "finding_id": finding.get("id"),
                "original_type": finding.get("type"),
                "original_severity": finding.get("severity"),
                "supporting_events": supporting_events,
                "exploitability_score": exploitability,
                "event_count": len(supporting_events),
                "max_confidence": max_confidence,
            })
        
        return correlated
    
    def _match_event_to_finding(
        self,
        finding_type: str,
        event_source: str,
        event_details: dict,
    ) -> float:
        """
        Score how well this event matches the finding.
        Returns confidence 0-1.
        """
        if finding_type not in self.rules:
            return 0.0
        
        rule = self.rules[finding_type]
        
        # Source must be relevant
        if event_source not in rule.event_sources:
            return 0.0
        
        # Check matchers in event details
        match_count = 0
        for matcher in rule.matchers:
            event_str = str(event_details).lower()
            if matcher.lower() in event_str:
                match_count += 1
        
        if match_count == 0:
            return 0.0
        
        # Score proportional to matches
        match_ratio = match_count / len(rule.matchers)
        return min(1.0, rule.confidence_boost + (match_ratio * 0.5))
    
    def _compute_exploitability(
        self,
        finding_type: str,
        supporting_events: List[dict],
        original_severity: str,
    ) -> float:
        """
        Compute exploitability score 0-100.
        Based on event count and match confidence.
        """
        if not supporting_events:
            return 0.0
        
        # Evidence-based scoring
        event_count = len(supporting_events)
        avg_confidence = sum(e["match_score"] for e in supporting_events) / event_count
        
        # Adjust by severity
        severity_multiplier = {
            "Critical": 1.0,
            "High": 0.85,
            "Medium": 0.7,
            "Low": 0.5,
            "Info": 0.3,
        }.get(original_severity, 0.5)
        
        # 1 event = 20, 5+ events = 80
        event_score = min(80.0, event_count * 20.0)
        confidence_score = avg_confidence * 100.0
        
        final_score = (event_score + confidence_score) / 2.0
        return final_score * severity_multiplier


@dataclass
class CorrelationResult:
    """Result of correlation analysis"""
    finding_id: str
    original_severity: str
    supporting_event_count: int
    exploitability_score: float  # 0-100
    max_event_confidence: float  # 0-1
    is_exploitable: bool  # >60 threshold
    
    def to_dict(self):
        return {
            "finding_id": self.finding_id,
            "original_severity": self.original_severity,
            "supporting_event_count": self.supporting_event_count,
            "exploitability_score": self.exploitability_score,
            "max_event_confidence": self.max_event_confidence,
            "is_exploitable": self.is_exploitable,
        }
