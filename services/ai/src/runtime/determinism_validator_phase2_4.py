"""
Phase 2.4: Determinism Validator
Validates 3-run reproducibility with strict checks on ordering, hashing, and severity.
Ensures Phase 2.4 determinism contract is maintained.
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class DeterminismCheckType(Enum):
    """Types of determinism checks"""
    HASH_CONSISTENCY = "hash_consistency"
    ORDERING_CONSISTENCY = "ordering_consistency"
    SEVERITY_CONSISTENCY = "severity_consistency"
    VERDICT_CONSISTENCY = "verdict_consistency"


@dataclass
class DeterminismCheck:
    """Result of a single determinism check"""
    check_type: DeterminismCheckType
    passed: bool
    message: str
    details: Dict = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class DeterminismValidationReport:
    """Complete determinism validation report for 3+ runs"""
    run_count: int
    checks: List[DeterminismCheck]
    overall_passed: bool
    errors: List[str]
    severity_variance: Dict[str, float]  # aggregation_id -> variance
    hash_consistency: Dict[str, bool]  # aggregation_id -> hash_match
    
    def summary(self) -> str:
        """Generate summary text"""
        passed_count = sum(1 for c in self.checks if c.passed)
        total_count = len(self.checks)
        
        return (
            f"Determinism Validation ({self.run_count} runs)\n"
            f"Checks: {passed_count}/{total_count} passed\n"
            f"Overall: {'PASS' if self.overall_passed else 'FAIL'}\n"
            f"Errors: {len(self.errors)}"
        )


class Phase2_4DeterminismValidator:
    """
    Validates reproducibility across 3+ runs of Phase 2.4 pipeline.
    Strict checks on aggregation, scoring, and verdicts.
    """
    
    # Max allowed severity variance across runs (strict ±0 for Phase 2.4)
    MAX_SEVERITY_VARIANCE = 0.0
    
    def __init__(self):
        logger.info("Initialized Phase 2.4 DeterminismValidator")
    
    def validate_3_runs(
        self,
        run1_results: Dict,  # batch aggregation + scoring + verdicts
        run2_results: Dict,
        run3_results: Dict,
    ) -> DeterminismValidationReport:
        """
        Validate reproducibility across 3 runs.
        
        Args:
            run1_results: Dict with 'aggregations', 'scores', 'verdicts'
            run2_results: Dict with 'aggregations', 'scores', 'verdicts'
            run3_results: Dict with 'aggregations', 'scores', 'verdicts'
            
        Returns:
            DeterminismValidationReport
        """
        logger.info("Validating Phase 2.4 determinism across 3 runs")
        
        runs = [run1_results, run2_results, run3_results]
        checks = []
        errors = []
        
        try:
            # Check 1: Aggregation hashing
            logger.info("Checking aggregation hash consistency...")
            hash_check = self._check_aggregation_hash_consistency(runs)
            checks.append(hash_check)
            if not hash_check.passed:
                errors.append(f"Aggregation hash mismatch: {hash_check.message}")
            
            # Check 2: Aggregation ordering
            logger.info("Checking aggregation ordering consistency...")
            order_check = self._check_aggregation_ordering(runs)
            checks.append(order_check)
            if not order_check.passed:
                errors.append(f"Aggregation ordering mismatch: {order_check.message}")
            
            # Check 3: Scoring consistency
            logger.info("Checking scoring consistency...")
            score_check = self._check_scoring_consistency(runs)
            checks.append(score_check)
            if not score_check.passed:
                errors.append(f"Scoring mismatch: {score_check.message}")
            
            # Check 4: Verdict consistency
            logger.info("Checking verdict consistency...")
            verdict_check = self._check_verdict_consistency(runs)
            checks.append(verdict_check)
            if not verdict_check.passed:
                errors.append(f"Verdict mismatch: {verdict_check.message}")
            
            # Check 5: Severity variance
            logger.info("Checking severity variance...")
            severity_check, severity_variance = self._check_severity_variance(runs)
            checks.append(severity_check)
            if not severity_check.passed:
                errors.append(f"Severity variance too high: {severity_check.message}")
        
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            errors.append(f"Validation error: {str(e)}")
            severity_variance = {}
        
        overall_passed = len(errors) == 0 and all(c.passed for c in checks)
        
        report = DeterminismValidationReport(
            run_count=3,
            checks=checks,
            overall_passed=overall_passed,
            errors=errors,
            severity_variance=severity_variance,
            hash_consistency=self._compute_hash_consistency(runs),
        )
        
        logger.info(report.summary())
        
        return report
    
    def _check_aggregation_hash_consistency(
        self,
        runs: List[Dict],
    ) -> DeterminismCheck:
        """Check that aggregation run hashes match across runs"""
        hashes = []
        details = {}
        
        for i, run in enumerate(runs):
            aggregation = run.get("aggregation", {})
            run_hash = aggregation.get("run_hash", "")
            hashes.append(run_hash)
            details[f"run_{i+1}_hash"] = run_hash[:16] + "..." if run_hash else "missing"
        
        all_match = len(set(hashes)) == 1 and hashes[0]
        
        return DeterminismCheck(
            check_type=DeterminismCheckType.HASH_CONSISTENCY,
            passed=all_match,
            message=(
                f"All aggregation hashes match: {hashes[0][:16]}..."
                if all_match else f"Hash mismatch: {hashes}"
            ),
            details=details,
        )
    
    def _check_aggregation_ordering(
        self,
        runs: List[Dict],
    ) -> DeterminismCheck:
        """Check that aggregation ordering is consistent"""
        orderings = []
        
        for run in runs:
            aggregation = run.get("aggregation", {})
            findings_per_asset = aggregation.get("findings_per_asset", {})
            ordering = sorted(findings_per_asset.keys())
            orderings.append(ordering)
        
        all_match = all(o == orderings[0] for o in orderings)
        
        return DeterminismCheck(
            check_type=DeterminismCheckType.ORDERING_CONSISTENCY,
            passed=all_match,
            message=(
                f"Aggregation ordering consistent ({len(orderings[0])} assets)"
                if all_match else f"Ordering mismatch: {orderings}"
            ),
        )
    
    def _check_scoring_consistency(
        self,
        runs: List[Dict],
    ) -> DeterminismCheck:
        """Check that enhanced scores are consistent"""
        all_scores = []
        
        for run in runs:
            scores = run.get("scores", {})
            score_hashes = {}
            for agg_id in sorted(scores.keys()):
                score = scores[agg_id]
                score_hashes[agg_id] = score.get("scoring_hash", "")
            all_scores.append(score_hashes)
        
        # Check if all score hashes match
        all_match = True
        for agg_id in all_scores[0].keys():
            hashes = [scores.get(agg_id, "") for scores in all_scores]
            if len(set(hashes)) > 1:
                all_match = False
                break
        
        return DeterminismCheck(
            check_type=DeterminismCheckType.HASH_CONSISTENCY,
            passed=all_match,
            message=(
                f"Scoring hashes consistent across {len(all_scores)} runs"
                if all_match else "Scoring hash mismatch"
            ),
        )
    
    def _check_verdict_consistency(
        self,
        runs: List[Dict],
    ) -> DeterminismCheck:
        """Check that AI verdicts are consistent"""
        all_verdicts = []
        
        for run in runs:
            verdicts = run.get("verdicts", {})
            verdict_data = {}
            for agg_id in sorted(verdicts.keys()):
                verdict = verdicts[agg_id]
                # Key deterministic fields
                verdict_data[agg_id] = (
                    verdict.get("ai_verdict_severity", ""),
                    round(verdict.get("confidence", 0.0), 4),
                    verdict.get("hash_value", ""),
                )
            all_verdicts.append(verdict_data)
        
        # Check if all verdicts match
        all_match = all(v == all_verdicts[0] for v in all_verdicts)
        
        return DeterminismCheck(
            check_type=DeterminismCheckType.VERDICT_CONSISTENCY,
            passed=all_match,
            message=(
                f"Verdicts consistent across {len(all_verdicts)} runs"
                if all_match else "Verdict mismatch detected"
            ),
        )
    
    def _check_severity_variance(
        self,
        runs: List[Dict],
    ) -> Tuple[DeterminismCheck, Dict[str, float]]:
        """Check severity variance (strict ±0 for Phase 2.4)"""
        severity_variance = {}
        all_match = True
        
        # Collect severities per aggregation across runs
        for agg_id in self._get_all_agg_ids(runs):
            severities = []
            for run in runs:
                # Get from aggregation
                aggregation = run.get("aggregation", {})
                findings = aggregation.get("findings_per_asset", {})
                
                for asset_findings in findings.values():
                    for finding in asset_findings:
                        if finding.get("aggregation_id") == agg_id:
                            severities.append(finding.get("severity", "unknown"))
            
            if severities:
                # For Phase 2.4, require all severities to be identical
                if len(set(severities)) > 1:
                    severity_variance[agg_id] = 1.0  # Max variance
                    all_match = False
                else:
                    severity_variance[agg_id] = 0.0  # Perfect match
        
        return DeterminismCheck(
            check_type=DeterminismCheckType.SEVERITY_CONSISTENCY,
            passed=all_match,
            message=(
                "Severity perfectly consistent (0 variance) across all runs"
                if all_match else f"Severity variance in {sum(1 for v in severity_variance.values() if v > 0)} findings"
            ),
            details={"severity_variance": severity_variance},
        ), severity_variance
    
    def _compute_hash_consistency(
        self,
        runs: List[Dict],
    ) -> Dict[str, bool]:
        """Compute hash consistency per aggregation ID"""
        consistency = {}
        
        for agg_id in self._get_all_agg_ids(runs):
            hashes = []
            for run in runs:
                aggregation = run.get("aggregation", {})
                findings = aggregation.get("findings_per_asset", {})
                
                for asset_findings in findings.values():
                    for finding in asset_findings:
                        if finding.get("aggregation_id") == agg_id:
                            hashes.append(finding.get("determinism_hash", ""))
            
            consistency[agg_id] = len(set(hashes)) == 1 and hashes[0]
        
        return consistency
    
    def _get_all_agg_ids(self, runs: List[Dict]) -> set:
        """Get all unique aggregation IDs across runs"""
        agg_ids = set()
        for run in runs:
            aggregation = run.get("aggregation", {})
            findings = aggregation.get("findings_per_asset", {})
            for asset_findings in findings.values():
                for finding in asset_findings:
                    agg_ids.add(finding.get("aggregation_id", ""))
        return agg_ids
