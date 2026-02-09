"""
AI reasoning layer for correlating findings and generating insights.
Uses GPT-4o to reason about severity, exploitability, and vulnerability chains.
"""

import json
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from .gpt4o import GPT4oClient
from ..graph.kg import KnowledgeGraph
from ..static_analysis.orchestrator import StaticFinding

logger = logging.getLogger(__name__)


@dataclass
class AIInsight:
    vulnerability_chain: List[str]  # Related vulnerability IDs
    exploitability_score: float  # 0.0 - 1.0
    attack_scenario: str
    impact_description: str
    requires_authentication: bool


class AIReasoningEngine:
    """Correlates findings and performs AI reasoning on vulnerabilities."""
    
    def __init__(self, gpt_client: GPT4oClient, kg: KnowledgeGraph):
        self.gpt = gpt_client
        self.kg = kg
    
    async def correlate_findings(
        self,
        findings: List[StaticFinding],
        code: str,
        language: str,
    ) -> List[AIInsight]:
        """
        Use GPT-4o to correlate static findings and generate insights.
        
        Args:
            findings: Static analysis findings
            code: Original source code
            language: Programming language
            
        Returns:
            List of AI insights linking related vulnerabilities
        """
        logger.info(f"Correlating {len(findings)} findings using AI reasoning")
        
        if not findings:
            return []
        
        # Build correlation prompt
        findings_text = "\n".join([
            f"- Line {f.line}: {f.type} - {f.message}"
            for f in findings
        ])
        
        prompt = f"""Analyze these security findings from {language} code and identify vulnerability chains:

{findings_text}

CODE CONTEXT:
{code[:1000]}...

For each correlated group of findings:
1. Identify if they form an exploitable vulnerability chain
2. Rate exploitability (0.0-1.0)
3. Describe a realistic attack scenario
4. Identify if authentication is required

Return JSON array of correlations.
        """
        
        try:
            response = await self.gpt.call(prompt)
            insights = self._parse_insights(response)
            
            # Store in knowledge graph
            for insight in insights:
                self.kg.add_vulnerability_chain(
                    vuln_ids=insight.vulnerability_chain,
                    exploitability=insight.exploitability_score,
                )
            
            return insights
            
        except Exception as e:
            logger.error(f"AI correlation error: {e}")
            return []
    
    def _parse_insights(self, response: str) -> List[AIInsight]:
        """Parse GPT-4o response into AIInsight objects."""
        insights = []
        
        try:
            # Extract JSON from response
            start = response.find("[")
            end = response.rfind("]") + 1
            
            if start == -1 or end == 0:
                logger.warning("No JSON array found in GPT response")
                return []
            
            data = json.loads(response[start:end])
            
            for item in data:
                insight = AIInsight(
                    vulnerability_chain=item.get("chain", []),
                    exploitability_score=float(item.get("exploitability", 0.5)),
                    attack_scenario=item.get("scenario", ""),
                    impact_description=item.get("impact", ""),
                    requires_authentication=item.get("requires_auth", False),
                )
                insights.append(insight)
                
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Error parsing insights: {e}")
        
        return insights
