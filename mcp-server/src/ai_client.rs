use tonic::transport::Channel;
use anyhow::Result;
use std::time::Duration;

pub mod ai {
    tonic::include_proto!("ai_service");
}

use ai::ai_service_client::AiServiceClient;
use ai::{CodeAnalysisRequest, HealthRequest, StaticAnalysisRequest, AstExtractionRequest, ReasoningRequest, ReportRequest};

pub struct AIServiceClient {
    client: AiServiceClient<Channel>,
}

impl AIServiceClient {
    pub async fn connect(url: &str) -> Result<Self> {
        let channel = Channel::from_shared(url.to_string())?
            .connect_timeout(Duration::from_secs(10))
            .connect()
            .await?;
        
        Ok(Self {
            client: AiServiceClient::new(channel),
        })
    }

    /// Phase 1: Step 1 - Run static analysis (CodeQL + Semgrep)
    pub async fn run_static_analysis(
        &mut self,
        language: String,
        code: String,
        filename: String,
    ) -> Result<ai::StaticAnalysisResponse> {
        let request = StaticAnalysisRequest {
            language,
            code_snippet: code,
            filename,
        };

        let response = self.client.static_analysis(request).await?;
        Ok(response.into_inner())
    }

    /// Phase 1: Step 2 - Extract AST
    pub async fn extract_ast(
        &mut self,
        language: String,
        code: String,
        filename: String,
    ) -> Result<ai::AstExtractionResponse> {
        let request = AstExtractionRequest {
            language,
            code_snippet: code,
            filename,
        };

        let response = self.client.extract_ast(request).await?;
        Ok(response.into_inner())
    }

    /// Phase 1: Step 3 - AI Reasoning on combined findings
    pub async fn reason_vulnerabilities(
        &mut self,
        findings: Vec<String>,
        ast_context: String,
        code: String,
    ) -> Result<ai::ReasoningResponse> {
        let request = ReasoningRequest {
            findings,
            ast_context,
            code_snippet: code,
        };

        let response = self.client.reason(request).await?;
        Ok(response.into_inner())
    }

    /// Phase 1: Step 4 - Generate final report
    pub async fn generate_report(
        &mut self,
        code_id: String,
        findings: Vec<String>,
        correlations: Vec<String>,
    ) -> Result<ai::ReportResponse> {
        let request = ReportRequest {
            code_id,
            findings,
            correlations,
        };

        let response = self.client.generate_report(request).await?;
        Ok(response.into_inner())
    }

    pub async fn health_check(&mut self) -> Result<ai::HealthResponse> {
        let request = HealthRequest {};
        let response = self.client.health(request).await?;
        Ok(response.into_inner())
    }
}
