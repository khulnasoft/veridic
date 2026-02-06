"""
Phase 2.2: mitmproxy Network Event Collector
Captures HTTP/HTTPS traffic with minimal scope:
- URL, method, status, headers (sanitized), timing, destination IP
- No request/response bodies
- No fuzzing, no replay
- Focuses on evidence for correlation to static findings
"""

import json
import logging
import time
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from datetime import datetime
from mitmproxy import http, ctx
from mitmproxy.addons.base import Addon
import hashlib
import uuid

logger = logging.getLogger(__name__)


@dataclass
class NetworkEventDetails:
    """Network event payload matching events_schema.json"""
    method: str
    url: str
    status_code: Optional[int]
    request_headers: Dict[str, str]
    response_headers: Dict[str, str]
    timing_ms: int
    destination_ip: str
    destination_port: int
    protocol: str  # http, https
    request_size: int
    response_size: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MitmproxyCollector(Addon):
    """
    mitmproxy addon for capturing HTTP/HTTPS network events.
    Integrates with Phase 2 trace storage.
    """
    
    def __init__(self, sandbox_id: str, trace_store_callback=None):
        self.sandbox_id = sandbox_id
        self.trace_store_callback = trace_store_callback
        self.request_times = {}  # Track request timing
        self.logger = logging.getLogger(__name__)
        self.version = "1.0.0"
    
    def request(self, data: http.Request) -> None:
        """Called when request is received"""
        try:
            request_id = str(uuid.uuid4())
            self.request_times[request_id] = {
                "start": time.time_ns(),
                "request": data
            }
            self.logger.debug(f"Captured request: {data.method} {data.pretty_url}")
        except Exception as e:
            self.logger.error(f"Error in request handler: {e}")
    
    def response(self, data: http.Response) -> None:
        """Called when response is received"""
        try:
            # Find matching request timing
            request_id = self._find_request_id(data.request)
            if not request_id:
                request_id = str(uuid.uuid4())
            
            timing_start = self.request_times.get(request_id, {}).get("start", time.time_ns())
            timing_end = time.time_ns()
            timing_ms = int((timing_end - timing_start) / 1_000_000)
            
            # Extract network event details
            event_details = NetworkEventDetails(
                method=data.request.method,
                url=data.request.pretty_url,
                status_code=data.status_code,
                request_headers=self._sanitize_headers(dict(data.request.headers)),
                response_headers=self._sanitize_headers(dict(data.headers)),
                timing_ms=timing_ms,
                destination_ip=data.request.host,
                destination_port=data.request.port or (443 if data.request.scheme == "https" else 80),
                protocol=data.request.scheme,
                request_size=len(data.request.content) if data.request.content else 0,
                response_size=len(data.content) if data.content else 0,
            )
            
            # Build event matching events_schema.json
            event = {
                "event_id": str(uuid.uuid4()),
                "timestamp": timing_end,  # nanoseconds
                "source": "mitmproxy",
                "event_type": "network",
                "confidence": 1.0,  # Network events are ground truth
                "collector_version": self.version,
                "sandbox_id": self.sandbox_id,
                "related_static_findings": self._extract_related_findings(event_details),
                "details": event_details.to_dict(),
                "determinism_metadata": {
                    "ordering_bucket": int(timing_end / 50_000_000),  # 50ms bucket
                    "hash": hashlib.sha256(
                        json.dumps(event_details.to_dict(), sort_keys=True).encode()
                    ).hexdigest()
                }
            }
            
            # Store event if callback provided
            if self.trace_store_callback:
                self.trace_store_callback(event)
            
            self.logger.info(f"Network event captured: {data.request.method} {data.request.host} -> {data.status_code}")
            
        except Exception as e:
            self.logger.error(f"Error in response handler: {e}")
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Remove sensitive headers from event data"""
        sensitive_keys = {
            "authorization", "cookie", "set-cookie", "x-api-key",
            "x-auth-token", "x-access-token", "password"
        }
        return {
            k: v for k, v in headers.items()
            if k.lower() not in sensitive_keys
        }
    
    def _extract_related_findings(self, event_details: NetworkEventDetails) -> list:
        """
        Extract potential vulnerability indicators from network event.
        Links to Phase 1 findings for correlation.
        """
        findings = []
        
        # SSRF indicators
        ssrf_patterns = ["localhost", "127.0.0.1", "169.254.169.254", "::1"]
        if any(pattern in event_details.destination_ip for pattern in ssrf_patterns):
            findings.append("ssrf")
        
        # SQLi indicators
        sqli_patterns = ["UNION", "SELECT", "DROP", "INSERT", "UPDATE", "DELETE"]
        if any(pattern in event_details.url.upper() for pattern in sqli_patterns):
            findings.append("sql_injection")
        
        # XSS indicators
        xss_patterns = ["<script>", "javascript:", "onclick=", "onerror="]
        for header_value in event_details.request_headers.values():
            if any(pattern in header_value for pattern in xss_patterns):
                findings.append("xss")
        
        return findings
    
    def _find_request_id(self, request: http.Request) -> Optional[str]:
        """Find matching request ID from timing tracking"""
        for req_id, timing in self.request_times.items():
            if timing.get("request") == request:
                return req_id
        return None


def create_mitmproxy_collector(sandbox_id: str, trace_store_callback=None) -> MitmproxyCollector:
    """Factory function to create configured mitmproxy collector"""
    return MitmproxyCollector(sandbox_id, trace_store_callback)
