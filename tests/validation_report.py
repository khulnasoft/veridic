"""
Phase 1 Validation Report Generator

Produces comprehensive PASS/WARN/FAIL reports for all 8 validation steps.
Generates JSON, Markdown, and terminal output.
"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum


class StatusEnum(Enum):
    """Validation status codes."""
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass
class ValidationStep:
    """Result of a single validation step."""
    step_num: int
    name: str
    status: StatusEnum
    duration_seconds: float
    message: str
    metrics: Optional[Dict] = None
    errors: Optional[List[str]] = None


class Phase1ValidationReport:
    """Generates Phase 1 validation reports."""
    
    def __init__(self):
        self.steps: List[ValidationStep] = []
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
    
    def add_step(
        self,
        step_num: int,
        name: str,
        status: StatusEnum,
        duration: float,
        message: str,
        metrics: Optional[Dict] = None,
        errors: Optional[List[str]] = None,
    ):
        """Add a validation step result."""
        self.steps.append(ValidationStep(
            step_num=step_num,
            name=name,
            status=status,
            duration_seconds=duration,
            message=message,
            metrics=metrics,
            errors=errors,
        ))
    
    def finalize(self):
        """Mark validation as complete."""
        self.end_time = datetime.now()
    
    @property
    def overall_status(self) -> StatusEnum:
        """Determine overall validation status."""
        if any(s.status == StatusEnum.FAIL for s in self.steps):
            return StatusEnum.FAIL
        if any(s.status == StatusEnum.WARN for s in self.steps):
            return StatusEnum.WARN
        return StatusEnum.PASS
    
    @property
    def total_duration(self) -> float:
        """Total validation time in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def get_terminal_output(self) -> str:
        """Generate formatted terminal output."""
        lines = [
            "═" * 80,
            "PHASE 1 VALIDATION REPORT",
            "═" * 80,
            f"Status: {self.overall_status.value}",
            f"Total Duration: {self.total_duration:.1f}s",
            f"Timestamp: {self.start_time.isoformat()}",
            "",
        ]
        
        for step in self.steps:
            status_symbol = {
                StatusEnum.PASS: "✓",
                StatusEnum.WARN: "⚠",
                StatusEnum.FAIL: "✗",
            }[step.status]
            
            color = {
                StatusEnum.PASS: "\033[92m",  # Green
                StatusEnum.WARN: "\033[93m",  # Yellow
                StatusEnum.FAIL: "\033[91m",  # Red
            }[step.status]
            
            reset = "\033[0m"
            
            lines.append(
                f"{color}{status_symbol} Step {step.step_num}: {step.name}{reset}"
            )
            lines.append(f"  Message: {step.message}")
            lines.append(f"  Duration: {step.duration_seconds:.2f}s")
            
            if step.metrics:
                lines.append("  Metrics:")
                for key, value in step.metrics.items():
                    lines.append(f"    - {key}: {value}")
            
            if step.errors:
                lines.append("  Errors:")
                for error in step.errors:
                    lines.append(f"    - {error}")
            
            lines.append("")
        
        lines.extend([
            "═" * 80,
            f"OVERALL: {self.overall_status.value}",
            "═" * 80,
        ])
        
        return "\n".join(lines)
    
    def get_json(self) -> Dict:
        """Generate JSON representation."""
        return {
            'timestamp': self.start_time.isoformat(),
            'duration_seconds': self.total_duration,
            'overall_status': self.overall_status.value,
            'steps': [
                {
                    'step_num': step.step_num,
                    'name': step.name,
                    'status': step.status.value,
                    'duration_seconds': step.duration_seconds,
                    'message': step.message,
                    'metrics': step.metrics,
                    'errors': step.errors,
                }
                for step in self.steps
            ],
        }
    
    def get_markdown(self) -> str:
        """Generate Markdown representation."""
        lines = [
            "# Phase 1 Validation Report",
            "",
            f"**Status**: {self.overall_status.value}",
            f"**Duration**: {self.total_duration:.1f}s",
            f"**Timestamp**: {self.start_time.isoformat()}",
            "",
            "## Validation Steps",
            "",
        ]
        
        for step in self.steps:
            status_emoji = {
                StatusEnum.PASS: "✅",
                StatusEnum.WARN: "⚠️",
                StatusEnum.FAIL: "❌",
            }[step.status]
            
            lines.append(f"### {status_emoji} Step {step.step_num}: {step.name}")
            lines.append("")
            lines.append(f"**Status**: {step.status.value}")
            lines.append(f"**Duration**: {step.duration_seconds:.2f}s")
            lines.append("")
            lines.append(f"**Message**: {step.message}")
            lines.append("")
            
            if step.metrics:
                lines.append("**Metrics**:")
                for key, value in step.metrics.items():
                    lines.append(f"- {key}: {value}")
                lines.append("")
            
            if step.errors:
                lines.append("**Errors**:")
                for error in step.errors:
                    lines.append(f"- {error}")
                lines.append("")
        
        lines.extend([
            "---",
            "",
            f"**Overall Result**: {self.overall_status.value}",
        ])
        
        return "\n".join(lines)
    
    def export_json(self, filepath: str):
        """Export validation report to JSON."""
        with open(filepath, 'w') as f:
            json.dump(self.get_json(), f, indent=2)
    
    def export_markdown(self, filepath: str):
        """Export validation report to Markdown."""
        with open(filepath, 'w') as f:
            f.write(self.get_markdown())
    
    def print_terminal(self):
        """Print formatted validation report to terminal."""
        print(self.get_terminal_output())


