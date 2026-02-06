// Models for Rust MCP Server
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CodeAnalysisRequest {
    pub language: String,
    pub code: String,
    pub filename: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VulnConfig {
    pub ai_service_url: String,
    pub timeout_secs: u64,
    pub max_retries: u32,
}

impl Default for VulnConfig {
    fn default() -> Self {
        Self {
            ai_service_url: "http://localhost:8000".to_string(),
            timeout_secs: 30,
            max_retries: 3,
        }
    }
}
