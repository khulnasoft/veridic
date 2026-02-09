"""
Report generation and export for vulnerability findings.
Supports JSON, Markdown, and SARIF formats.
"""

import json
import logging
from typing import List, Dict, Any
from dataclasses import asdict
from datetime import datetime
from ..static_analysis.orchestrator import StaticFinding

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate structured vulnerability reports in multiple formats."""
    
    def __init__(self):
        self.timestamp = datetime.utcnow().isoformat()
    
    def generate_json_report(
        self,
        findings: List[StaticFinding],
        metadata: Dict[str, Any],
    ) -> str:
        """
        Generate JSON format report.
        
        Args:
            findings: List of vulnerability findings
            metadata: Code metadata (language, filename, etc.)
            
        Returns:
            JSON report as string
        """
        report = {
            "report_metadata": {
                "generated_at": self.timestamp,
                "tool_version": "1.0.0",
                "language": metadata.get("language"),
                "filename": metadata.get("filename"),
            },
            "summary": {
                "total_findings": len(findings),
                "critical": sum(1 for f in findings if f.severity == "critical"),
                "high": sum(1 for f in findings if f.severity == "high"),
                "medium": sum(1 for f in findings if f.severity == "medium"),
                "low": sum(1 for f in findings if f.severity == "low"),
            },
            "findings": [
                {
                    **asdict(f),
                    "id": f"VULN-{metadata.get('filename')}-{f.line}",
                }
                for f in findings
            ],
        }
        
        return json.dumps(report, indent=2)
    
    def generate_markdown_report(
        self,
        findings: List[StaticFinding],
        metadata: Dict[str, Any],
    ) -> str:
        """
        Generate Markdown format report for human review.
        
        Args:
            findings: List of vulnerability findings
            metadata: Code metadata
            
        Returns:
            Markdown report as string
        """
        lines = [
            "# Security Analysis Report",
            f"\nGenerated: {self.timestamp}",
            f"\nFile: `{metadata.get('filename')}`",
            f"Language: `{metadata.get('language')}`",
            "",
            "## Summary",
            f"- Total Issues: {len(findings)}",
            f"- Critical: {sum(1 for f in findings if f.severity == 'critical')}",
            f"- High: {sum(1 for f in findings if f.severity == 'high')}",
            f"- Medium: {sum(1 for f in findings if f.severity == 'medium')}",
            f"- Low: {sum(1 for f in findings if f.severity == 'low')}",
            "",
            "## Detailed Findings",
            "",
        ]
        
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_findings = sorted(
            findings,
            key=lambda f: severity_order.get(f.severity, 4)
        )
        
        for i, finding in enumerate(sorted_findings, 1):
            lines.extend([
                f"### {i}. {finding.type.upper()}",
                f"- **Severity**: {finding.severity.upper()}",
                f"- **Tool**: {finding.tool}",
                f"- **Line**: {finding.line}",
                f"- **Confidence**: {finding.confidence:.1%}",
                "",
                f"**Message**: {finding.message}",
                "",
                f"**Code Snippet**:",
                "```",
                finding.code_snippet,
                "```",
                "",
                f"**Remediation**: {finding.remediation_hint}",
                "",
            ])
        
        return "\n".join(lines)
    
    def generate_sarif_report(
        self,
        findings: List[StaticFinding],
        metadata: Dict[str, Any],
    ) -> str:
        """
        Generate SARIF format report for IDE integration.
        
        Args:
            findings: List of vulnerability findings
            metadata: Code metadata
            
        Returns:
            SARIF report as string
        """
        sarif_results = []
        
        for finding in findings:
            sarif_result = {
                "ruleId": finding.rule_id,
                "message": {
                    "text": finding.message,
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": metadata.get("filename", "unknown"),
                            },
                            "region": {
                                "startLine": finding.line,
                                "startColumn": finding.column,
                            },
                        },
                    }
                ],
                "level": self._severity_to_sarif_level(finding.severity),
                "properties": {
                    "confidence": finding.confidence,
                    "tool": finding.tool,
                    "remediation": finding.remediation_hint,
                },
            }
            sarif_results.append(sarif_result)
        
        sarif_output = {
            "version": "2.1.0",
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "MCP Bug Bounty Server",
                            "version": "1.0.0",
                        },
                    },
                    "results": sarif_results,
                }
            ],
        }
        
        return json.dumps(sarif_output, indent=2)
    
    def _severity_to_sarif_level(self, severity: str) -> str:
        """Map severity to SARIF level."""
        level_map = {
            "critical": "error",
            "high": "error",
            "medium": "warning",
            "low": "note",
        }
        return level_map.get(severity, "warning")
