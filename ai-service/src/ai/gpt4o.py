import openai
from typing import Dict, Any, Optional
from src.config import settings
import json
import logging

logger = logging.getLogger(__name__)

class GPT4oClient:
    def __init__(self, api_key: Optional[str] = None):
        self.client = openai.OpenAI(api_key=api_key or settings.openai_api_key)
        self.model = settings.openai_model
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature

    async def analyze_code(self, code: str, language: str, system_prompt: str) -> Dict[str, Any]:
        """Call GPT-4o to analyze code for vulnerabilities."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Analyze this {language} code:\n\n```{language}\n{code}\n```"
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            
            content = response.choices[0].message.content
            logger.info(f"GPT-4o analysis completed for {language}")
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                logger.warning("GPT-4o response was not JSON, returning raw content")
                return {"raw_response": content}
                
        except Exception as e:
            logger.error(f"Error calling GPT-4o: {e}")
            raise

    async def classify_severity(self, vulnerability_desc: str) -> Dict[str, Any]:
        """Classify vulnerability severity."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Classify vulnerability severity as critical, high, medium, or low."
                    },
                    {"role": "user", "content": vulnerability_desc}
                ],
                max_tokens=256,
                temperature=0.1,
            )
            
            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"severity": "medium", "raw": content}
                
        except Exception as e:
            logger.error(f"Error classifying severity: {e}")
            raise
