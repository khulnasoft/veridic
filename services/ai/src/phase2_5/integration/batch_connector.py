"""
Batch Connector for Phase 2.4 Integration

Connects Phase 2.5 continuous scoring  with Phase 2.4 batch AI outputs.
Enables seamless integration between batch analysis and real-time scoring.
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..scoring.continuous_scoring import ContinuousScoringEngine, Finding, ThreatScore


class BatchConnector:
    """
    Connects Phase 2.4 batch outputs to Phase 2.5 continuous scoring.
    
    Supports:
    - Loading batch analysis results
    - Converting to continuous scoring format
    - Aggregating multi-batch results
    """
    
    def __init__(self, scoring_engine: Optional[ContinuousScoringEngine] = None):
        """
        Initialize batch connector.
        
        Args:
            scoring_engine: Optional scoring engine (creates new if None)
        """
        self.scoring_engine = scoring_engine or ContinuousScoringEngine()
    
    def load_batch_results(self, file_path: str) -> Dict[str, Any]:
        """
        Load batch analysis results from JSON file.
        
        Args:
            file_path: Path to batch results JSON
            
        Returns:
            Parsed batch results
        """
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def convert_batch_findings(
        self,
        batch_findings: List[Dict[str, Any]],
    ) -> List[Finding]:
        """
        Convert batch findings to continuous scoring format.
        
        Args:
            batch_findings: List of batch finding dictionaries
            
        Returns:
            List of Finding objects
        """
        findings = []
        
        for bf in batch_findings:
            finding = Finding(
                id=bf.get("id", bf.get("rule_id", "unknown")),
                type=bf.get("type", bf.get("check_id", "unknown")),
                severity=bf.get("severity", "medium").lower(),
                confidence=float(bf.get("confidence", 0.8)),
                source=bf.get("source", "batch"),
                line=bf.get("line"),
                exploit_chain=bf.get("exploit_chain"),
            )
            findings.append(finding)
        
        return findings
    
    def process_batch_file(
        self,
        file_path: str,
        asset_id: Optional[str] = None,
    ) -> ThreatScore:
        """
        Process a batch results file and compute threat score.
        
        Args:
            file_path: Path to batch results file
            asset_id: Optional asset ID (derived from filename if not provided)
            
        Returns:
            Computed ThreatScore
        """
        # Load batch results
        batch_results = self.load_batch_results(file_path)
        
        # Derive asset ID from filename if not provided
        if asset_id is None:
            asset_id = Path(file_path).stem
        
        # Extract findings from batch results
        batch_findings = batch_results.get("findings", [])
        
        # Convert to continuous scoring format
        findings = self.convert_batch_findings(batch_findings)
        
        # Compute threat score
        score = self.scoring_engine.compute_threat_score(asset_id, findings)
        
        return score
    
    def process_batch_directory(
        self,
        directory_path: str,
        pattern: str = "*.json",
    ) -> Dict[str, ThreatScore]:
        """
        Process all batch result files in a directory.
        
        Args:
            directory_path: Path to directory containing batch results
            pattern: Glob pattern for files to process
            
        Returns:
            Dict mapping asset_id to ThreatScore
        """
        scores = {}
        
        directory = Path(directory_path)
        for file_path in directory.glob(pattern):
            asset_id = file_path.stem
            try:
                score = self.process_batch_file(str(file_path), asset_id)
                scores[asset_id] = score
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        
        return scores
    
    def aggregate_multi_batch_results(
        self,
        batch_files: List[str],
        asset_id: str,
    ) -> ThreatScore:
        """
        Aggregate findings from multiple batch result files.
        
        Args:
            batch_files: List of batch result file paths
            asset_id: Asset identifier
            
        Returns:
            Aggregated ThreatScore
        """
        all_findings = []
        
        for file_path in batch_files:
            batch_results = self.load_batch_results(file_path)
            batch_findings = batch_results.get("findings", [])
            findings = self.convert_batch_findings(batch_findings)
            all_findings.extend(findings)
        
        # Deduplicate findings by ID
        unique_findings = {f.id: f for f in all_findings}.values()
        
        # Compute aggregated score
        score = self.scoring_engine.compute_threat_score(
            asset_id,
            list(unique_findings),
        )
        
        return score
    
    def export_score_to_batch_format(
        self,
        score: ThreatScore,
        output_path: str,
    ):
        """
        Export threat score back to batch-compatible format.
        
        Args:
            score: ThreatScore to export
            output_path: Path to write JSON file
        """
        batch_format = {
            "asset_id": score.asset_id,
            "threat_score": score.score,
            "severity_breakdown": score.severity_breakdown,
            "confidence_weighted_score": score.confidence_weighted_score,
            "exploit_chains_count": score.exploit_chains_count,
            "findings_count": score.findings_count,
            "timestamp": score.timestamp,
            "hash": score.hash,
            "version": "phase-2.5",
        }
        
        with open(output_path, 'w') as f:
            json.dump(batch_format, f, indent=2)


# Example usage
if __name__ == "__main__":
    # Create connector
    connector = BatchConnector()
    
    # Create sample batch results file
    batch_data = {
        "findings": [
            {
                "id": "VULN-001",
                "type": "sql_injection",
                "severity": "critical",
                "confidence": 0.95,
                "source": "static",
                "line": 42,
            },
            {
                "id": "VULN-002",
                "type": "xss",
                "severity": "high",
                "confidence": 0.85,
                "source": "static",
                "line": 78,
            },
        ]
    }
    
    # Write sample file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(batch_data, f)
        temp_file = f.name
    
    # Process batch file
    score = connector.process_batch_file(temp_file, "test-asset")
    
    print(f"Processed batch file:")
    print(f"  Asset: {score.asset_id}")
    print(f"  Score: {score.score}/100")
    print(f"  Findings: {score.findings_count}")
    print(f"  Hash: {score.hash[:16]}...")
    
    # Cleanup
    import os
    os.unlink(temp_file)
