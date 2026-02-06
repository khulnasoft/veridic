"""
Tool Attribution Metrics for Phase 1 Validation

Tracks which static analysis tools (CodeQL, Semgrep, AST) discover each vulnerability.
Provides insights into tool effectiveness, overlap, and complementary coverage.
"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Set
from collections import defaultdict


@dataclass
class VulnerabilityFinding:
    """Represents a single vulnerability finding with metadata."""
    id: str  # Unique identifier
    type: str  # SQL injection, XSS, race condition, etc.
    line: int
    file: str
    language: str
    severity: str  # Critical, High, Medium, Low
    found_by: List[str]  # Tools that detected this: ['codeql', 'semgrep', 'ast']
    confidence: float  # Combined confidence 0.0-1.0
    cvss_score: float


@dataclass
class ToolMetrics:
    """Metrics for a single analysis tool."""
    tool_name: str
    findings_count: int
    unique_findings: int  # Not found by other tools
    overlap_with_others: int  # Found by multiple tools
    average_confidence: float
    accuracy_rate: float  # Correct detections / total detections
    false_positive_rate: float
    response_time_ms: float


class ToolAttributionAnalyzer:
    """Analyzes tool effectiveness and attribution."""
    
    def __init__(self):
        self.findings: Dict[str, VulnerabilityFinding] = {}
        self.tool_metrics: Dict[str, ToolMetrics] = {}
    
    def add_finding(self, finding: VulnerabilityFinding):
        """Register a vulnerability finding."""
        if finding.id not in self.findings:
            self.findings[finding.id] = finding
        else:
            # Merge tool attribution
            existing = self.findings[finding.id]
            existing.found_by = list(set(existing.found_by + finding.found_by))
            existing.confidence = max(existing.confidence, finding.confidence)
    
    def compute_metrics(self) -> Dict[str, ToolMetrics]:
        """Compute metrics for each tool."""
        tool_findings: Dict[str, List[str]] = defaultdict(list)
        
        # Collect findings by tool
        for finding_id, finding in self.findings.items():
            for tool in finding.found_by:
                tool_findings[tool].append(finding_id)
        
        # Compute metrics
        metrics = {}
        for tool, finding_ids in tool_findings.items():
            unique = len([
                fid for fid in finding_ids
                if len(self.findings[fid].found_by) == 1
            ])
            overlap = len(finding_ids) - unique
            
            confidences = [
                self.findings[fid].confidence
                for fid in finding_ids
            ]
            
            metrics[tool] = ToolMetrics(
                tool_name=tool,
                findings_count=len(finding_ids),
                unique_findings=unique,
                overlap_with_others=overlap,
                average_confidence=sum(confidences) / len(confidences) if confidences else 0.0,
                accuracy_rate=0.0,  # Set by validation
                false_positive_rate=0.0,  # Set by validation
                response_time_ms=0.0  # Set by validation
            )
        
        self.tool_metrics = metrics
        return metrics
    
    def get_tool_overlap_matrix(self) -> Dict[str, Dict[str, int]]:
        """
        Compute overlap between tools.
        Returns matrix: overlap_matrix[tool_a][tool_b] = count of findings both found
        """
        tools = list(set(
            tool
            for finding in self.findings.values()
            for tool in finding.found_by
        ))
        
        overlap = {tool: {other: 0 for other in tools} for tool in tools}
        
        for finding in self.findings.values():
            for tool_a in finding.found_by:
                for tool_b in finding.found_by:
                    if tool_a != tool_b:
                        overlap[tool_a][tool_b] += 1
        
        return overlap
    
    def get_coverage_by_vulnerability_type(self) -> Dict[str, Dict]:
        """
        Analyze coverage by vulnerability type.
        Returns: {vuln_type: {tool: count, total: count}}
        """
        coverage = defaultdict(lambda: defaultdict(int))
        
        for finding in self.findings.values():
            vuln_type = finding.type
            for tool in finding.found_by:
                coverage[vuln_type][tool] += 1
            coverage[vuln_type]['total'] = coverage[vuln_type].get('total', 0) + 1
        
        return dict(coverage)
    
    def get_language_coverage(self) -> Dict[str, Dict]:
        """
        Analyze coverage by programming language.
        Returns: {language: {tool: count, total: count}}
        """
        coverage = defaultdict(lambda: defaultdict(int))
        
        for finding in self.findings.values():
            lang = finding.language
            for tool in finding.found_by:
                coverage[lang][tool] += 1
            coverage[lang]['total'] = coverage[lang].get('total', 0) + 1
        
        return dict(coverage)
    
    def generate_report(self) -> Dict:
        """Generate comprehensive tool attribution report."""
        self.compute_metrics()
        
        return {
            'summary': {
                'total_findings': len(self.findings),
                'tools_used': list(self.tool_metrics.keys()),
                'tools_count': len(self.tool_metrics),
                'average_tool_agreement': self._compute_tool_agreement(),
            },
            'tool_metrics': {
                name: asdict(metrics)
                for name, metrics in self.tool_metrics.items()
            },
            'overlap_matrix': self.get_tool_overlap_matrix(),
            'coverage_by_type': self.get_coverage_by_vulnerability_type(),
            'coverage_by_language': self.get_language_coverage(),
            'tools_complementarity': self._compute_complementarity(),
        }
    
    def _compute_tool_agreement(self) -> float:
        """Compute average agreement between tools (0.0-1.0)."""
        if not self.findings:
            return 0.0
        
        multi_tool_findings = len([
            f for f in self.findings.values()
            if len(f.found_by) > 1
        ])
        
        return multi_tool_findings / len(self.findings)
    
    def _compute_complementarity(self) -> Dict[str, float]:
        """
        Compute complementarity score for each tool.
        High score = tool finds unique vulnerabilities not found by others.
        """
        complementarity = {}
        
        for tool, metrics in self.tool_metrics.items():
            if metrics.findings_count == 0:
                complementarity[tool] = 0.0
            else:
                score = metrics.unique_findings / metrics.findings_count
                complementarity[tool] = score
        
        return complementarity
    
    def export_json(self, filepath: str):
        """Export metrics to JSON file."""
        report = self.generate_report()
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
    
    def export_markdown(self, filepath: str):
        """Export metrics to Markdown report."""
        report = self.generate_report()
        
        lines = [
            "# Phase 1 Tool Attribution Metrics\n",
            "## Summary",
            f"- Total Findings: {report['summary']['total_findings']}",
            f"- Tools Used: {', '.join(report['summary']['tools_used'])}",
            f"- Average Tool Agreement: {report['summary']['average_tool_agreement']:.1%}\n",
        ]
        
        lines.append("## Tool Metrics")
        for tool, metrics in report['tool_metrics'].items():
            lines.append(f"\n### {tool.upper()}")
            lines.append(f"- Findings Count: {metrics['findings_count']}")
            lines.append(f"- Unique Findings: {metrics['unique_findings']}")
            lines.append(f"- Overlap: {metrics['overlap_with_others']}")
            lines.append(f"- Avg Confidence: {metrics['average_confidence']:.2%}")
            lines.append(f"- Response Time: {metrics['response_time_ms']:.0f}ms")
        
        lines.append("\n## Coverage by Vulnerability Type")
        for vuln_type, coverage in report['coverage_by_type'].items():
            total = coverage.pop('total', 0)
            lines.append(f"\n### {vuln_type} ({total} findings)")
            for tool, count in coverage.items():
                lines.append(f"- {tool}: {count}")
        
        lines.append("\n## Complementarity Scores")
        for tool, score in report['tools_complementarity'].items():
            lines.append(f"- {tool}: {score:.1%}")
        
        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))
