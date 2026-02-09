"""
CodeQL integration for semantic vulnerability detection.
Supports: C#, C++, Go, Java, JavaScript, Python, Ruby
"""

import json
import subprocess
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CodeQLFinding:
    rule_id: str
    rule_name: str
    message: str
    line: int
    column: int
    url: str
    severity: str  # "error" | "warning" | "note"


class CodeQLRunner:
    """Runs CodeQL queries against code to detect vulnerabilities."""
    
    def __init__(self, codeql_path: str = "codeql"):
        self.codeql_path = codeql_path
        self.query_packs = {
            "javascript": "codeql/javascript-queries",
            "typescript": "codeql/javascript-queries",
            "python": "codeql/python-queries",
            "go": "codeql/go-queries",
            "java": "codeql/java-queries",
            "cpp": "codeql/cpp-queries",
            "csharp": "codeql/csharp-queries",
        }
    
    async def analyze(
        self,
        code: str,
        language: str,
        filename: str,
    ) -> List[CodeQLFinding]:
        """
        Run CodeQL analysis on code snippet.
        
        Args:
            code: Source code to analyze
            language: Programming language (javascript, python, go, rust, etc.)
            filename: Original filename for context
            
        Returns:
            List of CodeQL findings
        """
        logger.info(f"Starting CodeQL analysis for {language}: {filename}")
        
        try:
            # Create temporary database
            db_path = f"/tmp/codeql_db_{language}_{id(code)}"
            source_file = f"/tmp/{filename}"
            
            # Write code to temp file
            Path(source_file).write_text(code)
            
            # Create CodeQL database
            cmd_create = [
                self.codeql_path,
                "database", "create",
                db_path,
                "--language", language,
                "--source-root", "/tmp",
            ]
            
            result = subprocess.run(
                cmd_create,
                capture_output=True,
                timeout=30,
            )
            
            if result.returncode != 0:
                logger.warning(f"CodeQL database creation failed: {result.stderr.decode()}")
                return []
            
            # Run queries
            query_pack = self.query_packs.get(language)
            if not query_pack:
                logger.warning(f"No query pack for language: {language}")
                return []
            
            cmd_analyze = [
                self.codeql_path,
                "database", "analyze",
                db_path,
                query_pack,
                "--format=json",
                "--output=/tmp/codeql_results.json",
            ]
            
            result = subprocess.run(
                cmd_analyze,
                capture_output=True,
                timeout=60,
            )
            
            # Parse results
            findings = []
            try:
                with open("/tmp/codeql_results.json") as f:
                    results = json.load(f)
                
                for run in results.get("runs", []):
                    for result in run.get("results", []):
                        for location in result.get("locations", []):
                            finding = CodeQLFinding(
                                rule_id=result.get("ruleId", "unknown"),
                                rule_name=result.get("message", {}).get("text", "Unknown"),
                                message=result.get("message", {}).get("text", ""),
                                line=location.get("physicalLocation", {})
                                    .get("region", {})
                                    .get("startLine", 0),
                                column=location.get("physicalLocation", {})
                                    .get("region", {})
                                    .get("startColumn", 0),
                                url=result.get("ruleId", ""),
                                severity=result.get("level", "warning"),
                            )
                            findings.append(finding)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.error(f"Error parsing CodeQL results: {e}")
            
            logger.info(f"CodeQL found {len(findings)} issues")
            return findings
            
        except subprocess.TimeoutExpired:
            logger.error("CodeQL analysis timed out")
            return []
        except Exception as e:
            logger.error(f"CodeQL analysis error: {e}")
            return []
    
    def to_dict(self, finding: CodeQLFinding) -> Dict[str, Any]:
        """Convert finding to dictionary format."""
        return {
            "tool": "codeql",
            "rule_id": finding.rule_id,
            "rule_name": finding.rule_name,
            "message": finding.message,
            "line": finding.line,
            "column": finding.column,
            "severity": finding.severity,
            "url": finding.url,
        }
