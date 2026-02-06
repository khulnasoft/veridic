"""
Phase 1 baseline metrics generator.
Runs analysis on vulnerable fixtures and generates baseline metrics.
"""

import json
import asyncio
import time
from pathlib import Path
from dataclasses import asdict
from src.static_analysis import StaticAnalysisOrchestrator
from src.ast import ASTExtractor
from src.reports import ReportGenerator

FIXTURES_PATH = Path(__file__).parent / "fixtures"
METRICS_PATH = Path(__file__).parent / "phase1_baseline_metrics.json"


async def generate_baseline_metrics():
    """Generate baseline metrics for Phase 1 capabilities."""
    
    static_analyzer = StaticAnalysisOrchestrator()
    ast_extractor = ASTExtractor()
    report_generator = ReportGenerator()
    
    fixtures = {
        "typescript": FIXTURES_PATH / "vulnerable_typescript.ts",
        "python": FIXTURES_PATH / "vulnerable_python.py",
        "go": FIXTURES_PATH / "vulnerable_go.go",
        "rust": FIXTURES_PATH / "vulnerable_rust.rs",
    }
    
    metrics = {
        "timestamp": time.time(),
        "phase": "Phase 1 - Static Analysis AI",
        "results": {},
    }
    
    total_findings = 0
    total_time = 0
    
    for language, fixture_path in fixtures.items():
        if not fixture_path.exists():
            print(f"  ⚠️  Fixture not found: {fixture_path}")
            continue
        
        print(f"\n  Analyzing {language.upper()}...")
        code = fixture_path.read_text()
        
        start_time = time.time()
        
        # Static Analysis
        try:
            findings = await static_analyzer.analyze(
                code=code,
                language=language,
                filename=fixture_path.name,
            )
        except Exception as e:
            print(f"    ❌ Static analysis failed: {e}")
            findings = []
        
        # AST Extraction
        try:
            ast_data = await ast_extractor.extract(
                code=code,
                language=language,
                filename=fixture_path.name,
            )
        except Exception as e:
            print(f"    ❌ AST extraction failed: {e}")
            ast_data = {}
        
        # Report Generation
        report = report_generator.generate_json_report(
            findings,
            {"language": language, "filename": fixture_path.name}
        )
        
        analysis_time = time.time() - start_time
        
        # Summary
        severity_dist = {
            "critical": sum(1 for f in findings if f.severity == "critical"),
            "high": sum(1 for f in findings if f.severity == "high"),
            "medium": sum(1 for f in findings if f.severity == "medium"),
            "low": sum(1 for f in findings if f.severity == "low"),
        }
        
        metrics["results"][language] = {
            "fixture": fixture_path.name,
            "lines_of_code": len(code.split("\n")),
            "static_findings": len(findings),
            "severity_distribution": severity_dist,
            "ast_functions": len(ast_data.get("functions", [])),
            "ast_variables": len(ast_data.get("variables", [])),
            "ast_dataflow": len(ast_data.get("dataflow", [])),
            "analysis_time_ms": round(analysis_time * 1000, 2),
            "vulnerabilities_by_type": {},
        }
        
        # Vulnerability type breakdown
        for finding in findings:
            vuln_type = finding.type
            if vuln_type not in metrics["results"][language]["vulnerabilities_by_type"]:
                metrics["results"][language]["vulnerabilities_by_type"][vuln_type] = 0
            metrics["results"][language]["vulnerabilities_by_type"][vuln_type] += 1
        
        total_findings += len(findings)
        total_time += analysis_time
        
        print(f"    ✓ Found {len(findings)} vulnerabilities (avg severity: {severity_dist})")
        print(f"    ✓ Extracted {ast_data.get('functions', [])} functions in {analysis_time:.2f}s")
    
    # Aggregate metrics
    metrics["summary"] = {
        "total_findings": total_findings,
        "total_analysis_time_ms": round(total_time * 1000, 2),
        "avg_analysis_time_ms": round((total_time / len(fixtures)) * 1000, 2) if fixtures else 0,
        "languages_tested": list(fixtures.keys()),
    }
    
    # Save metrics
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    
    print(f"\n  📊 Baseline metrics saved to {METRICS_PATH}")
    print(f"\n  ═══ PHASE 1 BASELINE METRICS ═══")
    print(f"  Total Findings: {total_findings}")
    print(f"  Total Analysis Time: {total_time:.2f}s")
    print(f"  Languages Tested: {', '.join(fixtures.keys())}")
    
    return metrics


if __name__ == "__main__":
    asyncio.run(generate_baseline_metrics())
