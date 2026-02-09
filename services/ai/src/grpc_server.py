"""
MCP AI Service - gRPC-based AI analysis service for Phase 1.
Implements static analysis, AST extraction, AI reasoning, and report generation.
"""

import grpc
import logging
from concurrent import futures
from src.config import settings
from src.ai.gpt4o import GPT4oClient
from src.graph.kg import KnowledgeGraph
from src.prompts import load_prompt
from src.embeddings.cache import get_cache
from src.static_analysis.orchestrator import StaticAnalysisOrchestrator, StaticFinding
from src.ast_engine import ASTExtractor
from src.ai.correlation import AIReasoningEngine
from src.ai.scoring import CVSSScorer
from src.reports import ReportGenerator

# Protocol buffer generated files
from src.proto import ai_service_pb2
from src.proto import ai_service_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize global services
gpt_client = GPT4oClient()
kg = KnowledgeGraph()
embedding_cache = get_cache()
static_analyzer = StaticAnalysisOrchestrator()
ast_extractor = ASTExtractor()
ai_reasoner = AIReasoningEngine(gpt_client, kg)
cvss_scorer = CVSSScorer(gpt_client)
report_generator = ReportGenerator()


class AiServiceImpl(ai_service_pb2_grpc.AiServiceServicer):
    """gRPC service implementation for Phase 1 analysis pipeline."""
    
    async def StaticAnalysis(self, request, context):
        """
        Phase 1, Step 1: Run static analysis (CodeQL + Semgrep).
        """
        logger.info(f"StaticAnalysis request: {request.language} / {request.filename}")
        
        try:
            findings = await static_analyzer.analyze(
                code=request.code_snippet,
                language=request.language,
                filename=request.filename,
            )
            
            # Convert to protobuf format
            pb_findings = [
                ai_service_pb2.StaticFinding(
                    tool=f.tool,
                    rule_id=f.rule_id,
                    type=f.type,
                    message=f.message,
                    line=f.line,
                    column=f.column,
                    confidence=f.confidence,
                    severity=f.severity,
                    code_snippet=f.code_snippet,
                    remediation_hint=f.remediation_hint,
                )
                for f in findings
            ]
            
            logger.info(f"Found {len(pb_findings)} static findings")
            return ai_service_pb2.StaticAnalysisResponse(
                findings=pb_findings,
                analysis_time_ms=100,  # TODO: track actual time
            )
            
        except Exception as e:
            logger.error(f"StaticAnalysis error: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            raise
    
    async def ExtractAst(self, request, context):
        """
        Phase 1, Step 2: Extract AST from code.
        """
        logger.info(f"ExtractAst request: {request.language} / {request.filename}")
        
        try:
            ast_data = await ast_extractor.extract(
                code=request.code_snippet,
                language=request.language,
                filename=request.filename,
            )
            
            # Serialize AST to JSON
            import json
            ast_context = json.dumps(ast_data)
            
            return ai_service_pb2.AstExtractionResponse(
                functions=len(ast_data.get("functions", [])),
                variables=len(ast_data.get("variables", [])),
                dataflow_items=len(ast_data.get("dataflow", [])),
                ast_context=ast_context,
            )
            
        except Exception as e:
            logger.error(f"ExtractAst error: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            raise
    
    async def Reason(self, request, context):
        """
        Phase 1, Step 3: AI reasoning on findings and AST.
        """
        logger.info(f"Reason request: {len(request.findings)} findings")
        
        try:
            # Convert protobuf findings to domain objects
            findings = [
                StaticFinding(
                    tool=f.tool,
                    rule_id=f.rule_id,
                    type=f.type,
                    message=f.message,
                    line=f.line,
                    column=f.column,
                    confidence=f.confidence,
                    severity=f.severity,
                    code_snippet=f.code_snippet,
                    remediation_hint=f.remediation_hint,
                )
                for f in request.findings
            ]
            
            insights = await ai_reasoner.correlate_findings(
                findings=findings,
                code=request.code_snippet,
                language="unknown",  # TODO: add language to request if needed
            )
            
            # Convert insights to protobuf
            pb_correlations = [
                ai_service_pb2.VulnerabilityCorrelation(
                    vulnerability_ids=insight.vulnerability_chain,
                    exploitability=insight.exploitability_score,
                    attack_scenario=insight.attack_scenario,
                    impact=insight.impact_description,
                    requires_auth=insight.requires_authentication,
                )
                for insight in insights
            ]
            
            logger.info(f"Generated {len(pb_correlations)} correlations")
            return ai_service_pb2.ReasoningResponse(
                correlations=pb_correlations,
                reasoning_notes="AI reasoning complete",
            )
            
        except Exception as e:
            logger.error(f"Reason error: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            raise
    
    async def GenerateReport(self, request, context):
        """
        Phase 1, Step 4: Generate final vulnerability report.
        """
        logger.info(f"GenerateReport request: {request.code_id}")
        
        try:
            # Convert protobuf findings to domain objects
            findings = [
                StaticFinding(
                    tool=f.tool,
                    rule_id=f.rule_id,
                    type=f.type,
                    message=f.message,
                    line=f.line,
                    column=f.column,
                    confidence=f.confidence,
                    severity=f.severity,
                    code_snippet=f.code_snippet,
                    remediation_hint=f.remediation_hint,
                )
                for f in request.findings
            ]
            
            metadata = {
                "language": "unknown",
                "filename": request.code_id,
            }
            
            # Generate reports in all formats
            json_report = report_generator.generate_json_report(findings, metadata)
            markdown_report = report_generator.generate_markdown_report(findings, metadata)
            sarif_report = report_generator.generate_sarif_report(findings, metadata)
            
            # Convert findings to protobuf report vulnerabilities
            pb_vulns = []
            for f in findings:
                pb_vulns.append(
                    ai_service_pb2.ReportVulnerability(
                        id=f"VULN-{request.code_id}-{f.line}",
                        type=f.type,
                        severity=f.severity,
                        description=f.message,
                        line=f.line,
                        remediation=f.remediation_hint,
                        confidence=f.confidence,
                        cvss_vector="CVSS:3.1/AV:N/AT:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                        cvss_score=8.0,
                    )
                )
            
            logger.info(f"Generated report with {len(pb_vulns)} vulnerabilities")
            return ai_service_pb2.ReportResponse(
                vulnerabilities=pb_vulns,
                json_report=json_report,
                markdown_report=markdown_report,
                sarif_report=sarif_report,
            )
            
        except Exception as e:
            logger.error(f"GenerateReport error: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            raise
    
    async def Health(self, request, context):
        """Health check endpoint."""
        return ai_service_pb2.HealthResponse(status="healthy")


async def serve():
    """Start gRPC server."""
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    ai_service_pb2_grpc.add_AiServiceServicer_to_server(
        AiServiceImpl(), server
    )
    
    server.add_insecure_port(f"0.0.0.0:{settings.ai_service_port}")
    logger.info(f"Starting gRPC server on port {settings.ai_service_port}")
    
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    import asyncio
    asyncio.run(serve())
