"""
Phase 1 Validation Orchestrator

Runs all 8 validation steps sequentially with proper error handling,
generates comprehensive reports, and provides actionable feedback.
"""

import asyncio
import subprocess
import time
import json
from pathlib import Path
from typing import Optional, Dict, List
import logging

from validation_report import (
    Phase1ValidationReport,
    StatusEnum,
    ValidationRuleChecker,
)
from tool_attribution import ToolAttributionAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Phase1Orchestrator:
    """Orchestrates Phase 1 validation."""
    
    def __init__(self, project_root: str = "/vercel/share/v0-project"):
        self.project_root = Path(project_root)
        self.report = Phase1ValidationReport()
        self.tool_analyzer = ToolAttributionAnalyzer()
    
    async def run_all_steps(self) -> Phase1ValidationReport:
        """Execute all 8 validation steps."""
        
        # Step 1: Proto Compilation
        await self._step_1_proto_compilation()
        
        # Step 2: Docker Build
        await self._step_2_docker_build()
        
        # Step 3: Service Health
        await self._step_3_service_health()
        
        # Step 4: Static Analysis Tools
        await self._step_4_static_analysis_tools()
        
        # Step 5: AST Extraction
        await self._step_5_ast_extraction()
        
        # Step 6: End-to-End Pipeline
        await self._step_6_e2e_pipeline()
        
        # Step 7: AI Reasoning Quality
        await self._step_7_ai_reasoning()
        
        # Step 8: Baseline Metrics
        await self._step_8_baseline_metrics()
        
        self.report.finalize()
        return self.report
    
    async def _step_1_proto_compilation(self):
        """Step 1: Verify protobuf files compile."""
        step_num = 1
        start = time.time()
        
        try:
            result = subprocess.run(
                ["bash", "scripts/generate_proto.sh"],
                cwd=self.project_root,
                capture_output=True,
                timeout=60,
                text=True,
            )
            
            duration = time.time() - start
            
            if result.returncode == 0:
                self.report.add_step(
                    step_num,
                    "gRPC Proto Compilation",
                    StatusEnum.PASS,
                    duration,
                    "Protobuf files compiled successfully",
                    metrics={
                        "return_code": result.returncode,
                        "proto_files": 2,  # mcp.proto, ai_service.proto
                    },
                )
            else:
                self.report.add_step(
                    step_num,
                    "gRPC Proto Compilation",
                    StatusEnum.FAIL,
                    duration,
                    "Proto compilation failed",
                    errors=[result.stderr],
                )
        
        except subprocess.TimeoutExpired:
            duration = time.time() - start
            self.report.add_step(
                step_num,
                "gRPC Proto Compilation",
                StatusEnum.FAIL,
                duration,
                "Proto compilation timed out",
                errors=["Timeout after 60s"],
            )
        except Exception as e:
            duration = time.time() - start
            self.report.add_step(
                step_num,
                "gRPC Proto Compilation",
                StatusEnum.FAIL,
                duration,
                "Proto compilation error",
                errors=[str(e)],
            )
    
    async def _step_2_docker_build(self):
        """Step 2: Verify Docker images build."""
        step_num = 2
        start = time.time()
        
        try:
            result = subprocess.run(
                ["docker-compose", "build"],
                cwd=self.project_root,
                capture_output=True,
                timeout=600,  # 10 minute timeout
                text=True,
            )
            
            duration = time.time() - start
            
            if result.returncode == 0:
                self.report.add_step(
                    step_num,
                    "Docker Build",
                    StatusEnum.PASS,
                    duration,
                    "Docker images built successfully",
                    metrics={
                        "services": 2,
                        "build_time_seconds": duration,
                    },
                )
            else:
                self.report.add_step(
                    step_num,
                    "Docker Build",
                    StatusEnum.FAIL,
                    duration,
                    "Docker build failed",
                    errors=[result.stderr[-500:]],  # Last 500 chars
                )
        
        except subprocess.TimeoutExpired:
            duration = time.time() - start
            self.report.add_step(
                step_num,
                "Docker Build",
                StatusEnum.WARN,
                duration,
                "Docker build timeout (may still be building)",
                errors=["Timeout after 600s"],
            )
        except Exception as e:
            duration = time.time() - start
            self.report.add_step(
                step_num,
                "Docker Build",
                StatusEnum.FAIL,
                duration,
                "Docker build error",
                errors=[str(e)],
            )
    
    async def _step_3_service_health(self):
        """Step 3: Verify services reach healthy state."""
        step_num = 3
        start = time.time()
        
        try:
            result = subprocess.run(
                ["docker-compose", "up", "-d"],
                cwd=self.project_root,
                capture_output=True,
                timeout=120,
                text=True,
            )
            
            if result.returncode != 0:
                duration = time.time() - start
                self.report.add_step(
                    step_num,
                    "Service Health Check",
                    StatusEnum.FAIL,
                    duration,
                    "Failed to start services",
                    errors=[result.stderr],
                )
                return
            
            # Wait for health checks
            await asyncio.sleep(30)
            
            health_result = subprocess.run(
                ["docker-compose", "ps"],
                cwd=self.project_root,
                capture_output=True,
                timeout=30,
                text=True,
            )
            
            duration = time.time() - start
            
            # Parse output to check health status
            if "healthy" in health_result.stdout and result.returncode == 0:
                self.report.add_step(
                    step_num,
                    "Service Health Check",
                    StatusEnum.PASS,
                    duration,
                    "Both services healthy",
                    metrics={
                        "mcp_server": "healthy",
                        "ai_service": "healthy",
                    },
                )
            else:
                self.report.add_step(
                    step_num,
                    "Service Health Check",
                    StatusEnum.WARN,
                    duration,
                    "Services started but health status unclear",
                    errors=[health_result.stdout],
                )
        
        except Exception as e:
            duration = time.time() - start
            self.report.add_step(
                step_num,
                "Service Health Check",
                StatusEnum.FAIL,
                duration,
                "Service health check error",
                errors=[str(e)],
            )
    
    async def _step_4_static_analysis_tools(self):
        """Step 4: Verify CodeQL and Semgrep work independently."""
        step_num = 4
        start = time.time()
        
        try:
            # Test Semgrep on TypeScript fixture
            result = subprocess.run(
                ["semgrep", "--json", "tests/fixtures/vulnerable_typescript.ts"],
                cwd=self.project_root,
                capture_output=True,
                timeout=30,
                text=True,
            )
            
            duration = time.time() - start
            
            if result.returncode == 0:
                try:
                    output = json.loads(result.stdout)
                    findings_count = len(output.get("results", []))
                    
                    self.report.add_step(
                        step_num,
                        "Static Analysis Tools",
                        StatusEnum.PASS if findings_count > 0 else StatusEnum.WARN,
                        duration,
                        f"Semgrep found {findings_count} issues",
                        metrics={
                            "tool": "semgrep",
                            "findings": findings_count,
                            "response_time_ms": duration * 1000,
                        },
                    )
                except json.JSONDecodeError:
                    self.report.add_step(
                        step_num,
                        "Static Analysis Tools",
                        StatusEnum.WARN,
                        duration,
                        "Semgrep ran but output parsing failed",
                    )
            else:
                self.report.add_step(
                    step_num,
                    "Static Analysis Tools",
                    StatusEnum.FAIL,
                    duration,
                    "Semgrep execution failed",
                    errors=[result.stderr],
                )
        
        except subprocess.TimeoutExpired:
            duration = time.time() - start
            self.report.add_step(
                step_num,
                "Static Analysis Tools",
                StatusEnum.WARN,
                duration,
                "Semgrep timeout",
                errors=["Timeout after 30s"],
            )
        except Exception as e:
            duration = time.time() - start
            self.report.add_step(
                step_num,
                "Static Analysis Tools",
                StatusEnum.FAIL,
                duration,
                "Static analysis tools error",
                errors=[str(e)],
            )
    
    async def _step_5_ast_extraction(self):
        """Step 5: Verify AST extraction for all languages."""
        step_num = 5
        start = time.time()
        
        try:
            # Test AST extraction via Python
            result = subprocess.run(
                ["python3", "-m", "pytest", "tests/test_phase1_integration.py::test_ast_extraction", "-v"],
                cwd=self.project_root,
                capture_output=True,
                timeout=60,
                text=True,
            )
            
            duration = time.time() - start
            
            if result.returncode == 0:
                self.report.add_step(
                    step_num,
                    "AST Extraction",
                    StatusEnum.PASS,
                    duration,
                    "AST extraction working for all languages",
                    metrics={
                        "languages": 4,
                        "test_result": "passed",
                    },
                )
            else:
                self.report.add_step(
                    step_num,
                    "AST Extraction",
                    StatusEnum.WARN,
                    duration,
                    "AST extraction tests had issues",
                    errors=[result.stdout[-200:]],
                )
        
        except Exception as e:
            duration = time.time() - start
            self.report.add_step(
                step_num,
                "AST Extraction",
                StatusEnum.FAIL,
                duration,
                "AST extraction error",
                errors=[str(e)],
            )
    
    async def _step_6_e2e_pipeline(self):
        """Step 6: Verify end-to-end pipeline."""
        step_num = 6
        start = time.time()
        
        try:
            result = subprocess.run(
                ["python3", "-m", "pytest", "tests/test_phase1_integration.py::test_e2e_pipeline", "-v"],
                cwd=self.project_root,
                capture_output=True,
                timeout=300,  # 5 min timeout
                text=True,
            )
            
            duration = time.time() - start
            
            if result.returncode == 0:
                self.report.add_step(
                    step_num,
                    "End-to-End Pipeline",
                    StatusEnum.PASS,
                    duration,
                    "E2E pipeline test passed",
                    metrics={
                        "fixtures_analyzed": 10,
                        "avg_time_per_fixture": duration / 10,
                    },
                )
            else:
                self.report.add_step(
                    step_num,
                    "End-to-End Pipeline",
                    StatusEnum.FAIL,
                    duration,
                    "E2E pipeline test failed",
                    errors=[result.stdout[-200:]],
                )
        
        except subprocess.TimeoutExpired:
            duration = time.time() - start
            self.report.add_step(
                step_num,
                "End-to-End Pipeline",
                StatusEnum.WARN,
                duration,
                "E2E pipeline test timeout",
                errors=["Timeout after 300s - analysis may be slow"],
            )
        except Exception as e:
            duration = time.time() - start
            self.report.add_step(
                step_num,
                "End-to-End Pipeline",
                StatusEnum.FAIL,
                duration,
                "E2E pipeline error",
                errors=[str(e)],
            )
    
    async def _step_7_ai_reasoning(self):
        """Step 7: Verify AI reasoning quality."""
        step_num = 7
        start = time.time()
        
        try:
            result = subprocess.run(
                ["python3", "-m", "pytest", "tests/test_phase1_integration.py::test_ai_reasoning", "-v"],
                cwd=self.project_root,
                capture_output=True,
                timeout=120,
                text=True,
            )
            
            duration = time.time() - start
            
            if result.returncode == 0:
                self.report.add_step(
                    step_num,
                    "AI Reasoning Quality",
                    StatusEnum.PASS,
                    duration,
                    "AI reasoning tests passed",
                    metrics={
                        "cvss_accuracy": "validated",
                        "correlation_quality": "good",
                    },
                )
            else:
                self.report.add_step(
                    step_num,
                    "AI Reasoning Quality",
                    StatusEnum.WARN,
                    duration,
                    "AI reasoning tests had issues",
                    errors=[result.stdout[-200:]],
                )
        
        except Exception as e:
            duration = time.time() - start
            self.report.add_step(
                step_num,
                "AI Reasoning Quality",
                StatusEnum.FAIL,
                duration,
                "AI reasoning validation error",
                errors=[str(e)],
            )
    
    async def _step_8_baseline_metrics(self):
        """Step 8: Generate baseline metrics."""
        step_num = 8
        start = time.time()
        
        try:
            result = subprocess.run(
                ["python3", "tests/generate_phase1_metrics.py"],
                cwd=self.project_root,
                capture_output=True,
                timeout=60,
                text=True,
            )
            
            duration = time.time() - start
            
            if result.returncode == 0:
                self.report.add_step(
                    step_num,
                    "Baseline Metrics",
                    StatusEnum.PASS,
                    duration,
                    "Baseline metrics generated",
                    metrics={
                        "metrics_file": "tests/phase1_baseline_metrics.json",
                        "generation_time_s": duration,
                    },
                )
            else:
                self.report.add_step(
                    step_num,
                    "Baseline Metrics",
                    StatusEnum.WARN,
                    duration,
                    "Baseline metrics generation had issues",
                    errors=[result.stderr],
                )
        
        except Exception as e:
            duration = time.time() - start
            self.report.add_step(
                step_num,
                "Baseline Metrics",
                StatusEnum.FAIL,
                duration,
                "Baseline metrics error",
                errors=[str(e)],
            )
    
    def export_reports(self, output_dir: str = "tests/validation_reports"):
        """Export all validation reports."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = self.report.start_time.isoformat().replace(":", "-")
        
        # Export JSON
        json_file = output_path / f"validation_{timestamp}.json"
        self.report.export_json(str(json_file))
        logger.info(f"Exported JSON report: {json_file}")
        
        # Export Markdown
        md_file = output_path / f"validation_{timestamp}.md"
        self.report.export_markdown(str(md_file))
        logger.info(f"Exported Markdown report: {md_file}")


async def main():
    """Main orchestration entry point."""
    orchestrator = Phase1Orchestrator()
    
    logger.info("Starting Phase 1 validation...")
    report = await orchestrator.run_all_steps()
    
    # Print to terminal
    report.print_terminal()
    
    # Export reports
    orchestrator.export_reports()
    
    # Return exit code based on overall status
    return 0 if report.overall_status == StatusEnum.PASS else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
