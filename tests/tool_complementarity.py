#!/usr/bin/env python3
"""
Tool Complementarity Analysis for Phase 1

Analyzes how CodeQL, Semgrep, and AST extraction complement each other.
Metrics:
- Coverage: what vulnerabilities each tool detects
- Overlap: duplicate detections across tools
- Uniqueness: findings only one tool detects
- Efficiency: accuracy vs analysis time tradeoff
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolMetrics:
    tool_name: str
    findings_count: int
    unique_findings: int
    overlap_with_others: int
    accuracy_rate: float
    avg_confidence: float
    analysis_time_ms: int
    false_positive_rate: float


@dataclass
class ComplementarityReport:
    total_vulnerabilities_found: int
    total_unique_vulnerabilities: int
    overlap_findings: int
    tool_metrics: List[ToolMetrics]
    coverage_matrix: Dict[str, List[str]]  # tool -> vulnerability types it detects
    redundancy_ratio: float  # 0.0-1.0, lower is better
    effectiveness_score: float  # 0.0-1.0, higher is better
    recommendations: List[str]


class ToolComplementarityAnalyzer:
    """Analyzes how well different analysis tools work together."""

    def __init__(self):
        self.tool_results: Dict[str, List[Dict]] = {}
        self.fixture_expectations = self._load_expectations()

    def _load_expectations(self) -> Dict[str, Dict]:
        """Load expected vulnerabilities from fixture_expectations.json"""
        expectations_file = Path(__file__).parent / "fixtures" / "fixture_expectations.json"
        if expectations_file.exists():
            return json.loads(expectations_file.read_text())
        return {}

    def register_tool_results(self, tool_name: str, results: List[Dict]) -> None:
        """Register analysis results from a tool."""
        self.tool_results[tool_name] = results
        logger.info(f"Registered {len(results)} findings from {tool_name}")

    def analyze_complementarity(self, fixture_name: str) -> ComplementarityReport:
        """
        Analyze how tools complement each other for a specific fixture.
        """
        # Collect findings from all tools
        all_findings_by_tool: Dict[str, Set[Tuple]] = {}
        for tool, findings in self.tool_results.items():
            all_findings_by_tool[tool] = self._normalize_findings(findings)

        # Calculate metrics per tool
        tool_metrics = []
        for tool, findings in all_findings_by_tool.items():
            metrics = self._calculate_tool_metrics(tool, findings, fixture_name)
            tool_metrics.append(metrics)

        # Calculate overlap
        all_findings_set = set()
        for findings in all_findings_by_tool.values():
            all_findings_set.update(findings)

        overlap_findings = self._calculate_overlap(all_findings_by_tool)
        total_unique = len(all_findings_set)

        # Calculate coverage matrix
        coverage_matrix = self._build_coverage_matrix(all_findings_by_tool)

        # Calculate metrics
        total_found = sum(m.findings_count for m in tool_metrics)
        redundancy_ratio = (total_found - total_unique) / total_found if total_found > 0 else 0
        effectiveness_score = 1.0 - redundancy_ratio

        # Generate recommendations
        recommendations = self._generate_recommendations(
            tool_metrics, redundancy_ratio, effectiveness_score
        )

        return ComplementarityReport(
            total_vulnerabilities_found=total_found,
            total_unique_vulnerabilities=total_unique,
            overlap_findings=overlap_findings,
            tool_metrics=tool_metrics,
            coverage_matrix=coverage_matrix,
            redundancy_ratio=redundancy_ratio,
            effectiveness_score=effectiveness_score,
            recommendations=recommendations,
        )

    def _normalize_findings(self, findings: List[Dict]) -> Set[Tuple]:
        """Normalize findings to comparable tuples (type, line)."""
        normalized = set()
        for finding in findings:
            vuln_type = finding.get("type", "unknown")
            line = finding.get("line", 0)
            normalized.add((vuln_type, line))
        return normalized

    def _calculate_tool_metrics(self, tool: str, findings: Set[Tuple], fixture_name: str) -> ToolMetrics:
        """Calculate metrics for a single tool."""
        expected = self.fixture_expectations.get(fixture_name, {})
        expected_vulns = {
            (v["type"], v["line"]) for v in expected.get("expected_vulnerabilities", [])
        }

        # True positives, false positives
        true_positives = len(findings & expected_vulns)
        false_positives = len(findings - expected_vulns)
        false_negatives = len(expected_vulns - findings)

        total_findings = len(findings)
        accuracy = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        false_positive_rate = false_positives / total_findings if total_findings > 0 else 0

        return ToolMetrics(
            tool_name=tool,
            findings_count=total_findings,
            unique_findings=true_positives,
            overlap_with_others=false_positives,
            accuracy_rate=accuracy,
            avg_confidence=0.85,  # Would come from actual analysis
            analysis_time_ms=2500,  # Mock value
            false_positive_rate=false_positive_rate,
        )

    def _calculate_overlap(self, findings_by_tool: Dict[str, Set[Tuple]]) -> int:
        """Calculate number of duplicate findings across tools."""
        if len(findings_by_tool) < 2:
            return 0

        tools = list(findings_by_tool.values())
        intersection = tools[0]
        for tool_findings in tools[1:]:
            intersection = intersection & tool_findings

        return len(intersection)

    def _build_coverage_matrix(self, findings_by_tool: Dict[str, Set[Tuple]]) -> Dict[str, List[str]]:
        """Build coverage matrix showing which tools detect which vulnerability types."""
        coverage = {}
        for tool, findings in findings_by_tool.items():
            vuln_types = sorted(set(f[0] for f in findings))
            coverage[tool] = vuln_types

        return coverage

    def _generate_recommendations(
        self, tool_metrics: List[ToolMetrics], redundancy: float, effectiveness: float
    ) -> List[str]:
        """Generate actionable recommendations based on metrics."""
        recommendations = []

        # Redundancy analysis
        if redundancy > 0.3:
            recommendations.append("HIGH: Reduce tool redundancy by tuning rule sets")
        elif redundancy > 0.15:
            recommendations.append("MEDIUM: Consider disabling overlapping rules")

        # Effectiveness
        if effectiveness < 0.7:
            recommendations.append("HIGH: Add complementary analysis tools (e.g., static + dynamic)")
        elif effectiveness < 0.85:
            recommendations.append("MEDIUM: Fine-tune tool configurations for better coverage")

        # Tool-specific
        for metrics in tool_metrics:
            if metrics.false_positive_rate > 0.2:
                recommendations.append(f"HIGH: {metrics.tool_name} has high FP rate, needs filtering")
            if metrics.accuracy_rate < 0.7:
                recommendations.append(f"MEDIUM: {metrics.tool_name} accuracy below threshold")

        if not recommendations:
            recommendations.append("✓ Tool configuration optimal - no immediate changes needed")

        return recommendations

    def generate_report(self) -> str:
        """Generate formatted complementarity report."""
        if not self.tool_results:
            return "No tool results registered"

        # Analyze first fixture (for demo)
        fixture_name = list(self.fixture_expectations.keys())[0] if self.fixture_expectations else "unknown"
        report_data = self.analyze_complementarity(fixture_name)

        lines = [
            "╔════════════════════════════════════════════════════════════╗",
            "║      TOOL COMPLEMENTARITY & ATTRIBUTION REPORT            ║",
            "╚════════════════════════════════════════════════════════════╝",
            "",
            f"Fixture: {fixture_name}",
            f"Total Findings:        {report_data.total_vulnerabilities_found}",
            f"Unique Findings:       {report_data.total_unique_vulnerabilities}",
            f"Overlap:               {report_data.overlap_findings}",
            f"Redundancy Ratio:      {report_data.redundancy_ratio:.1%}",
            f"Effectiveness Score:   {report_data.effectiveness_score:.1%}",
            "",
            "Per-Tool Metrics:",
            "─" * 62,
        ]

        for metrics in report_data.tool_metrics:
            lines.append(
                f"{metrics.tool_name:15} | "
                f"Findings: {metrics.findings_count:2} | "
                f"Accuracy: {metrics.accuracy_rate:.1%} | "
                f"FP Rate: {metrics.false_positive_rate:.1%}"
            )

        lines.extend(
            [
                "",
                "Coverage Matrix (vulnerability types per tool):",
                "─" * 62,
            ]
        )

        for tool, vuln_types in report_data.coverage_matrix.items():
            lines.append(f"{tool:15}: {', '.join(vuln_types) if vuln_types else 'None'}")

        lines.extend(["", "Recommendations:", "─" * 62])
        for rec in report_data.recommendations:
            lines.append(f"• {rec}")

        return "\n".join(lines)


def main():
    analyzer = ToolComplementarityAnalyzer()

    # Register mock tool results
    analyzer.register_tool_results(
        "codeql",
        [
            {"type": "sql_injection", "line": 5, "tool": "codeql"},
            {"type": "unsafe_memory_access", "line": 8, "tool": "codeql"},
            {"type": "race_condition", "line": 12, "tool": "codeql"},
        ],
    )

    analyzer.register_tool_results(
        "semgrep",
        [
            {"type": "sql_injection", "line": 5, "tool": "semgrep"},
            {"type": "xss", "line": 20, "tool": "semgrep"},
            {"type": "hardcoded_credentials", "line": 2, "tool": "semgrep"},
        ],
    )

    print(analyzer.generate_report())

    # JSON output
    report = analyzer.analyze_complementarity("vulnerable_typescript.ts")
    print("\n\nJSON Report:")
    print(json.dumps(asdict(report), indent=2, default=str))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
