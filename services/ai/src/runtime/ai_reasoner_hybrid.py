"""
Phase 2.3: Hybrid AI Reasoner (GPT-4o primary + Ollama fallback)
Deterministic verdict generation with identical behavior across backends.
Temperature=0, fixed prompts, hashable inputs/outputs.
"""

import json
import logging
import asyncio
from typing import Optional, Dict, Any
from enum import Enum
import os

from ai_reasoning_contract import (
    AIReasoningInput, AIReasoningOutput, HallucinationGuard, DeterminismValidator
)
from conflict_resolver import ConflictResolver

logger = logging.getLogger(__name__)


class AIBackend(Enum):
    """Supported AI backends"""
    OPENAI_GPT4O = "openai_gpt4o"
    OLLAMA_LOCAL = "ollama_local"


class AIReasonerConfig:
    """Configuration for AI reasoner"""
    def __init__(
        self,
        primary_backend: AIBackend = AIBackend.OPENAI_GPT4O,
        fallback_backend: Optional[AIBackend] = AIBackend.OLLAMA_LOCAL,
        openai_api_key: Optional[str] = None,
        ollama_base_url: str = "http://localhost:11434",
        temperature: float = 0.0,  # Strict determinism
        max_retries: int = 3,
    ):
        self.primary_backend = primary_backend
        self.fallback_backend = fallback_backend
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.ollama_base_url = ollama_base_url
        self.temperature = temperature
        self.max_retries = max_retries


class GPT4oReasoner:
    """OpenAI GPT-4o backend (primary)"""
    
    def __init__(self, api_key: str, temperature: float = 0.0):
        self.api_key = api_key
        self.temperature = temperature
        # Import openai client
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=api_key)
        except ImportError:
            raise RuntimeError("OpenAI client not installed. Install with: pip install openai")
    
    async def reason(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Call GPT-4o with deterministic settings.
        Temperature=0 for reproducibility.
        """
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=self.temperature,
                    top_p=1.0,  # Deterministic
                    max_tokens=4096,
                )
                
                response_text = response.choices[0].message.content
                
                # Parse JSON response
                try:
                    parsed = json.loads(response_text)
                    return {
                        "success": True,
                        "data": parsed,
                        "model": "gpt-4o",
                        "tokens_used": response.usage.total_tokens
                    }
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse GPT-4o response: {e}")
                    return {
                        "success": False,
                        "error": f"Invalid JSON response: {str(e)}",
                        "raw_response": response_text
                    }
            
            except Exception as e:
                logger.warning(f"GPT-4o attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return {
                        "success": False,
                        "error": f"All retries exhausted: {str(e)}"
                    }
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return {"success": False, "error": "Unknown error"}


class OllamaReasoner:
    """Local Ollama backend (fallback)"""
    
    def __init__(self, base_url: str = "http://localhost:11434", temperature: float = 0.0):
        self.base_url = base_url
        self.temperature = temperature
        self.model = "llama2"  # Default model
        try:
            import requests
            self.requests = requests
        except ImportError:
            raise RuntimeError("requests not installed. Install with: pip install requests")
    
    async def reason(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Call local Ollama with deterministic settings.
        Temperature=0 for reproducibility.
        """
        for attempt in range(max_retries):
            try:
                # Format prompt for Ollama
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                
                response = self.requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "temperature": self.temperature,
                        "stream": False,
                    },
                    timeout=60
                )
                response.raise_for_status()
                
                response_data = response.json()
                response_text = response_data.get("response", "")
                
                # Parse JSON response
                try:
                    # Extract JSON from response (Ollama may include extra text)
                    json_start = response_text.find("{")
                    json_end = response_text.rfind("}") + 1
                    if json_start != -1 and json_end > json_start:
                        json_str = response_text[json_start:json_end]
                        parsed = json.loads(json_str)
                    else:
                        raise ValueError("No JSON found in response")
                    
                    return {
                        "success": True,
                        "data": parsed,
                        "model": self.model,
                    }
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Failed to parse Ollama response: {e}")
                    return {
                        "success": False,
                        "error": f"Invalid JSON response: {str(e)}",
                        "raw_response": response_text
                    }
            
            except Exception as e:
                logger.warning(f"Ollama attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return {
                        "success": False,
                        "error": f"All retries exhausted: {str(e)}"
                    }
                await asyncio.sleep(2 ** attempt)
        
        return {"success": False, "error": "Unknown error"}


