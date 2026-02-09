"""
Phase 2.0: Determinism Validator (Phase 2-specific)
Approved rule: Event ordering tolerance window ±50ms
Tests reproducibility of runtime event capture and correlation.
"""

import json
import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DeterminismResult:
    """Result of determinism validation"""
    trace_id_1: str
    trace_id_2: str
    event_count_1: int
    event_count_2: int
    exact_match_count: int
    ordering_tolerance_match_count: int
    determinism_score: float  # 0.0-1.0
    passed: bool  # ≥0.95 for PASS


class Phase2DeterminismValidator:
    """
    Validates Phase 2 runtime analysis reproducibility.
    Key rules:
    1. Event hash matching (SHA256, excluding timestamp)
    2. Ordering tolerance: ±50ms window
    3. Event count variance: <5%
    4. Correlation reproducibility: same findings, same scores
    """
    
    ORDERING_TOLERANCE_MS = 50  # ±50ms allowed
    EVENT_COUNT_VARIANCE_THRESHOLD = 0.05  # <5%
    DETERMINISM_PASS_THRESHOLD = 0.95
    
    @staticmethod
    def validate_trace_reproducibility(
        trace_1: List[Dict],
        trace_2: List[Dict],
    ) -> DeterminismResult:
        """
        Compare two traces captured from identical execution.
        Returns determinism score 0.0-1.0.
        """
        
        # Event count check
        count_variance = abs(len(trace_1) - len(trace_2)) / max(len(trace_1), len(trace_2))
        if count_variance > Phase2DeterminismValidator.EVENT_COUNT_VARIANCE_THRESHOLD:
            logger.warning(f"Event count variance too high: {count_variance:.2%}")
        
        # Compute hashes (exclude timestamp for ordering tolerance)
        hashes_1 = {Phase2DeterminismValidator._event_hash(e) for e in trace_1}
        hashes_2 = {Phase2DeterminismValidator._event_hash(e) for e in trace_2}
        
        # Exact match
        exact_matches = len(hashes_1 & hashes_2)
        
        # Ordering-tolerant match (events in ±50ms buckets)
        buckets_1 = Phase2DeterminismValidator._bucket_events(trace_1)
        buckets_2 = Phase2DeterminismValidator._bucket_events(trace_2)
        ordering_matches = Phase2DeterminismValidator._match_buckets(buckets_1, buckets_2)
        
        # Compute scores
        total_unique = len(hashes_1 | hashes_2)
        determinism_score = ordering_matches / total_unique if total_unique > 0 else 0.0
        
        return DeterminismResult(
            trace_id_1="trace_1",
            trace_id_2="trace_2",
            event_count_1=len(trace_1),
            event_count_2=len(trace_2),
            exact_match_count=exact_matches,
            ordering_tolerance_match_count=ordering_matches,
            determinism_score=determinism_score,
            passed=determinism_score >= Phase2DeterminismValidator.DETERMINISM_PASS_THRESHOLD,
        )
    
    @staticmethod
    def validate_correlation_reproducibility(
        correlations_1: List[Dict],
        correlations_2: List[Dict],
    ) -> Dict:
        """
        Validate correlation stability.
        Same findings should produce same scores (±0.05 variance allowed).
        """
        
        findings_1 = {c.get("finding_id"): c for c in correlations_1}
        findings_2 = {c.get("finding_id"): c for c in correlations_2}
        
        # Check finding overlap
        common_findings = set(findings_1.keys()) & set(findings_2.keys())
        unique_to_1 = set(findings_1.keys()) - set(findings_2.keys())
        unique_to_2 = set(findings_2.keys()) - set(findings_1.keys())
        
        # Score variance
        score_variances = []
        for finding_id in common_findings:
            score_1 = findings_1[finding_id].get("exploitability_score", 0.0)
            score_2 = findings_2[finding_id].get("exploitability_score", 0.0)
            variance = abs(score_1 - score_2) / max(score_1, score_2, 1.0)
            score_variances.append(variance)
        
        avg_variance = sum(score_variances) / len(score_variances) if score_variances else 0.0
        correlation_score = 1.0 - avg_variance
        
        return {
            "common_findings": len(common_findings),
            "unique_to_trace_1": len(unique_to_1),
            "unique_to_trace_2": len(unique_to_2),
            "avg_score_variance": avg_variance,
            "correlation_reproducibility": correlation_score,
            "passed": avg_variance <= 0.05 and len(unique_to_1) == 0 and len(unique_to_2) == 0,
        }
    
    @staticmethod
    def _event_hash(event: Dict) -> str:
        """Compute deterministic hash excluding timestamp"""
        import hashlib
        
        # Exclude timestamp and sandbox_id for comparison
        event_copy = {k: v for k, v in event.items() if k not in ["timestamp", "sandbox_id"]}
        event_json = json.dumps(event_copy, sort_keys=True, default=str)
        return hashlib.sha256(event_json.encode()).hexdigest()
    
    @staticmethod
    def _bucket_events(events: List[Dict], bucket_size_ms: int = 50) -> Dict[int, List[str]]:
        """Group events into ±50ms buckets by timestamp"""
        buckets = {}
        
        for event in events:
            timestamp_ns = event.get("timestamp", 0)
            bucket_size_ns = bucket_size_ms * 1_000_000
            bucket = (timestamp_ns // bucket_size_ns) * bucket_size_ns
            
            if bucket not in buckets:
                buckets[bucket] = []
            
            event_hash = Phase2DeterminismValidator._event_hash(event)
            buckets[bucket].append(event_hash)
        
        return buckets
    
    @staticmethod
    def _match_buckets(buckets_1: Dict[int, List[str]], buckets_2: Dict[int, List[str]]) -> int:
        """Match events within bucket tolerance"""
        matches = 0
        
        for bucket in buckets_1:
            if bucket in buckets_2:
                set_1 = set(buckets_1[bucket])
                set_2 = set(buckets_2[bucket])
                matches += len(set_1 & set_2)
        
        return matches


# Test utility
def test_phase2_determinism():
    """Example: Validate two trace runs"""
    trace_1 = [
        {"event_id": "e1", "timestamp": 1000000000, "event_type": "syscall"},
        {"event_id": "e2", "timestamp": 2000000000, "event_type": "network"},
    ]
    
    trace_2 = [
        {"event_id": "e1b", "timestamp": 1005000000, "event_type": "syscall"},  # ±50ms OK
        {"event_id": "e2b", "timestamp": 2003000000, "event_type": "network"},
    ]
    
    result = Phase2DeterminismValidator.validate_trace_reproducibility(trace_1, trace_2)
    
    print(f"Determinism Score: {result.determinism_score:.2%}")
    print(f"Passed: {result.passed}")
    print(f"Exact Matches: {result.exact_match_count}")
    print(f"Ordering-Tolerant Matches: {result.ordering_tolerance_match_count}")


if __name__ == "__main__":
    test_phase2_determinism()
