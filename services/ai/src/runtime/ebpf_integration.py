"""
Phase 2.1: eBPF Trace Integration
Orchestrates eBPF collection, normalization, and storage.
Provides clean interface between eBPF collector and trace_store.
"""

import logging
import uuid
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from .bpf_loader import EBPFCollector
from .event_normalizer import NormalizationPipeline
from .trace_store import TraceStore, EventFilter

logger = logging.getLogger(__name__)


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution with tracing"""
    sandbox_id: str
    execution_name: str
    capture_syscalls: List[str] = None
    timeout_seconds: int = 30
    max_events: Optional[int] = None
    
    def __post_init__(self):
        if self.capture_syscalls is None:
            # Default: capture all 5 Phase 2.1 syscalls
            self.capture_syscalls = ["execve", "openat", "read", "write", "connect"]


@dataclass
class ExecutionTrace:
    """Result of sandbox execution with runtime trace"""
    sandbox_id: str
    execution_id: str
    trace_id: str
    event_count: int
    execution_time_ms: float
    events: List[dict]
    stats: dict


class EBPFTraceOrchestrator:
    """
    High-level orchestrator for eBPF-based runtime analysis.
    Manages lifecycle: sandbox → collection → normalization → storage.
    """
    
    def __init__(self):
        self.collector = EBPFCollector()
        self.normalizer = NormalizationPipeline()
        self.trace_store = TraceStore()
        self.logger = logging.getLogger(__name__)
        self.active_traces: Dict[str, dict] = {}
    
    def start_sandbox_tracing(self, sandbox_config: SandboxConfig) -> str:
        """
        Start eBPF tracing for a sandbox.
        Returns execution_id for tracking.
        """
        execution_id = self.collector.start_sandbox_tracing(sandbox_config.sandbox_id)
        
        self.active_traces[execution_id] = {
            "sandbox_id": sandbox_config.sandbox_id,
            "config": sandbox_config,
            "events": [],
            "start_time": None,
            "end_time": None,
        }
        
        self.logger.info(
            f"Started sandbox tracing: {sandbox_config.sandbox_id} "
            f"(execution: {execution_id})"
        )
        
        return execution_id
    
    def stop_and_store_trace(self, execution_id: str) -> Optional[ExecutionTrace]:
        """
        Stop tracing, normalize events, and store in trace_store.
        Returns ExecutionTrace with all details and stats.
        """
        if execution_id not in self.active_traces:
            self.logger.error(f"Unknown execution: {execution_id}")
            return None
        
        trace_info = self.active_traces[execution_id]
        sandbox_id = trace_info["sandbox_id"]
        config = trace_info["config"]
        
        try:
            # Step 1: Capture raw syscall events
            self.logger.info(f"Capturing syscalls for {execution_id}")
            raw_events = self.collector.capture_syscalls(max_events=config.max_events)
            
            # Step 2: Normalize events
            self.logger.info(f"Normalizing {len(raw_events)} events")
            normalized_events = self.normalizer.process_events(raw_events)
            
            # Step 3: Store in trace_store
            self.logger.info(f"Storing trace in database")
            trace_id = self.trace_store.save_trace(
                sandbox_id=sandbox_id,
                execution_id=execution_id,
                events=normalized_events
            )
            
            # Build result
            result = ExecutionTrace(
                sandbox_id=sandbox_id,
                execution_id=execution_id,
                trace_id=trace_id,
                event_count=len(normalized_events),
                execution_time_ms=0.0,  # Would track actual time
                events=normalized_events,
                stats={
                    "raw_events": len(raw_events),
                    "normalized_events": len(normalized_events),
                    "normalization_rate": (
                        len(normalized_events) / len(raw_events) * 100 
                        if raw_events else 0.0
                    ),
                    "collector_stats": self.collector.loader.get_stats(),
                    "normalizer_stats": self.normalizer.get_stats(),
                }
            )
            
            self.logger.info(
                f"Trace complete: {len(normalized_events)} events stored "
                f"(trace_id: {trace_id})"
            )
            
            # Clean up active trace
            del self.active_traces[execution_id]
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error storing trace: {e}")
            return None
    
    def query_trace_events(
        self,
        sandbox_id: Optional[str] = None,
        event_type: Optional[str] = None,
        syscall_name: Optional[str] = None,
        related_findings: Optional[List[str]] = None,
    ) -> List[dict]:
        """
        Query stored events with flexible filtering.
        """
        filter_obj = EventFilter(
            sandbox_id=sandbox_id,
            event_type=event_type,
            related_findings=related_findings,
        )
        
        events = self.trace_store.query_events(filter_obj)
        
        # Additional filtering by syscall name
        if syscall_name:
            events = [
                e for e in events
                if e.get("details", {}).get("syscall_name") == syscall_name
            ]
        
        return events
    
    def analyze_determinism(
        self,
        trace_id_1: str,
        trace_id_2: str,
    ) -> dict:
        """
        Compare two traces for reproducibility.
        Returns determinism metrics.
        """
        trace1 = self.trace_store.get_trace(trace_id_1)
        trace2 = self.trace_store.get_trace(trace_id_2)
        
        if not trace1 or not trace2:
            self.logger.error("One or both traces not found")
            return {}
        
        events1 = trace1.get("events", [])
        events2 = trace2.get("events", [])
        
        # Use trace_store's determinism analyzer
        from .trace_store import DeterminismAnalyzer
        result = DeterminismAnalyzer.compare_traces(events1, events2, tolerance_ms=50)
        
        return {
            "trace_1": trace_id_1,
            "trace_2": trace_id_2,
            "determinism": result,
        }
    
    def get_orchestrator_stats(self) -> dict:
        """Return overall orchestration stats"""
        return {
            "active_traces": len(self.active_traces),
            "stored_traces": len(self.trace_store.traces),
            "collector": self.collector.get_collector_info(),
            "normalizer": self.normalizer.get_stats(),
        }


class RuntimeAnalysisService:
    """
    Service interface for Phase 2 runtime analysis.
    Exposes eBPF tracing via gRPC (as per runtime_interface.proto).
    """
    
    def __init__(self):
        self.orchestrator = EBPFTraceOrchestrator()
        self.logger = logging.getLogger(__name__)
    
    async def start_execution_tracing(
        self,
        sandbox_id: str,
        execution_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        gRPC handler: Start tracing for execution.
        """
        config = SandboxConfig(
            sandbox_id=sandbox_id,
            execution_name=execution_name or "default",
        )
        
        execution_id = self.orchestrator.start_sandbox_tracing(config)
        
        return {
            "execution_id": execution_id,
            "sandbox_id": sandbox_id,
            "status": "tracing",
        }
    
    async def stop_and_report_execution(
        self,
        execution_id: str,
    ) -> Dict[str, Any]:
        """
        gRPC handler: Stop tracing and get results.
        """
        trace = self.orchestrator.stop_and_store_trace(execution_id)
        
        if not trace:
            return {"status": "error", "message": "Failed to stop trace"}
        
        return {
            "status": "complete",
            "trace_id": trace.trace_id,
            "event_count": trace.event_count,
            "stats": trace.stats,
        }
    
    async def correlate_with_static_findings(
        self,
        trace_id: str,
        static_findings: List[dict],
    ) -> Dict[str, Any]:
        """
        gRPC handler: Correlate runtime trace with Phase 1 static findings.
        This is the bridge between Phase 1 and Phase 2 analysis.
        """
        trace = self.orchestrator.trace_store.get_trace(trace_id)
        
        if not trace:
            return {"status": "error", "message": f"Trace not found: {trace_id}"}
        
        events = trace.get("events", [])
        
        # Pre-filter events that relate to findings
        related_events = [
            e for e in events
            if any(f["id"] in e.get("related_static_findings", []) 
                   for f in static_findings)
        ]
        
        return {
            "status": "success",
            "trace_id": trace_id,
            "total_events": len(events),
            "related_events": len(related_events),
            "events": related_events[:100],  # Limit to first 100
        }
