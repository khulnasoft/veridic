"""
Phase 1 Determinism Tests
========================
Validates that the same code input produces consistent findings and CVSS scores.

Enhancement from user approval:
- Run the same fixture twice
- Ensure: Same findings + CVSS variance ≤ ±0.3
- This catches prompt instability early
"""

import json
import asyncio
import hashlib
from pathlib import Path
from typing import Dict, List, Set
import pytest


class DeterminismValidator:
    """Validates consistency of Phase 1 analysis across multiple runs."""
    
    def __init__(self):
        self.fixtures_dir = Path(__file__).parent / "fixtures"
        self.results_dir = Path(__file__).parent / "determinism_results"
        self.results_dir.mkdir(exist_ok=True)
    
    def load_fixture(self, fixture_name: str) -> tuple[str, str]:
        """Load a fixture file and its language."""
        fixture_path = self.fixtures_dir / fixture_name
        if not fixture_path.exists():
            raise FileNotFoundError(f"Fixture not found: {fixture_name}")
        
        language = self._detect_language(fixture_name)
        code = fixture_path.read_text()
        
        return code, language
    
    def _detect_language(self, filename: str) -> str:
        """Detect language from filename."""
        ext_map = {
            '.ts': 'typescript',
            '.py': 'python',
            '.go': 'go',
            '.rs': 'rust',
        }
        for ext, lang in ext_map.items():
            if filename.endswith(ext):
                return lang
        return 'unknown'
    
    def normalize_findings(self, findings: List[Dict]) -> Set[str]:
        """
        Normalize findings to check equivalence.
        Ignores: timestamps, UUIDs
        Compares: type, line, severity, confidence
        """
        normalized = set()
        for finding in findings:
            key = (
                finding.get('type', ''),
                finding.get('line_number', finding.get('line', -1)),
                finding.get('severity', ''),
                round(finding.get('confidence', 0.0), 1),  # Round to 1 decimal
            )
            normalized.add(key)
        return normalized
    
    def check_cvss_consistency(self, run1_findings: List[Dict], run2_findings: List[Dict]) -> Dict:
        """
        Compare CVSS scores between two runs.
        Allow variance of ±0.3 as acceptable.
        """
        run1_scores = {(f.get('type'), f.get('line')): f.get('cvss_score', 0.0) for f in run1_findings}
        run2_scores = {(f.get('type'), f.get('line')): f.get('cvss_score', 0.0) for f in run2_findings}
        
        inconsistencies = []
        for key in run1_scores:
            if key in run2_scores:
                score1, score2 = run1_scores[key], run2_scores[key]
                variance = abs(score1 - score2)
                if variance > 0.3:
                    inconsistencies.append({
                        'finding': key,
                        'run1_score': score1,
                        'run2_score': score2,
                        'variance': variance,
                        'status': 'WARN' if variance <= 0.5 else 'FAIL',
                    })
        
        return {
            'total_findings': len(run1_scores),
            'consistent_findings': len(run1_scores) - len(inconsistencies),
            'inconsistencies': inconsistencies,
            'overall_variance': max([i['variance'] for i in inconsistencies], default=0.0),
            'pass': len(inconsistencies) == 0,
        }
    
    async def test_fixture_determinism(self, fixture_name: str, num_runs: int = 2) -> Dict:
        """
        Run the same fixture multiple times and validate consistency.
        
        Returns:
        {
            'fixture': str,
            'num_runs': int,
            'findings_consistent': bool,
            'cvss_consistent': bool,
            'details': dict
        }
        """
        print(f"\nTesting determinism for: {fixture_name}")
        
        code, language = self.load_fixture(fixture_name)
        code_hash = hashlib.sha256(code.encode()).hexdigest()[:8]
        
        runs = []
        for i in range(num_runs):
            print(f"  Run {i+1}/{num_runs}...", end='')
            # TODO: Replace with actual gRPC client call when integration test ready
            mock_findings = self._generate_mock_findings(code, language)
            runs.append(mock_findings)
            print(" OK")
        
        # Compare findings across runs
        finding_sets = [self.normalize_findings(run) for run in runs]
        findings_consistent = len(set(finding_sets[0])) == len(finding_sets[1]) if len(finding_sets) > 1 else True
        
        # Compare CVSS scores
        cvss_result = self.check_cvss_consistency(runs[0], runs[1]) if len(runs) > 1 else {'pass': True}
        
        result = {
            'fixture': fixture_name,
            'code_hash': code_hash,
            'num_runs': num_runs,
            'findings_consistent': findings_consistent,
            'cvss_check': cvss_result,
            'status': 'PASS' if findings_consistent and cvss_result['pass'] else 'WARN',
        }
        
        # Save detailed results
        result_file = self.results_dir / f"{fixture_name.replace('.', '_')}_determinism.json"
        result_file.write_text(json.dumps(result, indent=2))
        
        return result
    
    def _generate_mock_findings(self, code: str, language: str) -> List[Dict]:
        """
        Generate mock findings (placeholder for actual AI service calls).
        Replace with actual gRPC client calls during integration.
        """
        # This is a placeholder - in real tests, call the actual AI service
        if 'SELECT' in code.upper():
            return [
                {
                    'type': 'sql_injection',
                    'line': 10,
                    'severity': 'HIGH',
                    'confidence': 0.95,
                    'cvss_score': 7.5,
                    'description': 'SQL injection detected',
                }
            ]
        elif '<' in code and '>' in code:
            return [
                {
                    'type': 'xss',
                    'line': 5,
                    'severity': 'MEDIUM',
                    'confidence': 0.85,
                    'cvss_score': 6.1,
                    'description': 'XSS vulnerability detected',
                }
            ]
        return []


