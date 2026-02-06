# Phase 2.4: Multi-Finding Aggregation & Deterministic AI Batch Reasoning

## Overview

Phase 2.4 extends Phase 2.3 by adding:
1. **Multi-Finding Aggregation**: Combines multiple static and runtime findings per asset with confidence weighting
2. **Enhanced CVSS Scoring**: Evidence-weighted vulnerability scoring incorporating confidence factors
3. **Batch AI Reasoning**: Deterministic verdict generation over aggregated findings (GPT-4o + Ollama fallback)
4. **Determinism Validation**: 3-run reproducibility checks with strict severity consistency (±0)

All modules are determinism-first with SHA256 hashing for reproducible outputs across runs.

---

## Architecture

### Module Dependencies

```
multi_finding_aggregator.py
    ↓
enhanced_scoring.py
    ↓
batch_inference.py
    ↓
determinism_validator_phase2_4.py
```

### Data Flow

```
Static + Runtime Findings
    ↓
[Aggregator] → Aggregated findings per asset (deterministically sorted)
    ↓
[Enhanced Scorer] → CVSS scores with evidence weighting
    ↓
[Batch Inference] → AI verdicts (GPT-4o or Ollama)
    ↓
[Determinism Validator] → 3-run validation report
```

---

## Modules

### 1. multi_finding_aggregator.py

**Purpose**: Combine multiple static and runtime findings per asset

**Key Classes**:
- `AggregatedFinding`: Single aggregated finding with confidence weights
- `MultiAssetAggregation`: Container for findings across multiple assets
- `MultiFinidngAggregator`: Aggregates findings deterministically

**Key Methods**:
```python
aggregator = MultiFinidngAggregator()

# Single asset aggregation
agg_finding = aggregator.aggregate(
    asset_id="/app/routes/api.py",
    static_findings=[...],
    runtime_findings=[...],
    evidence_chains=[...],
)

# Batch aggregation
batch = aggregator.aggregate_batch(
    assets_data={
        "asset_001": {"static": [...], "runtime": [...], "evidence_chains": [...]},
        "asset_002": {...},
    },
    run_id="run_001",
)
```

**Determinism Guarantees**:
- Findings sorted deterministically by ID
- Confidence scores computed consistently
- SHA256 hashes computed for aggregation validation
- Batch run hash validates all findings together

**Output Contracts**:
```python
AggregatedFinding {
    aggregation_id: str,              # Unique ID
    asset_id: str,                    # e.g., file path
    finding_type: str,                # e.g., "sql_injection"
    severity: str,                    # "critical|high|medium|low"
    static_confidence: float,         # 0.0-1.0
    runtime_confidence: float,        # 0.0-1.0
    combined_confidence: float,       # Weighted average
    exploit_chain_detected: bool,
    has_negative_proof: bool,
    determinism_hash: str,            # SHA256
}

MultiAssetAggregation {
    aggregation_run_id: str,
    findings_per_asset: Dict[str, List[AggregatedFinding]],
    run_hash: str,                    # SHA256 of all findings
}
```

---

### 2. enhanced_scoring.py

**Purpose**: Evidence-weighted CVSS v3.1 scoring

**Key Classes**:
- `ScoringInput`: Deterministic input for scoring
- `EnhancedScore`: CVSS score with evidence weighting
- `EnhancedCVSSScorer`: Computes evidence-weighted scores
- `ScoringBatchProcessor`: Batch processing

**Key Methods**:
```python
scorer = EnhancedCVSSScorer()

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

enhanced_score = scorer.score_aggregated_finding(scoring_input)
```

**Scoring Logic**:
- Base CVSS from CWE mappings (Phase 2.3)
- Exploitability boost from runtime evidence (+0.0 to +1.5)
- Exploit chain boost (+2.0 if detected)
- Mitigation penalty (-3.0 if negative proof)
- Static confidence penalty (-0.5 if low confidence)

**Output Contracts**:
```python
EnhancedScore {
    base_score: float,                # Traditional CVSS (0.0-10.0)
    exploitability_boost: float,      # Evidence-based adjustment
    impact_adjustment: float,         # Negative for mitigation
    final_score: float,               # Clamped to 0.0-10.0
    severity: str,                    # "critical|high|medium|low"
    evidence_factors: Dict[str, float],  # Breakdown of adjustments
    scoring_hash: str,                # SHA256 for determinism
}
```

---

### 3. batch_inference.py

**Purpose**: Deterministic AI batch reasoning (GPT-4o + Ollama)

**Key Classes**:
- `BatchInferenceInput`: Deterministic input for reasoning
- `AIVerdict`: Single AI verdict
- `BatchInferenceResult`: Results from batch reasoning
- `BatchInferenceEngine`: Main inference engine

