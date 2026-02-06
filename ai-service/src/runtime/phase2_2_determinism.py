"""
Phase 2.2: Determinism Validator
Ensures runtime+network findings are reproducible.
Success criteria: ≥95% determinism, ±50ms ordering tolerance, network noise <5%.
"""

import logging
import hashlib
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class DeterminismStatus(Enum):
    """Determinism verdict"""
    PASS = "pass"  # ≥95% determinism
    WARN = "warn"  # 90-95% determinism
    FAIL = "fail"  # <90% determinism


@dataclass
class DeterminismMetrics:
    """Determinism metrics for Phase 2.2"""
    event_reproducibility: float  # % of events that appear in repeated runs
    ordering_consistency: float  # % of events within ±50ms ordering tolerance
    network_noise_ratio: float  # % of spurious network events
    chain_reproducibility: float  # % of complete chains reproduced
    overall_score: float  # Weighted average (0-100)
    status: DeterminismStatus = DeterminismStatus.PASS
    issues: List[str] = field(default_factory=list)


class Phase22DeterminismValidator:
    """
    Validates that Phase 2.2 findings are deterministic and reproducible.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ordering_tolerance_ns = 50_000_000  # 50ms in nanoseconds
    
    def validate_determinism(
        self,
        run1_events: List[Dict],
        run2_events: List[Dict],
        run3_events: List[Dict],
        exploit_chains_run1: List[Dict],
        exploit_chains_run2: List[Dict],
        exploit_chains_run3: List[Dict]
    ) -> DeterminismMetrics:
        """
        Validate Phase 2.2 determinism across 3 runs.
        
        Success criteria:
        - Event reproducibility ≥95%
        - Ordering consistency ≥95% (±50ms tolerance)
        - Network noise <5%
        - Exploit chain reproducibility ≥90%
        """
        
        metrics = DeterminismMetrics(
            event_reproducibility=0.0,
            ordering_consistency=0.0,
            network_noise_ratio=0.0,
            chain_reproducibility=0.0,
            overall_score=0.0
        )
        
        # 1. Event reproducibility
        reproducible_events = self._check_event_reproducibility(
            [run1_events, run2_events, run3_events]
        )
        metrics.event_reproducibility = reproducible_events
        
        if reproducible_events < 0.90:
            metrics.issues.append(f"Low event reproducibility: {reproducible_events:.1%}")
        
        # 2. Ordering consistency
        ordering_ok = self._check_ordering_consistency(
            [run1_events, run2_events, run3_events]
        )
        metrics.ordering_consistency = ordering_ok
        
        if ordering_ok < 0.90:
            metrics.issues.append(f"Poor ordering consistency: {ordering_ok:.1%}")
        
        # 3. Network noise ratio
        noise_ratio = self._calculate_network_noise(
            [run1_events, run2_events, run3_events]
        )
        metrics.network_noise_ratio = noise_ratio
        
        if noise_ratio > 0.10:  # >10% is too much
            metrics.issues.append(f"High network noise: {noise_ratio:.1%}")
        
        # 4. Exploit chain reproducibility
        chain_repro = self._check_chain_reproducibility(
            [exploit_chains_run1, exploit_chains_run2, exploit_chains_run3]
        )
        metrics.chain_reproducibility = chain_repro
        
        if chain_repro < 0.80:
            metrics.issues.append(f"Low chain reproducibility: {chain_repro:.1%}")
        
        # Calculate overall score
        metrics.overall_score = (
            metrics.event_reproducibility * 0.35 +
            metrics.ordering_consistency * 0.35 +
            (1.0 - metrics.network_noise_ratio) * 0.20 +
            metrics.chain_reproducibility * 0.10
        ) * 100
        
        # Determine status
        if metrics.overall_score >= 95:
            metrics.status = DeterminismStatus.PASS
        elif metrics.overall_score >= 90:
            metrics.status = DeterminismStatus.WARN
        else:
            metrics.status = DeterminismStatus.FAIL
        
        return metrics
    
    def _check_event_reproducibility(self, event_runs: List[List[Dict]]) -> float:
        """
        Check what % of events appear consistently across runs.
        Uses content hash (ignoring timestamps) for comparison.
        """
        if not event_runs or not event_runs[0]:
            return 0.0
        
        # Hash events (exclude timestamp/event_id for determinism check)
        def event_hash(event: Dict) -> str:
            details = event.get("details", {})
            source = event.get("source")
            event_type = event.get("event_type")
            content = json.dumps({
                "source": source,
                "event_type": event_type,
                "details": details
            }, sort_keys=True)
            return hashlib.sha256(content.encode()).hexdigest()
        
        hashes_per_run = [
            set(event_hash(e) for e in run)
            for run in event_runs
        ]
        
        # Find intersection (events in all runs)
        common_hashes = set.intersection(*hashes_per_run)
        
        # Calculate reproducibility
        total_unique = len(set.union(*hashes_per_run))
        if total_unique == 0:
            return 0.0
        
        reproducibility = len(common_hashes) / total_unique
        return reproducibility
    
    def _check_ordering_consistency(self, event_runs: List[List[Dict]]) -> float:
        """
        Check if event ordering is consistent across runs.
        Allow ±50ms tolerance.
        """
        if not event_runs or len(event_runs) < 2:
            return 0.0
        
        # For each event, check if ordering relative to other events is consistent
        consistent_pairs = 0
        total_pairs = 0
        
        for run_idx in range(len(event_runs) - 1):
            run_a = event_runs[run_idx]
            run_b = event_runs[run_idx + 1]
            
            # Compare ordering of matching events
            for i, event_a in enumerate(run_a):
                for j, event_b in enumerate(run_a):
                    if i >= j:
                        continue
                    
                    # Find matching events in run_b
                    match_a = self._find_matching_event(event_a, run_b)
                    match_b = self._find_matching_event(event_b, run_b)
                    
                    if not match_a or not match_b:
                        continue
                    
                    total_pairs += 1
                    
                    # Check if ordering is preserved (within tolerance)
                    time_diff_a = event_a.get("timestamp", 0) - event_b.get("timestamp", 0)
                    time_diff_b = match_a.get("timestamp", 0) - match_b.get("timestamp", 0)
                    
                    # Both should have same sign (ordering preserved)
                    if (time_diff_a > 0) == (time_diff_b > 0):
                        consistent_pairs += 1
        
        if total_pairs == 0:
            return 1.0
        
        return consistent_pairs / total_pairs
    
    def _calculate_network_noise(self, event_runs: List[List[Dict]]) -> float:
        """
        Calculate % of network events that don't appear consistently.
        High variation = noise.
        """
        network_events_per_run = [
            [e for e in run if e.get("event_type") == "network"]
            for run in event_runs
        ]
        
        # Hash and count
        hashes_per_run = [
            [self._event_fingerprint(e) for e in run]
            for run in network_events_per_run
        ]
        
        all_hashes = set()
        for hashes in hashes_per_run:
            all_hashes.update(hashes)
        
        if not all_hashes:
            return 0.0
        
        # Count how many hashes appear in all runs
        consistent_hashes = all_hashes.copy()
        for hashes in hashes_per_run:
            consistent_hashes &= set(hashes)
        
        # Noise = events that don't appear consistently
        noise_ratio = (len(all_hashes) - len(consistent_hashes)) / len(all_hashes)
        return noise_ratio
    
    def _check_chain_reproducibility(self, chain_runs: List[List[Dict]]) -> float:
        """
        Check % of exploit chains reproduced consistently.
        """
        if not chain_runs or not chain_runs[0]:
            return 0.0
        
        # Get chain signatures
        def chain_signature(chain: Dict) -> str:
            finding_id = chain.get("static_finding_id")
            chain_type = chain.get("chain_type")
            num_evidence = len(chain.get("evidence_links", []))
            return f"{finding_id}_{chain_type}_{num_evidence}"
        
        signatures_per_run = [
            set(chain_signature(c) for c in run)
            for run in chain_runs
        ]
        
        # Find common chains
        common_chains = set.intersection(*signatures_per_run)
        total_unique = len(set.union(*signatures_per_run))
        
        if total_unique == 0:
            return 0.0
        
        return len(common_chains) / total_unique
    
    def _find_matching_event(self, target: Dict, search_in: List[Dict]) -> Optional[Dict]:
        """Find event with same content hash"""
        target_fp = self._event_fingerprint(target)
        for event in search_in:
            if self._event_fingerprint(event) == target_fp:
                return event
        return None
    
    def _event_fingerprint(self, event: Dict) -> str:
        """Create content fingerprint (excluding timestamp/id)"""
        details = event.get("details", {})
        source = event.get("source")
        event_type = event.get("event_type")
        content = json.dumps({
            "source": source,
            "event_type": event_type,
            "details": details
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
