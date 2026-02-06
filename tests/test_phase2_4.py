"""
Phase 2.4 Test Suite
Validates multi-finding aggregation, enhanced scoring, batch inference, and determinism.
All tests pass without external AI backends (mocked).
"""

import pytest
import json
import hashlib
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

# Import Phase 2.4 modules
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ai-service', 'src'))

from runtime.multi_finding_aggregator import (
    MultiFinidngAggregator, AggregatedFinding, MultiAssetAggregation
)
from ai.enhanced_scoring import (
    EnhancedCVSSScorer, ScoringInput, ScoringBatchProcessor
)
from runtime.batch_inference import (
    BatchInferenceEngine, BatchInferenceInput, AIVerdict
)
from runtime.determinism_validator_phase2_4 import (
    Phase2_4DeterminismValidator, DeterminismValidationReport
)


class TestMultiFindingAggregator:
    """Test multi-finding aggregation"""
    
    def test_single_finding_aggregation(self):
        """Test aggregating single static finding"""
        aggregator = MultiFinidngAggregator()
        
        static_findings = [
            {
                "id": "static_001",
                "type": "sql_injection",
                "severity": "high",
                "confidence": 0.85,
            }
        ]
        
        result = aggregator.aggregate(
            asset_id="/app/routes/api.py",
            static_findings=static_findings,
            runtime_findings=[],
        )
        
        assert result.aggregation_id
        assert result.finding_type == "sql_injection"
        assert result.severity == "high"
        assert result.static_confidence > 0.8
        assert result.determinism_hash
    
    def test_combined_static_runtime_aggregation(self):
        """Test aggregating both static and runtime findings"""
        aggregator = MultiFinidngAggregator()
        
        static_findings = [
            {
                "id": "static_001",
                "type": "sql_injection",
                "severity": "high",
                "confidence": 0.85,
            }
        ]
        
        runtime_findings = [
            {
                "id": "runtime_001",
                "type": "sql_injection",
                "severity": "critical",
                "confidence": 0.95,
                "evidence_type": "network_access",
            }
        ]
        
        result = aggregator.aggregate(
            asset_id="/app/routes/api.py",
            static_findings=static_findings,
            runtime_findings=runtime_findings,
        )
        
        assert result.finding_type == "sql_injection"
        # Combined confidence should favor runtime
        assert result.runtime_confidence > result.static_confidence
        assert result.combined_confidence > 0.85
    
    def test_batch_aggregation_determinism(self):
        """Test batch aggregation produces consistent run hashes"""
        aggregator = MultiFinidngAggregator()
        
        assets_data = {
            "/app/routes/api.py": {
                "static": [
                    {"id": "static_001", "type": "sql_injection", "severity": "high", "confidence": 0.85},
                ],
                "runtime": [],
                "evidence_chains": [],
            },
            "/app/routes/user.py": {
                "static": [
                    {"id": "static_002", "type": "xss", "severity": "medium", "confidence": 0.7},
                ],
                "runtime": [],
                "evidence_chains": [],
            },
        }
        
        # Run aggregation twice
        batch1 = aggregator.aggregate_batch(assets_data, "run_001")
        
        aggregator2 = MultiFinidngAggregator()
        batch2 = aggregator2.aggregate_batch(assets_data, "run_001")
        
        # Hashes should match
        assert batch1.run_hash == batch2.run_hash
        assert batch1.total_findings == batch2.total_findings
    
    def test_deterministic_sorting(self):
        """Test that findings are deterministically sorted"""
        aggregator = MultiFinidngAggregator()
        
        # Create findings in non-alphabetical order
        static_findings = [
            {"id": "z_last", "type": "sql_injection", "severity": "high", "confidence": 0.85},
            {"id": "a_first", "type": "sql_injection", "severity": "high", "confidence": 0.85},
            {"id": "m_middle", "type": "sql_injection", "severity": "high", "confidence": 0.85},
        ]
        
        result = aggregator.aggregate(
            asset_id="/app/routes/api.py",
            static_findings=static_findings,
            runtime_findings=[],
        )
        
        # Should be sorted by ID
        agg_dict = result.to_dict()
        static_ids = [f["id"] for f in agg_dict["static_findings"]]
        assert static_ids == ["a_first", "m_middle", "z_last"]


