"""
Tool Attribution Metrics
Measures which vulnerabilities are found by which tools and quantifies AI value.
"""

import json
from collections import Counter
from typing import Dict, List, Any, Set


class ToolAttributionAnalyzer:
    """Analyzes vulnerability discovery attribution across tools."""

    def __init__(self):
        self.stats = Counter()
        self.findings_by_tool = {}

    def analyze_findings(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Attribute each finding to its source tools.
        Categories:
        - codeql_only: Found only by CodeQL
        - semgrep_only: Found only by Semgrep
        - static_both: Found by both CodeQL and Semgrep
        - ai_correlated: Linked by AI reasoning
        - ai_only: Pure AI inference (no static tool found it)
        """
        self.stats.clear()
        self.findings_by_tool = {
            "codeql_only": [],
            "semgrep_only": [],
            "static_both": [],
            "ai_correlated": [],
            "ai_only": [],
        }

        for finding in findings:
            tools = set(finding.get("tools", []))
            finding_id = finding.get("id", "unknown")

            # Categorize by tool attribution
            if tools == {"codeql"}:
                self.stats["codeql_only"] += 1
                self.findings_by_tool["codeql_only"].append(finding_id)
            elif tools == {"semgrep"}:
                self.stats["semgrep_only"] += 1
                self.findings_by_tool["semgrep_only"].append(finding_id)
            elif tools == {"codeql", "semgrep"} or tools == {"semgrep", "codeql"}:
                self.stats["static_both"] += 1
                self.findings_by_tool["static_both"].append(finding_id)
            elif not tools:
                self.stats["ai_only"] += 1
                self.findings_by_tool["ai_only"].append(finding_id)

            # Check if AI enhanced the finding
            if finding.get("ai_enhanced"):
                self.stats["ai_correlated"] += 1
                if finding_id not in self.findings_by_tool["ai_correlated"]:
                    self.findings_by_tool["ai_correlated"].append(finding_id)

        return self.get_attribution_report()

    def get_attribution_report(self) -> Dict[str, Any]:
        """Generate comprehensive attribution report."""
        total_findings = sum(self.stats.values())

        # Calculate metrics
        static_coverage = self.stats["codeql_only"] + self.stats["semgrep_only"] + self.stats["static_both"]
        ai_value = self.stats["ai_only"] + self.stats["ai_correlated"]

        return {
            "total_findings": total_findings,
            "attribution": dict(self.stats),
            "by_category": self.findings_by_tool,
            "coverage": {
                "static_tools_coverage": round((static_coverage / total_findings * 100), 1) if total_findings else 0,
                "ai_added_findings": round((self.stats["ai_only"] / total_findings * 100), 1) if total_findings else 0,
                "ai_enhanced_findings": round((self.stats["ai_correlated"] / total_findings * 100), 1) if total_findings else 0,
            },
            "tool_effectiveness": {
                "codeql_independent": self.stats["codeql_only"],
                "semgrep_independent": self.stats["semgrep_only"],
                "complementary_findings": self.stats["static_both"],
            },
            "ai_value_score": self._calculate_ai_value_score(total_findings, ai_value),
        }

    def _calculate_ai_value_score(self, total: int, ai_value: int) -> float:
        """
        Score AI's contribution (0-100).
        Higher score = more valuable AI findings vs static tools.
        """
        if total == 0:
            return 0.0
        return round((ai_value / total) * 100, 1)

    def generate_complementarity_matrix(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Show how tools complement each other.
        High redundancy = tools finding same things
        Low redundancy = tools finding different things (good)
        """
        self.analyze_findings(findings)

        total = sum(self.stats.values())
        if total == 0:
            return {"error": "No findings to analyze"}

        redundancy_ratio = (
            self.stats["static_both"] / total * 100
        ) if total else 0

        return {
            "tool_overlap_percentage": round(redundancy_ratio, 1),
            "interpretation": {
                "high_overlap": "Tools are redundant - consider consolidating",
                "balanced": "Tools complement each other well",
                "low_overlap": "Tools find different vulnerabilities - keep both",
            }.get(
                "high_overlap" if redundancy_ratio > 50
                else "balanced" if redundancy_ratio > 25
                else "low_overlap"
            ),
            "recommendation": (
                "Leverage both tools for comprehensive coverage"
                if redundancy_ratio < 40
                else "Tools are highly redundant - focus on best performer"
            ),
        }


def generate_tool_attribution_report(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main entry point for tool attribution analysis.
    """
    analyzer = ToolAttributionAnalyzer()
    attribution = analyzer.analyze_findings(findings)
    complementarity = analyzer.generate_complementarity_matrix(findings)

    return {
        "status": "analyzed",
        "attribution_metrics": attribution,
        "complementarity_analysis": complementarity,
        "interpretation": {
            "key_findings": [
                f"CodeQL found {attribution['attribution']['codeql_only']} unique vulnerabilities",
                f"Semgrep found {attribution['attribution']['semgrep_only']} unique vulnerabilities",
                f"Both tools found {attribution['attribution']['static_both']} overlapping vulnerabilities",
                f"AI reasoning added {attribution['attribution']['ai_only']} new findings",
                f"AI correlated {attribution['attribution']['ai_correlated']} vulnerabilities",
            ]
        }
    }


if __name__ == "__main__":
    # Example usage
    sample_findings = [
        {
            "id": "VULN-001",
            "type": "sql_injection",
            "tools": ["codeql"],
            "ai_enhanced": False,
            "confidence": 0.95,
        },
        {
            "id": "VULN-002",
            "type": "xss",
            "tools": ["semgrep"],
            "ai_enhanced": False,
            "confidence": 0.88,
        },
        {
            "id": "VULN-003",
            "type": "path_traversal",
            "tools": ["codeql", "semgrep"],
            "ai_enhanced": True,
            "confidence": 0.92,
        },
        {
            "id": "VULN-004",
            "type": "race_condition",
            "tools": [],
            "ai_enhanced": True,
            "confidence": 0.75,
        },
    ]

    report = generate_tool_attribution_report(sample_findings)
    print(json.dumps(report, indent=2))
