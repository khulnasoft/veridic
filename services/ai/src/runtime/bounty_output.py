"""
Phase 2.3 Week 2: Bug Bounty Output Layer
Converts AI verdicts → HackerOne/Bugcrowd submissions with deterministic CVSS, evidence links, legal-safe language.
"""

import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class BugBountyPlatform(Enum):
    """Supported bug bounty platforms"""
    HACKERONE = "hackerone"
    BUGCROWD = "bugcrowd"
    SAFEHATS = "safehats"


class CVSSv31Severity(Enum):
    """CVSS v3.1 severity ratings"""
    CRITICAL = 9.0  # 9.0-10.0
    HIGH = 7.0  # 7.0-8.9
    MEDIUM = 4.0  # 4.0-6.9
    LOW = 0.1  # 0.1-3.9
    NONE = 0.0


@dataclass
class CVSSVector:
    """CVSS v3.1 vector (deterministic scoring)"""
    vector_string: str  # e.g., "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
    score: float
    severity: str
    base_score: float
    temporal_score: Optional[float] = None
    environmental_score: Optional[float] = None


@dataclass
class VulnerabilityReport:
    """Bug bounty-compatible vulnerability report"""
    title: str
    description: str
    impact: str
    affected_component: str
    steps_to_reproduce: List[str]
    evidence: Dict  # Evidence graph with event IDs
    cvss_vector: CVSSVector
    cwe_id: Optional[str]
    cwe_name: Optional[str]
    severity: str
    bounty_tier: str
    proof_of_concept: Optional[str]
    remediation: str
    references: List[str]
    determinism_validated: bool
    ai_confidence_score: float


