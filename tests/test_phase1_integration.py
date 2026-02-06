"""
Phase 1 integration tests for static analysis, AST extraction, and AI reasoning.
Tests the end-to-end pipeline with vulnerable code fixtures.
"""

import pytest
import asyncio
import json
from pathlib import Path
from src.static_analysis import StaticAnalysisOrchestrator
from src.ast import ASTExtractor
from src.ai.correlation import AIReasoningEngine
from src.ai.scoring import CVSSScorer
from src.reports import ReportGenerator
from src.ai.gpt4o import GPT4oClient
from src.graph.kg import KnowledgeGraph

# Test fixtures path
FIXTURES_PATH = Path(__file__).parent / "fixtures"


@pytest.fixture
def static_analyzer():
    return StaticAnalysisOrchestrator()


@pytest.fixture
def ast_extractor():
    return ASTExtractor()


@pytest.fixture
def gpt_client():
    return GPT4oClient()


@pytest.fixture
def kg():
    return KnowledgeGraph()


@pytest.fixture
def ai_reasoner(gpt_client, kg):
    from src.ai.correlation import AIReasoningEngine
    return AIReasoningEngine(gpt_client, kg)


@pytest.fixture
def cvss_scorer(gpt_client):
    return CVSSScorer(gpt_client)


@pytest.fixture
def report_generator():
    return ReportGenerator()


class TestStaticAnalysis:
    """Test static analysis tools (CodeQL + Semgrep)."""
    
    @pytest.mark.asyncio
    async def test_typescript_vulnerability_detection(self, static_analyzer):
        """Test detection of vulnerabilities in TypeScript code."""
        code = (FIXTURES_PATH / "vulnerable_typescript.ts").read_text()
        
        findings = await static_analyzer.analyze(
            code=code,
            language="typescript",
            filename="vulnerable_typescript.ts",
        )
        
        assert len(findings) > 0, "Should detect at least one vulnerability"
        assert any(f.type == "sql_injection" for f in findings), "Should detect SQL injection"
    
    @pytest.mark.asyncio
    async def test_python_vulnerability_detection(self, static_analyzer):
        """Test detection of vulnerabilities in Python code."""
        code = (FIXTURES_PATH / "vulnerable_python.py").read_text()
        
        findings = await static_analyzer.analyze(
            code=code,
            language="python",
            filename="vulnerable_python.py",
        )
        
        assert len(findings) > 0, "Should detect at least one vulnerability"
    
    @pytest.mark.asyncio
    async def test_go_vulnerability_detection(self, static_analyzer):
        """Test detection of vulnerabilities in Go code."""
        code = (FIXTURES_PATH / "vulnerable_go.go").read_text()
        
        findings = await static_analyzer.analyze(
            code=code,
            language="go",
            filename="vulnerable_go.go",
        )
        
        assert len(findings) > 0, "Should detect vulnerabilities in Go code"
    
    @pytest.mark.asyncio
    async def test_rust_vulnerability_detection(self, static_analyzer):
        """Test detection of vulnerabilities in Rust code."""
        code = (FIXTURES_PATH / "vulnerable_rust.rs").read_text()
        
        findings = await static_analyzer.analyze(
            code=code,
            language="rust",
            filename="vulnerable_rust.rs",
        )
        
        assert len(findings) > 0, "Should detect vulnerabilities in Rust code"
    
    @pytest.mark.asyncio
    async def test_deduplication(self, static_analyzer):
        """Test that duplicate findings are deduplicated."""
        code = "SELECT * FROM users WHERE id = '" + "' OR '1'='1"
        
        findings = await static_analyzer.analyze(
            code=code,
            language="python",
            filename="test.py",
        )
        
        # Check that we don't have duplicate findings on same line
        lines = [f.line for f in findings]
        assert len(lines) == len(set(lines)), "Should deduplicate findings on same line"