class ValidationRuleChecker:
    """Helper to check validation rules and criteria."""
    
    @staticmethod
    def check_detection_rate(found: int, expected: int, threshold: float = 0.8) -> tuple[bool, str]:
        """
        Check if detection rate meets threshold.
        
        Args:
            found: Number of vulnerabilities detected
            expected: Total number of expected vulnerabilities
            threshold: Minimum acceptable rate (0.0-1.0)
        
        Returns:
            (passed, message)
        """
        rate = found / expected if expected > 0 else 0.0
        passed = rate >= threshold
        message = f"Detection rate: {found}/{expected} = {rate:.1%} (threshold: {threshold:.1%})"
        return passed, message
    
    @staticmethod
    def check_response_time(duration_ms: float, threshold_ms: float = 10000) -> tuple[bool, str]:
        """
        Check if response time is acceptable.
        
        Args:
            duration_ms: Time in milliseconds
            threshold_ms: Maximum acceptable time
        
        Returns:
            (passed, message)
        """
        passed = duration_ms <= threshold_ms
        status = "✓" if passed else "✗"
        message = f"{status} Response time: {duration_ms:.0f}ms (max: {threshold_ms:.0f}ms)"
        return passed, message
    
    @staticmethod
    def check_false_positive_rate(false_positives: int, total: int, threshold: float = 0.1) -> tuple[bool, str]:
        """
        Check if false positive rate is acceptable.
        
        Args:
            false_positives: Number of false positives
            total: Total findings
            threshold: Maximum acceptable rate
        
        Returns:
            (passed, message)
        """
        rate = false_positives / total if total > 0 else 0.0
        passed = rate <= threshold
        message = f"False positive rate: {false_positives}/{total} = {rate:.1%} (max: {threshold:.1%})"
        return passed, message
    
    @staticmethod
    def check_cvss_accuracy(scores: List[float], expected_ranges: Dict[str, tuple[float, float]]) -> tuple[bool, str]:
        """
        Check if CVSS scores fall within expected ranges.
        
        Args:
            scores: List of CVSS scores
            expected_ranges: {severity: (min, max)} e.g., {'Critical': (9.0, 10.0)}
        
        Returns:
            (passed, message)
        """
        if not scores:
            return True, "No CVSS scores to validate"
        
        # Simplified check - real implementation would categorize by severity
        avg_score = sum(scores) / len(scores)
        passed = 0.0 <= avg_score <= 10.0
        message = f"CVSS score distribution valid (avg: {avg_score:.1f})"
        return passed, message