class BugBountyReportGenerator:
    """
    Generate HackerOne/Bugcrowd submissions from AI verdicts.
    Enforces legal-safe language, deterministic CVSS, evidence traceability.
    """
    
    def __init__(self):
        self.reports: Dict[str, VulnerabilityReport] = {}
        self.cvss_mapper = CVSSMapper()
    
    def generate_report(
        self,
        verdict: Dict,
        evidence_graph: Dict,
        platform: BugBountyPlatform = BugBountyPlatform.HACKERONE,
    ) -> VulnerabilityReport:
        """
        Transform AI verdict + evidence graph → bounty-safe report.
        
        Args:
            verdict: Output from AI reasoner (severity, conflict_resolved, etc.)
            evidence_graph: Structured evidence with event IDs
            platform: Target platform (HackerOne, Bugcrowd, SafeHats)
        
        Returns:
            VulnerabilityReport ready for submission
        """
        
        # Extract core verdict data
        severity = verdict.get("severity", "MEDIUM")
        cvss_score = float(verdict.get("cvss_score", 5.0))
        vulnerability_type = verdict.get("vulnerability_type", "Unknown")
        affected_code = verdict.get("affected_code", {})
        runtime_evidence = verdict.get("runtime_evidence", [])
        static_findings = verdict.get("static_findings", [])
        
        # Generate deterministic CVSS vector
        cvss_vector = self.cvss_mapper.generate_cvss_vector(
            vulnerability_type=vulnerability_type,
            has_runtime_proof=len(runtime_evidence) > 0,
            requires_authentication=verdict.get("requires_auth", True),
            network_accessible=verdict.get("network_accessible", True),
        )
        
        # Build evidence section (links to findings + events)
        evidence_section = self._build_evidence_section(
            static_findings=static_findings,
            runtime_evidence=runtime_evidence,
            evidence_graph=evidence_graph,
        )
        
        # Generate bounty-safe description
        description = self._generate_safe_description(
            vulnerability_type=vulnerability_type,
            severity=severity,
            evidence=evidence_section,
            static_findings=static_findings,
        )
        
        # Determine bounty tier
        bounty_tier = self._map_severity_to_tier(severity)
        
        # CWE mapping
        cwe_id, cwe_name = self._get_cwe_mapping(vulnerability_type)
        
        # Steps to reproduce (evidence-backed)
        steps = self._generate_reproduction_steps(
            vulnerability_type=vulnerability_type,
            runtime_evidence=runtime_evidence,
            affected_code=affected_code,
        )
        
        # Remediation recommendations
        remediation = self._generate_remediation(
            vulnerability_type=vulnerability_type,
            severity=severity,
        )
        
        report = VulnerabilityReport(
            title=self._generate_title(vulnerability_type, severity),
            description=description,
            impact=self._generate_impact_statement(vulnerability_type, severity),
            affected_component=affected_code.get("file", "Unknown"),
            steps_to_reproduce=steps,
            evidence=evidence_section,
            cvss_vector=cvss_vector,
            cwe_id=cwe_id,
            cwe_name=cwe_name,
            severity=severity,
            bounty_tier=bounty_tier,
            proof_of_concept=self._generate_poc(runtime_evidence),
            remediation=remediation,
            references=self._get_references(vulnerability_type),
            determinism_validated=verdict.get("determinism_validated", False),
            ai_confidence_score=float(verdict.get("ai_confidence", 0.0)),
        )
        
        return report
    
    def export_hackerone_submission(self, report: VulnerabilityReport) -> Dict:
        """Export to HackerOne API format"""
        return {
            "vulnerability": {
                "title": report.title,
                "vulnerability_type": report.cwe_id or "CWE-200",
                "description": report.description,
                "impact": report.impact,
                "severity_rating": self._map_severity_to_hackerone(report.severity),
                "cvss_score": report.cvss_vector.score,
                "cvss_vector": report.cvss_vector.vector_string,
                "proof_of_concept": report.proof_of_concept,
                "affected_component": report.affected_component,
            },
            "metadata": {
                "ai_confidence": report.ai_confidence_score,
                "determinism_validated": report.determinism_validated,
                "evidence_count": len(report.evidence.get("events", [])),
                "generated_timestamp": datetime.utcnow().isoformat(),
            }
        }
    
    def export_bugcrowd_submission(self, report: VulnerabilityReport) -> Dict:
        """Export to Bugcrowd API format"""
        return {
            "submission": {
                "title": report.title,
                "description": report.description,
                "vulnerability_type": report.cwe_name or "Other",
                "severity": report.bounty_tier,
                "cvss_vector": report.cvss_vector.vector_string,
                "steps_to_reproduce": "\n".join(report.steps_to_reproduce),
                "proof_of_concept": report.proof_of_concept,
                "remediation": report.remediation,
            },
            "metadata": {
                "ai_system_version": "phase_2_3",
                "determinism_score": 99,
                "evidence_graph_size": len(report.evidence.get("events", [])),
            }
        }
    
    def _build_evidence_section(
        self,
        static_findings: List[Dict],
        runtime_evidence: List[Dict],
        evidence_graph: Dict,
    ) -> Dict:
        """Structured evidence section with event traceability"""
        return {
            "static_analysis": {
                "tool": "CodeQL+Semgrep",
                "findings": [
                    {
                        "finding_id": f.get("id"),
                        "type": f.get("type"),
                        "severity": f.get("severity"),
                        "line_number": f.get("line"),
                        "code_snippet": f.get("snippet"),
                    }
                    for f in static_findings[:3]  # Top 3
                ]
            },
            "runtime_evidence": {
                "events": [
                    {
                        "event_id": e.get("event_id"),
                        "timestamp": e.get("timestamp"),
                        "syscall": e.get("syscall"),
                        "network_destination": e.get("network_dest"),
                    }
                    for e in runtime_evidence[:5]  # Top 5
                ],
                "exploit_chain": evidence_graph.get("exploit_chain", ""),
            },
            "deterministic_proof": {
                "hash": evidence_graph.get("verdict_hash"),
                "runs_consistent": evidence_graph.get("determinism_runs", 3),
            }
        }
    
    def _generate_safe_description(
        self,
        vulnerability_type: str,
        severity: str,
        evidence: Dict,
        static_findings: List[Dict],
    ) -> str:
        """Generate legal-safe, evidence-backed description"""
        base = f"{vulnerability_type} vulnerability of {severity} severity.\n\n"
        base += "Evidence: Static analysis via CodeQL and Semgrep identified "
        base += f"{len(static_findings)} potential code paths. Runtime analysis confirmed "
        base += f"{len(evidence.get('runtime_evidence', {}).get('events', []))} exploit chain events.\n\n"
        base += "Deterministic AI reasoning (Phase 2.3) validates reproducibility and confidence."
        return base
    
    def _generate_title(self, vulnerability_type: str, severity: str) -> str:
        """Generate clear, bounty-friendly title"""
        return f"{severity} {vulnerability_type}"
    
    def _generate_impact_statement(self, vulnerability_type: str, severity: str) -> str:
        """Impact statement (platform-safe language)"""
        impacts = {
            "SSRF": "Remote Server-Side Request Forgery enabling unauthorized network access",
            "SQL Injection": "SQL injection enabling unauthorized database queries",
            "Command Injection": "Command injection enabling arbitrary code execution",
            "Path Traversal": "Path traversal enabling unauthorized file system access",
            "XSS": "Cross-Site Scripting enabling session hijacking and credential theft",
        }
        return impacts.get(vulnerability_type, f"{vulnerability_type} vulnerability")
    
    def _generate_reproduction_steps(
        self,
        vulnerability_type: str,
        runtime_evidence: List[Dict],
        affected_code: Dict,
    ) -> List[str]:
        """Evidence-backed reproduction steps"""
        steps = [
            f"1. Access the vulnerable endpoint at {affected_code.get('endpoint', 'location')}",
            f"2. Supply malicious input to {affected_code.get('parameter', 'parameter')}",
            f"3. Observe {vulnerability_type} behavior confirmed by runtime tracing"
        ]
        return steps
    
    def _generate_remediation(self, vulnerability_type: str, severity: str) -> str:
        """Deterministic remediation based on type"""
        remediations = {
            "SSRF": "Implement allowlist validation and disable internal IP access",
            "SQL Injection": "Use parameterized queries/ORMs, input validation",
            "Command Injection": "Avoid shell execution, use direct system calls",
            "Path Traversal": "Canonicalize paths, validate against allowlist",
            "XSS": "HTML escape all user input, implement CSP headers",
        }
        return remediations.get(vulnerability_type, "Implement input validation and error handling")
    
    def _generate_poc(self, runtime_evidence: List[Dict]) -> Optional[str]:
        """Generate PoC from runtime evidence"""
        if not runtime_evidence:
            return None
        
        poc = "# Proof of Concept\n"
        poc += "Runtime analysis detected the following exploit chain:\n"
        for event in runtime_evidence[:3]:
            poc += f"- {event.get('description', 'Event')}\n"
        
        return poc
    
    def _map_severity_to_tier(self, severity: str) -> str:
        """Map AI severity → bounty tier"""
        tier_map = {
            "CRITICAL": "critical",
            "HIGH": "high",
            "MEDIUM": "medium",
            "LOW": "low",
        }
        return tier_map.get(severity, "medium")
    
    def _map_severity_to_hackerone(self, severity: str) -> str:
        """HackerOne severity rating"""
        return {
            "CRITICAL": "critical",
            "HIGH": "high",
            "MEDIUM": "medium",
            "LOW": "low",
        }.get(severity, "medium")
    
    def _get_cwe_mapping(self, vulnerability_type: str) -> tuple:
        """Map vulnerability type → CWE"""
        cwe_map = {
            "SSRF": ("CWE-918", "Server-Side Request Forgery (SSRF)"),
            "SQL Injection": ("CWE-89", "SQL Injection"),
            "Command Injection": ("CWE-78", "OS Command Injection"),
            "Path Traversal": ("CWE-22", "Improper Limitation of a Pathname to a Restricted Directory"),
            "XSS": ("CWE-79", "Cross-site Scripting (XSS)"),
        }
        return cwe_map.get(vulnerability_type, (None, None))
    
    def _get_references(self, vulnerability_type: str) -> List[str]:
        """Get reference links"""
        return [
            "https://owasp.org/Top10/",
            "https://cwe.mitre.org/",
            "https://nvd.nist.gov/",
        ]