class TestASTExtraction:
    """Test AST extraction for multiple languages."""
    
    @pytest.mark.asyncio
    async def test_typescript_ast_extraction(self, ast_extractor):
        """Test AST extraction for TypeScript."""
        code = (FIXTURES_PATH / "vulnerable_typescript.ts").read_text()
        
        ast_data = await ast_extractor.extract(
            code=code,
            language="typescript",
            filename="test.ts",
        )
        
        assert "functions" in ast_data
        assert "variables" in ast_data
    
    @pytest.mark.asyncio
    async def test_python_ast_extraction(self, ast_extractor):
        """Test AST extraction for Python."""
        code = (FIXTURES_PATH / "vulnerable_python.py").read_text()
        
        ast_data = await ast_extractor.extract(
            code=code,
            language="python",
            filename="test.py",
        )
        
        assert "functions" in ast_data
        assert "variables" in ast_data
        assert "classes" in ast_data
        assert "imports" in ast_data
    
    @pytest.mark.asyncio
    async def test_go_ast_extraction(self, ast_extractor):
        """Test AST extraction for Go."""
        code = (FIXTURES_PATH / "vulnerable_go.go").read_text()
        
        ast_data = await ast_extractor.extract(
            code=code,
            language="go",
            filename="test.go",
        )
        
        assert "functions" in ast_data
    
    @pytest.mark.asyncio
    async def test_rust_ast_extraction(self, ast_extractor):
        """Test AST extraction for Rust."""
        code = (FIXTURES_PATH / "vulnerable_rust.rs").read_text()
        
        ast_data = await ast_extractor.extract(
            code=code,
            language="rust",
            filename="test.rs",
        )
        
        assert "functions" in ast_data
        assert "unsafe_blocks" in ast_data


class TestReportGeneration:
    """Test report generation in multiple formats."""
    
    def test_json_report_generation(self, report_generator, static_analyzer):
        """Test JSON report generation."""
        from src.static_analysis.orchestrator import StaticFinding
        
        findings = [
            StaticFinding(
                tool="test",
                rule_id="TEST-001",
                type="sql_injection",
                message="Potential SQL injection",
                line=10,
                column=5,
                confidence=0.95,
                severity="high",
                code_snippet="SELECT * FROM users WHERE id = '" + "' OR '1'='1",
                remediation_hint="Use parameterized queries",
            )
        ]
        
        report = report_generator.generate_json_report(
            findings,
            {"language": "python", "filename": "test.py"}
        )
        
        assert isinstance(report, str)
        data = json.loads(report)
        assert data["summary"]["total_findings"] == 1
        assert data["summary"]["high"] == 1
    
    def test_markdown_report_generation(self, report_generator):
        """Test Markdown report generation."""
        from src.static_analysis.orchestrator import StaticFinding
        
        findings = [
            StaticFinding(
                tool="test",
                rule_id="TEST-001",
                type="xss",
                message="Potential XSS vulnerability",
                line=5,
                column=0,
                confidence=0.85,
                severity="medium",
                code_snippet="echo $_GET['user'];",
                remediation_hint="Sanitize user input with htmlspecialchars()",
            )
        ]
        
        report = report_generator.generate_markdown_report(
            findings,
            {"language": "php", "filename": "index.php"}
        )
        
        assert isinstance(report, str)
        assert "Security Analysis Report" in report
        assert "XSS" in report
        assert "medium" in report.lower()
    
    def test_sarif_report_generation(self, report_generator):
        """Test SARIF report generation for IDE integration."""
        from src.static_analysis.orchestrator import StaticFinding
        
        findings = [
            StaticFinding(
                tool="test",
                rule_id="TEST-001",
                type="hardcoded_secret",
                message="Hardcoded API key detected",
                line=15,
                column=20,
                confidence=1.0,
                severity="critical",
                code_snippet='api_key = "sk_live_xxx"',
                remediation_hint="Move secrets to environment variables",
            )
        ]
        
        report = report_generator.generate_sarif_report(
            findings,
            {"language": "python", "filename": "config.py"}
        )
        
        assert isinstance(report, str)
        data = json.loads(report)
        assert data["version"] == "2.1.0"
        assert len(data["runs"][0]["results"]) == 1


@pytest.mark.asyncio
async def test_phase1_end_to_end_pipeline(static_analyzer, ast_extractor, report_generator):
    """Test complete Phase 1 pipeline: static analysis → AST → report."""
    code = """
    import sqlite3
    
    def get_user(user_id):
        conn = sqlite3.connect('db.sqlite3')
        query = f"SELECT * FROM users WHERE id = {user_id}"
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.fetchone()
    """
    
    # Step 1: Static Analysis
    findings = await static_analyzer.analyze(
        code=code,
        language="python",
        filename="app.py",
    )
    
    # Step 2: AST Extraction
    ast_data = await ast_extractor.extract(
        code=code,
        language="python",
        filename="app.py",
    )
    
    # Step 3: Report Generation
    report = report_generator.generate_markdown_report(
        findings,
        {"language": "python", "filename": "app.py"}
    )
    
    assert len(findings) > 0, "Should detect SQL injection"
    assert "functions" in ast_data, "Should extract AST"
    assert "Security Analysis Report" in report, "Should generate report"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
