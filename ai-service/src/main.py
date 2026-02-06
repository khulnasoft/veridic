from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from src.config import settings
from src.ai.gpt4o import GPT4oClient
from src.graph.kg import KnowledgeGraph
from src.prompts import load_prompt, render_prompt
from src.embeddings.cache import get_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP AI Service", version="0.1.0")

# Initialize global services
gpt_client = GPT4oClient()
kg = KnowledgeGraph()
embedding_cache = get_cache()

class CodeSnippetRequest(BaseModel):
    language: str
    code: str
    filename: str

class HealthResponse(BaseModel):
    status: str
    version: str

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.1.0"
    )

@app.post("/analyze")
async def analyze_code(request: CodeSnippetRequest):
    """Analyze code for vulnerabilities using GPT-4o."""
    try:
        logger.info(f"Analyzing {request.language} code: {request.filename}")
        
        # Load prompt template
        prompt_config = load_prompt("code_vulnerability_detection")
        system_prompt = prompt_config["system"].format(language=request.language)
        
        # Call GPT-4o
        analysis = await gpt_client.analyze_code(
            code=request.code,
            language=request.language,
            system_prompt=system_prompt
        )
        
        # Add to knowledge graph
        code_id = f"code_{request.filename}"
        kg.add_code_node(code_id, request.language, request.filename)
        
        return {
            "code_id": code_id,
            "analysis": analysis,
            "cached": False
        }
    except Exception as e:
        logger.error(f"Error analyzing code: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph")
async def export_graph():
    """Export knowledge graph as JSON."""
    return kg.export_json()

@app.get("/stats")
async def get_stats():
    """Get system statistics."""
    return {
        "embedding_cache": embedding_cache.stats(),
        "graph_nodes": len(kg.graph.nodes()),
        "graph_edges": len(kg.graph.edges()),
        "severity_distribution": kg.get_severity_distribution()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.ai_service_host,
        port=settings.ai_service_port,
        log_level="info"
    )