class TestEnhancedScoring:
    """Test enhanced CVSS scoring"""
    
    def test_base_scoring(self):
        """Test basic CVSS scoring"""
        scorer = EnhancedCVSSScorer()
        
        scoring_input = ScoringInput(
            aggregation_id="agg_001",
            finding_type="sql_injection",
            static_confidence=0.85,
            runtime_confidence=0.95,
            combined_confidence=0.90,
            exploit_chain_detected=False,
            has_negative_proof=False,
            asset_context={},
        )
        
        result = scorer.score_aggregated_finding(scoring_input)
        
        assert result.base_score > 0
        assert result.final_score > 0
        assert result.final_score <= 10.0
        assert result.severity in ["critical", "high", "medium", "low"]
        assert result.scoring_hash
    
    def test_exploit_chain_boost(self):
        """Test that exploit chains boost score"""
        scorer = EnhancedCVSSScorer()
        
        # Without exploit chain
        input1 = ScoringInput(
            aggregation_id="agg_001",
            finding_type="sql_injection",
            static_confidence=0.85,
            runtime_confidence=0.95,
            combined_confidence=0.90,
            exploit_chain_detected=False,
            has_negative_proof=False,
            asset_context={},
        )
        
        score1 = scorer.score_aggregated_finding(input1)
        
        # With exploit chain
        input2 = ScoringInput(
            aggregation_id="agg_001",
            finding_type="sql_injection",
            static_confidence=0.85,
            runtime_confidence=0.95,
            combined_confidence=0.90,
            exploit_chain_detected=True,  # This time with exploit
            has_negative_proof=False,
            asset_context={},
        )
        
        score2 = scorer.score_aggregated_finding(input2)
        
        # Exploit chain should increase score
        assert score2.final_score > score1.final_score
    
    def test_negative_proof_penalty(self):
        """Test that negative proof (mitigation) reduces score"""
        scorer = EnhancedCVSSScorer()
        
        # Without mitigation
        input1 = ScoringInput(
            aggregation_id="agg_001",
            finding_type="sql_injection",
            static_confidence=0.85,
            runtime_confidence=0.95,
            combined_confidence=0.90,
            exploit_chain_detected=False,
            has_negative_proof=False,
            asset_context={},
        )
        
        score1 = scorer.score_aggregated_finding(input1)
        
        # With mitigation
        input2 = ScoringInput(
            aggregation_id="agg_001",
            finding_type="sql_injection",
            static_confidence=0.85,
            runtime_confidence=0.95,
            combined_confidence=0.90,
            exploit_chain_detected=False,
            has_negative_proof=True,  # Mitigated by input sanitization
            asset_context={},
        )
        
        score2 = scorer.score_aggregated_finding(input2)
        
        # Mitigation should decrease score
        assert score2.final_score < score1.final_score
    
    def test_scoring_determinism(self):
        """Test that scoring is deterministic"""
        scorer1 = EnhancedCVSSScorer()
        scorer2 = EnhancedCVSSScorer()
        
        scoring_input = ScoringInput(
            aggregation_id="agg_001",
            finding_type="sql_injection",
            static_confidence=0.85,
            runtime_confidence=0.95,
            combined_confidence=0.90,
            exploit_chain_detected=True,
            has_negative_proof=False,
            asset_context={},
        )
        
        # Score twice
        score1 = scorer1.score_aggregated_finding(scoring_input)
        score2 = scorer2.score_aggregated_finding(scoring_input)
        
        # Should be identical
        assert score1.scoring_hash == score2.scoring_hash
        assert score1.final_score == score2.final_score
    
    def test_batch_scoring(self):
        """Test batch scoring"""
        processor = ScoringBatchProcessor()
        
        inputs = {
            "agg_001": ScoringInput(
                aggregation_id="agg_001",
                finding_type="sql_injection",
                static_confidence=0.85,
                runtime_confidence=0.95,
                combined_confidence=0.90,
                exploit_chain_detected=False,
                has_negative_proof=False,
                asset_context={},
            ),
            "agg_002": ScoringInput(
                aggregation_id="agg_002",
                finding_type="xss",
                static_confidence=0.7,
                runtime_confidence=0.75,
                combined_confidence=0.73,
                exploit_chain_detected=False,
                has_negative_proof=False,
                asset_context={},
            ),
        }
        
        results = processor.score_batch(inputs)
        
        assert len(results) == 2
        assert "agg_001" in results
        assert "agg_002" in results
        assert all(r.scoring_hash for r in results.values())