**Key Methods**:
```python
engine = BatchInferenceEngine(gpt_client=gpt4o_client, temperature=0.0)

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
        },
    },
    scores={
        "agg_001": {
            "final_score": 9.5,
            "severity": "critical",
        },
    },
)

result = await engine.reason_batch(batch_input)
```

**AI Reasoning Contract**:
- Temperature: 0.0 for deterministic outputs
- Top-p: 1.0 for consistency
- Max tokens: 4096
- System prompt guides verdict generation
- Fallback to Ollama on GPT failure
- Mock reasoning for testing (no external deps)

**Output Contracts**:
```python
AIVerdict {
    aggregation_id: str,
    original_severity: str,
    ai_verdict_severity: str,        # Final verdict
    confidence: float,               # 0.0-1.0
    rationale: str,                  # Explanation
    reasoning_chain: List[str],      # Step-by-step reasoning
    requires_review: bool,           # If confidence < 0.7
    hash_value: str,                 # SHA256
}

BatchInferenceResult {
    batch_id: str,
    total_findings: int,
    verdicts: Dict[str, AIVerdict],
    backend_used: AIBackend,
    batch_hash: str,                 # SHA256 of all verdicts
    timestamp: str,
}
```

---

### 4. determinism_validator_phase2_4.py

**Purpose**: Validate 3-run reproducibility with strict checks

**Key Classes**:
- `DeterminismCheck`: Single check result
- `DeterminismValidationReport`: Full validation report
- `Phase2_4DeterminismValidator`: Main validator

**Key Methods**:
```python
validator = Phase2_4DeterminismValidator()

report = validator.validate_3_runs(
    run1_results={"aggregation": {...}, "scores": {...}, "verdicts": {...}},
    run2_results={...},
    run3_results={...},
)

print(report.summary())
print(f"Overall: {'PASS' if report.overall_passed else 'FAIL'}")
```

**Validation Checks**:
1. **Aggregation Hash Consistency**: All run hashes must match
2. **Aggregation Ordering**: Asset/finding ordering must be identical
3. **Scoring Hash Consistency**: CVSS scores must produce identical hashes
4. **Verdict Consistency**: AI verdicts must be identical
5. **Severity Variance**: Severity must be identical (±0, strict)

**Output Contracts**:
```python
DeterminismValidationReport {
    run_count: int,                  # Number of runs validated
    checks: List[DeterminismCheck],  # Individual check results
    overall_passed: bool,            # True only if all checks pass
    errors: List[str],               # Error messages
    severity_variance: Dict[str, float],  # Per-finding variance
    hash_consistency: Dict[str, bool],    # Per-aggregation consistency
}
```

---

## Determinism Guarantees

### What is Deterministic?

✓ **Aggregation**:
- Findings sorted deterministically by ID
- Confidence scores computed identically
- Aggregation hashes match across runs
- Asset/finding ordering consistent

✓ **Scoring**:
- CWE → CVSS mapping deterministic
- Evidence factor computation deterministic
- Score hashes match across runs
- Severity assignment deterministic

✓ **AI Reasoning**:
- Temperature = 0.0 (deterministic sampling)
- System/user prompts fixed
- Verdict hashes computed identically
- Batch processing order deterministic (alphabetical by aggregation_id)

✓ **Validation**:
- 3-run reproducibility validated
- Hash consistency checked
- Severity variance validated (strict ±0)

### SHA256 Hashing Strategy

Each level produces a SHA256 hash for validation:

```
AggregatedFinding.determinism_hash
    ↓
MultiAssetAggregation.run_hash
    ↓
EnhancedScore.scoring_hash
    ↓
AIVerdict.hash_value
    ↓
BatchInferenceResult.batch_hash
```

---

## Integration with Phase 2.3

Phase 2.4 **extends** Phase 2.3, not replaces it:

### Phase 2.3 Inputs to Phase 2.4
- **Conflict Resolution Results**: Used as input to batch inference
- **Evidence Chains**: Linked in aggregation
- **AI Reasoning Contract**: Extended for verdict confidence

### Phase 2.3 → Phase 2.4 Pipeline
```
Phase 2.3:
  Static Analysis → Conflict Resolution → Evidence Chains → AI Reasoning

Phase 2.4:
  [Phase 2.3 outputs] → Multi-Finding Aggregation → Enhanced Scoring → Batch Inference → Determinism Validation
```

---

## CI/CD Integration

### Determinism Validation in CI

```yaml
# .github/workflows/phase2_4_determinism.yml
name: Phase 2.4 Determinism Validation

on: [push, pull_request]

jobs:
  determinism_test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Phase 2.4 tests
        run: |
          pytest tests/test_phase2_4.py -v
      
      - name: Validate 3-run determinism
        run: |
          python scripts/validate_phase2_4_determinism.py
```

### What Determinism Script Does

