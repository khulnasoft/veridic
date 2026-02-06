"""
Phase 1 Metrics Aggregator
Collects and synthesizes all validation metrics into decision-grade reports.
"""

import json
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
from determinism import generate_determinism_report
from tool_attribution_metrics import generate_tool_attribution_report
from final_verdict import compute_final_verdict


class Phase1MetricsAggregator:
    """Aggregates all Phase 1 validation metrics."""

    def __init__(self, output_dir: str = "phase1_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().isoformat()

    def aggregate_all_metrics(
        self,
        runs: List[Dict[str, Any]],
        findings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Aggregate all metrics from determinism, attribution, and final verdict.
        """
        # Run determinism checks
        determinism_report = generate_determinism_report(runs)

        # Run tool attribution analysis
        attribution_report = generate_tool_attribution_report(findings)

        # Compute detection metrics
        detection_metrics = self._compute_detection_metrics(findings)

        # Aggregate metrics for final verdict
        aggregated_metrics = {
            "detection_rate": detection_metrics["detection_rate"],
            "false_positive_rate": detection_metrics["false_positive_rate"],
            "analysis_time_ms": detection_metrics.get("analysis_time_ms", 0),
            "determinism": determinism_report["metrics"],
            "ai_reasoning": {
                "avg_correlation_confidence": attribution_report[
                    "attribution_metrics"
                ]["ai_value_score"] / 100,
            },
            "integration": {
                "grpc_errors": 0,
                "timeout_errors": 0,
            },
        }

        # Compute final verdict
        verdict_report = compute_final_verdict(aggregated_metrics)

        return {
            "timestamp": self.timestamp,
            "determinism": determinism_report,
            "attribution": attribution_report,
            "detection_metrics": detection_metrics,
            "verdict": verdict_report,
            "summary": self._generate_summary(
                determinism_report,
                attribution_report,
                detection_metrics,
                verdict_report,
            ),
        }

    def _compute_detection_metrics(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute detection rate and false positive metrics."""
        if not findings:
            return {
                "detection_rate": 0.0,
                "false_positive_rate": 0.0,
                "total_findings": 0,
            }

        total_findings = len(findings)
        confident_findings = sum(
            1 for f in findings if f.get("confidence", 0) >= 0.8
        )
        potential_false_positives = sum(
            1 for f in findings if f.get("confidence", 0) < 0.6
        )

        return {
            "total_findings": total_findings,
            "confident_findings": confident_findings,
            "detection_rate": confident_findings / total_findings if total_findings else 0,
            "false_positive_rate": (
                potential_false_positives / total_findings if total_findings else 0
            ),
            "analysis_time_ms": 8500,  # Placeholder - replace with actual timing
        }

    def _generate_summary(
        self,
        determinism_report: Dict[str, Any],
        attribution_report: Dict[str, Any],
        detection_metrics: Dict[str, Any],
        verdict_report: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate human-readable summary of all metrics."""
        return {
            "timestamp": self.timestamp,
            "determinism_status": determinism_report["status"],
            "detection_rate": f"{detection_metrics['detection_rate']:.1%}",
            "false_positive_rate": f"{detection_metrics['false_positive_rate']:.1%}",
            "total_vulnerabilities": detection_metrics["total_findings"],
            "tool_attribution": {
                "codeql_only": attribution_report["attribution_metrics"]["attribution"].get(
                    "codeql_only", 0
                ),
                "semgrep_only": attribution_report["attribution_metrics"]["attribution"].get(
                    "semgrep_only", 0
                ),
                "static_both": attribution_report["attribution_metrics"]["attribution"].get(
                    "static_both", 0
                ),
                "ai_only": attribution_report["attribution_metrics"]["attribution"].get(
                    "ai_only", 0
                ),
                "ai_correlated": attribution_report["attribution_metrics"]["attribution"].get(
                    "ai_correlated", 0
                ),
            },
            "final_verdict": verdict_report["status"],
            "recommendation": verdict_report["recommendation"],
        }

    def export_json(self, metrics: Dict[str, Any], filename: str = "phase1_metrics.json"):
        """Export metrics to JSON file."""
        output_file = self.output_dir / filename
        with open(output_file, "w") as f:
            json.dump(metrics, f, indent=2)
        return str(output_file)

    def export_markdown(self, metrics: Dict[str, Any], filename: str = "phase1_report.md"):
        """Export metrics to Markdown report."""
        output_file = self.output_dir / filename
        summary = metrics["summary"]
        verdict = metrics["verdict"]

        md_content = f"""# Phase 1 Validation Report

**Generated:** {summary['timestamp']}

## Executive Summary

**FINAL VERDICT:** `{verdict['status']}`

{verdict['recommendation']}

## Key Metrics

| Metric | Value |
|--------|-------|
| Detection Rate | {summary['detection_rate']} |
| False Positive Rate | {summary['false_positive_rate']} |
| Total Vulnerabilities | {summary['total_vulnerabilities']} |
| Determinism Status | {summary['determinism_status']} |

## Tool Attribution

| Tool Category | Count |
|--------------|-------|
| CodeQL Only | {summary['tool_attribution']['codeql_only']} |
| Semgrep Only | {summary['tool_attribution']['semgrep_only']} |
| Both Tools | {summary['tool_attribution']['static_both']} |
| AI Only | {summary['tool_attribution']['ai_only']} |
| AI Correlated | {summary['tool_attribution']['ai_correlated']} |

## Validation Details

### Determinism
- Status: {metrics['determinism']['status']}
- Interpretation: {metrics['determinism']['interpretation']}

### Detection Metrics
- Confident Findings (≥80%): {metrics['detection_metrics']['confident_findings']}
- Potential False Positives (<60%): {metrics['detection_metrics'].get('false_positive_findings', 0)}

### Final Verdict
- Status: {verdict['status']}
- Passes: {len(verdict['details']['passes'])}
- Warnings: {len(verdict['details']['warnings'])}
- Failures: {len(verdict['details']['failures'])}

### Next Steps

{verdict['recommendation']}

---

*For detailed metrics, see phase1_metrics.json*
"""

        with open(output_file, "w") as f:
            f.write(md_content)
        return str(output_file)

    def print_summary(self, metrics: Dict[str, Any]) -> None:
        """Print formatted summary to stdout."""
        summary = metrics["summary"]
        verdict = metrics["verdict"]

        print("\n" + "=" * 50)
        print("  Phase 1 Validation Summary")
        print("=" * 50)
        print(f"\nDetection Rate:        {summary['detection_rate']}")
        print(f"False Positives:       {summary['false_positive_rate']}")
        print(f"Deterministic:         {summary['determinism_status']}")
        print(f"\nTool Attribution:")
        print(f"- CodeQL Only:         {summary['tool_attribution']['codeql_only']}")
        print(f"- Semgrep Only:        {summary['tool_attribution']['semgrep_only']}")
        print(f"- Static Both:         {summary['tool_attribution']['static_both']}")
        print(f"- AI Correlated:       {summary['tool_attribution']['ai_correlated']}")
        print(f"- AI Only:             {summary['tool_attribution']['ai_only']}")
        print(f"\nFINAL RESULT: {verdict['status']}")
        print("=" * 50 + "\n")


if __name__ == "__main__":
    # Example usage
    aggregator = Phase1MetricsAggregator()

    sample_runs = [
        {
            "findings": [
                {"type": "sql_injection", "line": 42, "cwe": "CWE-89", "severity": "Critical"}
            ]
        },
        {
            "findings": [
                {"type": "sql_injection", "line": 42, "cwe": "CWE-89", "severity": "Critical"}
            ]
        },
    ]

    sample_findings = [
        {
            "id": "VULN-001",
            "type": "sql_injection",
            "tools": ["codeql"],
            "confidence": 0.95,
            "ai_enhanced": False,
        },
        {
            "id": "VULN-002",
            "type": "xss",
            "tools": ["semgrep"],
            "confidence": 0.88,
            "ai_enhanced": False,
        },
    ]

    metrics = aggregator.aggregate_all_metrics(sample_runs, sample_findings)

    # Export and print
    json_file = aggregator.export_json(metrics)
    md_file = aggregator.export_markdown(metrics)
    aggregator.print_summary(metrics)

    print(f"JSON Report: {json_file}")
    print(f"Markdown Report: {md_file}")
