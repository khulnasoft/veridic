"""
Historical Aggregator for Threat Scores

Stores and retrieves historical threat scores for drift detection
and trend analysis. Supports both in-memory and persistent storage.
"""

import json
import sqlite3
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import asdict

from .continuous_scoring import ThreatScore


class HistoricalAggregator:
    """
    Stores and retrieves historical threat scores.
    
    Supports:
    - In-memory storage for testing
    - SQLite persistence for production
    - Time-series queries
    - Trend analysis
    """
    
    def __init__(self, db_path: Optional[str] = None, in_memory: bool = False):
        """
        Initialize historical aggregator.
        
        Args:
            db_path: Path to SQLite database file
            in_memory: Use in-memory storage (for testing)
        """
        self.in_memory = in_memory
        
        if in_memory:
            self.scores: Dict[str, List[ThreatScore]] = {}
        else:
            self.db_path = db_path or "threat_scores.db"
            self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS threat_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                score REAL NOT NULL,
                severity_breakdown TEXT NOT NULL,
                confidence_weighted_score REAL NOT NULL,
                exploit_chains_count INTEGER NOT NULL,
                findings_count INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                INDEX idx_asset_id (asset_id),
                INDEX idx_timestamp (timestamp),
                INDEX idx_created_at (created_at)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def store_score(self, score: ThreatScore):
        """
        Store a threat score.
        
        Args:
            score: ThreatScore to store
        """
        if self.in_memory:
            if score.asset_id not in self.scores:
                self.scores[score.asset_id] = []
            self.scores[score.asset_id].append(score)
        else:
            self._store_score_db(score)
    
    def _store_score_db(self, score: ThreatScore):
        """Store score in SQLite database."""
       conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO threat_scores (
                asset_id, score, severity_breakdown,
                confidence_weighted_score, exploit_chains_count,
                findings_count, timestamp, hash, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            score.asset_id,
            score.score,
            json.dumps(score.severity_breakdown),
            score.confidence_weighted_score,
            score.exploit_chains_count,
            score.findings_count,
            score.timestamp,
            score.hash,
            datetime.utcnow().isoformat(),
        ))
        
        conn.commit()
        conn.close()
    
    def get_latest_score(self, asset_id: str) -> Optional[ThreatScore]:
        """
        Get the most recent threat score for an asset.
        
        Args:
            asset_id: Asset identifier
            
        Returns:
            Most recent ThreatScore or None
        """
        if self.in_memory:
            scores = self.scores.get(asset_id, [])
            return scores[-1] if scores else None
        else:
            return self._get_latest_score_db(asset_id)
    
    def _get_latest_score_db(self, asset_id: str) -> Optional[ThreatScore]:
        """Get latest score from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT asset_id, score, severity_breakdown,
                   confidence_weighted_score, exploit_chains_count,
                   findings_count, timestamp, hash
            FROM threat_scores
            WHERE asset_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (asset_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return ThreatScore(
            asset_id=row[0],
            score=row[1],
            severity_breakdown=json.loads(row[2]),
            confidence_weighted_score=row[3],
            exploit_chains_count=row[4],
            findings_count=row[5],
            timestamp=row[6],
            hash=row[7],
        )
    
    def get_score_history(
        self,
        asset_id: str,
        days: int = 30,
    ) -> List[ThreatScore]:
        """
        Get historical threat scores for an asset.
        
        Args:
            asset_id: Asset identifier
            days: Number of days of history to retrieve
            
        Returns:
            List of ThreatScores ordered by timestamp
        """
        if self.in_memory:
            return self.scores.get(asset_id, [])
        else:
            return self._get_score_history_db(asset_id, days)
    
    def _get_score_history_db(
        self,
        asset_id: str,
        days: int,
    ) -> List[ThreatScore]:
        """Get score history from database."""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT asset_id, score, severity_breakdown,
                   confidence_weighted_score, exploit_chains_count,
                   findings_count, timestamp, hash
            FROM threat_scores
            WHERE asset_id = ? AND created_at >= ?
            ORDER BY created_at ASC
        """, (asset_id, cutoff_date))
        
        rows = cursor.fetchall()
        conn.close()
        
        scores = []
        for row in rows:
            scores.append(ThreatScore(
                asset_id=row[0],
                score=row[1],
                severity_breakdown=json.loads(row[2]),
                confidence_weighted_score=row[3],
                exploit_chains_count=row[4],
                findings_count=row[5],
                timestamp=row[6],
                hash=row[7],
            ))
        
        return scores
    
    def get_all_assets(self) -> List[str]:
        """
        Get list of all assets with stored scores.
        
        Returns:
            List of asset IDs
        """
        if self.in_memory:
            return list(self.scores.keys())
        else:
            return self._get_all_assets_db()
    
    def _get_all_assets_db(self) -> List[str]:
        """Get all asset IDs from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT asset_id
            FROM threat_scores
            ORDER BY asset_id
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in rows]
    
    def cleanup_old_scores(self, days: int = 90):
        """
        Remove scores older than specified days.
        
        Args:
            days: Number of days to retain
        """
        if self.in_memory:
            # Not applicable for in-memory storage
            return
        
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM threat_scores
            WHERE created_at < ?
        """, (cutoff_date,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count


# Example usage
if __name__ == "__main__":
    from continuous_scoring import ContinuousScoringEngine, Finding
    
    # Create aggregator (in-memory for testing)
    aggregator = HistoricalAggregator(in_memory=True)
    
    # Create scoring engine
    engine = ContinuousScoringEngine()
    
    # Simulate multiple scores over time
    findings = [
        Finding(
            id="VULN-001",
            type="sql_injection",
            severity="critical",
            confidence=0.95,
            source="static",
        ),
    ]
    
    # Store multiple scores
    for i in range(5):
        score = engine.compute_threat_score(f"asset-{i}", findings)
        aggregator.store_score(score)
        print(f"Stored score for asset-{i}: {score.score}")
    
    # Retrieve latest score
    latest = aggregator.get_latest_score("asset-0")
    print(f"\nLatest score for asset-0: {latest.score if latest else 'None'}")
    
    # Get all assets
    assets = aggregator.get_all_assets()
    print(f"\nAll assets: {assets}")