@pytest.mark.asyncio
class TestBatchInference:
    """Test batch AI inference"""
    
    async def test_mock_batch_reasoning(self):
        """Test batch reasoning with mock backend"""
        engine = BatchInferenceEngine()
        
        batch_input = BatchInferenceInput(
            batch_id="batch_001",
            findings={
                "agg_001": {
                    "finding_type": "sql_injection",
                    "severity": "high",
                    "static_confidence": 0.85,
                    "runtime_confidence": 0.95,
                    "combined_confidence": 0.90,
                    "exploit_chain_detected": True,
                    "has_negative_proof": False,
                }
            },
            scores={
                "agg_001": {
                    "final_score": 9.5,
                    "severity": "critical",
                }
            },
        )
        
        result = await engine.reason_batch(batch_input)
        
        assert result.batch_id == "batch_001"
        assert len(result.verdicts) == 1
        assert "agg_001" in result.verdicts
        
        verdict = result.verdicts["agg_001"]
        assert verdict.ai_verdict_severity in ["critical", "high", "medium", "low"]
        assert 0.0 <= verdict.confidence <= 1.0
        assert verdict.hash_value
    
    async def test_verdict_consistency(self):
        """Test that verdicts are consistent across runs"""
        engine = BatchInferenceEngine()
        
        batch_input = BatchInferenceInput(
            batch_id="batch_001",
            findings={
                "agg_001": {
                    "finding_type": "sql_injection",
                    "severity": "high",
                    "static_confidence": 0.85,
                    "runtime_confidence": 0.95,
                    "combined_confidence": 0.90,
                    "exploit_chain_detected": True,
                    "has_negative_proof": False,
                }
            },
            scores={
                "agg_001": {
                    "final_score": 9.5,
                    "severity": "critical",
                }
            },
        )
        
        # Run twice
        result1 = await engine.reason_batch(batch_input)
        result2 = await engine.reason_batch(batch_input)
        
        # Verdicts should be identical
        verdict1 = result1.verdicts["agg_001"]
        verdict2 = result2.verdicts["agg_001"]
        
        assert verdict1.hash_value == verdict2.hash_value
        assert verdict1.ai_verdict_severity == verdict2.ai_verdict_severity


