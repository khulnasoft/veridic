use tonic::transport::Channel;
use anyhow::Result;
use std::time::Duration;

pub mod ai {
    tonic::include_proto!("ai");
}

use ai::ai_service_client::AiServiceClient;
use ai::{CodeAnalysisRequest, HealthRequest};

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

    pub async fn analyze_code(
        &mut self,
        language: String,
        code: String,
        filename: String,
    ) -> Result<ai::CodeAnalysisResponse> {
        let request = CodeAnalysisRequest {
            language,
            code_snippet: code,
            filename,
        };

        let response = self.client.analyze_code(request).await?;
        Ok(response.into_inner())
    }

    pub async fn health_check(&mut self) -> Result<ai::HealthResponse> {
        let request = HealthRequest {};
        let response = self.client.health(request).await?;
        Ok(response.into_inner())
    }
}