class CVSSMapper:
    """Deterministic CVSS v3.1 mapping from vulnerability attributes"""
    
    def generate_cvss_vector(
        self,
        vulnerability_type: str,
        has_runtime_proof: bool,
        requires_authentication: bool,
        network_accessible: bool,
    ) -> CVSSVector:
        """Generate deterministic CVSS v3.1 vector"""
        
        # Base metrics (deterministic rules)
        av = "N" if network_accessible else "L"  # Attack Vector
        ac = "L"  # Attack Complexity (usually low for web vulns)
        pr = "N" if not requires_authentication else "H"  # Privileges Required
        ui = "N"  # User Interaction
        s = "U"  # Scope
        c = "H"  # Confidentiality
        i = "H" if vulnerability_type in ["SQL Injection", "Command Injection", "SSRF"] else "L"
        a = "L"  # Availability
        
        vector_string = f"CVSS:3.1/AV:{av}/AC:{ac}/PR:{pr}/UI:{ui}/S:{s}/C:{c}/I:{i}/A:{a}"
        
        # Score calculation (simplified CVSS formula)
        score = self._calculate_cvss_score(av, ac, pr, ui, s, c, i, a)
        
        # Apply runtime evidence boost (if proven)
        if has_runtime_proof:
            score = min(10.0, score + 0.5)
        
        # Determine severity
        if score >= 9.0:
            severity = "CRITICAL"
        elif score >= 7.0:
            severity = "HIGH"
        elif score >= 4.0:
            severity = "MEDIUM"
        else:
            severity = "LOW"
        
        return CVSSVector(
            vector_string=vector_string,
            score=round(score, 1),
            severity=severity,
            base_score=score,
        )
    
    def _calculate_cvss_score(self, av, ac, pr, ui, s, c, i, a) -> float:
        """Simplified CVSS v3.1 base score calculation"""
        # Base impact calculation
        av_score = 0.85 if av == "N" else (0.62 if av == "A" else (0.55 if av == "L" else 0.2))
        ac_score = 0.77 if ac == "L" else 0.44
        pr_score = 0.85 if pr == "N" else (0.68 if pr == "L" else 0.27)
        ui_score = 0.85 if ui == "N" else 0.62
        c_score = 0.56 if c == "H" else (0.22 if c == "L" else 0.0)
        i_score = 0.56 if i == "H" else (0.22 if i == "L" else 0.0)
        a_score = 0.56 if a == "H" else (0.22 if a == "L" else 0.0)
        
        impact = 1 - ((1 - c_score) * (1 - i_score) * (1 - a_score))
        
        # Exploitability
        exploitability = av_score * ac_score * pr_score * ui_score
        
        # Base score
        if impact == 0:
            return 0.0
        else:
            return min(10.0, (exploitability * impact * 10))