class TestDeterminismValidator:
    """Test Phase 2.4 determinism validation"""
    
    def test_3run_validation_pass(self):
        """Test validation passes with consistent runs"""
        validator = Phase2_4DeterminismValidator()
        
        # Create 3 identical runs
        run_template = {
            "aggregation": {
                "run_hash": "abc123",
                "findings_per_asset": {
                    "asset_001": [
                        {
                            "aggregation_id": "agg_001",
                            "finding_type": "sql_injection",
                            "severity": "high",
                            "determinism_hash": "hash001",
                        }
                    ]
                },
            },
            "scores": {
                "agg_001": {
                    "final_score": 9.0,
                    "severity": "high",
                    "scoring_hash": "scoring_hash001",
                }
            },
            "verdicts": {
                "agg_001": {
                    "ai_verdict_severity": "high",
                    "confidence": 0.95,
                    "hash_value": "verdict_hash001",
                }
            },
        }
        
        run1 = json.loads(json.dumps(run_template))
        run2 = json.loads(json.dumps(run_template))
        run3 = json.loads(json.dumps(run_template))
        
        report = validator.validate_3_runs(run1, run2, run3)
        
        assert report.overall_passed
        assert len(report.errors) == 0
        assert all(c.passed for c in report.checks)
    
    def test_3run_validation_hash_mismatch(self):
        """Test validation fails with hash mismatch"""
        validator = Phase2_4DeterminismValidator()
        
        run1 = {
            "aggregation": {
                "run_hash": "abc123",
                "findings_per_asset": {
                    "asset_001": [
                        {
                            "aggregation_id": "agg_001",
                            "determinism_hash": "hash001",
                        }
                    ]
                },
            },
            "scores": {},
            "verdicts": {},
        }
        
        run2 = json.loads(json.dumps(run1))
        
        run3 = json.loads(json.dumps(run1))
        run3["aggregation"]["run_hash"] = "different_hash"  # Different hash
        
        report = validator.validate_3_runs(run1, run2, run3)
        
        assert not report.overall_passed
        assert len(report.errors) > 0
    
    def test_severity_variance_check(self):
        """Test that severity variance is checked"""
        validator = Phase2_4DeterminismValidator()
        
        run1 = {
            "aggregation": {
                "findings_per_asset": {
                    "asset_001": [
                        {
                            "aggregation_id": "agg_001",
                            "severity": "high",
                        }
                    ]
                },
            },
            "scores": {},
            "verdicts": {},
        }
        
        run2 = json.loads(json.dumps(run1))
        
        run3 = json.loads(json.dumps(run1))
        # Change severity in run3
        run3["aggregation"]["findings_per_asset"]["asset_001"][0]["severity"] = "critical"
        
        report = validator.validate_3_runs(run1, run2, run3)
        
        # Should fail due to severity variance
        assert not report.overall_passed
        assert "severity" in str(report.errors).lower()


class TestIntegration:
    """Integration tests for Phase 2.4 pipeline"""
    
    def test_end_to_end_pipeline(self):
        """Test complete Phase 2.4 pipeline"""
        # Step 1: Aggregate findings
        aggregator = MultiFinidngAggregator()
        
        assets_data = {
            "api.py": {
                "static": [
                    {"id": "s1", "type": "sql_injection", "severity": "high", "confidence": 0.85},
                ],
                "runtime": [
                    {"id": "r1", "type": "sql_injection", "severity": "critical", "confidence": 0.95},
                ],
                "evidence_chains": [
                    {"id": "e1", "is_exploit": True},
                ],
            },
        }
        
        batch_agg = aggregator.aggregate_batch(assets_data, "test_run")
        assert batch_agg.total_findings > 0
        assert batch_agg.run_hash
        
        # Step 2: Score findings
        scorer = EnhancedCVSSScorer()
        
        for asset_id, findings in batch_agg.findings_per_asset.items():
            for finding in findings:
                scoring_input = ScoringInput(
                    aggregation_id=finding.aggregation_id,
                    finding_type=finding.finding_type,
                    static_confidence=finding.static_confidence,
                    runtime_confidence=finding.runtime_confidence,
                    combined_confidence=finding.combined_confidence,
                    exploit_chain_detected=finding.exploit_chain_detected,
                    has_negative_proof=finding.has_negative_proof,
                    asset_context={},
                )
                
                score = scorer.score_aggregated_finding(scoring_input)
                assert score.final_score > 0
        
        # Step 3: Validate determinism would happen across 3 runs
        # (This is tested separately in TestDeterminismValidator)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
