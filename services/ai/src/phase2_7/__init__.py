"""
Phase 2.7: Continuous Red-Team AI (Preview)

This module implements the strategy for autonomous attack generation
and coverage analysis.
"""

from .attack_planner import AttackPlanner
from .strategy_mutator import StrategyMutator
from .redteam_loop import RedTeamLoop

__all__ = [
    "AttackPlanner",
    "StrategyMutator",
    "RedTeamLoop",
]

__version__ = "2.7.0-preview"
