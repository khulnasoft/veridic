"""
Phase 2.4: Multi-Finding Aggregator
Combines multiple static and runtime findings per asset with confidence weighting.
Deterministic ordering ensures reproducible aggregation across 3+ runs.
"""

import logging
import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class FindingSource(Enum):
    """Source of finding"""
    STATIC = "static"
    RUNTIME = "runtime"
    COMBINED = "combined"


@dataclass
class AggregatedFinding:
    """Single aggregated finding with confidence weights"""
    aggregation_id: str  # Unique ID for this aggregation
    asset_id: str  # Identifier for the asset (file path, function name, etc.)
    finding_type: str  # e.g., "sql_injection", "xss", "race_condition"
    severity: str  # "critical", "high", "medium", "low"
    static_confidence: float  # 0.0-1.0 confidence from static analysis
    runtime_confidence: float  # 0.0-1.0 confidence from runtime evidence
    combined_confidence: float  # Weighted average of static + runtime
    static_findings: List[Dict] = field(default_factory=list)  # Original static findings
    runtime_findings: List[Dict] = field(default_factory=list)  # Original runtime findings
    evidence_chain_ids: List[str] = field(default_factory=list)  # Links to evidence chains
    exploit_chain_detected: bool = False
    has_negative_proof: bool = False
    metadata: Dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    determinism_hash: str = ""  # SHA256 hash for reproducibility validation
    
    def to_dict(self) -> Dict:
        """Convert to dictionary with deterministic ordering"""
        return {
            "aggregation_id": self.aggregation_id,
            "asset_id": self.asset_id,
            "finding_type": self.finding_type,
            "severity": self.severity,
            "static_confidence": self.static_confidence,
            "runtime_confidence": self.runtime_confidence,
            "combined_confidence": self.combined_confidence,
            "static_findings": sorted(self.static_findings, key=lambda x: x.get("id", "")),
            "runtime_findings": sorted(self.runtime_findings, key=lambda x: x.get("id", "")),
            "evidence_chain_ids": sorted(self.evidence_chain_ids),
            "exploit_chain_detected": self.exploit_chain_detected,
            "has_negative_proof": self.has_negative_proof,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "determinism_hash": self.determinism_hash,
        }
    
    def compute_determinism_hash(self) -> str:
        """Compute SHA256 hash for determinism validation"""
        # Exclude hash itself to avoid circular dependency
        data = {
            "aggregation_id": self.aggregation_id,
            "asset_id": self.asset_id,
            "finding_type": self.finding_type,
            "severity": self.severity,
            "static_confidence": round(self.static_confidence, 4),
            "runtime_confidence": round(self.runtime_confidence, 4),
            "combined_confidence": round(self.combined_confidence, 4),
            "exploit_chain_detected": self.exploit_chain_detected,
            "has_negative_proof": self.has_negative_proof,
        }
        
        import json
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class MultiAssetAggregation:
    """Container for aggregated findings across multiple assets"""
    aggregation_run_id: str
    total_assets: int
    findings_per_asset: Dict[str, List[AggregatedFinding]] = field(default_factory=dict)
    total_findings: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    run_hash: str = ""  # SHA256 of all aggregation hashes for full determinism
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "aggregation_run_id": self.aggregation_run_id,
            "total_assets": self.total_assets,
            "findings_per_asset": {
                asset_id: [f.to_dict() for f in findings]
                for asset_id, findings in self.findings_per_asset.items()
            },
            "total_findings": self.total_findings,
            "timestamp": self.timestamp,
            "run_hash": self.run_hash,
        }
    
    def compute_run_hash(self) -> str:
        """Compute hash of all findings for full run determinism"""
        hashes = []
        for asset_id in sorted(self.findings_per_asset.keys()):
            for finding in sorted(
                self.findings_per_asset[asset_id],
                key=lambda f: f.aggregation_id
            ):
                hashes.append(finding.compute_determinism_hash())
        
        content = "|".join(hashes)
        return hashlib.sha256(content.encode()).hexdigest()


