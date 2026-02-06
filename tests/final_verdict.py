"""
Final Verdict Engine
Decision-grade classification: PASS, WARN, FAIL
Determines if Phase 1 validation passes gates for Phase 2.
"""

import json
from typing import Dict, Any, List
from enum import Enum


class VerdictStatus(Enum):
    """Verdict classifications."""
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class VerdictCriteria:
    """Thresholds for phase 1 validation."""
    # Detection rate thresholds
    MIN_DETECTION_RATE = 0.70  # 70%
    MIN_DETECTION_RATE_WARN = 0.80  # 80%

    # Determinism thresholds
    MAX_CVSS_VARIANCE = 0.3
    MAX_FINDING_COUNT_VARIANCE = 0

    # Tool performance thresholds
    MAX_TOOL_RUNTIME = 15  # seconds
    MAX_FALSE_POSITIVE_RATE = 0.25  # 25%

    # AI confidence thresholds
    MIN_AI_CORRELATION_CONFIDENCE = 0.60


class FinalVerdictEngine:
    """Evaluates Phase 1 metrics and produces decision-grade verdict."""

    def __init__(self):
        self.criteria = VerdictCriteria()
        self.failures = []
        self.warnings = []
        self.passes = []

    def evaluate(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive evaluation producing PASS, WARN, or FAIL.
        """
        self.failures.clear()
        self.warnings.clear()
        self.passes.clear()

        # Evaluation checks
        self._check_detection_rate(metrics)
        self._check_determinism(metrics)
        self._check_tool_runtime(metrics)
        self._check_false_positives(metrics)
        self._check_ai_confidence(metrics)
        self._check_integration_health(metrics)

        # Determine overall verdict
        verdict = self._compute_verdict()

        return {
            "status": verdict,
            "summary": self._generate_summary(),
            "details": {
                "passes": self.passes,
                "warnings": self.warnings,
                "failures": self.failures,
            },
            "recommendation": self._generate_recommendation(verdict),
        }

    def _check_detection_rate(self, metrics: Dict[str, Any]) -> None:
        """Validate vulnerability detection rate."""
        detection_rate = metrics.get("detection_rate", 0)

        if detection_rate < self.criteria.MIN_DETECTION_RATE:
            self.failures.append(
                f"Detection rate {detection_rate:.1%} < {self.criteria.MIN_DETECTION_RATE:.1%}"
            )
        elif detection_rate < self.criteria.MIN_DETECTION_RATE_WARN:
            self.warnings.append(
                f"Detection rate {detection_rate:.1%} below target {self.criteria.MIN_DETECTION_RATE_WARN:.1%}"
            )
        else:
            self.passes.append(
                f"Detection rate {detection_rate:.1%} meets target"
            )

    def _check_determinism(self, metrics: Dict[str, Any]) -> None:
        """Validate determinism metrics."""
        determinism = metrics.get("determinism", {})

        if not determinism.get("fingerprint_match"):
            self.failures.append("Results are non-deterministic (fingerprint mismatch)")
        elif determinism.get("finding_count_variance", 0) > 0:
            self.failures.append(
                f"Finding count variance {determinism['finding_count_variance']} > 0"
            )
        elif determinism.get("cvss_delta", 0) > self.criteria.MAX_CVSS_VARIANCE:
            self.warnings.append(
                f"CVSS variance {determinism['cvss_delta']} > {self.criteria.MAX_CVSS_VARIANCE}"
            )
        else:
            self.passes.append("Determinism validated")

    def _check_tool_runtime(self, metrics: Dict[str, Any]) -> None:
        """Validate tool execution time."""
        runtime = metrics.get("analysis_time_ms", 0) / 1000  # Convert to seconds

        if runtime > self.criteria.MAX_TOOL_RUNTIME:
            self.warnings.append(
                f"Analysis time {runtime:.1f}s exceeds target {self.criteria.MAX_TOOL_RUNTIME}s"
            )
        else:
            self.passes.append(f"Analysis time {runtime:.1f}s within budget")

    def _check_false_positives(self, metrics: Dict[str, Any]) -> None:
        """Validate false positive rate."""
        fp_rate = metrics.get("false_positive_rate", 0)

        if fp_rate > self.criteria.MAX_FALSE_POSITIVE_RATE:
            self.warnings.append(
                f"False positive rate {fp_rate:.1%} > {self.criteria.MAX_FALSE_POSITIVE_RATE:.1%}"
            )
        else:
            self.passes.append(f"False positive rate {fp_rate:.1%} acceptable")

    def _check_ai_confidence(self, metrics: Dict[str, Any]) -> None:
        """Validate AI reasoning confidence."""
        ai_metrics = metrics.get("ai_reasoning", {})
        avg_confidence = ai_metrics.get("avg_correlation_confidence", 0)

        if avg_confidence < self.criteria.MIN_AI_CORRELATION_CONFIDENCE:
            self.warnings.append(
                f"AI confidence {avg_confidence:.2f} < {self.criteria.MIN_AI_CORRELATION_CONFIDENCE}"
            )
        else:
            self.passes.append(f"AI correlation confidence {avg_confidence:.2f} acceptable")

    def _check_integration_health(self, metrics: Dict[str, Any]) -> None:
        """Validate Rust ↔ Python integration."""
        integration = metrics.get("integration", {})

        if integration.get("grpc_errors", 0) > 0:
            self.failures.append(
                f"{integration['grpc_errors']} gRPC errors detected"
            )
        elif integration.get("timeout_errors", 0) > 0:
            self.warnings.append(
                f"{integration['timeout_errors']} timeout errors detected"
            )
        else:
            self.passes.append("gRPC integration healthy")

    def _compute_verdict(self) -> str:
        """Determine final verdict: PASS, WARN, or FAIL."""
        if self.failures:
            return VerdictStatus.FAIL.value
        elif self.warnings:
            return VerdictStatus.WARN.value
        else:
            return VerdictStatus.PASS.value

    def _generate_summary(self) -> str:
        """Generate human-readable summary."""
        return (
            f"Phase 1 Validation: {len(self.passes)} PASS, "
            f"{len(self.warnings)} WARN, {len(self.failures)} FAIL"
        )

    def _generate_recommendation(self, verdict: str) -> str:
        """Generate actionable recommendation."""
        if verdict == VerdictStatus.FAIL.value:
            return (
                "Phase 1 validation FAILED. Review failures and rerun validation. "
                "Do NOT proceed to Phase 2."
            )
        elif verdict == VerdictStatus.WARN.value:
            return (
                "Phase 1 validation has warnings. Acceptable to proceed to Phase 2 "
                "with caution. Monitor warning metrics closely."
            )
        else:
            return (
                "Phase 1 validation PASSED. Proceed to Phase 2 (Dynamic & Runtime Analysis). "
                "Lock prompts and thresholds before scaling to real OSS repos."
            )


def compute_final_verdict(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for final verdict computation.
    """
    engine = FinalVerdictEngine()
    return engine.evaluate(metrics)


if __name__ == "__main__":
    # Example usage
    sample_metrics = {
        "detection_rate": 0.87,
        "false_positive_rate": 0.09,
        "analysis_time_ms": 8500,
        "determinism": {
            "fingerprint_match": True,
            "finding_count_variance": 0,
            "cvss_delta": 0.12,
        },
        "ai_reasoning": {
            "avg_correlation_confidence": 0.85,
        },
        "integration": {
            "grpc_errors": 0,
            "timeout_errors": 0,
        }
    }

    verdict = compute_final_verdict(sample_metrics)
    print(json.dumps(verdict, indent=2))
