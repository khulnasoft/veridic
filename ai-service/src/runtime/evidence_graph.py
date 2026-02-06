"""
Phase 2.2: Evidence Graph
Lightweight node/edge structure for exploit chains.
Sets up for Phase 2.3 AI reasoning over evidence graphs.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum
import json

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Types of nodes in evidence graph"""
    STATIC_FINDING = "static_finding"
    SYSCALL_EVENT = "syscall_event"
    NETWORK_EVENT = "network_event"
    FILE_EVENT = "file_event"
    EXPLOIT_CHAIN = "exploit_chain"


class EdgeType(Enum):
    """Types of edges in evidence graph"""
    CAUSES = "causes"  # A leads to B
    SUPPORTS = "supports"  # Evidence supports finding
    REFUTES = "refutes"  # Evidence contradicts
    TEMPORAL = "temporal"  # B occurred after A
    CAUSAL = "causal"  # A caused B


@dataclass
class GraphNode:
    """Node in evidence graph"""
    node_id: str
    node_type: NodeType
    label: str
    confidence: float  # 0-1
    metadata: Dict = field(default_factory=dict)
    timestamp: Optional[int] = None
    
    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "label": self.label,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


@dataclass
class GraphEdge:
    """Edge in evidence graph"""
    edge_id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float  # 0-1 (strength of relationship)
    evidence: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value,
            "weight": self.weight,
            "evidence": self.evidence
        }


class EvidenceGraph:
    """
    Lightweight evidence graph for exploit chains.
    Nodes: findings, events
    Edges: causal relationships, temporal ordering, evidence support
    """
    
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}
        self.adjacency: Dict[str, Set[str]] = {}  # node_id -> set of connected node_ids
        self.logger = logging.getLogger(__name__)
    
    def add_node(self, node: GraphNode) -> None:
        """Add node to graph"""
        self.nodes[node.node_id] = node
        if node.node_id not in self.adjacency:
            self.adjacency[node.node_id] = set()
        self.logger.debug(f"Added node: {node.node_id} ({node.node_type.value})")
    
    def add_edge(self, edge: GraphEdge) -> None:
        """Add edge to graph"""
        # Validate nodes exist
        if edge.source_id not in self.nodes:
            self.logger.warning(f"Source node {edge.source_id} not in graph")
            return
        if edge.target_id not in self.nodes:
            self.logger.warning(f"Target node {edge.target_id} not in graph")
            return
        
        self.edges[edge.edge_id] = edge
        self.adjacency[edge.source_id].add(edge.target_id)
        self.adjacency[edge.target_id].add(edge.source_id)
        self.logger.debug(f"Added edge: {edge.source_id} -> {edge.target_id} ({edge.edge_type.value})")
    
    def find_paths(self, start_id: str, end_id: str, max_depth: int = 5) -> List[List[str]]:
        """Find all paths between two nodes (BFS)"""
        if start_id not in self.nodes or end_id not in self.nodes:
            return []
        
        paths = []
        visited = set()
        queue = [(start_id, [start_id])]
        
        while queue:
            current, path = queue.pop(0)
            if len(path) > max_depth:
                continue
            
            if current == end_id:
                paths.append(path)
                continue
            
            for neighbor in self.adjacency.get(current, set()):
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))
        
        return paths
    
    def get_evidence_chain(self, finding_id: str) -> Dict:
        """
        Extract evidence chain from finding node.
        Returns: Dict with finding, supporting events, and confidence scores.
        """
        if finding_id not in self.nodes:
            return {}
        
        finding_node = self.nodes[finding_id]
        chain = {
            "finding_id": finding_id,
            "finding_type": finding_node.label,
            "finding_confidence": finding_node.confidence,
            "supporting_events": [],
            "chain_confidence": finding_node.confidence
        }
        
        # Find all SUPPORTS edges pointing to this finding
        supporting_edges = [
            edge for edge in self.edges.values()
            if edge.target_id == finding_id and edge.edge_type == EdgeType.SUPPORTS
        ]
        
        for edge in supporting_edges:
            event_node = self.nodes.get(edge.source_id)
            if event_node:
                chain["supporting_events"].append({
                    "event_id": event_node.node_id,
                    "event_type": event_node.node_type.value,
                    "label": event_node.label,
                    "confidence": event_node.confidence,
                    "edge_weight": edge.weight,
                    "evidence": edge.evidence
                })
        
        # Calculate chain confidence
        if chain["supporting_events"]:
            avg_event_confidence = sum(
                e["confidence"] * e["edge_weight"] for e in chain["supporting_events"]
            ) / len(chain["supporting_events"])
            chain["chain_confidence"] = min(
                (finding_node.confidence + avg_event_confidence) / 2.0,
                1.0
            )
        
        return chain
    
    def get_subgraph(self, central_node_id: str, radius: int = 2) -> "EvidenceGraph":
        """
        Extract subgraph around central node.
        Useful for focused analysis.
        """
        subgraph = EvidenceGraph()
        
        if central_node_id not in self.nodes:
            return subgraph
        
        # BFS to find nodes within radius
        visited = {central_node_id}
        queue = [(central_node_id, 0)]
        connected_nodes = {central_node_id}
        
        while queue:
            current, depth = queue.pop(0)
            if depth >= radius:
                continue
            
            for neighbor in self.adjacency.get(current, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))
                    connected_nodes.add(neighbor)
        
        # Add nodes
        for node_id in connected_nodes:
            subgraph.add_node(self.nodes[node_id])
        
        # Add edges within subgraph
        for edge in self.edges.values():
            if edge.source_id in connected_nodes and edge.target_id in connected_nodes:
                subgraph.add_edge(edge)
        
        return subgraph
    
    def to_dict(self) -> Dict:
        """Serialize graph to JSON-compatible dict"""
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges.values()]
        }
    
    def to_json(self) -> str:
        """Serialize graph to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    def get_statistics(self) -> Dict:
        """Get graph statistics"""
        return {
            "num_nodes": len(self.nodes),
            "num_edges": len(self.edges),
            "node_types": {
                nt.value: len([n for n in self.nodes.values() if n.node_type == nt])
                for nt in NodeType
            },
            "edge_types": {
                et.value: len([e for e in self.edges.values() if e.edge_type == et])
                for et in EdgeType
            }
        }