class MultiFinidngAggregator:
    """
    Combines multiple static and runtime findings per asset.
    Ensures deterministic ordering and confidence weighting.
    """
    
    def __init__(self):
        self.findings_by_asset: Dict[str, List[AggregatedFinding]] = {}
        self.aggregation_counter = 0
    
    def aggregate(
        self,
        asset_id: str,
        static_findings: List[Dict],
        runtime_findings: List[Dict],
        evidence_chains: Optional[List[Dict]] = None,
    ) -> AggregatedFinding:
        """
        Aggregate static and runtime findings for a single asset.
        
        Args:
            asset_id: Identifier for the asset (file path, function name, etc.)
            static_findings: List of static analysis findings
            runtime_findings: List of runtime evidence findings
            evidence_chains: Optional evidence chain data
            
        Returns:
            Single AggregatedFinding combining both sources
        """
        logger.info(f"Aggregating findings for asset: {asset_id}")
        
        # Deterministic sorting - critical for reproducibility
        static_sorted = sorted(static_findings, key=lambda f: f.get("id", ""))
        runtime_sorted = sorted(runtime_findings, key=lambda f: f.get("id", ""))
        
        # Extract finding type (should be consistent across all findings for same vuln)
        finding_type = self._extract_finding_type(static_sorted, runtime_sorted)
        
        # Compute confidence scores
        static_conf = self._compute_static_confidence(static_sorted)
        runtime_conf = self._compute_runtime_confidence(runtime_sorted)
        combined_conf = self._combine_confidence(static_conf, runtime_conf)
        
        # Determine severity
        severity = self._determine_severity(static_sorted, runtime_sorted, combined_conf)
        
        # Check for exploit chains and negative proof
        exploit_chain = self._detect_exploit_chain(evidence_chains or [])
        has_negative = self._detect_negative_proof(runtime_sorted)
        
        # Create aggregated finding
        self.aggregation_counter += 1
        agg_id = f"{asset_id}_agg_{self.aggregation_counter}"
        
        finding = AggregatedFinding(
            aggregation_id=agg_id,
            asset_id=asset_id,
            finding_type=finding_type,
            severity=severity,
            static_confidence=static_conf,
            runtime_confidence=runtime_conf,
            combined_confidence=combined_conf,
            static_findings=static_sorted,
            runtime_findings=runtime_sorted,
            evidence_chain_ids=[c.get("id", "") for c in (evidence_chains or [])],
            exploit_chain_detected=exploit_chain,
            has_negative_proof=has_negative,
        )
        
        # Compute determinism hash
        finding.determinism_hash = finding.compute_determinism_hash()
        
        # Store for later aggregation
        if asset_id not in self.findings_by_asset:
            self.findings_by_asset[asset_id] = []
        self.findings_by_asset[asset_id].append(finding)
        
        logger.info(
            f"Aggregated finding for {asset_id}: "
            f"type={finding_type}, severity={severity}, combined_conf={combined_conf:.2f}"
        )
        
        return finding
    
    def aggregate_batch(
        self,
        assets_data: Dict[str, Dict],
        run_id: str,
    ) -> MultiAssetAggregation:
        """
        Aggregate findings across multiple assets (deterministic batch operation).
        
        Args:
            assets_data: Dict mapping asset_id to {"static": [...], "runtime": [...], "evidence_chains": [...]}
            run_id: Unique ID for this aggregation run
            
        Returns:
            MultiAssetAggregation containing all aggregated findings
        """
        logger.info(f"Starting batch aggregation run: {run_id}")
        
        # Clear previous state
        self.findings_by_asset = {}
        self.aggregation_counter = 0
        
        # Deterministic processing order
        for asset_id in sorted(assets_data.keys()):
            asset_info = assets_data[asset_id]
            self.aggregate(
                asset_id=asset_id,
                static_findings=asset_info.get("static", []),
                runtime_findings=asset_info.get("runtime", []),
                evidence_chains=asset_info.get("evidence_chains", None),
            )
        
        # Create batch aggregation
        batch = MultiAssetAggregation(
            aggregation_run_id=run_id,
            total_assets=len(assets_data),
            findings_per_asset=self.findings_by_asset,
            total_findings=sum(len(f) for f in self.findings_by_asset.values()),
        )
        
        # Compute run hash for full determinism
        batch.run_hash = batch.compute_run_hash()
        
        logger.info(
            f"Batch aggregation complete: {batch.total_assets} assets, "
            f"{batch.total_findings} findings, run_hash={batch.run_hash[:16]}..."
        )
        
        return batch
    
    def _extract_finding_type(
        self,
        static_findings: List[Dict],
        runtime_findings: List[Dict],
    ) -> str:
        """Extract finding type from sorted findings"""
        if static_findings:
            return static_findings[0].get("type", "unknown")
        if runtime_findings:
            return runtime_findings[0].get("type", "unknown")
        return "unknown"
    
    def _compute_static_confidence(self, findings: List[Dict]) -> float:
        """Compute confidence from static analysis findings"""
        if not findings:
            return 0.0
        
        # Average confidence from all findings, with weights
        confidences = [f.get("confidence", 0.5) for f in findings]
        return sum(confidences) / len(confidences) if confidences else 0.5
    
    def _compute_runtime_confidence(self, findings: List[Dict]) -> float:
        """Compute confidence from runtime evidence"""
        if not findings:
            return 0.0
        
        # Runtime evidence is stronger indicator when present
        confidences = [f.get("confidence", 0.7) for f in findings]
        return sum(confidences) / len(confidences) if confidences else 0.7
    
    def _combine_confidence(self, static_conf: float, runtime_conf: float) -> float:
        """Combine static and runtime confidence with weighting"""
        # Weighted average: prefer runtime evidence when both present
        if static_conf > 0 and runtime_conf > 0:
            return (static_conf * 0.3) + (runtime_conf * 0.7)
        elif runtime_conf > 0:
            return runtime_conf
        else:
            return static_conf
    
    def _determine_severity(
        self,
        static_findings: List[Dict],
        runtime_findings: List[Dict],
        combined_conf: float,
    ) -> str:
        """Determine severity from findings and confidence"""
        severities = ["critical", "high", "medium", "low"]
        
        # Collect severity levels
        levels = []
        for finding in static_findings:
            if finding.get("severity") in severities:
                levels.append(severities.index(finding.get("severity")))
        for finding in runtime_findings:
            if finding.get("severity") in severities:
                levels.append(severities.index(finding.get("severity")))
        
        if not levels:
            return "medium"  # Default
        
        # Use most severe (lowest index)
        max_severity_idx = min(levels)
        return severities[max_severity_idx]
    
    def _detect_exploit_chain(self, evidence_chains: List[Dict]) -> bool:
        """Check if evidence chains indicate exploit"""
        for chain in evidence_chains:
            if chain.get("is_exploit", False):
                return True
        return False
    
    def _detect_negative_proof(self, runtime_findings: List[Dict]) -> bool:
        """Check for evidence of mitigation (negative proof)"""
        for finding in runtime_findings:
            if finding.get("evidence_type") == "sanitized_input":
                return True
            if finding.get("evidence_type") == "network_isolated":
                return True
        return False
