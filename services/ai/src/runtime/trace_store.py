"""
Phase 2.0: Trace Storage (Stub)
Decoupled storage for runtime events.
Supports efficient querying and determinism analysis.
"""

import json
import logging
from dataclasses import dataclass, asdict
from typing import Optional, List
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class EventFilter:
    """Query filter for events"""
    sandbox_id: Optional[str] = None
    start_timestamp: Optional[int] = None
    end_timestamp: Optional[int] = None
    event_type: Optional[str] = None
    source: Optional[str] = None
    related_findings: Optional[List[str]] = None
    min_confidence: float = 0.0


class TraceStore:
    """
    In-memory trace storage with query support.
    In production, this would be backed by PostgreSQL/TimescaleDB.
    """
    
    def __init__(self):
        self.traces: dict[str, dict] = {}  # trace_id -> trace data
        self.events_by_sandbox: dict[str, list] = defaultdict(list)
        self.events_by_finding: dict[str, list] = defaultdict(list)
        self.logger = logging.getLogger(__name__)
    
    def save_trace(self, sandbox_id: str, execution_id: str, events: list) -> str:
        """Save trace with indexed lookups for querying"""
        trace_id = f"trace_{sandbox_id}_{execution_id}"
        
        trace_data = {
            "trace_id": trace_id,
            "sandbox_id": sandbox_id,
            "execution_id": execution_id,
            "event_count": len(events),
            "saved_at": int(datetime.utcnow().timestamp() * 1_000_000_000),
            "events": events,
        }
        
        self.traces[trace_id] = trace_data
        
        # Index by sandbox
        self.events_by_sandbox[sandbox_id].extend(events)
        
        # Index by finding
        for event in events:
            related = event.get("related_static_findings", [])
            for finding in related:
                self.events_by_finding[finding].append(event)
        
        self.logger.info(f"Trace saved: {trace_id} ({len(events)} events)")
        return trace_id
    
    def query_events(self, filter: EventFilter) -> List[dict]:
        """Query events with filtering"""
        results = []
        
        # Start with sandbox-specific events if provided
        if filter.sandbox_id:
            candidates = self.events_by_sandbox.get(filter.sandbox_id, [])
        else:
            # Flatten all events
            candidates = [e for events in self.events_by_sandbox.values() for e in events]
        
        # Apply filters
        for event in candidates:
            # Timestamp filter
            if filter.start_timestamp and event.get("timestamp", 0) < filter.start_timestamp:
                continue
            if filter.end_timestamp and event.get("timestamp", 0) > filter.end_timestamp:
                continue
            
            # Event type filter
            if filter.event_type and event.get("event_type") != filter.event_type:
                continue
            
            # Source filter
            if filter.source and event.get("source") != filter.source:
                continue
            
            # Confidence filter
            if event.get("confidence", 1.0) < filter.min_confidence:
                continue
            
            # Related findings filter
            if filter.related_findings:
                event_findings = set(event.get("related_static_findings", []))
                if not event_findings.intersection(filter.related_findings):
                    continue
            
            results.append(event)
        
        return results
    
    def get_events_for_finding(self, finding_id: str) -> List[dict]:
        """Get all events related to a specific finding"""
        return self.events_by_finding.get(finding_id, [])
    
    def get_trace(self, trace_id: str) -> Optional[dict]:
        """Retrieve trace by ID"""
        return self.traces.get(trace_id)
    
    def export_trace(self, trace_id: str) -> str:
        """Export trace as JSON string"""
        trace = self.get_trace(trace_id)
        if not trace:
            raise ValueError(f"Unknown trace: {trace_id}")
        return json.dumps(trace, indent=2, default=str)


class DeterminismAnalyzer:
    """
    Analyze determinism of captured events.
    Key insight: Event ordering has ±50ms tolerance window.
    """
    
    @staticmethod
    def bucket_by_time(events: list, bucket_size_ms: int = 50) -> dict:
        """Group events into time buckets for ordering tolerance"""
        buckets = defaultdict(list)
        for event in events:
            timestamp = event.get("timestamp", 0)
            bucket = (timestamp // (bucket_size_ms * 1_000_000)) * (bucket_size_ms * 1_000_000)
            buckets[bucket].append(event)
        return buckets
    
    @staticmethod
    def compute_event_hash(event: dict) -> str:
        """Compute hash of event (excluding timestamp for determinism)"""
        import hashlib
        event_copy = {k: v for k, v in event.items() if k != "timestamp"}
        event_json = json.dumps(event_copy, sort_keys=True, default=str)
        return hashlib.sha256(event_json.encode()).hexdigest()
    
    @staticmethod
    def compare_traces(trace1: list, trace2: list, tolerance_ms: int = 50) -> dict:
        """
        Compare two traces for reproducibility.
        Allows ±50ms event reordering.
        """
        buckets1 = DeterminismAnalyzer.bucket_by_time(trace1, tolerance_ms)
        buckets2 = DeterminismAnalyzer.bucket_by_time(trace2, tolerance_ms)
        
        hashes1 = {DeterminismAnalyzer.compute_event_hash(e) for bucket in buckets1.values() for e in bucket}
        hashes2 = {DeterminismAnalyzer.compute_event_hash(e) for bucket in buckets2.values() for e in bucket}
        
        match_count = len(hashes1 & hashes2)
        total_count = len(hashes1 | hashes2)
        
        return {
            "match_count": match_count,
            "total_count": total_count,
            "determinism_score": match_count / total_count if total_count > 0 else 0.0,
            "only_in_trace1": hashes1 - hashes2,
            "only_in_trace2": hashes2 - hashes1,
        }