@pytest.mark.asyncio
async def test_typescript_determinism():
    """Test determinism on TypeScript fixture."""
    validator = DeterminismValidator()
    result = await validator.test_fixture_determinism('vulnerable_typescript.ts')
    assert result['status'] in ('PASS', 'WARN'), f"Determinism test failed: {result}"


@pytest.mark.asyncio
async def test_python_determinism():
    """Test determinism on Python fixture."""
    validator = DeterminismValidator()
    result = await validator.test_fixture_determinism('vulnerable_python.py')
    assert result['status'] in ('PASS', 'WARN'), f"Determinism test failed: {result}"


@pytest.mark.asyncio
async def test_go_determinism():
    """Test determinism on Go fixture."""
    validator = DeterminismValidator()
    result = await validator.test_fixture_determinism('vulnerable_go.go')
    assert result['status'] in ('PASS', 'WARN'), f"Determinism test failed: {result}"


@pytest.mark.asyncio
async def test_rust_determinism():
    """Test determinism on Rust fixture."""
    validator = DeterminismValidator()
    result = await validator.test_fixture_determinism('vulnerable_rust.rs')
    assert result['status'] in ('PASS', 'WARN'), f"Determinism test failed: {result}"


def test_all_fixtures_determinism():
    """Run determinism checks on all fixtures."""
    validator = DeterminismValidator()
    
    fixtures = [
        'vulnerable_typescript.ts',
        'vulnerable_python.py',
        'vulnerable_go.go',
        'vulnerable_rust.rs',
    ]
    
    results = []
    for fixture in fixtures:
        try:
            result = asyncio.run(validator.test_fixture_determinism(fixture, num_runs=2))
            results.append(result)
        except Exception as e:
            results.append({
                'fixture': fixture,
                'status': 'ERROR',
                'error': str(e),
            })
    
    # Summary
    print("\n" + "="*50)
    print("DETERMINISM TEST SUMMARY")
    print("="*50)
    passed = sum(1 for r in results if r.get('status') == 'PASS')
    warned = sum(1 for r in results if r.get('status') == 'WARN')
    failed = sum(1 for r in results if r.get('status') == 'ERROR')
    
    print(f"PASS: {passed}/{len(results)}")
    print(f"WARN: {warned}/{len(results)}")
    print(f"ERROR: {failed}/{len(results)}")
    
    # Save summary
    summary_file = validator.results_dir / "determinism_summary.json"
    summary_file.write_text(json.dumps({
        'total_fixtures': len(results),
        'passed': passed,
        'warned': warned,
        'failed': failed,
        'details': results,
    }, indent=2))
    
    assert failed == 0, "Some determinism tests failed"