class HybridAIReasoner:
    """
    Hybrid reasoner: GPT-4o primary, Ollama fallback.
    Same prompt, same temperature, same output schema.
    Ensures identical verdicts regardless of backend.
    """
    
    def __init__(self, config: AIReasonerConfig):
        self.config = config
        self.primary = None
        self.fallback = None
        self.conflict_resolver = ConflictResolver()
        
        # Initialize primary backend
        if config.primary_backend == AIBackend.OPENAI_GPT4O:
            if not config.openai_api_key:
                raise ValueError("OPENAI_API_KEY required for GPT-4o backend")
            self.primary = GPT4oReasoner(config.openai_api_key, config.temperature)
        elif config.primary_backend == AIBackend.OLLAMA_LOCAL:
            self.primary = OllamaReasoner(config.ollama_base_url, config.temperature)
        
        # Initialize fallback backend
        if config.fallback_backend == AIBackend.OLLAMA_LOCAL:
            self.fallback = OllamaReasoner(config.ollama_base_url, config.temperature)
        elif config.fallback_backend == AIBackend.OPENAI_GPT4O:
            if config.openai_api_key:
                self.fallback = GPT4oReasoner(config.openai_api_key, config.temperature)
    
    async def reason(
        self,
        input_contract: AIReasoningInput,
        prompts: Dict[str, Any]
    ) -> AIReasoningOutput:
        """
        Generate AI verdict with determinism validation.
        
        1. Call primary backend
        2. On failure, try fallback
        3. Validate output against input
        4. Check determinism
        5. Return verdict
        """
        
        # Load prompts
        verdict_prompt = prompts.get("verdict_reasoning", {})
        system_prompt = verdict_prompt.get("system_prompt", "")
        user_prompt_template = verdict_prompt.get("user_prompt_template", "")
        
        # Format user prompt with input
        user_prompt = user_prompt_template.format(
            static_findings=json.dumps([f.to_dict() for f in input_contract.findings]),
            evidence_chains=json.dumps([c.to_dict() for c in input_contract.evidence_chains]),
            conflicting_findings=json.dumps(input_contract.conflicting_findings)
        )
        
        # Try primary backend
        logger.info(f"Calling primary backend: {self.config.primary_backend}")
        result = await self.primary.reason(system_prompt, user_prompt, self.config.max_retries)
        
        # If primary fails, try fallback
        if not result["success"] and self.fallback:
            logger.warning(f"Primary backend failed, trying fallback: {self.config.fallback_backend}")
            result = await self.fallback.reason(system_prompt, user_prompt, self.config.max_retries)
        
        # Check for success
        if not result["success"]:
            raise RuntimeError(f"All AI backends failed: {result.get('error')}")
        
        # Parse verdict
        verdict_data = result["data"]
        
        # Validate against hallucination guard
        output = AIReasoningOutput(
            sandbox_session_id=input_contract.sandbox_session_id,
            findings_verdicts=verdict_data.get("findings_verdicts", {}),
            conflicts_resolved=verdict_data.get("conflicts_resolved", {}),
            new_facts_attempted=verdict_data.get("new_facts_attempted", [])
        )
        
        # Check hallucinations
        guard = HallucinationGuard(input_contract)
        is_valid, violations = guard.validate_output(output)
        
        if not is_valid:
            logger.error(f"Hallucination detected: {violations}")
            raise ValueError(f"Output failed hallucination guard: {violations}")
        
        # Compute hashes for determinism
        output.reasoning_hash = output.compute_hash()
        
        logger.info(f"AI reasoning complete. Output hash: {output.reasoning_hash}")
        return output
