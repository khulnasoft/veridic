#!/usr/bin/env python3
"""
Determinism Validator for Phase 1

Validates that Phase 1 analysis produces consistent results across multiple runs.
Tests for:
- Finding consistency (same findings detected across runs)
- Finding ordering stability
- CVSS score consistency
- Report structure consistency
"""

import asyncio
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class DeterminismResult:
    fixture_name: str
    num_runs: int
    findings_hash_consistent: bool
    finding_hashes: List[str]
    cvss_scores_consistent: bool
    cvss_score_values: List[Dict[str, float]]
    ordering_consistent: bool
    vulnerability_type_consistency: float  # 0.0-1.0
    severity_consistency: float  # 0.0-1.0
    status: str  # PASS, WARN, FAIL
    details: Dict[str, Any]


class DeterminismValidator:
    """Validates consistency of vulnerability analysis across multiple runs."""

    def __init__(self, num_runs: int = 3):
        self.num_runs = num_runs
        self.results: List[DeterminismResult] = []

    async def validate_fixture(self, fixture_path: Path) -> DeterminismResult:
        """
        Run analysis on a fixture multiple times and check consistency.
        """
        logger.info(f"Validating determinism for {fixture_path.name} ({self.num_runs} runs)")

        runs_data = []

        # Run analysis multiple times
        for i in range(self.num_runs):
            logger.debug(f"Run {i+1}/{self.num_runs}")
            # Simulate analysis (in real implementation, call gRPC service)
            analysis_result = await self._run_analysis(fixture_path)
            runs_data.append(analysis_result)

        # Compare results
        result = self._compare_results(fixture_path, runs_data)
        self.results.append(result)
        return result

    async def _run_analysis(self, fixture_path: Path) -> Dict[str, Any]:
        """
        Simulate analysis run. In production, this calls the gRPC service.
        """
        code = fixture_path.read_text()

        # Mock analysis response
        return {
            "vulnerabilities": [
                {
                    "id": f"vuln_{i}",
                    "type": f"type_{i}",
                    "severity": "high",
                    "cvss_score": 7.5 + i * 0.1,
                    "line": 10 + i,
                }
                for i in range(3)
            ],
            "timestamp": "2024-01-01T00:00:00Z",
        }

    def _compare_results(self, fixture_path: Path, runs_data: List[Dict]) -> DeterminismResult:
        """
        Compare results across multiple runs.
        """
        # Extract findings from each run
        findings_per_run = [run["vulnerabilities"] for run in runs_data]

        # Check hash consistency
        finding_hashes = []
        for findings in findings_per_run:
            # Sort findings by line number for consistent hashing
            sorted_findings = sorted(findings, key=lambda x: x.get("line", 0))
            finding_json = json.dumps(sorted_findings, sort_keys=True)
            finding_hash = hashlib.sha256(finding_json.encode()).hexdigest()
            finding_hashes.append(finding_hash)

        findings_hash_consistent = len(set(finding_hashes)) == 1

        # Check CVSS score consistency
        cvss_scores_per_run = []
        for findings in findings_per_run:
            scores = {f["id"]: f.get("cvss_score") for f in findings}
            cvss_scores_per_run.append(scores)

        cvss_consistent = all(scores == cvss_scores_per_run[0] for scores in cvss_scores_per_run)

        # Check ordering consistency
        orderings = []
        for findings in findings_per_run:
            ordering = [f.get("line") for f in findings]
            orderings.append(ordering)

        ordering_consistent = all(ordering == orderings[0] for ordering in orderings)

        # Calculate type and severity consistency
        vuln_types_per_run = [[f["type"] for f in findings] for findings in findings_per_run]
        type_consistency = self._calculate_consistency(vuln_types_per_run)

        severities_per_run = [[f["severity"] for f in findings] for findings in findings_per_run]
        severity_consistency = self._calculate_consistency(severities_per_run)

        # Determine overall status
        if findings_hash_consistent and cvss_consistent and ordering_consistent:
            status = "PASS"
        elif type_consistency >= 0.8 and severity_consistency >= 0.8:
            status = "WARN"
        else:
            status = "FAIL"

        return DeterminismResult(
            fixture_name=fixture_path.name,
            num_runs=self.num_runs,
            findings_hash_consistent=findings_hash_consistent,
            finding_hashes=finding_hashes,
            cvss_scores_consistent=cvss_consistent,
            cvss_score_values=cvss_scores_per_run,
            ordering_consistent=ordering_consistent,
            vulnerability_type_consistency=type_consistency,
            severity_consistency=severity_consistency,
            status=status,
            details={
                "type_consistency_notes": f"{type_consistency:.1%} of findings consistent across runs",
                "severity_consistency_notes": f"{severity_consistency:.1%} of findings consistent across runs",
            },
        )

    def _calculate_consistency(self, data_per_run: List[List[str]]) -> float:
        """
        Calculate consistency score (0.0-1.0) for a set of lists.
        """
        if not data_per_run or not data_per_run[0]:
            return 1.0

        first_run = data_per_run[0]
        total_matches = 0

        for item in first_run:
            matches = sum(1 for run in data_per_run if item in run)
            total_matches += matches

        return total_matches / (len(first_run) * len(data_per_run)) if data_per_run else 1.0

    def generate_report(self) -> str:
        """Generate a formatted report of determinism validation results."""
        report_lines = [
            "╔════════════════════════════════════════════════════════════╗",
            "║          PHASE 1 DETERMINISM VALIDATION REPORT             ║",
            "╚════════════════════════════════════════════════════════════╝",
            "",
        ]

        pass_count = sum(1 for r in self.results if r.status == "PASS")
        warn_count = sum(1 for r in self.results if r.status == "WARN")
        fail_count = sum(1 for r in self.results if r.status == "FAIL")

        report_lines.append(f"Total Tests:     {len(self.results)}")
        report_lines.append(f"✓ PASS:          {pass_count}")
        report_lines.append(f"⚠ WARN:          {warn_count}")
        report_lines.append(f"✗ FAIL:          {fail_count}")
        report_lines.append("")

        for result in self.results:
            status_symbol = "✓" if result.status == "PASS" else "⚠" if result.status == "WARN" else "✗"
            report_lines.append(f"{status_symbol} {result.fixture_name}")
            report_lines.append(f"   Runs:                    {result.num_runs}")
            report_lines.append(
                f"   Hash Consistency:        {'Yes' if result.findings_hash_consistent else 'No'}"
            )
            report_lines.append(
                f"   CVSS Consistency:        {'Yes' if result.cvss_scores_consistent else 'No'}"
            )
            report_lines.append(
                f"   Ordering Consistency:    {'Yes' if result.ordering_consistent else 'No'}"
            )
            report_lines.append(f"   Type Consistency:        {result.vulnerability_type_consistency:.1%}")
            report_lines.append(f"   Severity Consistency:    {result.severity_consistency:.1%}")
            report_lines.append("")

        return "\n".join(report_lines)


async def main():
    validator = DeterminismValidator(num_runs=3)

    fixtures_dir = Path(__file__).parent / "fixtures"
    fixture_files = list(fixtures_dir.glob("vulnerable_*.py")) + list(
        fixtures_dir.glob("vulnerable_*.ts")
    )

    for fixture_file in fixture_files[:2]:  # Test first 2 fixtures
        await validator.validate_fixture(fixture_file)

    print(validator.generate_report())

    # Return JSON results
    results_json = json.dumps([asdict(r) for r in validator.results], indent=2, default=str)
    print("\nDetailed Results:")
    print(results_json)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
