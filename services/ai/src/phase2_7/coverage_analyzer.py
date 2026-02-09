"""
Coverage Analyzer

Analyzes scanning results versus total attack surface to identify
untested code paths or dataflows.
"""

from typing import Dict, Any, List

class CoverageAnalyzer:
    """
    Identifies "dark spots" in the security analysis.
    """

    def analyze_coverage(self, ast_data: Dict[str, Any], scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates coverage metrics and lists gaps.
        """
        total_funcs = len(ast_data.get("functions", []))
        scanned_funcs = len(set(f.get("line") for f in scan_results))
        
        coverage_pct = (scanned_funcs / total_funcs * 100) if total_funcs > 0 else 0
        
        return {
            "coverage_percentage": coverage_pct,
            "total_functions": total_funcs,
            "gap_count": total_funcs - scanned_funcs,
            "priority_gaps": self._identify_high_risk_gaps(ast_data, scan_results)
        }

    def _identify_high_risk_gaps(self, ast: Dict[str, Any], results: List[Dict[str, Any]]) -> List[str]:
        """Identifies functions with external input that haven't been scanned."""
        gaps = []
        for func in ast.get("functions", []):
            if func.get("uses_external") and not any(r.get("line") == func.get("line") for r in results):
                gaps.append(func.get("name"))
        return gaps
