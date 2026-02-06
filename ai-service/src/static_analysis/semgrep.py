"""
Semgrep integration for pattern-based AST vulnerability detection.
Lightweight alternative/complement to CodeQL.
"""

import json
import subprocess
import logging
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SemgrepFinding:
    check_id: str
    message: str
    line: int
    column: int
    severity: str  # "INFO" | "WARNING" | "ERROR"
    rule_source: str
    metadata: Dict[str, Any]


class SemgrepRunner:
    """Runs Semgrep pattern-based analysis on code."""
    
    def __init__(self, semgrep_api_url: str = "http://localhost:7953"):
        self.api_url = semgrep_api_url
        self.rule_packs = [
            "p/owasp-top-ten",
            "p/cwe-top-25",
            "p/security-audit",
            "p/ci",
        ]
    
    async def analyze(
        self,
        code: str,
        language: str,
        filename: str,
    ) -> List[SemgrepFinding]:
        """
        Run Semgrep analysis on code snippet.
        
        Args:
            code: Source code to analyze
            language: Programming language
            filename: Original filename
            
        Returns:
            List of Semgrep findings
        """
        logger.info(f"Starting Semgrep analysis for {language}: {filename}")
        
        try:
            # Map language to Semgrep language code
            lang_map = {
                "typescript": "ts",
                "javascript": "js",
                "python": "py",
                "go": "go",
                "java": "java",
                "cpp": "cpp",
                "csharp": "csharp",
                "rust": "rust",
            }
            
            semgrep_lang = lang_map.get(language.lower(), language.lower())
            
            # Build Semgrep command
            cmd = [
                "semgrep",
                "--json",
                "--config=" + ",".join(self.rule_packs),
                "--lang=" + semgrep_lang,
            ]
            
            # Run with code as stdin
            result = subprocess.run(
                cmd,
                input=code.encode(),
                capture_output=True,
                timeout=30,
            )
            
            findings = []
            try:
                output = json.loads(result.stdout.decode())
                
                for result in output.get("results", []):
                    finding = SemgrepFinding(
                        check_id=result.get("check_id", "unknown"),
                        message=result.get("extra", {}).get("message", result.get("check_id", "")),
                        line=result.get("start", {}).get("line", 0),
                        column=result.get("start", {}).get("col", 0),
                        severity=result.get("extra", {}).get("severity", "WARNING"),
                        rule_source=result.get("extra", {}).get("source", ""),
                        metadata=result.get("extra", {}),
                    )
                    findings.append(finding)
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error parsing Semgrep results: {e}")
            
            logger.info(f"Semgrep found {len(findings)} issues")
            return findings
            
        except subprocess.TimeoutExpired:
            logger.error("Semgrep analysis timed out")
            return []
        except Exception as e:
            logger.error(f"Semgrep analysis error: {e}")
            return []
    
    def to_dict(self, finding: SemgrepFinding) -> Dict[str, Any]:
        """Convert finding to dictionary format."""
        return {
            "tool": "semgrep",
            "check_id": finding.check_id,
            "message": finding.message,
            "line": finding.line,
            "column": finding.column,
            "severity": finding.severity,
            "rule_source": finding.rule_source,
            "metadata": finding.metadata,
        }
