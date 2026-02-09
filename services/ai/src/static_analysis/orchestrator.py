"""
Static Analysis Orchestrator - coordinates CodeQL, Semgrep, and AST extraction.
"""

import json
import logging
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from .codeql import CodeQLRunner, CodeQLFinding
from .semgrep import SemgrepRunner, SemgrepFinding

logger = logging.getLogger(__name__)


@dataclass
class StaticFinding:
    """Unified finding format across all static analysis tools."""
    tool: str  # "codeql" | "semgrep" | "ast"
    rule_id: str
    type: str  # "sql_injection" | "xss" | "race_condition" | etc.
    message: str
    line: int
    column: int
    confidence: float  # 0.0 - 1.0
    severity: str  # "critical" | "high" | "medium" | "low"
    code_snippet: str
    remediation_hint: str


class StaticAnalysisOrchestrator:
    """Coordinates all static analysis tools and deduplicates findings."""
    
    def __init__(self):
        self.codeql = CodeQLRunner()
        self.semgrep = SemgrepRunner()
        self.vulnerability_type_map = {
            "sql-injection": "sql_injection",
            "xss": "xss",
            "path-traversal": "path_traversal",
            "command-injection": "command_injection",
            "insecure-deserialization": "insecure_deserialization",
            "hardcoded-secret": "hardcoded_secret",
            "weak-cryptography": "weak_cryptography",
            "race-condition": "race_condition",
            "buffer-overflow": "buffer_overflow",
            "use-after-free": "use_after_free",
        }
    
    async def analyze(
        self,
        code: str,
        language: str,
        filename: str,
        include_codeql: bool = True,
        include_semgrep: bool = True,
    ) -> List[StaticFinding]:
        """
        Run all enabled static analysis tools on code.
        
        Args:
            code: Source code to analyze
            language: Programming language
            filename: Original filename
            include_codeql: Whether to run CodeQL
            include_semgrep: Whether to run Semgrep
            
        Returns:
            Deduplicated list of findings
        """
        logger.info(f"Starting orchestrated static analysis for {language}: {filename}")
        
        all_findings = []
        
        # Run CodeQL
        if include_codeql:
            try:
                codeql_findings = await self.codeql.analyze(code, language, filename)
                for finding in codeql_findings:
                    static_finding = self._codeql_to_static(finding, code)
                    all_findings.append(static_finding)
            except Exception as e:
                logger.error(f"CodeQL analysis failed: {e}")
        
        # Run Semgrep
        if include_semgrep:
            try:
                semgrep_findings = await self.semgrep.analyze(code, language, filename)
                for finding in semgrep_findings:
                    static_finding = self._semgrep_to_static(finding, code)
                    all_findings.append(static_finding)
            except Exception as e:
                logger.error(f"Semgrep analysis failed: {e}")
        
        # Deduplicate findings
        deduplicated = self._deduplicate(all_findings)
        logger.info(f"Found {len(deduplicated)} deduplicated findings")
        
        return deduplicated
    
    def _codeql_to_static(self, codeql_finding: CodeQLFinding, code: str) -> StaticFinding:
        """Convert CodeQL finding to StaticFinding format."""
        vuln_type = self.vulnerability_type_map.get(
            codeql_finding.rule_id.lower(),
            "unknown_vulnerability"
        )
        
        code_snippet = self._extract_snippet(code, codeql_finding.line)
        
        severity_map = {
            "error": "high",
            "warning": "medium",
            "note": "low",
        }
        
        return StaticFinding(
            tool="codeql",
            rule_id=codeql_finding.rule_id,
            type=vuln_type,
            message=codeql_finding.message,
            line=codeql_finding.line,
            column=codeql_finding.column,
            confidence=0.95,  # CodeQL has high confidence
            severity=severity_map.get(codeql_finding.severity, "medium"),
            code_snippet=code_snippet,
            remediation_hint=f"Review CodeQL rule: {codeql_finding.url}",
        )
    
    def _semgrep_to_static(self, semgrep_finding: SemgrepFinding, code: str) -> StaticFinding:
        """Convert Semgrep finding to StaticFinding format."""
        vuln_type = self.vulnerability_type_map.get(
            semgrep_finding.check_id.lower(),
            "unknown_vulnerability"
        )
        
        code_snippet = self._extract_snippet(code, semgrep_finding.line)
        
        severity_map = {
            "ERROR": "high",
            "WARNING": "medium",
            "INFO": "low",
        }
        
        return StaticFinding(
            tool="semgrep",
            rule_id=semgrep_finding.check_id,
            type=vuln_type,
            message=semgrep_finding.message,
            line=semgrep_finding.line,
            column=semgrep_finding.column,
            confidence=0.85,  # Semgrep slightly lower confidence
            severity=severity_map.get(semgrep_finding.severity, "medium"),
            code_snippet=code_snippet,
            remediation_hint=semgrep_finding.rule_source,
        )
    
    def _extract_snippet(self, code: str, line_number: int, context: int = 2) -> str:
        """Extract code snippet around the finding line."""
        lines = code.split("\n")
        start = max(0, line_number - context - 1)
        end = min(len(lines), line_number + context)
        snippet_lines = lines[start:end]
        return "\n".join(snippet_lines)
    
    def _deduplicate(self, findings: List[StaticFinding]) -> List[StaticFinding]:
        """Deduplicate findings by line + type, keeping highest confidence."""
        seen = {}
        
        for finding in findings:
            key = (finding.line, finding.type)
            
            if key not in seen:
                seen[key] = finding
            else:
                # Keep finding with higher confidence
                if finding.confidence > seen[key].confidence:
                    seen[key] = finding
        
        return list(seen.values())
    
    def to_dicts(self, findings: List[StaticFinding]) -> List[Dict[str, Any]]:
        """Convert findings to dictionary format."""
        return [asdict(f) for f in findings]