```python
# scripts/validate_phase2_4_determinism.py
import json
from ai_service.src.runtime.multi_finding_aggregator import MultiFinidngAggregator
from ai_service.src.runtime.determinism_validator_phase2_4 import Phase2_4DeterminismValidator

# Run pipeline 3 times with same inputs
results = []
for i in range(3):
    # Run aggregation → scoring → inference
    run_result = run_phase2_4_pipeline(test_data)
    results.append(run_result)

# Validate determinism
validator = Phase2_4DeterminismValidator()
report = validator.validate_3_runs(*results)

# Fail CI if not deterministic
assert report.overall_passed, f"Determinism validation failed:\n{report.summary()}"
```

---

## Testing

### Run All Tests

```bash
pytest tests/test_phase2_4.py -v
```

### Test Categories

**Unit Tests**:
- `TestMultiFindingAggregator`: Aggregation logic
- `TestEnhancedScoring`: Scoring calculations
- `TestBatchInference`: Verdict generation
- `TestDeterminismValidator`: Validation logic

**Integration Tests**:
- `TestIntegration`: End-to-end pipeline

**Determinism Tests**:
- All tests validate SHA256 hashing
- Batch tests run twice and compare hashes
- 3-run validation tests

---

## Example Usage

### Complete Phase 2.4 Pipeline

```python
from runtime.multi_finding_aggregator import MultiFinidngAggregator
from ai.enhanced_scoring import EnhancedCVSSScorer, ScoringInput
from runtime.batch_inference import BatchInferenceEngine, BatchInferenceInput
from runtime.determinism_validator_phase2_4 import Phase2_4DeterminismValidator

# Step 1: Aggregate findings
aggregator = MultiFinidngAggregator()
batch_agg = aggregator.aggregate_batch(
    assets_data={
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
    },
    run_id="test_run",
)

# Step 2: Score findings
scorer = EnhancedCVSSScorer()
scores = {}
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
        scores[finding.aggregation_id] = scorer.score_aggregated_finding(scoring_input)

# Step 3: Batch AI reasoning
engine = BatchInferenceEngine(temperature=0.0)
batch_input = BatchInferenceInput(
    batch_id="batch_001",
    findings={f["aggregation_id"]: f for f in batch_agg.findings_per_asset.values()},
    scores={k: {"final_score": v.final_score} for k, v in scores.items()},
)
inference_result = await engine.reason_batch(batch_input)

# Step 4: Validate determinism (would run 3 times in production)
# (See CI/CD integration section)
```

---

## Configuration

### Environment Variables

```bash
# For GPT-4o backend
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4o"

# For Ollama fallback
export OLLAMA_BASE_URL="http://localhost:11434"

# Determinism settings
export TEMPERATURE=0.0  # For deterministic sampling
```

---

## Troubleshooting

### Hash Mismatch in Determinism Validation

**Symptom**: `run_hash` differs between runs

**Causes**:
1. Non-deterministic sorting → Check `MultiFinidngAggregator._extract_finding_type()`
2. Float precision → Round to 4 decimal places (done in code)
3. Random ordering → All dictionaries sorted by key

**Solution**:
```python
# Ensure all dictionaries are sorted
data = {k: data[k] for k in sorted(data.keys())}

# Round floats consistently
confidence = round(confidence, 4)
```

### Verdict Mismatch Between Runs

**Symptom**: `AIVerdict` differs

**Causes**:
1. Temperature > 0 → Set temperature=0.0
2. Random prompting → Use fixed system/user prompts
3. Stochastic backend → Ensure GPT model is deterministic

**Solution**:
```python
engine = BatchInferenceEngine(temperature=0.0)  # Critical!
```

### Severity Variance Too High

**Symptom**: Severity changes between runs

**Causes**:
1. Evidence-based scoring not deterministic
2. AI verdicts changing severity non-deterministically
3. Confidence factors varying

**Solution**:
- Check `enhanced_scoring.py` for float precision
- Validate `batch_inference.py` temperature setting
- Run 3-run validation to find exact mismatch

---

## Future Enhancements

- [ ] Parallel batch processing (multiple GPUs)
- [ ] Caching of AI verdicts for repeated findings
- [ ] Extended reasoning chains (multi-turn prompting)
- [ ] Ensemble verdicts (multiple models)
- [ ] Confidence interval tracking

---

## Related Documentation

- **Phase 2.3**: `PHASE_2_3_README.md`
- **Phase 2.2**: `PHASE_2_2_README.md`
- **Phase 2.1**: `PHASE_2_1_README.md`
- **Phase 1**: `PHASE_1_README.md`

---

## Contact & Support

For Phase 2.4 implementation questions:
- Check `tests/test_phase2_4.py` for usage examples
- Review module docstrings for API details
- Open issue for determinism failures with 3-run data
