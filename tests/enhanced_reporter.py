#!/usr/bin/env python3
"""
Enhanced PASS/WARN/FAIL Reporter for Phase 1 Validation

Provides:
- Color-coded terminal output
- JSON export for CI/CD integration
- Markdown reports
- Decision trees for remediation
"""

import json
from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum
from datetime import datetime
import sys


class Status(Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    GREY = "\033[90m"


@dataclass
class ValidationStep:
    step_number: int
    name: str
    status: Status
    duration_seconds: float
    details: str
    remediation: str = ""


@dataclass
class ValidationReport:
    timestamp: str
    total_steps: int
    passed: int
    warned: int
    failed: int
    overall_status: Status
    steps: List[ValidationStep]
    metrics: Dict[str, Any]
    recommendations: List[str]


class EnhancedReporter:
    """Generates PASS/WARN/FAIL reports with rich formatting."""

    def __init__(self):
        self.steps: List[ValidationStep] = []
        self.metrics: Dict[str, Any] = {}
        self.recommendations: List[str] = []

    def add_step(
        self,
        step_number: int,
        name: str,
        status: Status,
        duration: float,
        details: str,
        remediation: str = "",
    ) -> None:
        """Add a validation step result."""
        step = ValidationStep(
            step_number=step_number,
            name=name,
            status=status,
            duration_seconds=duration,
            details=details,
            remediation=remediation,
        )
        self.steps.append(step)

    def set_metrics(self, metrics: Dict[str, Any]) -> None:
        """Set validation metrics."""
        self.metrics = metrics

    def add_recommendation(self, recommendation: str) -> None:
        """Add a recommendation."""
        self.recommendations.append(recommendation)

    def _get_status_color(self, status: Status) -> str:
        """Get color code for status."""
        if status == Status.PASS:
            return Color.GREEN
        elif status == Status.WARN:
            return Color.YELLOW
        else:
            return Color.RED

    def _get_status_symbol(self, status: Status) -> str:
        """Get symbol for status."""
        if status == Status.PASS:
            return "✓"
        elif status == Status.WARN:
            return "⚠"
        else:
            return "✗"

    def print_terminal_report(self) -> None:
        """Print colored terminal report."""
        passed = sum(1 for s in self.steps if s.status == Status.PASS)
        warned = sum(1 for s in self.steps if s.status == Status.WARN)
        failed = sum(1 for s in self.steps if s.status == Status.FAIL)

        overall = Status.FAIL if failed > 0 else (Status.WARN if warned > 0 else Status.PASS)

        # Header
        print("\n" + "═" * 70)
        print(
            f"{Color.BOLD}PHASE 1 VALIDATION REPORT{Color.RESET} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print("═" * 70)

        # Summary
        print(
            f"\nOverall Status: {self._get_status_color(overall)}{self._get_status_symbol(overall)} {overall.value}{Color.RESET}\n"
        )
        print(f"Total Steps:   {len(self.steps)}")
        print(f"{Color.GREEN}✓ PASS{Color.RESET}:     {passed}")
        print(f"{Color.YELLOW}⚠ WARN{Color.RESET}:     {warned}")
        print(f"{Color.RED}✗ FAIL{Color.RESET}:     {failed}")

        # Steps
        print("\n" + "─" * 70)
        print("VALIDATION STEPS:")
        print("─" * 70 + "\n")

        for step in self.steps:
            color = self._get_status_color(step.status)
            symbol = self._get_status_symbol(step.status)

            print(f"{color}{symbol}{Color.RESET} Step {step.step_number}: {Color.BOLD}{step.name}{Color.RESET}")
            print(f"   Duration: {step.duration_seconds:.2f}s")
            print(f"   {step.details}")

            if step.status != Status.PASS and step.remediation:
                print(f"   {Color.YELLOW}→ Remediation: {step.remediation}{Color.RESET}")

            print()

        # Metrics
        if self.metrics:
            print("─" * 70)
            print("METRICS:")
            print("─" * 70 + "\n")

            for key, value in self.metrics.items():
                if isinstance(value, float):
                    print(f"  {key:30s}: {value:.2%}")
                else:
                    print(f"  {key:30s}: {value}")
            print()

        # Recommendations
        if self.recommendations:
            print("─" * 70)
            print("RECOMMENDATIONS:")
            print("─" * 70 + "\n")

            for i, rec in enumerate(self.recommendations, 1):
                if rec.startswith("HIGH:"):
                    color = Color.RED
                elif rec.startswith("MEDIUM:"):
                    color = Color.YELLOW
                else:
                    color = Color.GREEN

                print(f"  {i}. {color}{rec}{Color.RESET}")
            print()

        # Decision tree
        print("─" * 70)
        print("DECISION TREE:")
        print("─" * 70 + "\n")

        if failed > 0:
            print(f"{Color.RED}Critical Issues Detected - Immediate Action Required{Color.RESET}")
            print(
                "  1. Review FAIL steps above\n"
                "  2. Run: make logs\n"
                "  3. Check docker-compose.yml configuration\n"
                "  4. Verify environment variables (.env)\n"
                "  5. Run: make clean && make build\n"
            )
        elif warned > 0:
            print(f"{Color.YELLOW}Warnings Found - Review Recommended{Color.RESET}")
            print(
                "  1. Review WARN steps above\n"
                "  2. Validate tool versions (CodeQL, Semgrep)\n"
                "  3. Consider updating Docker images\n"
                "  4. Proceed with Phase 1 testing with caution\n"
            )
        else:
            print(f"{Color.GREEN}All Validation Steps Passed!{Color.RESET}")
            print(
                "  ✓ Ready to proceed with Phase 1 end-to-end testing\n"
                "  ✓ Run: make test-phase1\n"
                "  ✓ Run: make metrics\n"
                "  ✓ Run: make test-determinism\n"
            )

        print("═" * 70 + "\n")

    def export_json(self) -> str:
        """Export report as JSON."""
        passed = sum(1 for s in self.steps if s.status == Status.PASS)
        warned = sum(1 for s in self.steps if s.status == Status.WARN)
        failed = sum(1 for s in self.steps if s.status == Status.FAIL)
        overall = Status.FAIL if failed > 0 else (Status.WARN if warned > 0 else Status.PASS)

        report = ValidationReport(
            timestamp=datetime.now().isoformat(),
            total_steps=len(self.steps),
            passed=passed,
            warned=warned,
            failed=failed,
            overall_status=overall,
            steps=self.steps,
            metrics=self.metrics,
            recommendations=self.recommendations,
        )

        return json.dumps(
            {
                "timestamp": report.timestamp,
                "summary": {
                    "total_steps": report.total_steps,
                    "passed": report.passed,
                    "warned": report.warned,
                    "failed": report.failed,
                    "overall_status": report.overall_status.value,
                },
                "steps": [
                    {
                        "step_number": s.step_number,
                        "name": s.name,
                        "status": s.status.value,
                        "duration_seconds": s.duration_seconds,
                        "details": s.details,
                        "remediation": s.remediation,
                    }
                    for s in report.steps
                ],
                "metrics": report.metrics,
                "recommendations": report.recommendations,
            },
            indent=2,
        )

    def export_markdown(self) -> str:
        """Export report as Markdown."""
        lines = [
            "# Phase 1 Validation Report",
            f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "\n## Summary\n",
        ]

        passed = sum(1 for s in self.steps if s.status == Status.PASS)
        warned = sum(1 for s in self.steps if s.status == Status.WARN)
        failed = sum(1 for s in self.steps if s.status == Status.FAIL)

        lines.append(f"| Metric | Count |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total Steps | {len(self.steps)} |")
        lines.append(f"| ✓ PASS | {passed} |")
        lines.append(f"| ⚠ WARN | {warned} |")
        lines.append(f"| ✗ FAIL | {failed} |")

        lines.append("\n## Validation Steps\n")

        for step in self.steps:
            status_icon = self._get_status_symbol(step.status)
            lines.append(f"### {status_icon} Step {step.step_number}: {step.name}")
            lines.append(f"- **Duration:** {step.duration_seconds:.2f}s")
            lines.append(f"- **Status:** {step.status.value}")
            lines.append(f"- **Details:** {step.details}")
            if step.remediation:
                lines.append(f"- **Remediation:** {step.remediation}")
            lines.append("")

        if self.metrics:
            lines.append("## Metrics\n")
            for key, value in self.metrics.items():
                if isinstance(value, float):
                    lines.append(f"- **{key}:** {value:.2%}")
                else:
                    lines.append(f"- **{key}:** {value}")
            lines.append("")

        if self.recommendations:
            lines.append("## Recommendations\n")
            for rec in self.recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        return "\n".join(lines)


def main():
    """Demo of enhanced reporter."""
    reporter = EnhancedReporter()

    reporter.add_step(1, "gRPC Protocol Compilation", Status.PASS, 3.5, "Proto files compiled successfully")
    reporter.add_step(2, "Docker Build Verification", Status.PASS, 45.2, "Both services built without errors")
    reporter.add_step(3, "Service Health Check", Status.PASS, 8.1, "Both services healthy and connected")
    reporter.add_step(
        4,
        "Static Analysis Tool Validation",
        Status.WARN,
        120.0,
        "CodeQL compiled but slow. Semgrep found expected issues.",
        "Consider caching CodeQL databases for faster iterations",
    )
    reporter.add_step(5, "AST Extraction Validation", Status.PASS, 15.3, "All 4 languages extracted successfully")
    reporter.add_step(6, "End-to-End Pipeline Test", Status.PASS, 85.0, "All fixtures analyzed, 85% detection rate")
    reporter.add_step(7, "AI Reasoning Quality", Status.WARN, 45.0, "Correlations good but CVSS scoring needs tuning")
    reporter.add_step(8, "Baseline Metrics Generation", Status.PASS, 12.0, "Metrics baseline established")

    reporter.set_metrics(
        {
            "Detection Rate": 0.85,
            "False Positive Rate": 0.08,
            "CVSS Accuracy": 0.78,
            "Avg Analysis Time": 8.5,
            "Tool Complementarity": 0.92,
        }
    )

    reporter.add_recommendation("HIGH: Optimize CodeQL startup by pre-caching databases")
    reporter.add_recommendation("MEDIUM: Tune CVSS scoring rules for better accuracy")
    reporter.add_recommendation("MEDIUM: Consider adding tool caching layer")
    reporter.add_recommendation("LOW: Document Phase 1 output schema for Phase 2")

    # Terminal output
    reporter.print_terminal_report()

    # JSON export
    print("\n" + "=" * 70)
    print("JSON EXPORT")
    print("=" * 70)
    print(reporter.export_json())

    # Markdown export
    print("\n" + "=" * 70)
    print("MARKDOWN EXPORT")
    print("=" * 70)
    print(reporter.export_markdown())


if __name__ == "__main__":
    main()
