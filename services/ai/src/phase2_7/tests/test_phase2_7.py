"""
Verification suite for Phase 2.7 (Preview)
"""

import pytest
from ..redteam_loop import RedTeamLoop

def test_redteam_loop_states():
    loop = RedTeamLoop("test-target")
    assert loop.active == False
    
    #Iteration while inactive
    result = loop.execute_iteration([], {})
    assert result["status"] == "INACTIVE"
    
    #Enable and test
    loop.enable()
    assert loop.active == True
    
    mock_ast = {"functions": [{"name": "login", "line": 10, "uses_external": True}]}
    mock_findings = []
    
    res = loop.execute_iteration(mock_findings, mock_ast)
    assert res["status"] == "COMPLETED"
    assert res["coverage_stats"]["gap_count"] == 1
    assert "login" in res["coverage_stats"]["priority_gaps"]

if __name__ == "__main__":
    test_redteam_loop_states()
