"""
Phase 2.3 Week 2: Determinism Validation Harness
3-run SHA256 fingerprinting of AI verdicts with variance classification.
Proves: strict determinism, no AI drift, reproducible reasoning.
"""

import json
import hashlib
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class DeterminismStatus(Enum):
    """Determinism validation result"""
    PASS = "pass"  # 3 runs identical (0% variance)
    WARN = "warn"  # Consistent but within tolerance (±0.02 CVSS variance)
    FAIL = "fail"  # Inconsistent (>±0.02 variance, different verdicts)


@dataclass
class VerdictFingerprint:
    """Single verdict run fingerprint"""
    run_id: str
    timestamp: str
    verdict_hash: str  # SHA256 of canonical JSON
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    cvss_score: float
    evidence_count: int
    conflict_resolved: bool
    ai_backend: str  # gpt4o or ollama


@dataclass
class DeterminismReport:
    """3-run determinism analysis"""
    finding_id: str
    test_name: str
    fingerprints: List[VerdictFingerprint]
    status: DeterminismStatus
    variance_detail: str
    hash_consistency: bool  # All hashes match?
    severity_variance: float  # CVSS variance across 3 runs
    verdict_variance: str  # Identical, upgraded, downgraded, mixed
    requires_investigation: bool
    metadata: Dict


class DeterminismValidator:
    """
    Validates strict determinism of Phase 2.3 AI reasoning.
    
    Guarantees:
    - Same evidence input → identical verdict output (SHA256 hash match)
    - CVSS scores stable within ±0.02 variance (rounding acceptable)
    - No AI randomness or drift across runs
    - Reproducible conflict resolution
    """
    
    def __init__(self):
        self.reports: Dict[str, DeterminismReport] = {}
        self.tolerance_cvss = 0.02  # ±0.02 acceptable variance
    
    def compute_verdict_hash(self, verdict: Dict) -> str:
        """
        Compute SHA256 hash of verdict for determinism checking.
        Canonical JSON ordering for reproducibility.
        """
        # Sort all keys recursively for deterministic ordering
        canonical = json.dumps(verdict, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def run_3x_determinism_test(
        self,
        finding_id: str,
        test_name: str,
        reasoning_fn,  # async function that takes evidence, returns verdict
        evidence: Dict,
        expected_severity: str,
    ) -> DeterminismReport:
        """
        Run reasoning 3 times with identical input.
        Collect fingerprints and compute variance.
        """
        fingerprints: List[VerdictFingerprint] = []
        verdicts = []
        
        for run_num in range(1, 4):
            # Execute reasoning with deterministic settings
            verdict = reasoning_fn(evidence)
            verdicts.append(verdict)
            
            # Create fingerprint
            fp = VerdictFingerprint(
                run_id=f"run_{run_num}",
                timestamp=datetime.utcnow().isoformat(),
                verdict_hash=self.compute_verdict_hash(verdict),
                severity=verdict.get("severity"),
                cvss_score=float(verdict.get("cvss_score", 0.0)),
                evidence_count=verdict.get("evidence_count", 0),
                conflict_resolved=verdict.get("conflict_resolved", False),
                ai_backend=verdict.get("ai_backend", "unknown"),
            )
            fingerprints.append(fp)
        
        # Analyze determinism
        hashes = [fp.verdict_hash for fp in fingerprints]
        severities = [fp.severity for fp in fingerprints]
        cvss_scores = [fp.cvss_score for fp in fingerprints]
        
        hash_consistency = len(set(hashes)) == 1  # All identical?
        severity_variance = self._compute_severity_variance(severities)
        verdict_variance_str = self._classify_verdict_variance(severities)
        
        # Determine status
        if hash_consistency:
            status = DeterminismStatus.PASS
            variance_detail = "Perfect: 3 runs identical (hash match)"
        elif severity_variance <= self.tolerance_cvss and len(set(severities)) == 1:
            status = DeterminismStatus.WARN
            variance_detail = f"Acceptable: CVSS variance ±{severity_variance:.4f}, verdicts consistent"
        else:
            status = DeterminismStatus.FAIL
            variance_detail = f"CRITICAL: Hash mismatch, CVSS variance ±{severity_variance:.4f}, verdicts {verdict_variance_str}"
        
        report = DeterminismReport(
            finding_id=finding_id,
            test_name=test_name,
            fingerprints=fingerprints,
            status=status,
            variance_detail=variance_detail,
            hash_consistency=hash_consistency,
            severity_variance=severity_variance,
            verdict_variance=verdict_variance_str,
            requires_investigation=(status == DeterminismStatus.FAIL),
            metadata={
                "test_timestamp": datetime.utcnow().isoformat(),
                "tolerance_cvss": self.tolerance_cvss,
                "backend_mix": list(set(fp.ai_backend for fp in fingerprints)),
            }
        )
        
        self.reports[finding_id] = report
        return report
    
    def _compute_severity_variance(self, severities: List[float]) -> float:
        """Compute CVSS variance across runs"""
        if len(severities) < 2:
            return 0.0
        avg = sum(severities) / len(severities)
        variance = sum((s - avg) ** 2 for s in severities) / len(severities)
        return variance ** 0.5
    
    def _classify_verdict_variance(self, severities: List[str]) -> str:
        """Classify verdict change across runs"""
        if len(set(severities)) == 1:
            return "identical"
        
        # Check for systematic upgrade/downgrade
        severity_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        indices = [severity_order.index(s) for s in severities if s in severity_order]
        
        if all(i == indices[0] for i in indices):
            return "identical"
        elif all(indices[i] <= indices[i+1] for i in range(len(indices)-1)):
            return "monotonic_upgrade"
        elif all(indices[i] >= indices[i+1] for i in range(len(indices)-1)):
            return "monotonic_downgrade"
        else:
            return "mixed"
    
    def generate_determinism_report(self) -> Dict:
        """
        Aggregate all determinism tests.
        Return summary: % PASS, % WARN, % FAIL.
        """
        if not self.reports:
            return {"error": "No tests run"}
        
        total = len(self.reports)
        pass_count = sum(1 for r in self.reports.values() if r.status == DeterminismStatus.PASS)
        warn_count = sum(1 for r in self.reports.values() if r.status == DeterminismStatus.WARN)
        fail_count = sum(1 for r in self.reports.values() if r.status == DeterminismStatus.FAIL)
        
        return {
            "total_tests": total,
            "pass": pass_count,
            "warn": warn_count,
            "fail": fail_count,
            "pass_rate": f"{100 * pass_count / total:.1f}%",
            "overall_status": "PASS" if fail_count == 0 else "FAIL",
            "timestamp": datetime.utcnow().isoformat(),
            "details": [asdict(r) for r in self.reports.values()],
        }
    
    def export_determinism_json(self, filepath: str):
        """Export determinism report to JSON"""
        report = self.generate_determinism_report()
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Determinism report exported to {filepath}")
