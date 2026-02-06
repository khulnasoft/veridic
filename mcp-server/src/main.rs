use tonic::{transport::Server, Request, Response, Status};
use tracing_subscriber;
use std::sync::{Arc, Mutex};

mod models;
mod handlers;
mod ai_client;

pub mod mcp {
    tonic::include_proto!("mcp");
}

use mcp::{mcp_server::{Mcp, McpServer}, CodeSnippet, VulnerabilityReport, QueryRequest, Vulnerability, Empty, HealthResponse};
use ai_client::AIServiceClient;

#[derive(Clone)]
pub struct McpService {
    ai_client: Arc<Mutex<Option<AIServiceClient>>>,
}

impl Default for McpService {
    fn default() -> Self {
        Self {
            ai_client: Arc::new(Mutex::new(None)),
        }
    }
}

impl McpService {
    pub async fn with_ai_client(ai_url: &str) -> Result<Self, Box<dyn std::error::Error>> {
        let client = AIServiceClient::connect(ai_url).await?;
        Ok(Self {
            ai_client: Arc::new(Mutex::new(Some(client))),
        })
    }
}

#[tonic::async_trait]
impl Mcp for McpService {
    async fn analyze_code(
        &self,
        request: Request<CodeSnippet>,
    ) -> Result<Response<VulnerabilityReport>, Status> {
        let snippet = request.into_inner();
        let code_id = format!("code_{}", uuid::Uuid::new_v4());
        
        tracing::info!(
            code_id = %code_id,
            language = %snippet.language,
            filename = %snippet.filename,
            "Starting Phase 1 orchestrated analysis pipeline"
        );

        let mut ai_lock = self.ai_client.lock().unwrap();
        
        if let Some(ref mut client) = *ai_lock {
            // Phase 1 Orchestration Pipeline:
            // 1. Run static analysis (CodeQL + Semgrep)
            tracing::debug!("Step 1: Running static analysis tools");
            match client.run_static_analysis(
                snippet.language.clone(),
                snippet.code.clone(),
                snippet.filename.clone(),
            ).await {
                Ok(static_findings) => {
                    tracing::info!("Static analysis found {} issues", static_findings.findings.len());
                    
                    // 2. Extract AST for code understanding
                    tracing::debug!("Step 2: Extracting AST");
                    match client.extract_ast(
                        snippet.language.clone(),
                        snippet.code.clone(),
                        snippet.filename.clone(),
                    ).await {
                        Ok(ast_data) => {
                            tracing::debug!("AST extraction complete: {} functions", ast_data.functions.len());
                            
                            // 3. Run AI reasoning on combined findings
                            tracing::debug!("Step 3: Running AI reasoning");
                            match client.reason_vulnerabilities(
                                static_findings.findings.clone(),
                                ast_data.ast_context.clone(),
                                snippet.code.clone(),
                            ).await {
                                Ok(ai_insights) => {
                                    tracing::debug!("AI reasoning generated {} insights", ai_insights.correlations.len());
                                    
                                    // 4. Generate final report
                                    tracing::debug!("Step 4: Generating vulnerability report");
                                    match client.generate_report(
                                        code_id.clone(),
                                        static_findings.findings.clone(),
                                        ai_insights.correlations.clone(),
                                    ).await {
                                        Ok(report_data) => {
                                            let vulnerabilities = report_data.vulnerabilities
                                                .into_iter()
                                                .map(|v| Vulnerability {
                                                    id: format!("vuln_{}", uuid::Uuid::new_v4()),
                                                    type_: v.type_,
                                                    severity: v.severity,
                                                    description: v.description,
                                                    line_number: v.line,
                                                    remediation: v.remediation,
                                                    confidence: v.confidence as f32,
                                                })
                                                .collect();
                                            
                                            let final_report = VulnerabilityReport {
                                                code_id,
                                                vulnerabilities,
                                                analysis_timestamp: chrono::Utc::now().to_rfc3339(),
                                                model_used: "gpt-4o + static-analysis".to_string(),
                                            };
                                            
                                            tracing::info!("Analysis complete: {} vulnerabilities found", final_report.vulnerabilities.len());
                                            Ok(Response::new(final_report))
                                        },
                                        Err(e) => {
                                            tracing::error!("Report generation error: {}", e);
                                            Err(Status::internal(format!("Report generation error: {}", e)))
                                        }
                                    }
                                },
                                Err(e) => {
                                    tracing::error!("AI reasoning error: {}", e);
                                    Err(Status::internal(format!("AI reasoning error: {}", e)))
                                }
                            }
                        },
                        Err(e) => {
                            tracing::error!("AST extraction error: {}", e);
                            Err(Status::internal(format!("AST extraction error: {}", e)))
                        }
                    }
                },
                Err(e) => {
                    tracing::error!("Static analysis error: {}", e);
                    Err(Status::internal(format!("Static analysis error: {}", e)))
                }
            }
        } else {
            tracing::warn!("AI service not connected");
            Err(Status::unavailable("AI service not connected"))
        }
    }

    async fn get_vulnerabilities(
        &self,
        _request: Request<QueryRequest>,
    ) -> Result<Response<tonic::codec::Streaming<Vulnerability>>, Status> {
        // TODO: Implement streaming from database
        let (tx, rx) = tokio::sync::mpsc::channel(10);

        tokio::spawn(async move {
            drop(tx);
        });

        Ok(Response::new(
            tonic::codec::Streaming::new(
                rx
            ),
        ))
    }

    async fn health(
        &self,
        _request: Request<Empty>,
    ) -> Result<Response<HealthResponse>, Status> {
        Ok(Response::new(HealthResponse {
            status: "healthy".to_string(),
            version: env!("CARGO_PKG_VERSION").to_string(),
        }))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt::init();

    let addr = "127.0.0.1:50051".parse()?;
    let ai_service_url = std::env::var("AI_SERVICE_URL")
        .unwrap_or_else(|_| "http://localhost:8000".to_string());

    tracing::info!("MCP gRPC server listening on {}", addr);
    tracing::info!("Connecting to AI service at {}", ai_service_url);

    let service = McpService::with_ai_client(&ai_service_url).await
        .unwrap_or_else(|e| {
            tracing::warn!("Failed to connect to AI service: {}", e);
            McpService::default()
        });

    Server::builder()
        .add_service(McpServer::new(service))
        .serve(addr)
        .await?;

    Ok(())
}

