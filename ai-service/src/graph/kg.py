import networkx as nx
from typing import Dict, List, Set
import logging

logger = logging.getLogger(__name__)

class KnowledgeGraph:
    """NetworkX-based knowledge graph for code analysis and reasoning."""
    
    def __init__(self):
        self.graph = nx.DiGraph()
    
    def add_vulnerability_node(self, vuln_id: str, vuln_type: str, severity: str):
        """Add a vulnerability node to the graph."""
        self.graph.add_node(
            vuln_id,
            node_type="vulnerability",
            vuln_type=vuln_type,
            severity=severity
        )
        logger.debug(f"Added vulnerability node: {vuln_id}")
    
    def add_code_node(self, code_id: str, language: str, filename: str):
        """Add a code snippet node to the graph."""
        self.graph.add_node(
            code_id,
            node_type="code",
            language=language,
            filename=filename
        )
    
    def add_relation(self, source: str, target: str, relation_type: str):
        """Add an edge between two nodes."""
        self.graph.add_edge(source, target, relation_type=relation_type)
        logger.debug(f"Added relation: {source} --{relation_type}--> {target}")
    
    def get_related_vulnerabilities(self, code_id: str) -> List[Dict]:
        """Get all vulnerabilities related to a code snippet."""
        related = []
        for successor in self.graph.successors(code_id):
            if self.graph.nodes[successor].get("node_type") == "vulnerability":
                related.append({
                    "id": successor,
                    "type": self.graph.nodes[successor].get("vuln_type"),
                    "severity": self.graph.nodes[successor].get("severity")
                })
        return related
    
    def get_severity_distribution(self) -> Dict[str, int]:
        """Get distribution of vulnerabilities by severity."""
        distribution = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for node_id, attrs in self.graph.nodes(data=True):
            if attrs.get("node_type") == "vulnerability":
                severity = attrs.get("severity", "low")
                if severity in distribution:
                    distribution[severity] += 1
        return distribution
    
    def export_json(self) -> Dict:
        """Export graph as JSON for visualization."""
        return {
            "nodes": [
                {"id": n, **attrs}
                for n, attrs in self.graph.nodes(data=True)
            ],
            "edges": [
                {"source": u, "target": v, **attrs}
                for u, v, attrs in self.graph.edges(data=True)
            ]
        }
